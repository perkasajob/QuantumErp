# -*- coding: utf-8 -*-
# Copyright (c) 2020, Quantum Labs
from __future__ import unicode_literals

__version__ = '0.0.1'

import frappe
from frappe.utils import today, flt


@frappe.whitelist()
def get_logged_user_dept():
	# if "SM" in frappe.get_roles(frappe.session.user):
	# 	return True
    return frappe.db.sql("select dept_code from `tabDepartment` dept left join `tabEmployee` emp ON emp.department = dept.name where emp.user_id='{0}'".format(frappe.session.user), as_dict=1)


