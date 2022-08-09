# -*- coding: utf-8 -*-
# Copyright (c) 2020, Quantum Labs
from __future__ import unicode_literals

__version__ = '1.0.1'

import frappe
# from frappe.utils import today, flt
# from frappe.utils import flt, get_link_to_form
# from dateutil.parser._parser import ParserError
# import operator
# import re, datetime, math, time
# from dateutil import parser
# from six import iteritems, text_type, string_types, integer_types
# from erpnext.utilities.transaction_base import TransactionBase
<<<<<<< HEAD
# # from frappe import _
# # # from erpnext.controllers.accounts_controller import AccountsController
# # from erpnext.controllers.buying_controller import BuyingController
# # from erpnext.controllers.stock_controller import StockController
=======
# from frappe import _
# # from erpnext.controllers.accounts_controller import AccountsController
# from erpnext.controllers.buying_controller import BuyingController
# from erpnext.controllers.stock_controller import StockController
>>>>>>> c5e2dd73b817a1cd23f907aba1411bf0958d8dec
# from ql.overrides import ql_validate_rate_with_reference_doc, money_in_words, validate_multiple_billing, update_raw_materials_supplied_based_on_bom, buyingcontroller_validate, stockcontroller_validate
# from frappe.model.base_document import get_controller


@frappe.whitelist()
def get_logged_user_dept():
	# if "SM" in frappe.get_roles(frappe.session.user):
	# 	return True
	return frappe.db.sql("select dept_code from `tabDepartment` dept left join `tabEmployee` emp ON emp.department = dept.name where emp.user_id='{0}'".format(frappe.session.user), as_dict=1)

# frappe.model.base_document.get_controller = get_controller
# TransactionBase.validate_rate_with_reference_doc = ql_validate_rate_with_reference_doc
# frappe.utils.money_in_words = money_in_words
<<<<<<< HEAD
# # AccountsController.validate_multiple_billing = validate_multiple_billing
# # BuyingController.update_raw_materials_supplied_based_on_bom = update_raw_materials_supplied_based_on_bom
=======
# AccountsController.validate_multiple_billing = validate_multiple_billing
# BuyingController.update_raw_materials_supplied_based_on_bom = update_raw_materials_supplied_based_on_bom
>>>>>>> c5e2dd73b817a1cd23f907aba1411bf0958d8dec
# BuyingController.validate = buyingcontroller_validate

# StockController.validate = stockcontroller_validate