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
from erpnext.controllers.buying_controller import BuyingController



@frappe.whitelist()
def check_PO_qty(docname=None, item_names=None, purchase_order_item=None):
	res = []
	item_names = json.loads(item_names)
	purchase_order_item	= json.loads(purchase_order_item)
	for poi in purchase_order_item:
		res.append(frappe.db.sql("""  select poi.item_name as item_name, poi.name as purchase_order_item, poi.idx as poi_idx, poi.schedule_date as schedule_date, IFNULL(sum(pri.qty),0) as pri_qty, poi.qty as poi_qty from `tabPurchase Receipt Item` pri left join `tabPurchase Order Item` poi on poi.name=pri.purchase_order_item where pri.docstatus < 2 and poi.name='{}' """.format(poi), as_dict=1))

		#  res.append(frappe.db.sql("""  select pri.item_name as item_name,sum(pri.qty) as pri_qty, poi.qty as poi_qty from `tabPurchase Receipt Item` pri left join `tabPurchase Order Item` poi on poi.name=pri.purchase_order_item where pri.docstatus < 2 and pri.purchase_order_item='{}' and pri.item_name='{}'""".format(purchase_order_item[i], item_names[i]), as_dict=1))
	return res

class QLPurchaseInvoice(BuyingController):
	def validate_with_previous_doc(self):
		super(PurchaseInvoice, self).validate_with_previous_doc({
			"Purchase Order": {
				"ref_dn_field": "purchase_order",
				"compare_fields": [["supplier", "="], ["company", "="], ["currency", "="]],
			},
			"Purchase Order Item": {
				"ref_dn_field": "po_detail",
				"compare_fields": [["project", "="], ["item_code", "="], ["uom", "="]],
				"is_child_table": True,
				"allow_duplicate_prev_row_id": True
			},
			"Purchase Receipt": {
				"ref_dn_field": "purchase_receipt",
				"compare_fields": [["supplier", "="], ["company", "="], ["currency", "="]],
			},
			"Purchase Receipt Item": {
				"ref_dn_field": "pr_detail",
				"compare_fields": [["project", "="], ["item_code", "="], ["uom", "="]],
				"is_child_table": True
			}
		})

		if cint(frappe.db.get_single_value('Buying Settings', 'maintain_same_rate')) and not self.is_return:
			self.validate_rate_with_reference_doc([
				["Purchase Order", "purchase_order", "po_detail"],
				["Purchase Receipt", "purchase_receipt", "pr_detail"]
			])