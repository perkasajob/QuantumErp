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
		for item in self.get("purchase_inv_payments"):
			self.total = self.total + item.amount

@frappe.whitelist()
def get_items(account, from_date, to_date):

	cec = frappe.db.sql('''select cec.name, ge.posting_date, cec.description, cec.total, ge.name, jea.name
				from `tabGL Entry` ge
				left join (`tabJournal Entry Account` jea) on (ge.voucher_no = jea.parent)
				left join (`tabCash Expense Claim` cec) on (jea.reference_name = cec.name)
				where ge.voucher_type = "Journal Entry" AND ge.account = %s AND ge.posting_date BETWEEN %s AND %s''',(account, from_date, to_date), as_dict = 1)

	# ec = frappe.db.sql('''select ec.name, ec.posting_date, ec.remark, ec.total_sanctioned_amount
	# 			from `tabJournal Entry` je
	# 			left join (`tabExpense Claim` ec) on (je.reference_name = ec.journal_entry)
	# 			where not exists (
	# 				select * from `tabPetty Reimbursement Item` pcri where pcri.expense_claim = ec.name
	# 			) AND ec.docstatus = 1 AND je.docstatus = 1 AND ec.cash_account = %s AND ec.posting_date BETWEEN %s AND %s''',(account, from_date, to_date), as_dict = 1)

	pe = frappe.db.sql('''select pe.name, pe.posting_date, pe.paid_amount, GROUP_CONCAT(pii.item_name ORDER BY pii.item_name SEPARATOR ', ') as description
				from `tabPayment Entry` pe
				left join (`tabPayment Entry Reference` per, `tabPurchase Invoice Item` pii) on (per.parent = pe.name AND per.reference_name = pii.parent)
				where not exists (
					select * from `tabPetty Cash Payment Reimbursement Item` pcpri where pcpri.payment_entry = pe.name
				) AND pe.docstatus = 1 AND pe.paid_from = %s AND pe.posting_date BETWEEN %s AND %s
				group by pe.name LIMIT 10''',(account, from_date, to_date), as_dict = 1)

	return {'cec': cec, 'pe': pe}
