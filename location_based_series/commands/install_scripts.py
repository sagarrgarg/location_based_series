import frappe
from location_based_series.events.client_scripts import install_client_scripts, uninstall_client_scripts


def install_warehouse_filtering():
    """
    Console command to install warehouse filtering client scripts.
    Usage: frappe.call('location_based_series.commands.install_scripts.install_warehouse_filtering')
    """
    try:
        install_client_scripts()
        print("✅ Successfully installed warehouse filtering client scripts")
        return "Success"
    except Exception as e:
        print(f"❌ Error installing scripts: {str(e)}")
        return f"Error: {str(e)}"


def uninstall_warehouse_filtering():
    """
    Console command to uninstall warehouse filtering client scripts.
    Usage: frappe.call('location_based_series.commands.install_scripts.uninstall_warehouse_filtering')
    """
    try:
        uninstall_client_scripts()
        print("✅ Successfully uninstalled warehouse filtering client scripts")
        return "Success"
    except Exception as e:
        print(f"❌ Error uninstalling scripts: {str(e)}")
        return f"Error: {str(e)}"


def reinstall_warehouse_filtering():
    """
    Console command to reinstall warehouse filtering client scripts.
    Usage: frappe.call('location_based_series.commands.install_scripts.reinstall_warehouse_filtering')
    """
    try:
        print("🔄 Uninstalling existing scripts...")
        uninstall_client_scripts()
        print("🔄 Installing updated scripts...")
        install_client_scripts()
        print("✅ Successfully reinstalled warehouse filtering client scripts")
        return "Success"
    except Exception as e:
        print(f"❌ Error reinstalling scripts: {str(e)}")
        return f"Error: {str(e)}" 


def install_shipping_location_functionality():
    """
    Console command to install shipping location functionality.
    This includes custom fields and client scripts for shipping location support.
    Usage: frappe.call('location_based_series.commands.install_scripts.install_shipping_location_functionality')
    """
    try:
        # Install custom fields from fixtures
        print("🔄 Installing custom fields for shipping location...")
        frappe.call('frappe.desk.page.setup_wizard.setup_wizard.load_custom_fields')
        
        # Install client scripts
        print("🔄 Installing client scripts for shipping location...")
        install_client_scripts()
        
        print("✅ Successfully installed shipping location functionality")
        print("📝 Features installed:")
        print("   - Shipping Location field for PO, PI, PR")
        print("   - Address filtering based on shipping location")
        print("   - Warehouse filtering based on shipping location")
        print("   - Auto-selection of shipping address and warehouse")
        print("   - Validation for shipping location requirements")
        
        return "Success"
    except Exception as e:
        print(f"❌ Error installing shipping location functionality: {str(e)}")
        return f"Error: {str(e)}"


def uninstall_shipping_location_functionality():
    """
    Console command to uninstall shipping location functionality.
    Usage: frappe.call('location_based_series.commands.install_scripts.uninstall_shipping_location_functionality')
    """
    try:
        # Remove custom fields
        print("🔄 Removing shipping location custom fields...")
        custom_fields = [
            "Purchase Order-custom_shipping_location",
            "Purchase Invoice-custom_shipping_location", 
            "Purchase Receipt-custom_shipping_location"
        ]
        
        for field_name in custom_fields:
            if frappe.db.exists("Custom Field", field_name):
                frappe.delete_doc("Custom Field", field_name)
                print(f"   - Removed {field_name}")
        
        # Uninstall client scripts
        print("🔄 Uninstalling client scripts...")
        uninstall_client_scripts()
        
        print("✅ Successfully uninstalled shipping location functionality")
        return "Success"
    except Exception as e:
        print(f"❌ Error uninstalling shipping location functionality: {str(e)}")
        return f"Error: {str(e)}"


def reinstall_shipping_location_functionality():
    """
    Console command to reinstall shipping location functionality.
    Usage: frappe.call('location_based_series.commands.install_scripts.reinstall_shipping_location_functionality')
    """
    try:
        print("🔄 Uninstalling existing shipping location functionality...")
        uninstall_shipping_location_functionality()
        print("🔄 Installing updated shipping location functionality...")
        install_shipping_location_functionality()
        print("✅ Successfully reinstalled shipping location functionality")
        return "Success"
    except Exception as e:
        print(f"❌ Error reinstalling shipping location functionality: {str(e)}")
        return f"Error: {str(e)}" 