# -*- coding: utf-8 -*-
# Copyright (c) 2022, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PreProductionPlan(Document):
	def validate(self):
		for item in self.planned_qty:
			item.batch_qty = item.qty/item.batch_size
		self.total_planned_qty = sum(item.qty for item in self.planned_qty)
		self.total_batch_qty = sum(item.batch_qty for item in self.planned_qty)


@frappe.whitelist()
def get_data(item_group=None, target_date=None, month=None, year=None):
	wh_fg = frappe.db.get_list("Warehouse", {"warehouse_type":["in",["Production Output"]]}, ["name"])
	wip = frappe.db.get_list("Warehouse", {"warehouse_type": "Production"}, ["name"])
	items = [i.item for i in frappe.get_doc("PPP Item Group", item_group).item]
	items = ', '.join(['"%s"']*len(items))% tuple(items)

	month_arr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
		"Dec"]

	prev_month = month_arr[int(month)-1]
	next_month = month_arr[(int(month)+1) % len(month_arr)]

	res = {"ams":frappe.db.sql("""SELECT SI.qtya AS ams3, AMS12.qty AS ams12, AMS12.std_val as std_val, TOTAL_SALES.qty AS total_sales
		FROM (SELECT item_code,sum(qty)/3 qtya from `tabSales Invoice Item` WHERE docstatus=1 and creation BETWEEN (SELECT DATE_SUB("{0}", INTERVAL 3 MONTH )) AND "{0}" and item_code IN({1})) SI
		LEFT JOIN (SELECT item_code,sum(qty)/12 qty, std(qty) std_val from `tabSales Invoice Item`
		WHERE docstatus=1 and creation BETWEEN (SELECT DATE_SUB("{0}", INTERVAL 12 MONTH )) AND "{0}" and item_code IN({1})) AMS12 ON AMS12.item_code=SI.item_code
		LEFT JOIN (SELECT item_code,sum(qty) qty, std(qty) std_val from `tabSales Invoice Item`
		WHERE docstatus=1 and creation BETWEEN (SELECT DATE_SUB("{0}", INTERVAL 1 MONTH )) AND "{0}" and item_code IN({1})) TOTAL_SALES ON TOTAL_SALES.item_code=SI.item_code""".format(target_date,
		items), as_dict=True)[0],

			"stock":frappe.db.sql("""SELECT sum(projected_qty) AS qty, warehouse FROM tabBin
		WHERE warehouse IN ({0}) and item_code IN ({1}) group by warehouse""".format(', '.join(['"%s"' % d.name for d in wh_fg]), items), as_dict=True),

		"wip":frappe.db.sql("""SELECT sum(projected_qty) AS qty, warehouse FROM tabBin
		WHERE warehouse IN ({0}) and item_code IN ({1}) group by warehouse""".format(', '.join(['"%s"' % d.name for d in wip]), items), as_dict=True),

			"stock_dist":frappe.db.sql("""SELECT sum(projected_qty) AS qty, warehouse FROM tabBin
		WHERE warehouse REGEXP '^D [A-Z]{3} - [A-Z]{2}' and item_code IN (%s) group by warehouse""" % items, as_dict=True),

			"prevFcRofo":frappe.db.sql("""SELECT forecast, rofo FROM `tabForecast ROFO`
		WHERE month=%s and year=%s and item_group=%s LIMIT 1""",
			(prev_month, year, item_group), as_dict=True)[0],
			"nextFcRofo":frappe.db.sql("""SELECT forecast, rofo FROM `tabForecast ROFO`
		WHERE month=%s and year=%s and item_group=%s LIMIT 1""",
			(next_month, year, item_group), as_dict=True)[0]}

	res['stock_qty']	= sum([i.qty for i in res['stock']])
	res['stock_dist_qty']	= sum([i.qty for i in res['stock_dist']])
	res['wip_qty']	= sum([i.qty for i in res['wip']])

	return res