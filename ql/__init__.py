# -*- coding: utf-8 -*-
# Copyright (c) 2020, Quantum Labs
from __future__ import unicode_literals

__version__ = '1.0.1'

import frappe
from frappe.utils import today, flt
from frappe.utils import flt, get_link_to_form
from dateutil.parser._parser import ParserError
import operator
import re, datetime, math, time
from dateutil import parser
from six import iteritems, text_type, string_types, integer_types
from erpnext.utilities.transaction_base import TransactionBase
from frappe import _
from erpnext.controllers.accounts_controller import AccountsController
from ql.overrides import ql_validate_rate_with_reference_doc, money_in_words, validate_multiple_billing

@frappe.whitelist()
def get_logged_user_dept():
	# if "SM" in frappe.get_roles(frappe.session.user):
	# 	return True
    return frappe.db.sql("select dept_code from `tabDepartment` dept left join `tabEmployee` emp ON emp.department = dept.name where emp.user_id='{0}'".format(frappe.session.user), as_dict=1)


TransactionBase.validate_rate_with_reference_doc = ql_validate_rate_with_reference_doc
frappe.utils.money_in_words = money_in_words
AccountsController.validate_multiple_billing = validate_multiple_billing