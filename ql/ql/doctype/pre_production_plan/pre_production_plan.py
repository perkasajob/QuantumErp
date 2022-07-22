# -*- coding: utf-8 -*-
# Copyright (c) 2022, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PreProductionPlan(Document):
	pass

@frappe.whitelist()
def get_data(item_code=None, target_date=None, month=None, year=None):
	wh_fg = frappe.db.get_list("Warehouse", {"warehouse_type":["in",["Production","Production Output"]]}, ["name"])


	month_arr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
		"Dec"]

	prev_month = month_arr[int(month)-1]
	next_month = month_arr[(int(month)+1) % len(month_arr)]

	#warehouse IN (%(wh_fg)s) and
	return {"ams":frappe.db.sql("""SELECT SI.item_code, SI.qtya AS ams3, AMS12.qty AS ams12, AMS12.std_val as std_val, TOTAL_SALES.qty AS total_sales
	FROM (SELECT item_code,sum(qty)/3 qtya from `tabSales Invoice Item` WHERE docstatus=1 and creation > (SELECT DATE_SUB(%(target_date)s, INTERVAL 3 MONTH )) and item_code=%(item_code)s) SI
	LEFT JOIN (SELECT item_code,sum(qty)/12 qty, std(qty) std_val from `tabSales Invoice Item`
	WHERE docstatus=1 and creation > (SELECT DATE_SUB(%(target_date)s, INTERVAL 12 MONTH )) and item_code=%(item_code)s) AMS12 ON AMS12.item_code=SI.item_code
	LEFT JOIN (SELECT item_code,sum(qty) qty, std(qty) std_val from `tabSales Invoice Item`
	WHERE docstatus=1 and creation > (SELECT DATE_SUB(%(target_date)s, INTERVAL 1 MONTH )) and item_code=%(item_code)s) TOTAL_SALES ON TOTAL_SALES.item_code=SI.item_code""",
		{"target_date": target_date, "item_code":item_code}, as_dict=True)[0],

		"stock":frappe.db.sql("""SELECT projected_qty AS qty, warehouse FROM tabBin
	 WHERE warehouse IN (%(wh_fg)s) and item_code=%(item_code)s""" ,
		{"wh_fg":', '.join(['"%s"' % d.name for d in wh_fg]), "item_code":item_code}, as_dict=True),

		"stock_dist":frappe.db.sql("""SELECT projected_qty AS qty, warehouse FROM tabBin
	 WHERE warehouse REGEXP '^D [A-Z]{3} - [A-Z]{2}' and item_code=%(item_code)s""",
		{ "item_code":item_code}, as_dict=True),

		"prevFcRofo":frappe.db.sql("""SELECT forecast, rofo FROM `tabForecast ROFO`
	 WHERE month=%s and year=%s and item_code=%s LIMIT 1""",
		(prev_month, year, item_code), as_dict=True),
		"nextFcRofo":frappe.db.sql("""SELECT forecast, rofo FROM `tabForecast ROFO`
	 WHERE month=%s and year=%s and item_code=%s LIMIT 1""",
		(next_month, year, item_code), as_dict=True)}



# return {"ams":frappe.db.sql("""SELECT SI.item_code,FORMAT(SI.qtya, 2) AS ams3, FORMAT(AMS12.qty,2) AS ams12, BIN.projected_qty, BIN.warehouse
# 	FROM (SELECT item_code,avg(qty) qtya from `tabSales Invoice Item` WHERE docstatus=1 and creation > (SELECT DATE_SUB(%(target_date)s, INTERVAL 3 MONTH )) GROUP BY item_code) SI
# 	LEFT JOIN tabBin BIN ON BIN.item_code= SI.item_code
# 	LEFT JOIN (SELECT item_code,avg(qty) qty from `tabSales Invoice Item`
# 	WHERE docstatus=1 and creation > (SELECT DATE_SUB(%(target_date)s, INTERVAL 12 MONTH )) GROUP BY item_code) AMS12 ON AMS12.item_code=SI.item_code WHERE warehouse REGEXP '^D [A-Z]{3} - [A-Z]{2}' and BIN.item_code=%(item_code)s""",
# 		{"target_date": target_date, "item_code":item_code}, as_dict=True),