# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

from __future__ import unicode_literals

import frappe, erpnext, json, math
import frappe.defaults
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from frappe import throw, _
from frappe.utils import formatdate, get_number_format_info
from six import iteritems



def update_completed_with_draft_qty(self, mr_items=None, update_modified=True):
		if self.material_request_type == "Purchase":
			if self.department == "PPIC":
				for d in self.get("items"):
					require_project = frappe.db.get_value('Item', d.item_code, 'require_project')
					if require_project and not d.project:
						frappe.throw("Item {0} on row {1} need a Project").format(d.item_code, d.ID)
			return

		if not mr_items:
			mr_items = [d.name for d in self.get("items")]

		for d in self.get("items"):
			if d.name in mr_items:
				if self.material_request_type in ("Material Issue", "Material Transfer", "Customer Provided"):
					d.ordered_qty =  flt(frappe.db.sql("""select sum(transfer_qty)
						from `tabStock Entry Detail` where material_request = %s
						and material_request_item = %s and docstatus = 1 or docstatus = 0""",
						(self.name, d.name))[0][0])

					# frappe.msgprint("this is it !!")
					if d.ordered_qty and d.ordered_qty > d.stock_qty:
						frappe.throw(_("The total Issue / Transfer quantity {0} in Material Request {1}  \
							cannot be greater than requested quantity {2} for Item {3}").format(d.ordered_qty, d.parent, d.qty, d.item_code))

				elif self.material_request_type == "Manufacture":
					d.ordered_qty = flt(frappe.db.sql("""select sum(qty)
						from `tabWork Order` where material_request = %s
						and material_request_item = %s and docstatus = 1 or docstatus = 0""",
						(self.name, d.name))[0][0])

				frappe.db.set_value(d.doctype, d.name, "ordered_qty", d.ordered_qty)