# -*- coding: utf-8 -*-
# Copyright (c) 2021, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext, json
from frappe.model.document import Document
from frappe.utils import cint, flt
from frappe.utils.user import get_user_fullname
from frappe.utils import flt, nowdate
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

class CashAdvanceRequest(Document):
	def __init__(self, *args, **kwargs):
		super(CashAdvanceRequest, self).__init__(*args, **kwargs)

	def onload(self):
		employee = frappe.db.get_all('Employee', filters={'user_id': frappe.session['user']}, fields=['name', 'employee_number'])
		if employee:
			self.employee = employee[0].name
			self.employee_number = employee[0].employee_number

	def validate(self):
		self.calculate_item_values()

	def on_update(self):
		if self.workflow_state == "Draft":
			self.db_set('requestee', get_user_fullname(frappe.session['user']))
			if not self.employee:
				employee = frappe.db.get_list("Employee", filters={"user_id": frappe.session['user']})
				if employee:
					self.db_set('employee', employee[0].name)

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


@frappe.whitelist()
def make_bank_entry(dt, dn):
	doc = frappe.get_doc(dt, dn)
	company  = erpnext.get_default_company()
	payment_account = get_default_bank_cash_account(company, account_type="Cash",
		mode_of_payment=doc.mode_of_payment)

	je = frappe.new_doc("Journal Entry")
	je.posting_date = nowdate()
	je.voucher_type = 'Bank Entry'
	je.company = company
	je.remark = 'Payment against Cash Advance Request: ' + dn + '\n' + doc.description if doc.description else ""
	je.mode_of_payment = doc.mode_of_payment
	cost_center = doc.cost_center if doc.cost_center else erpnext.get_default_cost_center(doc.company)

	je.append("accounts", {
		"account": doc.advance_account,
		"debit_in_account_currency": flt(doc.credit_in_account_currency),
		"reference_type": "Cash Advance Request",
		"reference_name": doc.name,
		"party_type": "Employee",
		"cost_center": cost_center,
		"party": doc.employee,
		"is_advance": "Yes"
	})

	je.append("accounts", {
		"account": payment_account.account,
		"cost_center": cost_center,
		"credit_in_account_currency": flt(doc.credit_in_account_currency),
		"account_currency": payment_account.account_currency,
		"account_type": payment_account.account_type
	})

	return je.as_dict()