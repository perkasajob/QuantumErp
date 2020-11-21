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
# app_include_js = "/assets/ql/js/ql.js"

# include js, css files in header of web template
# web_include_css = "/assets/ql/css/ql.css"
# web_include_js = "/assets/ql/js/ql.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

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

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
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
	"Sales Invoice": {
		"validate": "ql.ql.sales.update_discount"
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ql.tasks.all"
# 	],
# 	"daily": [
# 		"ql.tasks.daily"
# 	],
# 	"hourly": [
# 		"ql.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ql.tasks.weekly"
# 	]
# 	"monthly": [
# 		"ql.tasks.monthly"
# 	]
# }

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

default_mail_footer = """
    <div>
        Sent via <a href="http://qs.quantum-laboratories.com//" target="_blank">Quantum Laboratories</a>
    </div>
"""

