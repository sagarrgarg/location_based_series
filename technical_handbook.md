# Location Based Series — Technical Handbook

## Overview

Frappe app that overrides the default `naming_series` for transactional DocTypes with a location-aware, fiscal-year-aware autoname pattern.

Supported DocTypes: Sales Invoice, Purchase Invoice, Sales Order, Purchase Order, Delivery Note, Purchase Receipt.

---

## Naming Convention

### Series Prefix Table

| DocType            | Condition          | Prefix | Example Name          |
|--------------------|--------------------|--------|-----------------------|
| Sales Invoice      | Regular            | SI     | SIMUM26-0001          |
| Sales Invoice      | is_debit_note      | SIDR   | SIDRMUM26-0001        |
| Sales Invoice      | is_return (CN)     | CN     | CNMUM26-0001          |
| Purchase Invoice   | Regular            | PI     | PIMUM26-0001          |
| Purchase Invoice   | is_return (DN)     | DN     | DNMUM26-0001          |
| Sales Order        | —                  | SO     | SOMUM26-0001          |
| Purchase Order     | —                  | PO     | POMUM26-0001          |
| Delivery Note      | Regular            | DN     | DNMUM26-0001          |
| Delivery Note      | is_return          | DNSR   | DNSRMUM26-0001        |
| Purchase Receipt   | Regular            | PR     | PRMUM26-0001          |
| Purchase Receipt   | is_return          | PRRR   | PRRRMUM26-0001        |

### Pattern Structure

`{PREFIX}.{LOCATION_CODE}.{FISCAL_YEAR_2DIGIT}.-.####`

Each `.`-separated segment is concatenated by Frappe's `make_autoname`. The `-` inserts a literal hyphen before the 4-digit counter.

### Key Fields (Custom)

- `lbs_location_code` — 2–4 char code from the linked Location record
- `lbs_doctype_code` — sub-code (DR, CR, SR, RR, or empty) stored for filtering/reference

---

## Architecture

### Hook Chain

1. `hooks.py` → `doc_events.{DocType}.autoname` → `events.naming.custom_autoname`
2. `hooks.py` → `doc_events.{DocType}.validate` → `events.validation.validate_doc`

### File Map

| File                        | Purpose                                              |
|-----------------------------|------------------------------------------------------|
| `events/naming.py`         | Autoname logic: template selection, fiscal year, counter |
| `events/validation.py`     | Location validation, address/warehouse filtering      |
| `events/client_scripts.py` | (Legacy) client script installation                   |
| `install.py`               | Post-install setup: autoname meta, custom fields      |
| `uninstall.py`             | Reverts autoname to `naming_series`                   |
| `utils.py`                 | Warehouse/address query helpers, GST state mapping    |
| `hooks.py`                 | DocType JS includes, doc_events, fixtures             |
| `public/js/*.js`           | Client-side location/warehouse filtering per DocType  |
| `fixtures/custom_field.json` | Custom fields for all supported DocTypes            |

---

## Changelog

### 2026-04-01 — Series prefix cleanup

**What changed:**
- Sales Invoice returns (Credit Notes): prefix changed from `SICR` → `CN`
- Purchase Invoice returns (Debit Notes): prefix changed from `PIDR` → `DN`
- Refactored `custom_autoname` to use `_get_naming_template(doc)` for full template selection instead of embedding `{lbs_doctype_code}` into a per-DocType template string.
- `get_lbs_doctype_code` still returns DR/CR/SR/RR for the `lbs_doctype_code` field value but no longer drives the series prefix.

**Why:**
- SICR and PIDR were unintuitive combined abbreviations. CN (Credit Note) and DN (Debit Note) are standard accounting terms.

**Impacted modules:**
- `events/naming.py` — template selection refactored
- `install.py` — reference format strings updated

**Note:** Purchase Invoice returns (DN prefix) and regular Delivery Notes both start with "DN". They share the `tabSeries` counter for the same location+FY combination but live in separate DocType tables, so no name collision occurs.
