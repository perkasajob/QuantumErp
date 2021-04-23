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
		self.planned_operating_cost, self.actual_operating_cost = 0.0, 0.0
		for d in self.get("operations"):
			d.planned_operating_cost = flt(d.hour_rate) * (flt(d.time_in_mins) / 60.0)
			d.actual_operating_cost = flt(d.hour_rate) * (flt(d.actual_operation_time) / 60.0)

			self.planned_operating_cost += flt(d.planned_operating_cost)
			self.actual_operating_cost += flt(d.actual_operating_cost)

		variable_cost = self.actual_operating_cost if self.actual_operating_cost \
			else self.planned_operating_cost
		self.total_operating_cost = flt(self.additional_operating_cost) + flt(variable_cost)

	def get_status(self, status=None):
		'''Return the status based on stock entries against this work order'''
		if not status:
			status = self.status

		if self.docstatus==0:
			status = 'Draft'
		elif self.docstatus==1:
			if status != 'Stopped':
				stock_entries = frappe._dict(frappe.db.sql("""select purpose, sum(fg_completed_qty)
					from `tabStock Entry` where work_order=%s and docstatus=1
					group by purpose""", self.name))

				status = "Not Started"
				if stock_entries:
					status = "In Process"
					produced_qty = stock_entries.get("Manufacture")
					if flt(produced_qty) >= flt(self.qty) and "Material Consumption for Manufacture" in stock_entries.keys(): #PJOB
						status = "Completed"
		else:
			status = 'Cancelled'

		return status


def work_order_validate(doc, method):

	total_operating_cost = frappe.db.sql(""" select ifnull(sum(wo.total_operating_cost), 0) FROM `tabWork Order` wo WHERE wo.project = %s """, doc.project, as_list=1)

	frappe.db.set_value('Project', doc.project, 'total_operating_cost', total_operating_cost)