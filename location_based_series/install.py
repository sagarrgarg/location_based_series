# location_based_series/install.py

import frappe

def set_autoname_for_target_doctypes():
    doctype_naming_map = {
        "Sales Invoice": "SI.{doctype_code}.{location_code}.FY.-.####",
        "Purchase Invoice": "PI.{doctype_code}.{location_code}.FY.-.####",
        "Sales Order": "SO.{location_code}.FY.-.####",
        "Purchase Order": "PO.{location_code}.FY.-.####",
        "Delivery Note": "DN.{doctype_code}.{location_code}.FY.-.####",
        "Purchase Receipt": "PR.{doctype_code}.{location_code}.FY.-.####"
    }

    log = frappe.logger("location_based_series")

    for dt, series_format in doctype_naming_map.items():
        try:
            meta = frappe.get_doc("DocType", dt)
            meta.autoname = series_format  # This is just for visibility/reference
            meta.save()
            frappe.db.commit()
            log.info(f"[✓] Set autoname format for {dt}: {series_format}")
        except Exception as e:
            log.error(f"[✗] Failed to update autoname for {dt}: {e}")

def add_shipping_location_field(doctype):
    """Add shipping_location field to the specified doctype."""
    try:
        # Check if field already exists
        if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": "shipping_location"}):
            return
        
        # Create custom field
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": doctype,
            "fieldname": "shipping_location",
            "label": "Shipping Location",
            "fieldtype": "Link",
            "options": "Location",
            "insert_after": "location",
            "description": "Select a location to filter shipping addresses and warehouses separately from the main location.",
            "allow_on_submit": 1,
            "print_hide": 1
        })
        custom_field.insert()
        frappe.db.commit()
        
        frappe.logger("location_based_series").info(f"[✓] Added shipping_location field to {doctype}")
        
    except Exception as e:
        frappe.logger("location_based_series").error(f"[✗] Failed to add shipping_location field to {doctype}: {e}")

def add_dispatch_location_field(doctype):
    """Add dispatch_location field to the specified doctype."""
    try:
        # Check if field already exists
        if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": "dispatch_location"}):
            return
        
        # Determine insert position based on doctype
        if doctype == "Sales Invoice":
            insert_after = "shipping_addr_col_break"
        elif doctype == "Sales Order":
            insert_after = "column_break_93"
        elif doctype == "Delivery Note":
            insert_after = "column_break_95"
        else:
            insert_after = "location"
        
        # Create custom field
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": doctype,
            "fieldname": "dispatch_location",
            "label": "Dispatch Location",
            "fieldtype": "Link",
            "options": "Location",
            "insert_after": insert_after,
            "description": "Select a location to filter dispatch addresses and warehouses separately from the main location.",
            "allow_on_submit": 1,
            "print_hide": 1
        })
        custom_field.insert()
        frappe.db.commit()
        
        frappe.logger("location_based_series").info(f"[✓] Added dispatch_location field to {doctype}")
        
    except Exception as e:
        frappe.logger("location_based_series").error(f"[✗] Failed to add dispatch_location field to {doctype}: {e}")

def clear_existing_client_scripts():
    """Remove any existing client scripts created by this app."""
    target_doctypes = [
        "Sales Invoice",
        "Purchase Invoice", 
        "Sales Order",
        "Purchase Order",
        "Delivery Note",
        "Purchase Receipt"
    ]
    
    log = frappe.logger("location_based_series")
    
    for doctype in target_doctypes:
        script_name = f"Location Based Warehouse Filter - {doctype}"
        
        if frappe.db.exists("Client Script", {"name": script_name}):
            try:
                frappe.delete_doc("Client Script", script_name)
                log.info(f"[✓] Removed existing client script for {doctype}")
            except Exception as e:
                log.error(f"[✗] Failed to remove client script for {doctype}: {e}")
    
    frappe.db.commit()

def install():
    """Main installation function."""
    log = frappe.logger("location_based_series")
    log.info("Starting Location Based Series installation...")
    
    # Clear existing client scripts
    clear_existing_client_scripts()
    
    # Set autoname formats
    set_autoname_for_target_doctypes()
    
    # Add shipping_location field to purchase documents
    add_shipping_location_field("Purchase Order")
    add_shipping_location_field("Purchase Invoice") 
    add_shipping_location_field("Purchase Receipt")
    
    # Add dispatch_location field to sales documents
    add_dispatch_location_field("Sales Order")
    add_dispatch_location_field("Sales Invoice")
    add_dispatch_location_field("Delivery Note")
    
    log.info("Location Based Series installation completed!")
