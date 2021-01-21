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


@frappe.whitelist()
def purchase_receipt_on_submit(doc, method): #pr, doc, method
	# if(not pr):
	# 	return {'status': 'pr cannot be empty'}
	# doc = frappe.get_doc('Purchase Receipt', pr)
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = "Material Transfer"
	stock_entry.stock_entry_type = "Material Transfer"
	stock_entry.to_warehouse = "QC Pandaan - QL"

	for d in doc.get('items'):
		if (d.quality_inspection):
			quality_inspection = frappe.get_doc('Quality Inspection', d.quality_inspection)
			if (quality_inspection.sample_size > 0):
				stock_entry.append('items', {'item_code': d.item_code,'item_name': d.item_name,'s_warehouse': d.warehouse, 't_warehouse': 'QC Pandaan - QL', 'qty': quality_inspection.sample_size, 'uom': d.uom, 'remarks': doc.name, 'batch_no': d.batch_no, 'parent': quality_inspection.name, 'parentfield': 'material_transfer', 'parenttype': 'Quality Inspection' }) #

	try:
		stock_entry.insert(ignore_permissions=True)
		stock_entry.add_comment('Comment', text=doc.name)
		stock_entry.submit()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
	return stock_entry.as_dict()



def purchase_receipt_validate(doc, method):
	'''Checks if quality inspection is set for Items that require inspection.
		On submit, throw an exception'''
	inspection_required_fieldname = None

	# if self.doctype in ["Purchase Receipt", "Purchase Invoice"]:
	# 	inspection_required_fieldname = "inspection_required_before_purchase"
	# elif self.doctype in ["Delivery Note", "Sales Invoice"]:
	# 	inspection_required_fieldname = "inspection_required_before_delivery"

	# if ((not inspection_required_fieldname and self.doctype != "Stock Entry") or
	# 	(self.doctype == "Stock Entry" and not self.inspection_required) or
	# 	(self.doctype in ["Sales Invoice", "Purchase Invoice"] and not self.update_stock)):
	# 		return

	# for d in self.get('items'):
	# 	qa_required = False
	# 	if (inspection_required_fieldname and not d.quality_inspection and
	# 		frappe.db.get_value("Item", d.item_code, inspection_required_fieldname)):
	# 		qa_required = True
	# 	elif self.doctype == "Stock Entry" and not d.quality_inspection and d.t_warehouse:
	# 		qa_required = True
	# 	if self.docstatus == 1 and d.quality_inspection:
	# 		qa_doc = frappe.get_doc("Quality Inspection", d.quality_inspection)
	# 		if qa_doc.docstatus == 0:
	# 			link = frappe.utils.get_link_to_form('Quality Inspection', d.quality_inspection)
	# 			frappe.throw(_("Quality Inspection: {0} is not submitted for the item: {1} in row {2}").format(link, d.item_code, d.idx), QualityInspectionNotSubmittedError)

	# 		qa_failed = any([r.status=="Rejected" for r in qa_doc.readings])
	# 		if qa_failed:
	# 			frappe.throw(_("Row {0}: Quality Inspection rejected for item {1}")
	# 				.format(d.idx, d.item_code), QualityInspectionRejectedError)
	# 	elif qa_required :
	# 		action = frappe.get_doc('Stock Settings').action_if_quality_inspection_is_not_submitted
	# 		if self.docstatus==1 and action == 'Stop':
	# 			frappe.throw(_("Quality Inspection required for Item {0} to submit").format(frappe.bold(d.item_code)),
	# 				exc=QualityInspectionRequiredError)
	# 		else:
	# 			frappe.msgprint(_("Create Quality Inspection for Item {0}").format(frappe.bold(d.item_code)))
	# for item in doc.items:
	# 	if not item.quality_inspection:
	# 		qi = frappe.new_doc('Quality Inspection')
	# 		qi.item_code = item.item_code
	# 		qi.report_date = nowdate()
	# 		qi.sample_size = 0.00
	# 		qi.inspection_type = 'Incoming'
	# 		qi.reference_type = 'Purchase Receipt'
	# 		qi.save()
