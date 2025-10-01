from frappe.contacts.doctype.address.address import get_address_display
import frappe
from location_based_series.utils import (
    get_filtered_warehouses_for_location, 
    get_filtered_warehouses_for_shipping_location,
    get_filtered_addresses_for_shipping_location,
    get_filtered_warehouses_for_dispatch_location,
    get_filtered_addresses_for_dispatch_location,
    auto_set_warehouse_for_location,
    auto_set_warehouse_for_shipping_location,
    auto_set_shipping_address_for_shipping_location,
    validate_warehouse_against_location,
    validate_warehouse_against_shipping_location,
    validate_shipping_address_against_shipping_location,
    validate_warehouse_against_dispatch_location,
    validate_dispatch_address_against_dispatch_location,
    set_place_of_supply_for_purchase_doc
)

def validate_doc(doc, method):
    # STEP 1: Check if 'Location' is enabled as an Accounting Dimension
    dim_exists = frappe.db.exists("Accounting Dimension", {
        "document_type": "Location",
        "disabled": 0
    })
    if not dim_exists:
        frappe.throw("Please enable 'Location' as an active Accounting Dimension before using it in transactions.")

    # STEP 2: Validate selected Location
    if doc.location:
        loc = frappe.get_doc("Location", doc.location)

        if not loc.lbs_location_code:
            frappe.throw("Selected Location must have a Location Code.")
        if not loc.linked_address:
            frappe.throw("Selected Location must have a Linked Address.")

        # Auto-fill location code
        doc.lbs_location_code = loc.lbs_location_code

        # Handle based on document type
        purchase_doctypes = ["Purchase Invoice", "Purchase Receipt", "Purchase Order"]
        if doc.doctype in purchase_doctypes:
            # Only set billing address for purchase documents, shipping address should be manual
            doc.billing_address = loc.linked_address
            doc.billing_address_display = get_address_display(loc.linked_address)

            # ✅ Set company GSTIN from billing address
            gstin = frappe.db.get_value("Address", loc.linked_address, "gstin")
            if gstin:
                doc.company_gstin = gstin

            # Clear any auto-filled shipping address if it matches billing address
            if hasattr(doc, 'shipping_address') and doc.shipping_address == loc.linked_address:
                doc.shipping_address = ''
                doc.shipping_address_display = ''
        else:
            doc.company_address = loc.linked_address
            doc.company_address_display = get_address_display(loc.linked_address)

            # ✅ Set company GSTIN from company address
            gstin = frappe.db.get_value("Address", loc.linked_address, "gstin")
            if gstin:
                doc.company_gstin = gstin
    else:
        frappe.throw("Select Location before Saving")

    # STEP 3: Handle shipping location validation if present
    if hasattr(doc, 'shipping_location') and doc.shipping_location:
        # Validate shipping location
        shipping_loc = frappe.get_doc("Location", doc.shipping_location)
        
        if not shipping_loc.linked_address:
            frappe.throw("Selected Shipping Location must have a Linked Address.")
        
        if not shipping_loc.linked_warehouse:
            frappe.throw("Selected Shipping Location must have a Linked Warehouse.")
        
        # Auto-set shipping address if not already set
        if hasattr(doc, 'shipping_address') and not doc.shipping_address:
            doc.shipping_address = shipping_loc.linked_address
            doc.shipping_address_display = get_address_display(shipping_loc.linked_address)

    # STEP 3.5: Handle dispatch location validation if present
    if hasattr(doc, 'dispatch_location') and doc.dispatch_location:
        # Validate dispatch location
        dispatch_loc = frappe.get_doc("Location", doc.dispatch_location)
        
        if not dispatch_loc.linked_address:
            frappe.throw("Selected Dispatch Location must have a Linked Address.")
        
        if not dispatch_loc.linked_warehouse:
            frappe.throw("Selected Dispatch Location must have a Linked Warehouse.")
        
        # Auto-set dispatch address if not already set
        if hasattr(doc, 'dispatch_address_name') and not doc.dispatch_address_name:
            doc.dispatch_address_name = dispatch_loc.linked_address
            doc.dispatch_address = get_address_display(dispatch_loc.linked_address)

    # STEP 4: Handle warehouse filtering and validation
    # Use shipping location for warehouse filtering if available, otherwise use regular location
    handle_combined_location_validation(doc)

    # STEP 5: Set Place of Supply for Purchase documents
    # This sets place_of_supply based on location's linked address (billing address)
    set_place_of_supply_for_purchase_doc(doc)

    # STEP 6: Lock fields after first save
    if not doc.is_new():
        old = frappe.get_doc(doc.doctype, doc.name)

        # Ensure linked address doesn't change after first save
        if doc.location:
            loc = frappe.get_doc("Location", doc.location)
            expected_address = loc.linked_address
            current_address_field = "billing_address" if doc.doctype in purchase_doctypes else "company_address"
            if getattr(doc, current_address_field) != expected_address:
                frappe.throw(f"❌ Field {current_address_field} cannot be changed after saving.")

        # Ensure shipping location and address don't change after first save (only in draft state)
        if hasattr(doc, 'shipping_location') and doc.shipping_location:
            # Allow shipping_location changes only in draft state
            if doc.docstatus != 0:  # Not in draft state
                if doc.shipping_location != old.get('shipping_location'):
                    frappe.throw("❌ Field 'shipping_location' cannot be changed after document is submitted.")
                
                if hasattr(doc, 'shipping_address') and doc.shipping_address != old.get('shipping_address'):
                    frappe.throw("❌ Field 'shipping_address' cannot be changed after document is submitted.")

        # Ensure dispatch location and address don't change after first save (only in draft state)
        if hasattr(doc, 'dispatch_location') and doc.dispatch_location:
            # Allow dispatch_location changes only in draft state
            if doc.docstatus != 0:  # Not in draft state
                if doc.dispatch_location != old.get('dispatch_location'):
                    frappe.throw("❌ Field 'dispatch_location' cannot be changed after document is submitted.")
                
                if hasattr(doc, 'dispatch_address_name') and doc.dispatch_address_name != old.get('dispatch_address_name'):
                    frappe.throw("❌ Field 'dispatch_address_name' cannot be changed after document is submitted.")

        for field in ["location", "is_return", "is_rate_adjustment"]:
            if hasattr(doc, field) and doc.get(field) != old.get(field):
                frappe.throw(f"❌ Field '{field}' cannot be changed after saving.")


