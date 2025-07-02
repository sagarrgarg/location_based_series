from frappe.contacts.doctype.address.address import get_address_display
import frappe
from location_based_series.utils import (
    get_filtered_warehouses_for_location, 
    auto_set_warehouse_for_location,
    validate_warehouse_against_location
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
            doc.billing_address = loc.linked_address
            doc.billing_address_display = get_address_display(loc.linked_address)

            # ✅ Set company GSTIN from billing address
            gstin = frappe.db.get_value("Address", loc.linked_address, "gstin")
            if gstin:
                doc.company_gstin = gstin
        else:
            doc.company_address = loc.linked_address
            doc.company_address_display = get_address_display(loc.linked_address)

            # ✅ Set company GSTIN from company address
            gstin = frappe.db.get_value("Address", loc.linked_address, "gstin")
            if gstin:
                doc.company_gstin = gstin
    else:
        frappe.throw("Select Location before Saving")

    # STEP 3: Handle warehouse filtering and validation based on location
    handle_warehouse_validation(doc)

    # STEP 4: Lock fields after first save
    if not doc.is_new():
        old = frappe.get_doc(doc.doctype, doc.name)

        # Ensure linked address doesn't change after first save
        if doc.location:
            loc = frappe.get_doc("Location", doc.location)
            expected_address = loc.linked_address
            current_address_field = "billing_address" if doc.doctype in purchase_doctypes else "company_address"
            if getattr(doc, current_address_field) != expected_address:
                frappe.throw(f"❌ Field {current_address_field} cannot be changed after saving.")

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
        warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse', 'target_warehouse']
        for field in warehouse_fields:
            if hasattr(doc, field) and not getattr(doc, field, None):
                setattr(doc, field, single_warehouse)
        
        # Auto-set warehouse in child tables
        auto_set_child_table_warehouses(doc, single_warehouse, valid_warehouses)
    
    # Validate all warehouse fields against location
    validate_document_warehouses(doc, valid_warehouses)


def auto_set_child_table_warehouses(doc, single_warehouse, valid_warehouses):
    """Auto-set warehouse in child tables if there's only one valid warehouse."""
    
    # Common child table fields that contain warehouses
    child_table_fields = ['items', 'item_details', 'stock_entries']
    warehouse_fields_in_child = ['warehouse', 's_warehouse', 't_warehouse', 'source_warehouse', 'target_warehouse']
    
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
    warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse', 'target_warehouse']
    for field in warehouse_fields:
        if hasattr(doc, field):
            warehouse = getattr(doc, field, None)
            if warehouse and warehouse not in valid_warehouses:
                frappe.throw(f"Warehouse '{warehouse}' in field '{field}' is not valid for location '{doc.location}'. Valid warehouses are: {', '.join(valid_warehouses)}")
    
    # Validate warehouse fields in child tables
    child_table_fields = ['items', 'item_details', 'stock_entries']
    warehouse_fields_in_child = ['warehouse', 's_warehouse', 't_warehouse', 'source_warehouse', 'target_warehouse']
    
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
