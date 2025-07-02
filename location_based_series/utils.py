import frappe
from frappe.utils.nestedset import get_descendants_of


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


def validate_warehouse_against_location(doc, warehouse_field="warehouse"):
    """
    Validate that the selected warehouse is valid for the location.
    """
    if not doc.location:
        return
    
    warehouse = getattr(doc, warehouse_field, None)
    if not warehouse:
        return
    
    valid_warehouses = get_filtered_warehouses_for_location(doc.location)
    
    if warehouse not in valid_warehouses:
        frappe.throw(f"Warehouse '{warehouse}' is not valid for location '{doc.location}'. Valid warehouses are: {', '.join(valid_warehouses)}")


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