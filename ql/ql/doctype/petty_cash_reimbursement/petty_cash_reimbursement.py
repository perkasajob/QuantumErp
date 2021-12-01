# -*- coding: utf-8 -*-
# Copyright (c) 2021, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe.utils import cint, flt
from frappe.utils.user import get_user_fullname

class PettyCashReimbursement(Document):
	def __init__(self, *args, **kwargs):
		super(PettyCashReimbursement, self).__init__(*args, **kwargs)

	def validate(self):
		self.calculate_item_values()

	def on_update(self):
		if self.workflow_state == "Draft":
			self.db_set('requestee', get_user_fullname(frappe.session['user']))

	def calculate_item_values(self):
		self.total = 0.0

		for item in self.get("items"):
			self.total = self.total + item.amount

@frappe.whitelist()
def get_items(petty_cash):
	return frappe.db.sql('''select name, purchase_date, description, total
				from `tabCash Expense Claim` cec
				where not exists (
					select * from `tabPetty Cash Reimbursement Item` pcri where pcri.cash_expense_claim = cec.name
				) AND cec.docstatus = 1 AND cec.petty_cash = %s''',(petty_cash), as_dict = 1)