def handle_warehouse_validation(doc):
    """
    Handle warehouse filtering and validation based on location.
    Auto-select warehouse if there's only one valid option.
    Validate warehouse selection against location.
    """
    if not doc.location:
        return
    
    # Get valid warehouses for this location
    valid_warehouses = get_filtered_warehouses_for_location(doc.location)
    
    if not valid_warehouses:
        frappe.throw(f"No valid warehouses found for location '{doc.location}'. Please ensure the location has a linked warehouse.")
    
    # Auto-set warehouse fields if there's only one valid warehouse
    if len(valid_warehouses) == 1:
        single_warehouse = valid_warehouses[0]
        
        # Auto-set document level warehouse fields if they exist and are empty
        # Exclude target_warehouse from autofill to prevent conflict with delivery warehouse
        warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse']
        for field in warehouse_fields:
            if hasattr(doc, field) and not getattr(doc, field, None):
                setattr(doc, field, single_warehouse)
        
        # Auto-set warehouse in child tables
        auto_set_child_table_warehouses(doc, single_warehouse, valid_warehouses)
    
    # Validate all warehouse fields against location
    validate_document_warehouses(doc, valid_warehouses)


def handle_shipping_location_validation(doc):
    """
    Handle warehouse filtering and validation based on shipping location.
    Auto-select warehouse and shipping address if there's only one valid option.
    Validate warehouse selection and shipping address against shipping location.
    """
    if not doc.shipping_location:
        return
    
    # Get valid warehouses for this shipping location
    valid_warehouses = get_filtered_warehouses_for_shipping_location(doc.shipping_location)
    
    if not valid_warehouses:
        frappe.throw(f"No valid warehouses found for shipping location '{doc.shipping_location}'. Please ensure the shipping location has a linked warehouse.")
    
    # Auto-set warehouse fields if there's only one valid warehouse
    if len(valid_warehouses) == 1:
        single_warehouse = valid_warehouses[0]
        
        # Auto-set document level warehouse fields if they exist and are empty
        # Exclude target_warehouse from autofill to prevent conflict with delivery warehouse
        warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse']
        for field in warehouse_fields:
            if hasattr(doc, field) and not getattr(doc, field, None):
                setattr(doc, field, single_warehouse)
        
        # Auto-set warehouse in child tables
        auto_set_child_table_warehouses(doc, single_warehouse, valid_warehouses)
    
    # Validate all warehouse fields against shipping location
    validate_document_warehouses_for_shipping_location(doc, valid_warehouses)
    
    # Handle shipping address validation and auto-selection
    handle_shipping_address_validation(doc)


