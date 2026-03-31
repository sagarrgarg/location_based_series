// Location-based warehouse filtering for Delivery Note
// Load shared utility functions
frappe.require('/assets/location_based_series/js/location_utils.js');

frappe.ui.form.on('Delivery Note', {
    location: function(frm) {
        if (window.locationUtils) {
            window.locationUtils.setLocationQueries(frm, 'main', 'location');
        }
    },
    dispatch_location: function(frm) {
        if (window.locationUtils) {
            window.locationUtils.handleLocationChange(frm, 'dispatch', 'dispatch_location');
        }
    },
    refresh: function(frm) {
        if (window.locationUtils) {
            if (frm.doc.location) {
                window.locationUtils.setLocationQueries(frm, 'main', 'location');
            }
            if (frm.doc.dispatch_location) {
                window.locationUtils.setLocationQueries(frm, 'dispatch', 'dispatch_location');
            }
        }
    }
}); 