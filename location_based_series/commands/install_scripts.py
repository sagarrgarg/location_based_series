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