# Copyright (c) 2013, Perkasa JoB and contributors
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
			"label": _("Material Request Date"),
			"fieldname": "material_request_date",
			"fieldtype": "Date",
			"width": 140
		},
		{
			"label": _("Material Request No"),
			"options": "Material Request",
			"fieldname": "material_request_no",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Cost Center"),
			"options": "Cost Center",
			"fieldname": "cost_center",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Project"),
			"options": "Project",
			"fieldname": "project",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Requesting Site"),
			"options": "Warehouse",
			"fieldname": "requesting_site",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Requestor"),
			"options": "Employee",
			"fieldname": "requestor",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Item"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150
		},
		{
			"label": _("Quantity"),
			"fieldname": "quantity",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Unit of Measure"),
			"options": "UOM",
			"fieldname": "unit_of_measurement",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "data",
			"width": 140
		},
		{
			"label": _("Purchase Order Date"),
			"fieldname": "purchase_order_date",
			"fieldtype": "Date",
			"width": 140
		},
		{
			"label": _("Purchase Order"),
			"options": "Purchase Order",
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Supplier"),
			"options": "Supplier",
			"fieldname": "supplier",
			"fieldtype": "Link",
			"width": 140
		},
		{
			"label": _("Estimated Cost"),
			"fieldname": "estimated_cost",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Actual Cost"),
			"fieldname": "actual_cost",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Purchase Order Amount"),
			"fieldname": "purchase_order_amt",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Purchase Order Amount(Company Currency)"),
			"fieldname": "purchase_order_amt_in_company_currency",
			"fieldtype": "Float",
			"width": 140
		},
		{
			"label": _("Expected Delivery Date"),
			"fieldname": "expected_delivery_date",
			"fieldtype": "Date",
			"width": 140
		},
		{
			"label": _("Actual Delivery Date"),
			"fieldname": "actual_delivery_date",
			"fieldtype": "Date",
			"width": 140
		},
		{
			"label": _("Delivery Different"),
			"fieldname": "delivery_diff",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Actual Lead Time"),
			"fieldname": "actual_lead_time",
			"fieldtype": "Int",
			"width": 100
		},
	]
	return columns

def get_conditions(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " AND parent.company=%s" % frappe.db.escape(filters.get('company'))

	if filters.get("cost_center") or filters.get("project"):
		conditions += """
			AND (child.`cost_center`=%s OR child.`project`=%s)
			""" % (frappe.db.escape(filters.get('cost_center')), frappe.db.escape(filters.get('project')))

	if filters.get("from_date"):
		conditions += " AND parent.transaction_date>='%s'" % filters.get('from_date')

	if filters.get("to_date"):
		conditions += " AND parent.transaction_date<='%s'" % filters.get('to_date')
	return conditions

def get_data(filters):
	conditions = get_conditions(filters)
	purchase_order_entry = get_po_entries(conditions)
	mr_records, procurement_record_against_mr = get_mapped_mr_details(conditions)
	pr_records = get_mapped_pr_records()
	pi_records = get_mapped_pi_records()

	procurement_record=[]
	if procurement_record_against_mr:
		procurement_record += procurement_record_against_mr
	for po in purchase_order_entry:
		# fetch material records linked to the purchase order item
		mr_record = mr_records.get(po.material_request_item, [{}])[0]
		procurement_detail = {
			"material_request_date": mr_record.get('transaction_date'),
			"cost_center": po.cost_center,
			"project": po.project,
			"requesting_site": po.warehouse,
			"requestor": po.owner,
			"material_request_no": po.material_request,
			"item_code": po.item_code,
			"quantity": flt(po.qty),
			"unit_of_measurement": po.stock_uom,
			"status": po.status,
			"purchase_order_date": po.transaction_date,
			"purchase_order": po.parent,
			"supplier": po.supplier,
			"estimated_cost": flt(mr_record.get('amount')),
			"actual_cost": flt(pi_records.get(po.name)),
			"purchase_order_amt": flt(po.amount),
			"purchase_order_amt_in_company_currency": flt(po.base_amount),
			"expected_delivery_date": po.schedule_date,
			"actual_delivery_date": pr_records.get(po.name),
			"delivery_diff": date_diff(po.schedule_date, pr_records.get(po.name)),
			"actual_lead_time" : date_diff(pr_records.get(po.name), po.transaction_date)
		}
		procurement_record.append(procurement_detail)
	return procurement_record