def handle_shipping_address_validation(doc):
    """
    Handle shipping address validation and auto-selection based on shipping location.
    """
    if not doc.shipping_location:
        return
    
    # Get valid addresses for this shipping location
    valid_addresses = get_filtered_addresses_for_shipping_location(doc.shipping_location)
    
    if not valid_addresses:
        frappe.throw(f"No valid addresses found for shipping location '{doc.shipping_location}'. Please ensure the shipping location has a linked address.")
    
    # Auto-set shipping address if there's only one valid address
    if len(valid_addresses) == 1:
        single_address = valid_addresses[0]
        
        # Auto-set shipping address field if it exists and is empty
        if hasattr(doc, 'shipping_address') and not doc.shipping_address:
            doc.shipping_address = single_address
    
    # Validate shipping address against shipping location
    validate_shipping_address_against_shipping_location(doc)


def auto_set_child_table_warehouses(doc, single_warehouse, valid_warehouses):
    """Auto-set warehouse in child tables if there's only one valid warehouse."""
    child_table_fields = ['items', 'item_details', 'stock_entries']
    warehouse_fields_in_child = ['warehouse', 's_warehouse', 't_warehouse', 'source_warehouse']
    
    for table_field in child_table_fields:
        if hasattr(doc, table_field):
            child_table = getattr(doc, table_field, [])
            if child_table:  # Only process if table has rows
                for row in child_table:
                    for wh_field in warehouse_fields_in_child:
                        if hasattr(row, wh_field) and not getattr(row, wh_field, None):
                            setattr(row, wh_field, single_warehouse)


def validate_document_warehouses(doc, valid_warehouses):
    """Validate all warehouse fields in document and child tables."""
    
    # Validate document level warehouse fields
    # Exclude target_warehouse from validation as it's optional and can be different from location
    warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse']
    for field in warehouse_fields:
        if hasattr(doc, field):
            warehouse = getattr(doc, field, None)
            if warehouse and warehouse not in valid_warehouses:
                frappe.throw(f"Warehouse '{warehouse}' in field '{field}' is not valid for location '{doc.location}'. Valid warehouses are: {', '.join(valid_warehouses)}")
    
    # Validate warehouse fields in child tables
    child_table_fields = ['items', 'item_details', 'stock_entries']
    # Exclude target_warehouse from validation as it's optional and can be different from location
    warehouse_fields_in_child = ['warehouse', 's_warehouse', 't_warehouse', 'source_warehouse']
    
    for table_field in child_table_fields:
        if hasattr(doc, table_field):
            child_table = getattr(doc, table_field, [])
            if child_table:  # Only process if table has rows
                for idx, row in enumerate(child_table):
                    for wh_field in warehouse_fields_in_child:
                        if hasattr(row, wh_field):
                            warehouse = getattr(row, wh_field, None)
                            if warehouse and warehouse not in valid_warehouses:
                                frappe.throw(f"Warehouse '{warehouse}' in row {idx + 1}, field '{wh_field}' is not valid for location '{doc.location}'. Valid warehouses are: {', '.join(valid_warehouses)}")


def validate_document_warehouses_for_shipping_location(doc, valid_warehouses):
    """Validate all warehouse fields in document and child tables against shipping location."""
    
    # Validate document level warehouse fields
    # Exclude target_warehouse from validation as it's optional and can be different from shipping location
    warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse']
    for field in warehouse_fields:
        if hasattr(doc, field):
            warehouse = getattr(doc, field, None)
            if warehouse and warehouse not in valid_warehouses:
                frappe.throw(f"Warehouse '{warehouse}' in field '{field}' is not valid for shipping location '{doc.shipping_location}'. Valid warehouses are: {', '.join(valid_warehouses)}")
    
    # Validate warehouse fields in child tables
    child_table_fields = ['items', 'item_details', 'stock_entries']
    # Exclude target_warehouse from validation as it's optional and can be different from shipping location
    warehouse_fields_in_child = ['warehouse', 's_warehouse', 't_warehouse', 'source_warehouse']
    
    for table_field in child_table_fields:
        if hasattr(doc, table_field):
            child_table = getattr(doc, table_field, [])
            if child_table:  # Only process if table has rows
                for idx, row in enumerate(child_table):
                    for wh_field in warehouse_fields_in_child:
                        if hasattr(row, wh_field):
                            warehouse = getattr(row, wh_field, None)
                            if warehouse and warehouse not in valid_warehouses:
                                frappe.throw(f"Warehouse '{warehouse}' in row {idx + 1}, field '{wh_field}' is not valid for shipping location '{doc.shipping_location}'. Valid warehouses are: {', '.join(valid_warehouses)}")


