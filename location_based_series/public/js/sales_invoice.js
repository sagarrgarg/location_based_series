// Location-based warehouse filtering for Sales Invoice
frappe.ui.form.on('Sales Invoice', {
    location: function(frm) {
        // Update warehouse queries when location changes
        set_warehouse_queries(frm);
    },
    
    refresh: function(frm) {
        // Set warehouse queries on form load
        set_warehouse_queries(frm);
    }
});

function set_warehouse_queries(frm) {
    if (!frm.doc.location) {
        // Clear warehouse fields if no location
        clear_warehouse_fields(frm);
        return;
    }
    
    // Set query for document-level warehouse fields
    // Exclude target_warehouse from filtering as it's optional and can be different from location
    const warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse'];
    
    warehouse_fields.forEach(function(fieldname) {
        if (frm.fields_dict[fieldname]) {
            frm.set_query(fieldname, function() {
                return {
                    query: 'location_based_series.utils.location_based_warehouse_query',
                    filters: {
                        'location': frm.doc.location
                    }
                };
            });
        }
    });
    
    // Set query for child table warehouse fields
    const child_tables = ['items', 'item_details', 'stock_entries'];
    // Exclude target_warehouse from filtering as it's optional and can be different from location
    const child_warehouse_fields = ['warehouse', 's_warehouse', 't_warehouse', 'source_warehouse'];
    
    child_tables.forEach(function(table_name) {
        if (frm.fields_dict[table_name]) {
            child_warehouse_fields.forEach(function(field_name) {
                frm.set_query(field_name, table_name, function(doc, cdt, cdn) {
                    return {
                        query: 'location_based_series.utils.child_table_warehouse_query',
                        filters: {
                            'location': frm.doc.location,
                            'parent_doctype': frm.doc.doctype,
                            'parent': frm.doc.name || ''
                        }
                    };
                });
            });
        }
    });
}

function clear_warehouse_fields(frm) {
    // Clear warehouse queries when no location is selected
    // Exclude target_warehouse from clearing as it's optional and can be different from location
    const warehouse_fields = ['warehouse', 'set_warehouse', 'source_warehouse'];
    
    warehouse_fields.forEach(function(fieldname) {
        if (frm.fields_dict[fieldname]) {
            frm.set_query(fieldname, function() {
                return {
                    filters: {
                        'name': ['in', []]  // Empty filter to show no results
                    }
                };
            });
        }
    });
    
    // Clear child table warehouse queries
    const child_tables = ['items', 'item_details', 'stock_entries'];
    // Exclude target_warehouse from clearing as it's optional and can be different from location
    const child_warehouse_fields = ['warehouse', 's_warehouse', 't_warehouse', 'source_warehouse'];
    
    child_tables.forEach(function(table_name) {
        if (frm.fields_dict[table_name]) {
            child_warehouse_fields.forEach(function(field_name) {
                frm.set_query(field_name, table_name, function(doc, cdt, cdn) {
                    return {
                        filters: {
                            'name': ['in', []]  // Empty filter
                        }
                    };
                });
            });
        }
    });
} 