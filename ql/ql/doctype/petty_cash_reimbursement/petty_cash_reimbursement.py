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

		for item in self.get("cash_expense_claims"):
			self.total = self.total + item.amount
		for item in self.get("expense_claims"):
			self.total = self.total + item.total_sanctioned_amount
		for item in self.get("purchase_inv_payments"):
			self.total = self.total + item.amount

@frappe.whitelist()
def get_items(account, from_date, to_date):

	cec = frappe.db.sql('''select cec.name, gle.posting_date as date, cec.description, cec.total, gle.name as gle, jea.name as jea
				from `tabGL Entry` gle
				left join (`tabJournal Entry Account` jea) on (gle.voucher_no = jea.parent)
				left join (`tabCash Expense Claim` cec) on (jea.reference_name = cec.name)
				where  not exists (
	 				select * from `tabPetty Reimbursement CEC Item` pri where pri.cash_expense_claim = cec.name
	 			) and cec.name != '' and gle.voucher_type = "Journal Entry" AND gle.account = %s AND gle.posting_date BETWEEN %s AND %s
				group by gle.name''',(account, from_date, to_date), as_dict = 1)

	ec = frappe.db.sql('''select ec.name, gle.posting_date as date, ec.remark, ec.total_sanctioned_amount, gle.name as gle
				from `tabGL Entry` gle
				left join (`tabExpense Claim` ec) on (gle.voucher_no = ec.name)
				where  not exists (
	 				select * from `tabPetty Reimbursement EC Item` pri where pri.expense_claim = ec.name
	 			) AND gle.voucher_type = "Expense Claim" AND gle.account = %s AND gle.posting_date BETWEEN %s AND %s
				group by gle.name''',(account, from_date, to_date), as_dict = 1)

	pe = frappe.db.sql('''select pe.name, pe.posting_date, pe.paid_amount, GROUP_CONCAT(pii.item_name ORDER BY pii.item_name SEPARATOR ', ') as description
				from `tabPayment Entry` pe
				left join (`tabPayment Entry Reference` per, `tabPurchase Invoice Item` pii) on (per.parent = pe.name AND per.reference_name = pii.parent)
				where not exists (
					select * from `tabPetty Cash Payment Reimbursement Item` pcpri where pcpri.payment_entry = pe.name
				) AND pe.docstatus = 1 AND pe.paid_from = %s AND pe.posting_date BETWEEN %s AND %s
				group by pe.name''',(account, from_date, to_date), as_dict = 1)

	return {'cec': cec, 'ec': ec, 'pe': pe}