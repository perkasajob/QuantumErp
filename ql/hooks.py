# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "ql"
app_title = "QL"
app_publisher = "Perkasa JoB"
app_description = "Supporting Future of Medicine"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "perkasajob@gmail.com"
app_license = "MIT"
app_logo_url = '/assets/ql/images/logo.png'

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ql/css/ql.css"
app_include_css = ["/assets/css/ql.css"]
# app_include_js = "/assets/ql/js/ql.js"
app_include_js = ["/assets/ql/js/base_control.js"]

# include js, css files in header of web template
# web_include_css = "/assets/ql/css/ql.css"
# web_include_js = "/assets/ql/js/ql.js"

# include js in page
# page_js = {"Stock Ledger" : "public/js/stock_ledger.js"}

# include js in doctype views
doctype_js = {"Sales Order" : "public/js/sales_order.js","Sales Invoice" : "public/js/sales_invoice.js","Purchase Order" : "public/js/purchase_order.js", "Purchase Receipt" : "public/js/purchase_receipt.js", "Purchase Invoice" : "public/js/purchase_invoice.js", "Quality Inspection" : "public/js/quality_inspection.js","Material Request" : "public/js/material_request.js","Stock Entry" : "public/js/stock_entry.js","Batch" : "public/js/batch.js","Job Card" : "public/js/job_card.js","Pick List" : "public/js/pick_list.js","Warehouse" : "public/js/warehouse.js","Work Order" : "public/js/work_order.js","BOM" : "public/js/bom.js", "Payment Entry" : "public/js/payment_entry.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# doctype_js = {"Kanban Board" : "public/js/kanban_board.js"}
doctype_tree_js = {"Warehouse" : "public/js/warehouse_list.js"}
doctype_list_js = {"Purchase Order" : "public/js/purchase_order_list.js", "Purchase Receipt" : "public/js/purchase_receipt_list.js", "Project" : "public/js/kanban_list.js"}
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "ql.utils.get_home_page"

has_website_permission = {
	"Good Receipt": "ql.ql.web_form.good_receipt.good_receipt.has_website_permission",
}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

website_context = {
    "favicon": "/assets/ql/images/favicon.png",
    "splash_image": "/assets/ql/images/splashLogo.png"
}

# Installation
# ------------

# before_install = "ql.install.before_install"
# after_install = "ql.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ql.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Employee Advance": "ql.ql.permissions.ea_query_perm",
	"Expense Claim": "ql.ql.permissions.ec_query_perm"
}
	# "Cash Expense Claim": "ql.ql.permissions.cec_query_perm",
	# "Cash Advance Request": "ql.ql.permissions.car_query_perm",

#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }
doc_events = {
	# "*": {
	# 	"before_save": "ql.overrides.before_save"
	# },
	"Material Request": {
		"validate": "ql.ql.buying.update_completed_with_draft_qty"
	},
	"Purchase Receipt": {
		"on_submit":"ql.ql.stock.purchase_receipt_on_submit",
		"validate":"ql.ql.stock.purchase_receipt_validate",
	},
	"Work Order": {
		"validate":"ql.ql.work_order.work_order_validate",
	}
}


# Scheduled Tasks
# ---------------
scheduler_events = {
	"daily": [
		"ql.ql.tasks.daily"
	]
}

# Testing
# -------

# before_tests = "ql.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ql.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ql.task.get_dashboard_data"
# }

override_whitelisted_methods = {
	"frappe.desk.query_report.run": "ql.ql.events.run",
	"erpnext.buying.doctype.purchase_order.purchase_order.make_rm_stock_entry" :"ql.ql.stock.make_rm_stock_entry",
	"erpnext.stock.doctype.pick_list.pick_list.create_stock_entry" :"ql.ql.pick_list.create_stock_entry",
	"erpnext.stock.doctype.material_request.material_request.raise_work_orders" :"ql.ql.work_order.raise_work_orders",
	# "erpnext.manufacturing.doctype.work_order.work_order.create_pick_list" :"ql.ql.work_order.create_pick_list",
}

override_doctype_class = {
	'Work Order': 'ql.ql.work_order.QLWorkOrder',
	'Job Card': 'ql.ql.job_card.QLJobCard',
	'Stock Entry': 'ql.ql.stock_entry.QLStockEntry',
	'Pick List': 'ql.ql.pick_list.QLPickList',
	'Material Request': 'ql.ql.material_request.QLMaterialRequest',
}

before_migrate = "ql.migrate.before_migrate"

#'erpnext.erpnext.utilities.transaction_base.'
default_mail_footer = """
    <div>
        Sent via <a href="http://qs.quantum-laboratories.com//" target="_blank">Quantum Laboratories</a>
    </div>
"""

