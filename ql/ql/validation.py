# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

from __future__ import unicode_literals

import frappe, erpnext, json, math
import frappe.defaults
from frappe.utils import nowdate, cstr, flt, cint, now, getdate, today
from frappe import throw, _
from frappe.utils import formatdate, get_number_format_info
from six import iteritems
from datetime import datetime
from six import string_types
from erpnext.buying.doctype.purchase_order.purchase_order import get_item_details



def get_missing_asl(item_code):
	ref_types = ['CoA', 'Halal', 'GMP', 'MSDS', 'SQM', 'CDOB', 'Supply Chain', 'SQS']
	# 1. Get the filtered ASL document types
	# We use a set comprehension directly for efficiency after fetching
	existing_asl_types = {
			doc.type
			for doc in frappe.get_list(
					"ASL Document",
					filters={
							"item_code": item_code,
							"docstatus": 0,
							"expiry": (">", today())
					},
					fields=["type"]
			)
	}

	# 2. Compare against ref_types and find missing items
	return [
			ref_item for ref_item in ref_types if ref_item not in existing_asl_types
	]



def quality_inspection_validate(doc, method):
	if not doc.get('asl_required'):
		return

	item_code = doc.get('item_code')
	missing_asl = get_missing_asl(item_code)
	if missing_asl:
		frappe.msgprint(f"The following required <a href=\"/desk#List/ASL%20Document/List?item_code='{item_code}'\">ASL Document</a> types are missing for Item '{item_code}': "
								f"{', '.join(missing_asl)}. "
								"Please ensure active ASL Documents with these types exist and are not expired.")
	else:
		frappe.msgprint(f"All required ASL Document types for Item '{item_code}' are present.")


def purchase_order_validate(doc, method):
	for d in doc.get('items'):
		if d.asl_required:
			missing_asl = get_missing_asl(d.item_code)
			if missing_asl:
				frappe.msgprint(f"The following required <a href=\"/desk#List/ASL%20Document/List?item_code='{d.item_code}'\">ASL Document</a> types are missing for Item '{d.item_code}': "
										f"{', '.join(missing_asl)}. "
										"Please ensure active ASL Documents with these types exist and are not expired.")


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

		if d.asl_required:
			missing_asl = get_missing_asl(d.item_code)
			if missing_asl:
				frappe.msgprint(f"The following required <a href=\"/desk#List/ASL%20Document/List?item_code='{d.item_code}'\">ASL Document</a> types are missing for Item '{d.item_code}': "
										f"{', '.join(missing_asl)}. "
										"Please ensure active ASL Documents with these types exist and are not expired.")