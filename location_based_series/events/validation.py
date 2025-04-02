from frappe.contacts.doctype.address.address import get_address_display
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

        if not loc.lbs_location_code:
            frappe.throw("Selected Location must have a Location Code.")
        if not loc.linked_address:
            frappe.throw("Selected Location must have a Linked Address.")

        # Auto-fill location code
        doc.lbs_location_code = loc.lbs_location_code

        # Handle based on document type
        purchase_doctypes = ["Purchase Invoice", "Purchase Receipt", "Purchase Order"]
        if doc.doctype in purchase_doctypes:
            doc.billing_address = loc.linked_address
            doc.billing_address_display = get_address_display(loc.linked_address)

            # ✅ Set company GSTIN from billing address
            gstin = frappe.db.get_value("Address", loc.linked_address, "gstin")
            if gstin:
                doc.company_gstin = gstin
        else:
            doc.company_address = loc.linked_address
            doc.company_address_display = get_address_display(loc.linked_address)

            # ✅ Set company GSTIN from company address
            gstin = frappe.db.get_value("Address", loc.linked_address, "gstin")
            if gstin:
                doc.company_gstin = gstin
    else:
        frappe.throw("Select Location before Saving")

    # STEP 3: Lock fields after first save
    if not doc.is_new():
        old = frappe.get_doc(doc.doctype, doc.name)

        # Ensure linked address doesn't change after first save
        expected_address = loc.linked_address
        current_address_field = "billing_address" if doc.doctype in purchase_doctypes else "company_address"
        if getattr(doc, current_address_field) != expected_address:
            frappe.throw(f"❌ Field {current_address_field} cannot be changed after saving.")

        for field in ["location", "is_return", "is_rate_adjustment"]:
            if hasattr(doc, field) and doc.get(field) != old.get(field):
                frappe.throw(f"❌ Field '{field}' cannot be changed after saving.")
