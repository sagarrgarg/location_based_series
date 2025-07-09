// Location-based warehouse filtering for Purchase Invoice
// Load shared utility functions
frappe.require('/assets/location_based_series/js/location_utils.js');

frappe.ui.form.on('Purchase Invoice', {
    location: function(frm) {
        // Update warehouse queries when location changes
        if (window.locationUtils) {
            window.locationUtils.setLocationQueries(frm, 'main', 'location');
        }
    },
    
    shipping_location: function(frm) {
        // Update shipping address and warehouse queries when shipping location changes
        if (window.locationUtils) {
            window.locationUtils.handleLocationChange(frm, 'shipping', 'shipping_location');
        }
    },
    
    refresh: function(frm) {
        // Set warehouse queries on form load
        if (window.locationUtils) {
            if (frm.doc.location) {
                window.locationUtils.setLocationQueries(frm, 'main', 'location');
            }
            if (frm.doc.shipping_location) {
                window.locationUtils.setLocationQueries(frm, 'shipping', 'shipping_location');
            }
        }
        }
}); 