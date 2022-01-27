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
from datetime import datetime
from six import string_types
from erpnext.buying.doctype.purchase_order.purchase_order import get_item_details

from erpnext.controllers.stock_controller import StockController
class QualityInspectionRequiredError(frappe.ValidationError): pass
class QualityInspectionRejectedError(frappe.ValidationError): pass
class QualityInspectionNotSubmittedError(frappe.ValidationError): pass


@frappe.whitelist()
def purchase_receipt_on_submit(doc, method): #pr, doc, method
	# if(not pr):
	# 	return {'status': 'pr cannot be empty'}
	# doc = frappe.get_doc('Purchase Receipt', pr)
	ql_settings = frappe.get_doc('QL Settings')
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = "Material Issue"
	stock_entry.stock_entry_type = "Material Issue"
	stock_entry.to_warehouse = ql_settings.qi_warehouse
	need_inspection = False

	for d in doc.get('items'):
		if (d.quality_inspection):
			quality_inspection = frappe.get_doc('Quality Inspection', d.quality_inspection)
			if quality_inspection.sample_size > 0 and quality_inspection.status != "Rejected":
				stock_entry.append('items', {'item_code': d.item_code,'item_name': d.item_name,'s_warehouse': d.warehouse, 'qty': quality_inspection.sample_size, 'conversion_factor': d.conversion_factor, 'uom': d.stock_uom, 'remarks': doc.name, 'batch_no': d.batch_no }) #, 'parent': quality_inspection.name, 'parentfield': 'material_transfer', 'parenttype': 'Quality Inspection'
				need_inspection = True
		if doc.is_subcontracted and d.project:
			pri_qty = frappe.db.sql(""" select ifnull(sum(pri.qty), 0)
				from
					`tabPurchase Receipt` pr, `tabPurchase Receipt Item` pri
				where
					pri.project = %s and pri.parent = pr.name and pr.docstatus = 1
					""", d.project, as_list=1)
			pri_qty = pri_qty[0][0] if pri_qty else 0
			mri_qty = frappe.db.sql(""" select ifnull(sum(mri.qty), 0)
				from
					`tabMaterial Request` mr, `tabMaterial Request Item` mri
				where
					mri.project = %s and mri.parent = mr.name and mr.docstatus = 1
					""", d.project, as_list=1)
			scrap_qty = (1.0-flt(pri_qty/mri_qty[0][0]))*100 if mri_qty[0][0] else 0
			frappe.db.set_value('Project', d.project, 'scrap_qty', scrap_qty)

	stock_entry_fi = frappe.new_doc("Stock Entry")
	stock_entry_fi.purpose = "Material Receipt"
	stock_entry_fi.stock_entry_type = "Material Receipt"
	stock_entry_fi.to_warehouse = doc.set_warehouse
	stock_entry_fi.set_posting_time = doc.set_posting_time
	stock_entry_fi.posting_date = doc.posting_date
	stock_entry_fi.posting_time = doc.posting_time

	for d in doc.get('free_items'):
		if not stock_entry_fi.to_warehouse:
			stock_entry_fi.to_warehouse = d.warehouse
		stock_entry_fi.append('items', {'item_code': d.item_code,'item_name': d.item_name,'s_warehouse': d.warehouse, 't_warehouse': d.warehouse, 'qty': d.received_qty, 'uom': d.uom, 'remarks': doc.name, 'batch_no': d.batch_no, 'quality_inspection': d.quality_inspection })

	try:
		if need_inspection:
			stock_entry.insert(ignore_permissions=True)
			stock_entry.add_comment('Comment', text=doc.name + ": QI Consumption")
			stock_entry.submit()
		if len(stock_entry_fi.get('items')) > 0 :
			stock_entry_fi.insert(ignore_permissions=True)
			stock_entry_fi.add_comment('Comment', text=doc.name + ": QI Consumption")
			stock_entry_fi.submit()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
	return stock_entry.as_dict()


