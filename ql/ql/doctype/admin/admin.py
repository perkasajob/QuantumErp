# -*- coding: utf-8 -*-
# Copyright (c) 2022, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class Admin(Document):
	def __init__(self, *args, **kwargs):
		super(Admin, self).__init__(*args, **kwargs)

	def validate(self):
		if self.action == "Set WO to In Process":
			if getattr(self, "param1", None):
				if not frappe.db.exists('Work Order', self.param1):
					frappe.throw("Work Order not Found")
			else:
				frappe.throw("param1 cannot be empty")
		if self.action == "Set QI to Draft":
			if getattr(self, "param1", None):
				if not frappe.db.exists('Quality Inspection', self.param1):
					frappe.throw("'Quality Inspection not Found")
			else:
				frappe.throw("param1 cannot be empty")
		if self.action == "Set CEC to Approved":
			if getattr(self, "param1", None):
				if not frappe.db.exists('Cash Expense Claim', self.param1):
					frappe.throw("Cash Expense Claim not Found")
			else:
				frappe.throw("param1 cannot be empty")

	def on_submit(self):
		if self.action == "Set WO to In Process":
			frappe.db.sql('''update `tabWork Order` set status="In Process" where name=%s ''', (self.param1), as_dict=True)
		elif self.action == "Set QI to Draft":
			frappe.db.sql('''update `tabQuality Inspection` set docstatus=0 where name=%s ''', (self.param1), as_dict=True)
		elif self.action == "Set CEC to Approved":
			frappe.db.sql('''update `tabCash Expense Claim` set docstatus=0, workflow_state="Approved" where name=%s ''', (self.param1), as_dict=True)
		frappe.db.commit()


## TODO
# unlock WO
# unlock PR-QI
# remove stock entry caused by QI/PR cancellation with 'remarks': PR.name