// Location-based warehouse filtering for Sales Invoice
// Load shared utility functions
frappe.require('/assets/location_based_series/js/location_utils.js');

frappe.ui.form.on('Sales Invoice', {
    location: function(frm) {
        // Update warehouse queries when location changes
        if (window.locationUtils) {
            window.locationUtils.setLocationQueries(frm, 'main', 'location');
        }
    },
    
    dispatch_location: function(frm) {
        // Update dispatch address and warehouse queries when dispatch location changes
        if (window.locationUtils) {
            window.locationUtils.handleLocationChange(frm, 'dispatch', 'dispatch_location');
        }
    },
    
    refresh: function(frm) {
        // Set warehouse queries on form load with proper priority
        if (window.locationUtils) {
            // First check for dispatch location
            if (frm.doc.dispatch_location) {
                window.locationUtils.setLocationQueries(frm, 'dispatch', 'dispatch_location');
            } else if (frm.doc.location) {
                window.locationUtils.setLocationQueries(frm, 'main', 'location');
            }
        }
        }
}); 