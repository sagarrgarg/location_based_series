import frappe
from frappe.utils.nestedset import get_descendants_of


def _get_location_based_query_result(location_type, location_name, doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Generic function to handle location-based queries for both shipping and dispatch locations.
    This reduces code redundancy while maintaining exact same logic.
    
    Args:
        location_type: 'shipping', 'dispatch', or 'main'
        location_name: The actual location name
        doctype: The doctype to query (Warehouse or Address)
        txt: Search text
        searchfield: Field to search in
        start: Start position
        page_len: Page length
        filters: Additional filters
        **kwargs: Additional arguments
    """
    
    if not location_name:
        return []
    
    # Get the location document
    try:
        loc_doc = frappe.get_doc("Location", location_name)
    except frappe.DoesNotExistError:
        return []
    
    # Determine which field to check based on doctype
    if doctype == "Warehouse":
        linked_field = 'linked_warehouse'
        result_doctype = "Warehouse"
        result_fields = ["name", "warehouse_name"]
    elif doctype == "Address":
        linked_field = 'linked_address'
        result_doctype = "Address"
        result_fields = ["name", "address_title"]
    else:
        return []
    
    # Check if location has the required linked field
    linked_value = getattr(loc_doc, linked_field, None)
    if not linked_value:
        return []
    
    # Check if the linked value exists
    if not frappe.db.exists(result_doctype, linked_value):
        return []
    
    # Base filters
    filters_dict = {
        "name": linked_value
    }
    
    # Add text search if provided
    if txt:
        if txt.lower() not in linked_value.lower():
            return []
    
    # Get result using frappe.get_all
    result = frappe.get_all(result_doctype,
                           filters=filters_dict,
                           fields=result_fields,
                           order_by="name",
                           limit_start=start,
                           limit_page_length=page_len,
                           as_list=True)
    
    return result


def _get_filtered_warehouses_for_location_generic(location):
    """
    Generic function to get filtered warehouses for any location type.
    This reduces code redundancy while maintaining exact same logic.
    """
    if not location:
        return []
    
    try:
        loc_doc = frappe.get_doc("Location", location)
    except frappe.DoesNotExistError:
        return []
    except Exception as e:
        frappe.logger().error(f"Error getting location {location}: {str(e)}")
        return []
    
    linked_warehouse = getattr(loc_doc, 'linked_warehouse', None)
    if not linked_warehouse:
        return []
    
    # Get warehouse info in one call
    warehouse_info = frappe.db.get_value("Warehouse", linked_warehouse, 
                                        ["name", "is_group", "disabled"], as_dict=True)
    
    if not warehouse_info:
        return []
    
    if warehouse_info.is_group:
        # Get all non-group descendants
        try:
            descendant_warehouses = get_descendants_of("Warehouse", linked_warehouse, 
                                                     ignore_permissions=True)
            if descendant_warehouses:
                non_group_descendants = frappe.get_all("Warehouse", 
                                                      filters={
                                                          "name": ["in", descendant_warehouses],
                                                          "is_group": 0,
                                                          "disabled": 0
                                                      },
                                                      pluck="name")
                return non_group_descendants
        except Exception:
            pass
    else:
        # If it's a non-group warehouse, only return that warehouse if not disabled
        if not warehouse_info.disabled:
            return [linked_warehouse]
    
    return []


def _get_filtered_addresses_for_location_generic(location):
    """
    Generic function to get filtered addresses for any location type.
    This reduces code redundancy while maintaining exact same logic.
    """
    if not location:
        return []
    
    try:
        loc_doc = frappe.get_doc("Location", location)
    except frappe.DoesNotExistError:
        return []
    except Exception as e:
        frappe.logger().error(f"Error getting location {location}: {str(e)}")
        return []
    
    linked_address = getattr(loc_doc, 'linked_address', None)
    if not linked_address:
        return []
    
    # Check if the linked address exists
    if frappe.db.exists("Address", linked_address):
        return [linked_address]
    
    return []


def _validate_warehouse_against_location_generic(doc, location_field, warehouse_field="warehouse"):
    """
    Generic function to validate warehouse against any location type.
    This reduces code redundancy while maintaining exact same logic.
    """
    location = getattr(doc, location_field, None)
    if not location:
        return
    
    warehouse = getattr(doc, warehouse_field, None)
    if not warehouse:
        return
    
    valid_warehouses = _get_filtered_warehouses_for_location_generic(location)
    
    if warehouse not in valid_warehouses:
        frappe.throw(f"Warehouse '{warehouse}' is not valid for {location_field} '{location}'. Valid warehouses are: {', '.join(valid_warehouses)}")


def _validate_address_against_location_generic(doc, location_field, address_field):
    """
    Generic function to validate address against any location type.
    This reduces code redundancy while maintaining exact same logic.
    """
    location = getattr(doc, location_field, None)
    if not location:
        return
    
    address = getattr(doc, address_field, None)
    if not address:
        return
    
    valid_addresses = _get_filtered_addresses_for_location_generic(location)
    
    if address not in valid_addresses:
        frappe.throw(f"Address '{address}' is not valid for {location_field} '{location}'. Valid addresses are: {', '.join(valid_addresses)}")


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Server-side query method to filter warehouses based on location.
    If location has a group warehouse, show only descendants.
    If location has a non-group warehouse, show only that warehouse.
    """
    
    # Get the location from filters (passed from the form)
    location = filters.get("location") if filters else None
    
    if not location:
        # If no location specified, return empty result to force location selection
        return []
    
    # Get the location document to find the linked warehouse
    try:
        loc_doc = frappe.get_doc("Location", location)
    except frappe.DoesNotExistError:
        return []
    
    # Check if location has a linked warehouse
    linked_warehouse = getattr(loc_doc, 'linked_warehouse', None)
    if not linked_warehouse:
        # No linked warehouse, return empty
        return []
    
    # Check if the linked warehouse exists and get its properties
    warehouse_info = frappe.db.get_value("Warehouse", linked_warehouse, 
                                        ["name", "is_group", "company"], as_dict=True)
    
    if not warehouse_info:
        return []
    
    # Determine which warehouses are valid for this location
    valid_warehouses = []
    
    if warehouse_info.is_group:
        # If it's a group warehouse, get all descendants
        try:
            descendant_warehouses = get_descendants_of("Warehouse", linked_warehouse, 
                                                     ignore_permissions=True)
            if descendant_warehouses:
                non_group_descendants = frappe.get_all("Warehouse", 
                                                      filters={
                                                          "name": ["in", descendant_warehouses],
                                                          "is_group": 0,
                                                          "disabled": 0
                                                      },
                                                      pluck="name")
                valid_warehouses = non_group_descendants
        except Exception:
            pass
    else:
        # If it's a non-group warehouse, only show that warehouse
        if frappe.db.get_value("Warehouse", linked_warehouse, "disabled") != 1:
            valid_warehouses = [linked_warehouse]
    
    if not valid_warehouses:
        return []
    
    # Base filters for frappe.get_all
    filters_dict = {
        "name": ["in", valid_warehouses],
        "disabled": 0
    }
    
    # Add text search if provided
    if txt:
        # Filter valid warehouses by text search
        matching_warehouses = [w for w in valid_warehouses if txt.lower() in w.lower()]
        if matching_warehouses:
            filters_dict["name"] = ["in", matching_warehouses]
        else:
            return []
    
    # Get warehouses using frappe.get_all for better handling
    result = frappe.get_all("Warehouse",
                           filters=filters_dict,
                           fields=["name", "warehouse_name"],
                           order_by="name",
                           limit_start=start,
                           limit_page_length=page_len,
                           as_list=True)
    
    return result


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def shipping_location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Server-side query method to filter warehouses based on shipping location.
    This is similar to location_based_warehouse_query but uses shipping_location.
    """
    
    # Get the shipping location from filters
    shipping_location = filters.get("shipping_location") if filters else None
    
    if not shipping_location:
        # If no shipping location specified, return empty result
        return []
    
    # Use the same logic as location_based_warehouse_query but with shipping_location
    filters_with_location = dict(filters)
    filters_with_location['location'] = shipping_location
    
    return location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters_with_location, **kwargs)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def shipping_location_based_address_query(doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Server-side query method to filter addresses based on shipping location.
    Returns addresses that are linked to the shipping location.
    """
    shipping_location = filters.get("shipping_location") if filters else None
    return _get_location_based_query_result("shipping", shipping_location, "Address", txt, searchfield, start, page_len, filters, **kwargs)


def get_filtered_warehouses_for_location(location):
    """
    Get list of valid warehouses for a given location.
    Returns a list of warehouse names that should be available for the location.
    """
    if not location:
        return []
    
    try:
        loc_doc = frappe.get_doc("Location", location)
    except frappe.DoesNotExistError:
        return []
    except Exception as e:
        frappe.logger().error(f"Error getting location {location}: {str(e)}")
        return []
    
    linked_warehouse = getattr(loc_doc, 'linked_warehouse', None)
    if not linked_warehouse:
        return []
    
    # Get warehouse info in one call
    warehouse_info = frappe.db.get_value("Warehouse", linked_warehouse, 
                                        ["name", "is_group", "disabled"], as_dict=True)
    
    if not warehouse_info:
        return []
    
    if warehouse_info.is_group:
        # Get all non-group descendants
        try:
            descendant_warehouses = get_descendants_of("Warehouse", linked_warehouse, 
                                                     ignore_permissions=True)
            if descendant_warehouses:
                non_group_descendants = frappe.get_all("Warehouse", 
                                                      filters={
                                                          "name": ["in", descendant_warehouses],
                                                          "is_group": 0,
                                                          "disabled": 0
                                                      },
                                                      pluck="name")
                return non_group_descendants
        except Exception:
            return []
    else:
        # Return the single warehouse only if it's not disabled
        if warehouse_info.disabled != 1:
            return [linked_warehouse]
        return []
    
    return []


def get_filtered_warehouses_for_shipping_location(shipping_location):
    """
    Get list of valid warehouses for a given shipping location.
    This is a wrapper around get_filtered_warehouses_for_location.
    """
    return get_filtered_warehouses_for_location(shipping_location)


@frappe.whitelist()
def get_filtered_addresses_for_shipping_location(shipping_location):
    """
    Get list of valid addresses for a given shipping location.
    Returns a list of address names that should be available for the shipping location.
    """
    if not shipping_location:
        return []
    
    try:
        loc_doc = frappe.get_doc("Location", shipping_location)
    except frappe.DoesNotExistError:
        return []
    except Exception as e:
        frappe.logger().error(f"Error getting shipping location {shipping_location}: {str(e)}")
        return []
    
    linked_address = getattr(loc_doc, 'linked_address', None)
    if not linked_address:
        return []
    
    # Check if the linked address exists
    if frappe.db.exists("Address", linked_address):
        return [linked_address]
    
    return []


def auto_set_warehouse_for_location(doc):
    """
    Auto-set warehouse based on location for documents.
    If location has a single warehouse, auto-select it.
    """
    if not doc.location:
        return
    
    valid_warehouses = get_filtered_warehouses_for_location(doc.location)
    
    # If there's exactly one valid warehouse, auto-select it
    if len(valid_warehouses) == 1:
        # Set the warehouse field if it exists and is empty
        if hasattr(doc, 'warehouse') and not doc.warehouse:
            doc.warehouse = valid_warehouses[0]
        
        # For documents with item tables, we need to handle those separately
        # This will be handled in the validation function


def auto_set_warehouse_for_shipping_location(doc):
    """
    Auto-set warehouse based on shipping location for documents.
    If shipping location has a single warehouse, auto-select it.
    """
    if not doc.shipping_location:
        return
    
    valid_warehouses = get_filtered_warehouses_for_shipping_location(doc.shipping_location)
    
    # If there's exactly one valid warehouse, auto-select it
    if len(valid_warehouses) == 1:
        # Set the warehouse field if it exists and is empty
        if hasattr(doc, 'warehouse') and not doc.warehouse:
            doc.warehouse = valid_warehouses[0]
        
        # For documents with item tables, we need to handle those separately
        # This will be handled in the validation function


def auto_set_shipping_address_for_shipping_location(doc):
    """
    Auto-set shipping address based on shipping location for documents.
    If shipping location has a linked address, auto-select it.
    """
    if not doc.shipping_location:
        return
    
    valid_addresses = get_filtered_addresses_for_shipping_location(doc.shipping_location)
    
    # If there's exactly one valid address, auto-select it
    if len(valid_addresses) == 1:
        # Set the shipping address field if it exists and is empty
        if hasattr(doc, 'shipping_address') and not doc.shipping_address:
            doc.shipping_address = valid_addresses[0]


def validate_warehouse_against_location(doc, warehouse_field="warehouse"):
    """
    Validate that the selected warehouse is valid for the location.
    """
    _validate_warehouse_against_location_generic(doc, 'location', warehouse_field)


def validate_warehouse_against_shipping_location(doc, warehouse_field="warehouse"):
    """
    Validate that the selected warehouse is valid for the shipping location.
    """
    _validate_warehouse_against_location_generic(doc, 'shipping_location', warehouse_field)


def validate_shipping_address_against_shipping_location(doc):
    """
    Validate that the selected shipping address is valid for the shipping location.
    """
    _validate_address_against_location_generic(doc, 'shipping_location', 'shipping_address')


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs  
def child_table_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Server-side query method for warehouse fields in child tables.
    Filters warehouses based on the parent document's location.
    """
    
    # Extract parent information from filters
    parent_doctype = filters.get("parent_doctype")
    parent_name = filters.get("parent")
    
    if not parent_doctype or not parent_name:
        # If no parent info, fall back to basic location filtering
        return location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs)
    
    # Get the parent document to find its location
    if not parent_name:  # Handle new documents
        return []
        
    try:
        parent_doc = frappe.get_doc(parent_doctype, parent_name)
        location = getattr(parent_doc, 'location', None)
    except (frappe.DoesNotExistError, AttributeError):
        return []
    
    if not location:
        return []
    
    # Use the main location-based query with the parent's location
    filters_with_location = dict(filters)
    filters_with_location['location'] = location
    
    return location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters_with_location, **kwargs) 


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs  
def child_table_shipping_location_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Server-side query method for warehouse fields in child tables.
    Filters warehouses based on the parent document's shipping location.
    """
    
    # Extract parent information from filters
    parent_doctype = filters.get("parent_doctype")
    parent_name = filters.get("parent")
    
    if not parent_doctype or not parent_name:
        # If no parent info, fall back to basic shipping location filtering
        return shipping_location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs)
    
    # Get the parent document to find its shipping location
    if not parent_name:  # Handle new documents
        return []
        
    try:
        parent_doc = frappe.get_doc(parent_doctype, parent_name)
        shipping_location = getattr(parent_doc, 'shipping_location', None)
    except (frappe.DoesNotExistError, AttributeError):
        return []
    
    if not shipping_location:
        return []
    
    # Use the main shipping location-based query with the parent's shipping location
    filters_with_shipping_location = dict(filters)
    filters_with_shipping_location['shipping_location'] = shipping_location
    
    return shipping_location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters_with_shipping_location, **kwargs) 


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def dispatch_location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Server-side query method to filter warehouses based on dispatch location.
    Returns warehouses that are linked to the dispatch location.
    """
    dispatch_location = filters.get("dispatch_location") if filters else None
    return _get_location_based_query_result("dispatch", dispatch_location, "Warehouse", txt, searchfield, start, page_len, filters, **kwargs)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def dispatch_location_based_address_query(doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Server-side query method to filter addresses based on dispatch location.
    Returns addresses that are linked to the dispatch location.
    """
    dispatch_location = filters.get("dispatch_location") if filters else None
    return _get_location_based_query_result("dispatch", dispatch_location, "Address", txt, searchfield, start, page_len, filters, **kwargs)


