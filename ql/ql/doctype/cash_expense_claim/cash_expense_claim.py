# -*- coding: utf-8 -*-
# Copyright (c) 2021, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt
from frappe.utils.user import get_user_fullname

class CashExpenseClaim(Document):
	def __init__(self, *args, **kwargs):
		super(CashExpenseClaim, self).__init__(*args, **kwargs)

	def validate(self):
		self.calculate_item_values()

	def on_update(self):
		if self.workflow_state == "Draft":
			self.db_set('requestee', get_user_fullname(frappe.session['user']))

	def calculate_item_values(self):
		if len(self.get("items")) > 0:
			self.total = 0.0

		for item in self.get("items"):
			item.amount = flt(item.rate * item.qty,	0)
			self.total = self.total + item.amount

		if not self.cash_advance_request_amount:
			self.cash_advance_request_amount = 0.0

		self.outstanding_amount =  self.cash_advance_request_amount - self.total
