# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

from __future__ import unicode_literals

import frappe, erpnext, json
import frappe.defaults
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from frappe import throw, _
from frappe.utils import formatdate, get_number_format_info
from six import iteritems



@frappe.whitelist()
def check_PO_qty(docname=None, item_names=None, purchase_order_item=None):
	res = []
	item_names = json.loads(item_names)
	purchase_order_item	= json.loads(purchase_order_item)
	for poi in purchase_order_item:		
		res.append(frappe.db.sql("""  select poi.item_name as item_name, poi.name as purchase_order_item, poi.idx as poi_idx, poi.schedule_date as schedule_date, IFNULL(sum(pri.qty),0) as pri_qty, poi.qty as poi_qty from `tabPurchase Receipt Item` pri left join `tabPurchase Order Item` poi on poi.name=pri.purchase_order_item where pri.docstatus < 2 and poi.name='{}' """.format(poi), as_dict=1))

		#  res.append(frappe.db.sql("""  select pri.item_name as item_name,sum(pri.qty) as pri_qty, poi.qty as poi_qty from `tabPurchase Receipt Item` pri left join `tabPurchase Order Item` poi on poi.name=pri.purchase_order_item where pri.docstatus < 2 and pri.purchase_order_item='{}' and pri.item_name='{}'""".format(purchase_order_item[i], item_names[i]), as_dict=1))
	return res