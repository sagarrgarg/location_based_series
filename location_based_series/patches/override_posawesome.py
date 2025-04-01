import frappe, json
from frappe.utils import getdate
from posawesome.posawesome.api.posapp import add_taxes_from_tax_template

@frappe.whitelist()
def update_invoice(data):
    data = json.loads(data)
    
    # Inject location from POS Profile if not present
    if not data.get("location") and data.get("pos_profile"):
        location = frappe.db.get_value("POS Profile", data["pos_profile"], "location")
        if location:
            data["location"] = location
            frappe.logger("location_based_series").info(f"[POSA] Injected location: {location}")
    if data.get("location"):
        loc = frappe.get_doc("Location", data["location"])
        data["location_code"] = loc.location_code
        data["company_address"] = loc.linked_address

    if data.get("name"):
        invoice_doc = frappe.get_doc("Sales Invoice", data.get("name"))
        invoice_doc.update(data)
    else:
        invoice_doc = frappe.get_doc(data)

    invoice_doc.set_missing_values()
    invoice_doc.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True

    if invoice_doc.is_return and invoice_doc.return_against:
        ref_doc = frappe.get_cached_doc(invoice_doc.doctype, invoice_doc.return_against)
        if not ref_doc.update_stock:
            invoice_doc.update_stock = 0
        if len(invoice_doc.payments) == 0:
            invoice_doc.payments = ref_doc.payments
        invoice_doc.paid_amount = invoice_doc.rounded_total or invoice_doc.grand_total or invoice_doc.total
        for payment in invoice_doc.payments:
            if payment.default:
                payment.amount = invoice_doc.paid_amount

    allow_zero_rated_items = frappe.get_cached_value("POS Profile", invoice_doc.pos_profile, "posa_allow_zero_rated_items")
    for item in invoice_doc.items:
        if not item.rate or item.rate == 0:
            if allow_zero_rated_items:
                item.price_list_rate = 0.00
                item.is_free_item = 1
            else:
                frappe.throw(("Rate cannot be zero for item {0}").format(item.item_code))
        else:
            item.is_free_item = 0
        add_taxes_from_tax_template(item, invoice_doc)

    if frappe.get_cached_value("POS Profile", invoice_doc.pos_profile, "posa_tax_inclusive"):
        if invoice_doc.get("taxes"):
            for tax in invoice_doc.taxes:
                tax.included_in_print_rate = 1

    today_date = getdate()
    if invoice_doc.get("posting_date") and getdate(invoice_doc.posting_date) != today_date:
        invoice_doc.set_posting_time = 1

    invoice_doc.save()
    return invoice_doc