@frappe.whitelist()
def create_inspection(batch_no, item_code, warehouse, qty, new_batch_id=None): #pr, doc, method
	# batch = frappe.get_doc(dict(doctype='Batch', item=item_code, batch_id=new_batch_id)).insert()
	ql_settings = frappe.get_doc('QL Settings')

	company = frappe.db.get_value('Stock Ledger Entry', dict(
			item_code=item_code,
			batch_no=batch_no,
			warehouse=warehouse
		), ['company'])

	stock_entry_out = frappe.get_doc(dict(
		doctype='Stock Entry',
		purpose='Material Transfer',
		stock_entry_type = "Material Transfer",
		company=company,
		to_warehouse=ql_settings.qi_warehouse,
		items=[
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				s_warehouse=warehouse,
				t_warehouse=ql_settings.qi_warehouse,
				batch_no=batch_no
			)
		]
	))

	qi_doc = frappe.get_all('Quality Inspection', filters={'batch_no':batch_no}, fields='*', order_by='modified')
	cnt = len(qi_doc)
	if cnt > 0:
		new_qi_doc = frappe.copy_doc(frappe.get_doc('Quality Inspection', qi_doc[0].name))
		new_qi_doc.update({"name": batch_no + '_D'+ str(cnt), "completion_status": "Not Started", "status": "Rejected", "report_date": datetime.now().date(), "received_qty": float(qty or 0), "inspected_by": ql_settings.qi_inspected_by_default })
	else:
		new_qi_doc = frappe.get_doc(dict(
			doctype='Quality Inspection',
			name= batch_no + '_D'+ str(cnt),
			completion_status= "Not Started",
			status= "Rejected",
			received_qty= float(qty or 0),
			inspected_by= ql_settings.qi_inspected_by_default,
			report_date= datetime.now().date()
		))

	new_qi_doc.insert()

	stock_entry_in = frappe.get_doc(dict(
		doctype='Stock Entry',
		purpose='Material Transfer',
		stock_entry_type = "Material Transfer",
		inspection_required= 1,
		company=company,
		to_warehouse=warehouse,
		items=[
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				s_warehouse=ql_settings.qi_warehouse,
				t_warehouse=warehouse,
				quality_inspection=new_qi_doc.name,
				batch_no=batch_no
			)
		]
	))

	try:
		stock_entry_out.insert()
		stock_entry_out.submit()
		stock_entry_in.insert()
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()

	return new_qi_doc



@frappe.whitelist()
def qi_reject(batch_no, item_code, qty, new_batch_id=None):
	ql_settings = frappe.get_doc('QL Settings')
	batch = frappe.get_doc(dict(doctype='Batch', item=item_code, batch_id=new_batch_id)).insert()

	company = frappe.db.get_value('Stock Ledger Entry', dict(
			item_code=item_code,
			batch_no=batch_no,
			warehouse=ql_settings.qi_warehouse
		), ['company'])

	stock_entry = frappe.get_doc(dict(
		doctype='Stock Entry',
		purpose='Repack',
		to_warehouse = ql_settings.qi_reject_warehouse,
		company=company,
		items=[
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				s_warehouse=ql_settings.qi_warehouse,
				batch_no=batch_no
			),
			dict(
				item_code=item_code,
				qty=float(qty or 0),
				t_warehouse=ql_settings.qi_reject_warehouse,
				batch_no=batch.name
			),
		]
	))
	stock_entry.set_stock_entry_type()
	stock_entry.insert()
	stock_entry.submit()

	return stock_entry


@frappe.whitelist()
def get_bom_uom(work_order, material_request):
	if work_order :
		qis = frappe.db.sql("""SELECT item_code,uom,`tabBOM Item`.stock_uom FROM `tabWork Order` \
			INNER JOIN `tabBOM Item` ON `tabWork Order`.bom_no=`tabBOM Item`.parent \
			WHERE `tabWork Order`.NAME="{}" AND `tabBOM Item`.stock_uom<>uom;""".format(work_order), as_dict=True)
	else :
		qis = frappe.db.sql("""SELECT item_code,uom,`tabBOM Item`.stock_uom FROM `tabMaterial Request` \
			INNER JOIN `tabBOM Item` ON `tabMaterial Request`.bom_no=`tabBOM Item`.parent \
			WHERE `tabMaterial Request`.NAME="{}" AND `tabBOM Item`.stock_uom<>uom;""".format(material_request), as_dict=True)

	return qis


