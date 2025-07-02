import frappe
from location_based_series.events.client_scripts import install_client_scripts

def execute():
    """
    Patch to install warehouse filtering client scripts.
    This can be run on existing installations to add the functionality.
    """
    frappe.logger().info("Installing location-based warehouse filtering client scripts...")
    
    try:
        install_client_scripts()
        frappe.logger().info("Successfully installed warehouse filtering client scripts")
    except Exception as e:
        frappe.logger().error(f"Error installing warehouse filtering client scripts: {str(e)}")
        raise 