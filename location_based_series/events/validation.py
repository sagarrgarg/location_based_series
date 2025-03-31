import frappe

def validate_doc(doc, method):
    # STEP 1: Check if 'Location' is enabled as an Accounting Dimension
    dim_exists = frappe.db.exists("Accounting Dimension", {
        "document_type": "Location",
        "disabled": 0
    })
    if not dim_exists:
        frappe.throw("Please enable 'Location' as an active Accounting Dimension before using it in transactions.")

    # STEP 2: Validate selected Location
    if doc.location:
        loc = frappe.get_doc("Location", doc.location)

        if not loc.location_code:
            frappe.throw("Selected Location must have a Location Code.")
        if not loc.linked_address:
            frappe.throw("Selected Location must have a Linked Address.")

        # Auto-fill fields
        doc.location_code = loc.location_code
        doc.company_address = loc.linked_address
    else:
        frappe.throw("Select Location before Saving")
    # STEP 3: Lock fields after first save
    if not doc.is_new():
        old = frappe.get_doc(doc.doctype, doc.name)
        for field in ["location", "company_address", "is_return", "is_rate_adjustment"]:
            if hasattr(doc, field) and doc.get(field) != old.get(field):
                frappe.throw(f"❌ Field '{field}' cannot be changed after saving.")
