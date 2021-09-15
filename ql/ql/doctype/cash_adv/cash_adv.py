# -*- coding: utf-8 -*-
# Copyright (c) 2021, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt
from frappe.utils.user import get_user_fullname

class CashAdv(Document):
	def __init__(self, *args, **kwargs):
		super(CashAdv, self).__init__(*args, **kwargs)

	def validate(self):
		self.calculate_item_values()

	def on_update(self):
		if self.workflow_state == "Draft":
			self.db_set('requestee', get_user_fullname(frappe.session['user']))

	def calculate_item_values(self):
		total = 0
		if not self.is_fixed_amount:
			self.credit_in_account_currency = 0.0

		for item in self.get("items"):
			item.amount = flt(item.rate * item.qty,	0)
			total = total + item.amount

		if not self.is_fixed_amount or not self.requested_amount:
			self.requested_amount = total

		if not self.credit_in_account_currency:
			self.credit_in_account_currency = self.requested_amount if self.is_fixed_amount else total

