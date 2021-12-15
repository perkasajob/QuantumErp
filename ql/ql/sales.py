# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

from __future__ import unicode_literals

import frappe, erpnext, json, math
import frappe.defaults
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from frappe import throw, _
from frappe.utils import formatdate, get_number_format_info
from six import iteritems



def update_discount(doc, method):
	# doc.db_set('discount_amount', math.ceil(float(doc.mdp_discount_amount or 0.0) + float(doc.mdp_discount_margin or 0.0)/100 * (doc.total-float(doc.mdp_discount_amount or 0.0))))
	doc.discount_amount = math.ceil(float(doc.mdp_discount_amount or 0.0) + float(doc.mdp_discount_margin or 0.0)/100 * (doc.total-float(doc.mdp_discount_amount or 0.0)))
	doc.net_total = doc.total - doc.discount_amount