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

	res = {"ams3":frappe.db.sql("""SELECT sum(i.qty)/3 AS qty from `tabSales Invoice` p LEFT JOIN `tabSales Invoice Item` i ON p.name=i.parent
						WHERE p.docstatus=1 and p.posting_date BETWEEN (SELECT DATE_SUB("{0}", INTERVAL 3 MONTH )) AND "{0}" and i.item_code IN({1})"""
						.format(target_date, items), as_dict=True)[0],

		"ams12": frappe.db.sql("""SELECT sum(i.qty)/12 qty, std(i.qty) std_val from `tabSales Invoice` p LEFT JOIN `tabSales Invoice Item` i ON p.name=i.parent
			WHERE p.docstatus=1 and p.posting_date BETWEEN (SELECT DATE_SUB("{0}", INTERVAL 12 MONTH )) AND "{0}" and i.item_code IN({1})"""
			.format(target_date, items), as_dict=True)[0],

		"total_sales": frappe.db.sql("""SELECT sum(i.qty) AS qty from `tabSales Invoice` p LEFT JOIN `tabSales Invoice Item` i ON p.name=i.parent
			WHERE p.docstatus=1 and p.posting_date BETWEEN (SELECT DATE_SUB("{0}", INTERVAL 1 MONTH )) AND "{0}" and i.item_code IN({1})"""
			.format(target_date, items), as_dict=True)[0],

		"stock":frappe.db.sql("""SELECT sum(actual_qty) AS qty, warehouse FROM tabBin
			WHERE warehouse IN ({0}) and item_code IN ({1}) group by warehouse""".format(', '.join(['"%s"' % d.name for d in wh_fg]), items), as_dict=True),

		"wip":frappe.db.sql("""SELECT sum(actual_qty) AS qty, warehouse FROM tabBin
			WHERE warehouse IN ({0}) and item_code IN ({1}) group by warehouse""".format(', '.join(['"%s"' % d.name for d in wip]), items), as_dict=True),

		"stock_dist":frappe.db.sql("""SELECT sum(actual_qty) AS qty, warehouse FROM tabBin
			WHERE warehouse REGEXP '^D [A-Z]{3} - [A-Z]{2}' and item_code IN (%s) group by warehouse""" % items, as_dict=True),

		"prevFcRofo":frappe.db.sql("""SELECT forecast, rofo FROM `tabSales Forecast`
			WHERE month=%s and year=%s and item_group=%s LIMIT 1""",
				(prev_month, year, item_group), as_dict=True),
		"nextFcRofo":frappe.db.sql("""SELECT forecast, rofo FROM `tabSales Forecast`
			WHERE month=%s and year=%s and item_group=%s LIMIT 1""",
				(next_month, year, item_group), as_dict=True)}

	res['stock_qty']	= sum([i.qty for i in res['stock']])
	res['stock_dist_qty']	= sum([i.qty for i in res['stock_dist']])
	res['wip_qty']	= sum([i.qty for i in res['wip']])

	return res