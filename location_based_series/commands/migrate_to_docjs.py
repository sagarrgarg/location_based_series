import frappe
from frappe.commands import pass_context, get_site
from frappe.utils import cint

@pass_context
def migrate_to_docjs(context):
    """Migrate from client scripts to doc.js files for location-based warehouse filtering."""
    
    site = get_site(context)
    frappe.init(site=site)
    frappe.connect()
    
    try:
        # Clear existing client scripts
        from location_based_series.install import clear_existing_client_scripts
        clear_existing_client_scripts()
        
        print("✓ Successfully migrated to doc.js files")
        print("✓ Removed existing client scripts")
        print("✓ Doc.js files are now loaded automatically via hooks.py")
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        frappe.db.rollback()
    finally:
        frappe.destroy()

def migrate_to_docjs_command():
    """Command to migrate from client scripts to doc.js files."""
    migrate_to_docjs() 