import frappe
from frappe.utils.nestedset import get_descendants_of

# Comprehensive state mapping for Indian states and territories
# This includes all states, union territories, and special territories
STATE_NUMBERS = {
    "Andaman and Nicobar Islands": "35",
    "Andhra Pradesh": "37", 
    "Arunachal Pradesh": "12",
    "Assam": "18",
    "Bihar": "10",
    "Chandigarh": "04",
    "Chhattisgarh": "22",
    "Dadra and Nagar Haveli and Daman and Diu": "26",
    "Delhi": "07",
    "Goa": "30",
    "Gujarat": "24",
    "Haryana": "06",
    "Himachal Pradesh": "02",
    "Jammu and Kashmir": "01",
    "Jharkhand": "20",
    "Karnataka": "29",
    "Kerala": "32",
    "Ladakh": "38",
    "Lakshadweep Islands": "31",
    "Madhya Pradesh": "23",
    "Maharashtra": "27",
    "Manipur": "14",
    "Meghalaya": "17",
    "Mizoram": "15",
    "Nagaland": "13",
    "Odisha": "21",
    "Other Countries": "96",
    "Other Territory": "97",
    "Puducherry": "34",
    "Punjab": "03",
    "Rajasthan": "08",
    "Sikkim": "11",
    "Tamil Nadu": "33",
    "Telangana": "36",
    "Tripura": "16",
    "Uttar Pradesh": "09",
    "Uttarakhand": "05",
    "West Bengal": "19",
}

# Reverse mapping for state code to state name
STATE_CODE_TO_NAME = {v: k for k, v in STATE_NUMBERS.items()}


def get_state_from_gstin(gstin):
    """
    Extract state code from GSTIN (first 2 digits).
    Returns state code and state name.
    """
    if not gstin or len(gstin) < 2:
        return None, None
    
    state_code = gstin[:2]
    state_name = STATE_CODE_TO_NAME.get(state_code)
    return state_code, state_name


def get_place_of_supply_from_address(address_name):
    """
    Get place of supply from address.
    Returns format: "state_code-state_name" (e.g., "07-Delhi")
    """
    if not address_name:
        return None
    
    # Get address details
    address_details = frappe.db.get_value("Address", address_name, 
        ["gstin", "gst_state_number", "gst_state", "state", "country"], as_dict=True)
    
    if not address_details:
        return None
    
    # For non-Indian addresses, return Other Countries
    if address_details.country != "India":
        return "96-Other Countries"
    
    # If GSTIN is available, use first 2 digits
    if address_details.gstin:
        state_code, state_name = get_state_from_gstin(address_details.gstin)
        if state_code and state_name:
            return f"{state_code}-{state_name}"
    
    # If GST state number is available, use it
    if address_details.gst_state_number:
        state_name = STATE_CODE_TO_NAME.get(address_details.gst_state_number)
        if state_name:
            return f"{address_details.gst_state_number}-{state_name}"
    
    # If GST state is available, find its code
    if address_details.gst_state:
        state_code = STATE_NUMBERS.get(address_details.gst_state)
        if state_code:
            return f"{state_code}-{address_details.gst_state}"
    
    # If regular state is available, find its code
    if address_details.state:
        state_code = STATE_NUMBERS.get(address_details.state)
        if state_code:
            return f"{state_code}-{address_details.state}"
    
    return None


def set_place_of_supply_for_purchase_doc(doc):
    """
    Set place of supply for purchase documents (PI, PO, PR) based on location's linked address.
    This is called during document validation.
    """
    purchase_doctypes = ["Purchase Invoice", "Purchase Order", "Purchase Receipt"]
    
    if doc.doctype not in purchase_doctypes:
        return
    
    # Get the billing address (company address for purchase documents)
    billing_address = None
    
    if hasattr(doc, 'billing_address') and doc.billing_address:
        billing_address = doc.billing_address
    elif hasattr(doc, 'company_address') and doc.company_address:
        billing_address = doc.company_address
    
    if not billing_address:
        return
    
    # Get place of supply from billing address
    place_of_supply = get_place_of_supply_from_address(billing_address)
    
    if place_of_supply and hasattr(doc, 'place_of_supply'):
        doc.place_of_supply = place_of_supply
        frappe.logger("location_based_series").info(f"[POS] Set place_of_supply to '{place_of_supply}' for {doc.doctype} {doc.name}")