def get_filtered_warehouses_for_dispatch_location(dispatch_location):
    """
    Get list of warehouses that are valid for the given dispatch location.
    """
    return _get_filtered_warehouses_for_location_generic(dispatch_location)


@frappe.whitelist()
def get_filtered_addresses_for_dispatch_location(dispatch_location):
    """
    Get list of addresses that are valid for the given dispatch location.
    """
    return _get_filtered_addresses_for_location_generic(dispatch_location)


def auto_set_warehouse_for_dispatch_location(doc):
    """
    Auto-set warehouse based on dispatch location for documents.
    If dispatch location has a single warehouse, auto-select it.
    """
    if not doc.dispatch_location:
        return
    
    valid_warehouses = get_filtered_warehouses_for_dispatch_location(doc.dispatch_location)
    
    # If there's exactly one valid warehouse, auto-select it
    if len(valid_warehouses) == 1:
        # Set the warehouse field if it exists and is empty
        if hasattr(doc, 'warehouse') and not doc.warehouse:
            doc.warehouse = valid_warehouses[0]
        
        # For documents with item tables, we need to handle those separately
        # This will be handled in the validation function


def auto_set_dispatch_address_for_dispatch_location(doc):
    """
    Auto-set dispatch address based on dispatch location for documents.
    If dispatch location has a linked address, auto-select it.
    """
    if not doc.dispatch_location:
        return
    
    valid_addresses = get_filtered_addresses_for_dispatch_location(doc.dispatch_location)
    
    # If there's exactly one valid address, auto-select it
    if len(valid_addresses) == 1:
        # Set the dispatch address field if it exists and is empty
        if hasattr(doc, 'dispatch_address_name') and not doc.dispatch_address_name:
            doc.dispatch_address_name = valid_addresses[0]


