# -*- coding: utf-8 -*-
# Copyright (c) 2022, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class GoodReceipt(Document):
	def autoname(self):
		self.name = "GR" + self.stock_entry[7:]

	def validate(self):
		self.set_transfer_qty()

	def set_transfer_qty(self):
			for item in self.get("items"):
				if not flt(item.qty):
					frappe.throw(_("Row {0}: Qty is mandatory").format(item.idx))
				if not flt(item.conversion_factor):
					frappe.throw(_("Row {0}: UOM Conversion Factor is mandatory").format(item.idx))
				item.transfer_qty = flt(flt(item.qty) * flt(item.conversion_factor),
					self.precision("transfer_qty", item))