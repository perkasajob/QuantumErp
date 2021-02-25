# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, time_diff_in_hours, get_datetime, time_diff, get_link_to_form
from erpnext.manufacturing.doctype.job_card.job_card import JobCard

class QLJobCard(JobCard):
	def validate_job_card(self):
		if not self.time_logs:
			frappe.throw(_("Time logs are required for {0} {1}")
				.format(frappe.bold("Job Card"), get_link_to_form("Job Card", self.name)))