def purchase_receipt_validate(doc, method):
	'''Checks if quality inspection is set for Items that require inspection.
		On submit, throw an exception'''
	inspection_required_fieldname = None

	# frappe.throw(_("Quality Inspection: "))

	if doc.doctype in ["Purchase Receipt", "Purchase Invoice"]:
		inspection_required_fieldname = "inspection_required_before_purchase"
	elif doc.doctype in ["Delivery Note", "Sales Invoice"]:
		inspection_required_fieldname = "inspection_required_before_delivery"

	if ((not inspection_required_fieldname and doc.doctype != "Stock Entry") or
		(doc.doctype == "Stock Entry" and not doc.inspection_required) or
		(doc.doctype in ["Sales Invoice", "Purchase Invoice"] and not doc.update_stock)):
			return

	for d in doc.get('items'):
		if doc.docstatus == 1 and d.quality_inspection:
			qa_doc = frappe.get_doc("Quality Inspection", d.quality_inspection)
			if qa_doc.docstatus == 0:
				link = frappe.utils.get_link_to_form('Quality Inspection', d.quality_inspection)
				frappe.throw(_("Quality Inspection: {0} is not submitted for the item: {1} in row {2}").format(link, d.item_code, d.idx), QualityInspectionNotSubmittedError)

			qa_failed = qa_doc.status=="Rejected"
			if qa_failed and d.qty > 0:
				frappe.message(_("Row {0}: Quality Inspection rejected for item {1}, set accepted qty to 0")
					.format(d.idx, d.item_code), QualityInspectionRejectedError)


@frappe.whitelist()
def make_rm_stock_entry(purchase_order, rm_items):
	project = ""

	if isinstance(rm_items, string_types):
		rm_items_list = json.loads(rm_items)
	else:
		frappe.throw(_("No Items available for transfer"))

	if rm_items_list:
		fg_items = list(set(d["item_code"] for d in rm_items_list))
	else:
		frappe.throw(_("No Items selected for transfer"))

	if purchase_order:
		purchase_order = frappe.get_doc("Purchase Order", purchase_order)
		for item in purchase_order.items: #pjob
			if item.project :
				project = item.project
				break

	if fg_items:
		items = tuple(set(d["rm_item_code"] for d in rm_items_list))
		item_wh = get_item_details(items)

		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.purpose = "Send to Subcontractor"
		stock_entry.purchase_order = purchase_order.name
		stock_entry.supplier = purchase_order.supplier
		stock_entry.supplier_name = purchase_order.supplier_name
		stock_entry.supplier_address = purchase_order.supplier_address
		stock_entry.address_display = purchase_order.address_display
		stock_entry.company = purchase_order.company
		stock_entry.project = project
		stock_entry.to_warehouse = purchase_order.supplier_warehouse
		stock_entry.set_stock_entry_type()

		for item_code in fg_items:
			for rm_item_data in rm_items_list:
				if rm_item_data["item_code"] == item_code:
					rm_item_code = rm_item_data["rm_item_code"]
					items_dict = {
						rm_item_code: {
							"po_detail": rm_item_data.get("name"),
							"item_name": rm_item_data["item_name"],
							"description": item_wh.get(rm_item_code, {}).get('description', ""),
							'qty': rm_item_data["qty"],
							'from_warehouse': rm_item_data["warehouse"],
							'stock_uom': rm_item_data["stock_uom"],
							'main_item_code': rm_item_data["item_code"],
							'allow_alternative_item': item_wh.get(rm_item_code, {}).get('allow_alternative_item')
						}
					}
					stock_entry.add_to_stock_entry_detail(items_dict)
					stock_entry.items
		return stock_entry.as_dict()
	else:
		frappe.throw(_("No Items selected for transfer"))
	return purchase_order.name

