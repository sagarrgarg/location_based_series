from frappe.model.naming import make_autoname
import frappe
from frappe.utils import getdate

def custom_autoname(doc, method):
    logger = frappe.logger("location_based_series")

    location_code = doc.location_code
    company = doc.company
    posting_date = getdate(getattr(doc, "posting_date", frappe.utils.nowdate()))
    logger.info(f"[LBS] Posting Date: {posting_date}, Company: {company}, Location Code: {location_code}")

    # Get fiscal year code
    fiscal_year = get_fiscal_year_code(posting_date, company)
    logger.info(f"[LBS] Fiscal Year Code resolved to: {fiscal_year}")

    # Determine doctype_code
    doctype_code = get_doctype_code(doc)

    logger.info(f"[LBS] Doctype: {doc.doctype}, Doctype Code: {doctype_code}")
    doc.doctype_code = doctype_code

    # Define series format per Doctype
    naming_templates = {
        "Sales Invoice": "SI.{doctype_code}.{location_code}.{fiscal_year}.-.####",
        "Purchase Invoice": "PI.{doctype_code}.{location_code}.{fiscal_year}.-.####",
        "Sales Order": "SO.{location_code}.{fiscal_year}.-.####",
        "Purchase Order": "PO.{location_code}.{fiscal_year}.-.####",
        "Delivery Note": "DN.{doctype_code}.{location_code}.{fiscal_year}.-.####",
        "Purchase Receipt": "PR.{doctype_code}.{location_code}.{fiscal_year}.-.####"
    }

    # Select template for current DocType
    template = naming_templates.get(doc.doctype)

    if not template:
        logger.error(f"[LBS] No series format defined for {doc.doctype}")
        return

    # Replace placeholders
    series_pattern = template.format(
        doctype_code=doctype_code,
        location_code=location_code,
        fiscal_year=fiscal_year
    )

    logger.info(f"[LBS] Final Series Pattern: {series_pattern}")
    doc.name = make_autoname(series_pattern, doc=doc)


def get_doctype_code(doc):
    """Return doctype code based on flags like is_return, is_debit_note, etc."""
    if doc.doctype == "Sales Invoice":
        if doc.get("is_debit_note"):
            return "DR"
        elif doc.get("is_return"):
            return "CR"
        return "SI"
    elif doc.doctype == "Purchase Invoice":
        return "DR" if doc.get("is_return") else "PI"
    elif doc.doctype == "Delivery Note":
        return "SR" if doc.get("is_return") else "DN"
    elif doc.doctype == "Purchase Receipt":
        return "RR" if doc.get("is_return") else "PR"
    else:
        return doc.doctype[:2].upper()  # Fallback (e.g., SO for Sales Order)


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
            return fy.name[-2:]

    if fiscal_years:
        return fiscal_years[0]["name"][-2:]

    return "00"