@frappe.whitelist()
def test_place_of_supply_logic():
    """
    Test function to demonstrate place of supply logic.
    This can be called from console to test the functionality.
    """
    test_cases = [
        {
            "description": "GSTIN with state code 07 (Delhi)",
            "gstin": "07ABCDE1234F1Z5",
            "expected": "07-Delhi"
        },
        {
            "description": "GSTIN with state code 27 (Maharashtra)", 
            "gstin": "27ABCDE1234F1Z5",
            "expected": "27-Maharashtra"
        },
        {
            "description": "Non-Indian address",
            "country": "United States",
            "expected": "96-Other Countries"
        }
    ]
    
    results = []
    for case in test_cases:
        if "gstin" in case:
            state_code, state_name = get_state_from_gstin(case["gstin"])
            result = f"{state_code}-{state_name}" if state_code and state_name else None
        elif "country" in case:
            result = "96-Other Countries" if case["country"] != "India" else None
        else:
            result = None
            
        results.append({
            "description": case["description"],
            "expected": case["expected"],
            "actual": result,
            "match": result == case["expected"]
        })
    
    return results


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
    
    # Handle warehouse filtering with group warehouse support
    if doctype == "Warehouse":
        # Get warehouse info to check if it's a group warehouse
        warehouse_info = frappe.db.get_value("Warehouse", linked_value, 
                                            ["name", "is_group", "disabled"], as_dict=True)
        
        if not warehouse_info or warehouse_info.disabled:
            return []
        
        if warehouse_info.is_group:
            # Get all non-group descendants
            try:
                descendant_warehouses = get_descendants_of("Warehouse", linked_value, 
                                                         ignore_permissions=True)
                if descendant_warehouses:
                    # Get non-group descendants that are not disabled
                    non_group_descendants = frappe.get_all("Warehouse", 
                                                          filters={
                                                              "name": ["in", descendant_warehouses],
                                                              "is_group": 0,
                                                              "disabled": 0
                                                          },
                                                          fields=result_fields,
                                                          order_by="name")
                    
                    # Filter by search text if provided
                    if txt:
                        filtered_results = []
                        for warehouse in non_group_descendants:
                            if (txt.lower() in warehouse.name.lower() or 
                                txt.lower() in warehouse.warehouse_name.lower()):
                                filtered_results.append([warehouse.name, warehouse.warehouse_name])
                        return filtered_results[start:start + page_len]
                    else:
                        return [[warehouse.name, warehouse.warehouse_name] 
                               for warehouse in non_group_descendants[start:start + page_len]]
            except Exception as e:
                frappe.logger().error(f"Error getting descendants for warehouse {linked_value}: {str(e)}")
                return []
        else:
            # Non-group warehouse - return only this warehouse
            warehouse_name = frappe.db.get_value("Warehouse", linked_value, "warehouse_name")
            
            # Check if search text matches
            if txt:
                if (txt.lower() not in linked_value.lower() and 
                    txt.lower() not in warehouse_name.lower()):
                    return []
            
            return [[linked_value, warehouse_name]]
    else:
        # For Address doctype, return the linked address
        address_title = frappe.db.get_value("Address", linked_value, "address_title")
        
        # Check if search text matches
        if txt:
            if (txt.lower() not in linked_value.lower() and 
                txt.lower() not in address_title.lower()):
                return []
        
        return [[linked_value, address_title]]


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