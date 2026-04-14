import frappe


def execute():
    """Seed DBN-/CDN- tabSeries counters from existing DN-/CN- rows.

    Debit Note (PI return) prefix changed DN -> DBN.
    Credit Note (SI return) prefix changed CN -> CDN.
    New prefix counters must continue from the current DN/CN counter values
    (per location + fiscal year) so numbering does not reset.

    Delivery Note continues to use the DN- rows untouched.
    Idempotent: re-running only raises counters, never lowers them.
    """
    logger = frappe.logger("location_based_series")

    rows = frappe.db.sql(
        """
        SELECT name, `current`
        FROM `tabSeries`
        WHERE name LIKE 'DN-%' OR name LIKE 'CN-%'
        """,
        as_dict=True,
    )

    seeded = 0
    for row in rows:
        old_key = row["name"]
        current_value = row["current"] or 0

        if old_key.startswith("DN-"):
            new_key = "DBN-" + old_key[len("DN-"):]
        elif old_key.startswith("CN-"):
            new_key = "CDN-" + old_key[len("CN-"):]
        else:
            continue

        existing = frappe.db.sql(
            "SELECT `current` FROM `tabSeries` WHERE name = %s",
            (new_key,),
        )

        if not existing:
            frappe.db.sql(
                "INSERT INTO `tabSeries` (name, `current`) VALUES (%s, %s)",
                (new_key, current_value),
            )
            seeded += 1
            logger.info(f"[LBS] Seeded {new_key} = {current_value} (from {old_key})")
        else:
            existing_value = existing[0][0] or 0
            if existing_value < current_value:
                frappe.db.sql(
                    "UPDATE `tabSeries` SET `current` = %s WHERE name = %s",
                    (current_value, new_key),
                )
                seeded += 1
                logger.info(
                    f"[LBS] Raised {new_key} {existing_value} -> {current_value} (from {old_key})"
                )

    frappe.db.commit()
    logger.info(f"[LBS] seed_dbn_cdn_counters patch complete — {seeded} rows updated")
