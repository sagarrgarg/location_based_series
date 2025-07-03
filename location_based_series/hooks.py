app_name = "location_based_series"
app_title = "Location Based Series"
app_publisher = "Sagar"
app_description = "dds location-based naming conventions and validation for transactional documents like Sales and Purchase Invoices."
app_email = "sagar1ratan1garg1@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "location_based_series",
# 		"logo": "/assets/location_based_series/logo.png",
# 		"title": "Location Based Series",
# 		"route": "/location_based_series",
# 		"has_permission": "location_based_series.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/location_based_series/css/location_based_series.css"
# app_include_js = "/assets/location_based_series/js/location_based_series.js"

# include js, css files in header of web template
# web_include_css = "/assets/location_based_series/css/location_based_series.css"
# web_include_js = "/assets/location_based_series/js/location_based_series.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "location_based_series/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
    "Purchase Invoice": "public/js/purchase_invoice.js", 
    "Sales Order": "public/js/sales_order.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Purchase Receipt": "public/js/purchase_receipt.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "location_based_series/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "location_based_series.utils.jinja_methods",
# 	"filters": "location_based_series.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "location_based_series.install.before_install"
after_install = "location_based_series.install.clear_existing_client_scripts"
# after_install = "location_based_series.install.set_autoname_for_target_doctypes"

# Uninstallation
# ------------

# before_uninstall = "location_based_series.events.client_scripts.uninstall_client_scripts"
# after_uninstall = "location_based_series.uninstall.after_uninstall"
# before_uninstall = "location_based_series.uninstall.revert_autoname_for_target_doctypes"
# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "location_based_series.utils.before_app_install"
# after_app_install = "location_based_series.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "location_based_series.utils.before_app_uninstall"
# after_app_uninstall = "location_based_series.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "location_based_series.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Sales Invoice": {
        "autoname": "location_based_series.events.naming.custom_autoname",
        "validate": "location_based_series.events.validation.validate_doc"
    },
    "Purchase Invoice": {
        "autoname": "location_based_series.events.naming.custom_autoname",
        "validate": "location_based_series.events.validation.validate_doc"
    },
    "Sales Order": {
        "autoname": "location_based_series.events.naming.custom_autoname",
        "validate": "location_based_series.events.validation.validate_doc"
    },
    "Purchase Order": {
        "autoname": "location_based_series.events.naming.custom_autoname",
        "validate": "location_based_series.events.validation.validate_doc"
    },
    "Delivery Note": {
        "autoname": "location_based_series.events.naming.custom_autoname",
        "validate": "location_based_series.events.validation.validate_doc"
    },
    "Purchase Receipt": {
        "autoname": "location_based_series.events.naming.custom_autoname",
        "validate": "location_based_series.events.validation.validate_doc"
    }
}

fixtures = [{"doctype": "Custom Field", "filters": [["module" , "in" , ("Location Based Series" )]]},]



# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"location_based_series.tasks.all"
# 	],
# 	"daily": [
# 		"location_based_series.tasks.daily"
# 	],
# 	"hourly": [
# 		"location_based_series.tasks.hourly"
# 	],
# 	"weekly": [
# 		"location_based_series.tasks.weekly"
# 	],
# 	"monthly": [
# 		"location_based_series.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "location_based_series.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "location_based_series.event.get_events"
# }
override_whitelisted_methods = {
    "posawesome.posawesome.api.posapp.update_invoice": "location_based_series.patches.override_posawesome.update_invoice"
}

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "location_based_series.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["location_based_series.utils.before_request"]
# after_request = ["location_based_series.utils.after_request"]

# Job Events
# ----------
# before_job = ["location_based_series.utils.before_job"]
# after_job = ["location_based_series.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"location_based_series.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

