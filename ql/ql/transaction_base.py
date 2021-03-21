# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

from __future__ import unicode_literals
import frappe
import frappe.share
from frappe import _
from frappe.utils import cstr, now_datetime, cint, flt, get_time, get_link_to_form
from erpnext.controllers.status_updater import StatusUpdater

from six import string_types

class QLTransactionBase(StatusUpdater):
	def validate_rate_with_reference_doc(self, ref_details):
		buying_doctypes = ["Purchase Order", "Purchase Invoice", "Purchase Receipt"]
		frappe.msgprint("QLTransactionBase is CALLED ")

		if self.doctype in buying_doctypes:
			to_disable = "Maintain same rate throughout Purchase cycle"
			settings_page = "Buying Settings"
		else:
			to_disable = "Maintain same rate throughout Sales cycle"
			settings_page = "Selling Settings"

		for ref_dt, ref_dn_field, ref_link_field in ref_details:
			for d in self.get("items"):
				if d.get(ref_link_field):
					ref_rate = frappe.db.get_value(ref_dt + " Item", d.get(ref_link_field), "rate")

					if abs(flt(d.rate - ref_rate, d.precision("rate"))) >= .01:
						frappe.msgprint(_("Row #{0}: Rate must be same as {1}: {2} ({3} / {4}) ")
							.format(d.idx, ref_dt, d.get(ref_dn_field), d.rate, ref_rate))
						frappe.throw(_("To allow different rates, disable the {0} checkbox in {1}.")
							.format(frappe.bold(_(to_disable)),
							get_link_to_form(settings_page, settings_page, frappe.bold(settings_page))))
