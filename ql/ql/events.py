# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

import frappe
import os, json

from frappe import _
from frappe.modules import scrub, get_module_path
from frappe.utils import (
	flt,
	cint,
	cstr,
	get_html_format,
	get_url_to_form,
	gzip_decompress
)
from frappe.desk.query_report import(
	get_report_doc,
	get_prepared_report_result,
	generate_report_result
)
from frappe.model.utils import render_include
from six import string_types, iteritems


@frappe.whitelist()
@frappe.read_only()
def run(report_name, filters=None, user=None, ignore_prepared_report=False, custom_columns=None):
	report = get_report_doc(report_name)
	if not user:
		user = frappe.session.user
	if not frappe.has_permission(report.ref_doctype, "report"):
		frappe.msgprint(_("Must have report permission to access this report."),
			raise_exception=True)

	result = None

	if report.prepared_report and not report.disable_prepared_report and not ignore_prepared_report and not custom_columns:
		if filters:
			if isinstance(filters, string_types):
				filters = json.loads(filters)

			dn = filters.get("prepared_report_name")
			filters.pop("prepared_report_name", None)
		else:
			dn = ""
		result = get_prepared_report_result(report, filters, dn, user)
	else:
		result = generate_report_result(report, filters, user, custom_columns)

	result["add_total_row"] = report.add_total_row and not result.get('skip_total_row', False)

	allowed_roles= ['Accounts Manager']

	for ar in allowed_roles:
		if ar in frappe.get_roles():
			return result

	if(report_name == "Stock Ledger"):
		for i, o in enumerate(result['result']):
			del o['incoming_rate']
			del o['valuation_rate']
			del o['stock_value']
	elif(report_name == "Stock Balance"):
		for i, o in enumerate(result['result']):
			if "in_val" in o:
				o.pop('out_val')
				o.pop('bal_val')
				o.pop('in_val')
				o.pop('opening_val')
				o.pop('val_rate')
	return result