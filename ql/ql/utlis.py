# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

from __future__ import unicode_literals

import frappe, erpnext, json, math
import frappe.defaults
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from frappe import throw, _
from frappe.utils import formatdate, get_number_format_info
from six import iteritems, string_types
from datetime import datetime

@frappe.whitelist()
def get_latest_stock_qty(item_code, warehouse=None, project="", work_order=""):
	values, condition = [item_code], ""
	if warehouse:
		lft, rgt, is_group = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt", "is_group"])

		if is_group:
			values.extend([lft, rgt])
			condition += "and exists (\
				select name from `tabWarehouse` wh where wh.name = tabBin.warehouse\
				and wh.lft >= %s and wh.rgt <= %s)"

		else:
			values.append(warehouse)
			condition += " AND warehouse = %s"

	actual_qty = frappe.db.sql("""select sum(actual_qty) from tabBin
		where item_code=%s {0}""".format(condition), values)[0][0]

	return actual_qty