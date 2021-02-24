# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import (flt, cint, time_diff_in_hours, get_datetime, getdate,
	get_time, add_to_date, time_diff, add_days, get_datetime_str, get_link_to_form)
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder

class QLWorkOrder(WorkOrder):
	def calculate_operating_cost(self):
		# super(WorkOrder, self).validate()
		self.calculate_operating_cost_ql()

	def calculate_operating_cost_ql(self):
		for d in self.get("operations"):
			d.planned_operating_cost = flt(d.hour_rate) * (flt(d.time_in_mins) / 60.0)
			d.actual_operating_cost = flt(d.hour_rate) * (flt(d.actual_operation_time) / 60.0)

			self.planned_operating_cost += flt(d.planned_operating_cost)
			self.actual_operating_cost += flt(d.actual_operating_cost)

		variable_cost = self.actual_operating_cost if self.actual_operating_cost \
			else self.planned_operating_cost
		frappe.msgprint("HELLo")
		self.total_operating_cost = 123456789 #flt(self.additional_operating_cost) + flt(variable_cost)