def validate_warehouse_against_dispatch_location(doc, warehouse_field="warehouse"):
    """
    Validate that the selected warehouse is valid for the dispatch location.
    """
    _validate_warehouse_against_location_generic(doc, 'dispatch_location', warehouse_field)


def validate_dispatch_address_against_dispatch_location(doc):
    """
    Validate that the selected dispatch address is valid for the dispatch location.
    """
    _validate_address_against_location_generic(doc, 'dispatch_location', 'dispatch_address_name')


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs  
def child_table_dispatch_location_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs):
    """
    Server-side query method for warehouse fields in child tables.
    Filters warehouses based on the parent document's dispatch location.
    """
    
    # Extract parent information from filters
    parent_doctype = filters.get("parent_doctype")
    parent_name = filters.get("parent")
    
    if not parent_doctype or not parent_name:
        # If no parent info, fall back to basic dispatch location filtering
        return dispatch_location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters, **kwargs)
    
    # Get the parent document to find its dispatch location
    if not parent_name:  # Handle new documents
        return []
        
    try:
        parent_doc = frappe.get_doc(parent_doctype, parent_name)
        dispatch_location = getattr(parent_doc, 'dispatch_location', None)
    except (frappe.DoesNotExistError, AttributeError):
        return []
    
    if not dispatch_location:
        return []
    
    # Use the main dispatch location-based query with the parent's dispatch location
    filters_with_dispatch_location = dict(filters)
    filters_with_dispatch_location['dispatch_location'] = dispatch_location
    
    return dispatch_location_based_warehouse_query(doctype, txt, searchfield, start, page_len, filters_with_dispatch_location, **kwargs) 