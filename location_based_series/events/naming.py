# from frappe.model.naming import make_autoname
import frappe
from frappe.utils import getdate

def custom_autoname(doc, method):
    logger = frappe.logger("location_based_series")

    location_code = doc.location_code or "0000"
    company = doc.company
    posting_date = getdate(getattr(doc, "posting_date", frappe.utils.nowdate()))
    logger.info(f"[LBS] Posting Date: {posting_date}, Company: {company}, Location Code: {location_code}")

    # Get fiscal year code
    # fiscal_year = get_fiscal_year_code(posting_date, company)
    # logger.info(f"[LBS] Fiscal Year Code resolved to: {fiscal_year}")

    # Determine doctype_code
    doctype_code = ""

    # Handle special flags
    if doc.doctype == "Sales Invoice":
        if doc.get("is_debit_note"):
            doctype_code = "DR"
        elif doc.get("is_return"):
            doctype_code = "CR"
    elif doc.doctype == "Purchase Invoice" and doc.get("is_return"):
        doctype_code = "DR"
    elif doc.doctype == "Delivery Note" and doc.get("is_return"):
        doctype_code = "SR"
    elif doc.doctype == "Purchase Receipt" and doc.get("is_return"):
        doctype_code = "PR"

    logger.info(f"[LBS] Doctype: {doc.doctype}, Doctype Code: {doctype_code}")

    doc.doctype_code = doctype_code
    # series_pattern = f"{location_code}{doctype_code}{fiscal_year}-.####"
    # logger.info(f"[LBS] Series Pattern: {series_pattern}")
    # doc.name = make_autoname(series_pattern, doc=doc)



def get_fiscal_year_code(posting_date, company):
    posting_date = getdate(posting_date)

    fiscal_years = frappe.get_all(
        "Fiscal Year",
        fields=["name", "year_start_date", "year_end_date"],
        filters={
            "disabled": 0,
            "year_start_date": ("<=", posting_date),
            "year_end_date": (">=", posting_date),
        },
        order_by="year_start_date desc"
    )

    for fy in fiscal_years:
        linked_companies = frappe.get_all(
            "Fiscal Year Company",
            filters={"parent": fy.name, "company": company},
            pluck="company"
        )
        if linked_companies:
            return fy.name[-2:]  # Get last 2 digits of Fiscal Year name (e.g., "2025")

    # Fallback to first matching fiscal year (if no link to company)
    if fiscal_years:
        return fiscal_years[0]["name"][-2:]

    # Absolute fallback
    return "00"
