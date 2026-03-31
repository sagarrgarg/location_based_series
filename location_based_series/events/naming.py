from frappe.model.naming import make_autoname
import frappe
from frappe.utils import getdate


def custom_autoname(doc, method):
    """Generate location-based document name with fiscal year and sequential numbering."""
    logger = frappe.logger("location_based_series")

    lbs_location_code = doc.lbs_location_code
    company = doc.company
    posting_date = getdate(getattr(doc, "posting_date", frappe.utils.nowdate()))
    logger.info(f"[LBS] Posting Date: {posting_date}, Company: {company}, Location Code: {lbs_location_code}")

    fiscal_year = get_fiscal_year_code(posting_date, company)
    logger.info(f"[LBS] Fiscal Year Code resolved to: {fiscal_year}")

    lbs_doctype_code = get_lbs_doctype_code(doc)
    logger.info(f"[LBS] Doctype: {doc.doctype}, Doctype Code: {lbs_doctype_code}")
    doc.lbs_doctype_code = lbs_doctype_code

    template = _get_naming_template(doc)
    if not template:
        logger.error(f"[LBS] No series format defined for {doc.doctype}")
        return

    series_pattern = template.format(
        lbs_location_code=lbs_location_code,
        fiscal_year=fiscal_year,
    )

    logger.info(f"[LBS] Final Series Pattern: {series_pattern}")
    doc.name = make_autoname(series_pattern, doc=doc)


def _get_naming_template(doc):
    """Return the full naming template based on doctype and document flags.

    Prefix mapping:
        SI = Sales Invoice (regular)
        CN = Credit Note  (Sales Invoice return)
        PI = Purchase Invoice (regular)
        DN = Debit Note   (Purchase Invoice return)
        SO = Sales Order
        PO = Purchase Order
        DN = Delivery Note
        PR = Purchase Receipt
    """
    if doc.doctype == "Sales Invoice":
        if doc.get("is_debit_note"):
            return "SI.DR.{lbs_location_code}.{fiscal_year}.-.####"
        if doc.get("is_return"):
            return "CN.{lbs_location_code}.{fiscal_year}.-.####"
        return "SI.{lbs_location_code}.{fiscal_year}.-.####"

    if doc.doctype == "Purchase Invoice":
        if doc.get("is_return"):
            return "DN.{lbs_location_code}.{fiscal_year}.-.####"
        return "PI.{lbs_location_code}.{fiscal_year}.-.####"

    if doc.doctype == "Delivery Note":
        if doc.get("is_return"):
            return "DN.SR.{lbs_location_code}.{fiscal_year}.-.####"
        return "DN.{lbs_location_code}.{fiscal_year}.-.####"

    if doc.doctype == "Purchase Receipt":
        if doc.get("is_return"):
            return "PR.RR.{lbs_location_code}.{fiscal_year}.-.####"
        return "PR.{lbs_location_code}.{fiscal_year}.-.####"

    return {
        "Sales Order": "SO.{lbs_location_code}.{fiscal_year}.-.####",
        "Purchase Order": "PO.{lbs_location_code}.{fiscal_year}.-.####",
    }.get(doc.doctype)


def get_lbs_doctype_code(doc):
    """Return doctype sub-code based on flags like is_return, is_debit_note.

    Stored on the document via lbs_doctype_code for reference/filtering.
    """
    if doc.doctype == "Sales Invoice":
        if doc.get("is_debit_note"):
            return "DR"
        if doc.get("is_return"):
            return "CR"
        return ""

    if doc.doctype == "Purchase Invoice":
        return "DR" if doc.get("is_return") else ""

    if doc.doctype == "Delivery Note":
        return "SR" if doc.get("is_return") else ""

    if doc.doctype == "Purchase Receipt":
        return "RR" if doc.get("is_return") else ""

    return ""


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