def handle_combined_location_validation(doc):
    """
    Handle validation for documents that can have location, shipping_location, and dispatch_location.
    This function determines which location to use for warehouse filtering based on the document's configuration.
    """
    # Check if document has dispatch_location field and if it's set
    has_dispatch_location = hasattr(doc, 'dispatch_location') and doc.dispatch_location
    
    # Check if document has shipping_location field and if it's set
    has_shipping_location = hasattr(doc, 'shipping_location') and doc.shipping_location
    
    if has_dispatch_location:
        # Use dispatch location for warehouse filtering
        handle_dispatch_location_validation(doc)
    elif has_shipping_location:
        # Use shipping location for warehouse filtering
        handle_shipping_location_validation(doc)
    elif hasattr(doc, 'location') and doc.location:
        # Use regular location for warehouse filtering
        handle_warehouse_validation(doc)
    else:
        # No location specified, skip validation
        pass


def handle_dispatch_location_validation(doc):
    """
    Handle warehouse filtering and validation based on dispatch location.
    Auto-select warehouse and dispatch address if there's only one valid option.
    Validate warehouse selection and dispatch address against dispatch location.
    """
    if not doc.dispatch_location:
        return
    
    # Get valid warehouses for this dispatch location
    valid_warehouses = get_filtered_warehouses_for_dispatch_location(doc.dispatch_location)
    
    if not valid_warehouses:
        frappe.throw(f"No valid warehouses found for dispatch location '{doc.dispatch_location}'. Please ensure the dispatch location has a linked warehouse.")
    
    # Auto-set warehouse fields if there's only one valid warehouse
    if len(valid_warehouses) == 1:
        single_warehouse = valid_warehouses[0]
        
        # Auto-set document level warehouse fields if they exist and are empty
        # Exclude target_warehouse from autofill to prevent conflict with delivery warehouse
        warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse']
        for field in warehouse_fields:
            if hasattr(doc, field) and not getattr(doc, field, None):
                setattr(doc, field, single_warehouse)
        
        # Auto-set warehouse in child tables
        auto_set_child_table_warehouses(doc, single_warehouse, valid_warehouses)
    
    # Validate all warehouse fields against dispatch location
    validate_document_warehouses_for_dispatch_location(doc, valid_warehouses)
    
    # Handle dispatch address validation and auto-selection
    handle_dispatch_address_validation(doc)


def handle_dispatch_address_validation(doc):
    """
    Handle dispatch address validation and auto-selection based on dispatch location.
    """
    if not doc.dispatch_location:
        return
    
    # Get valid addresses for this dispatch location
    valid_addresses = get_filtered_addresses_for_dispatch_location(doc.dispatch_location)
    
    if not valid_addresses:
        frappe.throw(f"No valid addresses found for dispatch location '{doc.dispatch_location}'. Please ensure the dispatch location has a linked address.")
    
    # Auto-set dispatch address if there's only one valid address
    if len(valid_addresses) == 1:
        single_address = valid_addresses[0]
        
        # Auto-set dispatch address field if it exists and is empty
        if hasattr(doc, 'dispatch_address_name') and not doc.dispatch_address_name:
            doc.dispatch_address_name = single_address
    
    # Validate dispatch address against dispatch location
    validate_dispatch_address_against_dispatch_location(doc)


def validate_document_warehouses_for_dispatch_location(doc, valid_warehouses):
    """Validate all warehouse fields in document and child tables against dispatch location."""
    
    # Validate document level warehouse fields
    # Exclude target_warehouse from validation as it's optional and can be different from dispatch location
    warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse']
    for field in warehouse_fields:
        if hasattr(doc, field):
            warehouse = getattr(doc, field, None)
            if warehouse and warehouse not in valid_warehouses:
                frappe.throw(f"Warehouse '{warehouse}' in field '{field}' is not valid for dispatch location '{doc.dispatch_location}'. Valid warehouses are: {', '.join(valid_warehouses)}")
    
    # Validate warehouse fields in child tables
    child_table_fields = ['items', 'item_details', 'stock_entries']
    # Exclude target_warehouse from validation as it's optional and can be different from dispatch location
    warehouse_fields_in_child = ['warehouse', 's_warehouse', 't_warehouse', 'source_warehouse']
    
    for table_field in child_table_fields:
        if hasattr(doc, table_field):
            child_table = getattr(doc, table_field, [])
            if child_table:  # Only process if table has rows
                for idx, row in enumerate(child_table):
                    for wh_field in warehouse_fields_in_child:
                        if hasattr(row, wh_field):
                            warehouse = getattr(row, wh_field, None)
                            if warehouse and warehouse not in valid_warehouses:
                                frappe.throw(f"Warehouse '{warehouse}' in row {idx + 1}, field '{wh_field}' is not valid for dispatch location '{doc.dispatch_location}'. Valid warehouses are: {', '.join(valid_warehouses)}")
