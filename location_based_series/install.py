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
