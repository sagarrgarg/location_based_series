// Shared utility functions for location-based warehouse filtering
// This module reduces code redundancy across different document types

// Generic function to set warehouse queries based on location type
function setLocationQueries(frm, locationType, locationField) {
    if (!frm.doc[locationField]) return;
    
    const queryMethod = locationType === 'dispatch' 
        ? 'location_based_series.utils.dispatch_location_based_warehouse_query'
        : locationType === 'shipping'
        ? 'location_based_series.utils.shipping_location_based_warehouse_query'
        : 'location_based_series.utils.location_based_warehouse_query';
    
    const filterKey = locationType === 'dispatch' 
        ? 'dispatch_location'
        : locationType === 'shipping'
        ? 'shipping_location'
        : 'location';
    
    // Set warehouse query for document level warehouse fields
    if (frm.fields_dict.set_warehouse) {
        frm.set_query('set_warehouse', function() {
            return {
                query: queryMethod,
                filters: {
                    [filterKey]: frm.doc[locationField]
                }
            };
        });
    }
    
    // Set warehouse query for child table warehouse fields
    if (frm.fields_dict.items) {
        const childQueryMethod = locationType === 'dispatch'
            ? 'location_based_series.utils.child_table_dispatch_location_warehouse_query'
            : locationType === 'shipping'
            ? 'location_based_series.utils.child_table_shipping_location_warehouse_query'
            : 'location_based_series.utils.child_table_warehouse_query';
        
        frm.set_query('warehouse', 'items', function() {
            return {
                query: childQueryMethod,
                filters: {
                    'parent_doctype': frm.doctype,
                    'parent': frm.doc.name || '',
                    [filterKey]: frm.doc[locationField]
                }
            };
        });
    }
    
    // Set address query based on location type (for shipping/dispatch)
    if (locationType !== 'main') {
        const addressField = locationType === 'dispatch' ? 'dispatch_address_name' : 'shipping_address';
        const addressQueryMethod = locationType === 'dispatch'
            ? 'location_based_series.utils.dispatch_location_based_address_query'
            : 'location_based_series.utils.shipping_location_based_address_query';
        
        if (frm.fields_dict[addressField]) {
            frm.set_query(addressField, function() {
                return {
                    query: addressQueryMethod,
                    filters: {
                        [filterKey]: frm.doc[locationField]
                    }
                };
            });
        }
    }
}

// Generic function to clear location fields
function clearLocationFields(frm, locationType) {
    if (locationType === 'main') return;
    
    const addressField = locationType === 'dispatch' ? 'dispatch_address_name' : 'shipping_address';
    
    // Clear address query when no location is selected
    if (frm.fields_dict[addressField]) {
        frm.set_query(addressField, function() {
            return {
                filters: {
                    'name': ['in', []]  // Empty filter to show no results
                }
            };
        });
    }
    
    // Note: We don't clear warehouse fields here because we want to revert to main location filtering
    // The calling function will handle re-applying main location warehouse filtering
}

// Generic function to auto-fill address
function autoFillAddress(frm, locationType, locationField) {
    if (!frm.doc[locationField]) return;
    
    const addressField = locationType === 'dispatch' ? 'dispatch_address_name' : 'shipping_address';
    const methodName = locationType === 'dispatch' 
        ? 'location_based_series.utils.get_filtered_addresses_for_dispatch_location'
        : 'location_based_series.utils.get_filtered_addresses_for_shipping_location';
    const paramName = locationType === 'dispatch' ? 'dispatch_location' : 'shipping_location';
    
    if (frm.fields_dict[addressField]) {
        frappe.call({
            method: methodName,
            args: {
                [paramName]: frm.doc[locationField]
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    // Set the address to the first (and only) available address
                    frm.set_value(addressField, r.message[0]);
                }
            }
        });
    }
}

// Generic function to reset warehouse fields
function resetWarehouseFields(frm) {
    // Reset warehouse fields to null when location is cleared
    if (frm.fields_dict.set_warehouse) {
        frm.set_value('set_warehouse', '');
    }
    
    // Reset warehouse fields in child tables
    if (frm.fields_dict.items && frm.doc.items) {
        frm.doc.items.forEach(function(item) {
            if (item.warehouse) {
                item.warehouse = '';
            }
        });
        frm.refresh_field('items');
    }
}

// Generic function to handle location change events
function handleLocationChange(frm, locationType, locationField) {
    if (frm.doc[locationField]) {
        setLocationQueries(frm, locationType, locationField);
        // Auto-fill address since it's one-to-one relationship
        autoFillAddress(frm, locationType, locationField);
    } else {
        // If location is cleared, revert to main location filtering
        clearLocationFields(frm, locationType);
        // Reset warehouse fields to null
        resetWarehouseFields(frm);
        // Re-apply main location filtering if location exists
        if (frm.doc.location) {
            setLocationQueries(frm, 'main', 'location');
        }
    }
}

// Export functions for use in other modules
window.locationUtils = {
    setLocationQueries,
    clearLocationFields,
    autoFillAddress,
    resetWarehouseFields,
    handleLocationChange
}; 