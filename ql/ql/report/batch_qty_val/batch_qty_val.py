# Copyright (c) 2021, Perkasa JoB and contributors
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
			"label": _("Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 80
		},
		{
			"label": "Batch No",
			"options": "Batch",
			"fieldname": "batch_no",
			"fieldtype": "Link",
			"width": 80
		},
		{
			"label": "Item",
			"options": "Item",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"width": 80
		},
		{
			"label": "Item Name",
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": "Warehouse",
			"options": "Warehouse",
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"width": 100
		},
		{
			"label": "Qty",
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 80
		},
		{
			"label": "Valuation Rate",
			"fieldname": "valuation_rate",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": "Stock Value",
			"fieldname": "stock_value",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": "UoM",
			"fieldname": "uom",
			"fieldtype": "Data",
			"width": 80
		},
		{
			"label": "Exp Date",
			"fieldname": "expiry_date",
			"fieldtype": "Data",
			"width": 80
		}
	]
	return columns

def get_conditions(filters):
	conditions = ""

	if filters.get("end_date"):
		conditions += "sle.posting_date < {}".format(frappe.db.escape(filters.get('end_date')))

	if filters.get("batch_no_flt"):
		conditions += " AND sle.batch_no = {}".format(frappe.db.escape(filters.get('batch_no_flt')))

	if filters.get("warehouse"):
		conditions += " AND sle.warehouse = {}".format(frappe.db.escape(filters.get('warehouse')))

	return conditions

def get_data(filters):
	conditions = get_conditions(filters)
	batches = get_mapped_batches_details(conditions)

	return batches

def get_mapped_batches_details(conditions):
	batches_details = frappe.db.sql("""
    SELECT
			sle.posting_date,
			sle.batch_no,
			sle.item_code,
			i.item_name,
			sle.warehouse,
			SUM(sle.actual_qty) as qty,
			sl.valuation_rate as valuation_rate,
			sl.valuation_rate * SUM(sle.actual_qty) as stock_value,
			sle.stock_uom as uom,
			b.expiry_date
		FROM
			`tabStock Ledger Entry` sle
		INNER JOIN 	(SELECT sli.* FROM (SELECT item_code, warehouse, valuation_rate, first_value(valuation_rate) over (partition by item_code, warehouse order by posting_date DESC) AS val_rate FROM  `tabStock Ledger Entry`)
		    sli GROUP BY sli.item_code, sli.warehouse) sl
			ON sle.item_code = sl.item_code AND sle.warehouse = sl.warehouse
		INNER JOIN
			`tabItem` i ON sle.item_code = i.item_code
		INNER JOIN
			`tabBatch` b ON sle.batch_no = b.name
		WHERE {conditions}
		GROUP BY sle.warehouse, sle.batch_no
		HAVING SUM(sle.actual_qty) > 0
		ORDER BY sle.posting_date ASC
		""".format(conditions=conditions), as_dict=1) #nosec

	return batches_details