# -*- coding: utf-8 -*-
# Copyright (c) 2021, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe.contacts.address_and_contact import load_address_and_contact

class DistributorWarehouse(Document):
	def onload(self):
		load_address_and_contact(self)
