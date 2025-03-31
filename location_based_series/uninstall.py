# location_based_series/uninstall.py

import frappe

def revert_autoname_for_target_doctypes():
    target_doctypes = [
        "Sales Invoice",
        "Purchase Invoice",
        "Sales Order",
        "Purchase Order",
        "Delivery Note",
        "Purchase Receipt"
    ]

    for dt in target_doctypes:
        try:
            meta = frappe.get_doc("DocType", dt)

            # Revert safely to naming_series or empty
            meta.autoname = "naming_series"
            meta.save()
            frappe.db.commit()
            frappe.logger("location_based_series").info(f"[Uninstall] Reverted autoname for {dt}")
        except Exception as e:
            frappe.logger("location_based_series").error(f"[Uninstall Error] {dt}: {e}")
