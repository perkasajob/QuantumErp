# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, date_diff

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 80
		},
		{
			"label": _("Account Head"),
			"options": "Account",
			"fieldname": "account_head",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"options": "Sales Invoice",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Purchase Invoice"),
			"fieldname": "purchase_invoice",
			"options": "Purchase Invoice",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Tax Date"),
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 80
		},
		{
			"label": _("Reference Number"),
			"fieldname": "reference_number",
			"fieldtype": "Data",
			"width": 140
		},
		{
			"label": _("Rate"),
			"fieldname": "rate",
			"fieldtype": "Float",
			"width": 50
		},
		{
			"label": _("Total"),
			"fieldname": "total",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Tax Amount"),
			"fieldname": "tax_amount",
			"fieldtype": "Float",
			"width": 140
		}
	]
	return columns

def get_conditions(filters):
	conditions = ""

	if filters.get("account_head"):
		conditions += """
			AND (child.`account_head`=%s)
			""" % (frappe.db.escape(filters.get('account_head')))

	if filters.get("from_date"):
		conditions += " AND parent.posting_date>='%s'" % filters.get('from_date')

	if filters.get("to_date"):
		conditions += " AND parent.posting_date<='%s'" % filters.get('to_date')
	return conditions

def get_mapped_tax(conditions):
	mr_details = frappe.db.sql("""
		SELECT
			parent.name as sales_invoice,
			NULL as purchase_invoice,
			parent.title,
			parent.posting_date,
			child.parenttype,
			child.account_head,
			NULL as date,
			NULL as reference_number,
			child.rate,
			child.tax_amount,
			child.total
		FROM `tabSales Invoice` parent, `tabSales Taxes and Charges` child
		WHERE
			parent.docstatus=1
			AND parent.name = child.parent
			{conditions}
		UNION
		SELECT
			NULL as sales_invoice,
			parent.name as purchase_invoice,
			parent.title,
			parent.posting_date,
			child.parenttype,
			child.account_head,
			child.date,
			child.reference_number,
			child.rate,
			child.tax_amount,
			child.total
		FROM `tabPurchase Invoice` parent, `tabPurchase Taxes and Charges` child
		WHERE
			parent.docstatus=1
			AND parent.name = child.parent
			{conditions}
		ORDER BY posting_date
		""".format(conditions=conditions), as_dict=1) #nosec


	return mr_details

def get_data(filters):
	conditions = get_conditions(filters)
	return get_mapped_tax(conditions)

