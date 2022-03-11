# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

from __future__ import unicode_literals

import frappe
import frappe.defaults
from frappe import _


def car_query_perm(user):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return
	match_role = list(set(['FIN','Finance Manager', 'CSD', 'Accounts Manager', 'System Manager']) & set(frappe.get_roles(user)))
	if match_role:
		return
	return "(`tabCash Advance Request`.owner = {user} or `tabCash Advance Request`.verifier  = {user})".format(user=frappe.db.escape(user))


def cec_query_perm(user):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return
	match_role = list(set(['FIN','Finance Manager', 'CSD', 'Accounts Manager', 'System Manager']) & set(frappe.get_roles(user)))
	if match_role:
		return
	return "(`tabCash Expense Claim`.owner = {user} or `tabCash Expense Claim`.verifier  = {user})".format(user=frappe.db.escape(user))


def ea_query_perm(user):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return
	match_role = list(set(['FIN','Finance Manager', 'CSD', 'Accounts Manager', 'System Manager']) & set(frappe.get_roles(user)))
	if match_role:
		return
	return "(`tabEmployee Advance`.owner={user} or `tabEmployee Advance`.approver_1={user} or `tabEmployee Advance`.approver_2={user} or `tabEmployee Advance`.approver_3={user})".format(user=frappe.db.escape(user))


def ec_query_perm(user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return
	match_role = list(set(['FIN','Finance Manager', 'CSD', 'Accounts Manager', 'System Manager']) & set(frappe.get_roles(user)))
	if match_role:
		return
	return "(`tabExpense Claim`.owner={user} or `tabExpense Claim`.approver_1={user} or `tabExpense Claim`.approver_2={user} or `tabExpense Claim`.approver_3={user})".format(user=frappe.db.escape(user))