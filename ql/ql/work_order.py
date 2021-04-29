# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

import frappe, json
from frappe.model.document import Document
from frappe.utils import (flt, cint, time_diff_in_hours, get_datetime, getdate,
	get_time, add_to_date, time_diff, add_days, get_datetime_str, get_link_to_form)
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from frappe.model.mapper import get_mapped_doc

class OverProductionError(frappe.ValidationError): pass
class StockOverProductionError(frappe.ValidationError): pass
class OperationTooLongError(frappe.ValidationError): pass
class ItemHasVariantError(frappe.ValidationError): pass

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
					if flt(produced_qty) >= flt(self.qty) and "Material Transfer" in stock_entries.keys() and "Material Consumption for Manufacture" in stock_entries.keys() : #PJOB
						# if stock_entries.get("from_warehouse")[:16] == "Work-in-Progress" :
							status = "Completed"
		else:
			status = 'Cancelled'

		return status

	def update_work_order_qty(self):
		"""Update **Manufactured Qty** and **Material Transferred for Qty** in Work Order
			based on Stock Entry"""

		allowance_percentage = flt(frappe.db.get_single_value("Manufacturing Settings",
			"overproduction_percentage_for_work_order"))

		for purpose, fieldname in (("Manufacture", "produced_qty"),
			("Material Transfer for Manufacture", "material_transferred_for_manufacturing")):
			if (purpose == 'Material Transfer for Manufacture' and
				self.operations and self.transfer_material_against == 'Job Card'):
				continue

			qty = flt(frappe.db.sql("""select sum(fg_completed_qty)
				from `tabStock Entry` where work_order=%s and docstatus=1
				and purpose=%s""", (self.name, purpose))[0][0])

			completed_qty = self.qty + (allowance_percentage/100 * self.qty)
			# if qty > completed_qty: #pjob
			# 	frappe.throw(_("{0} ({1}) cannot be greater than planned quantity ({2}) in Work Order {3}").format(\
			# 		self.meta.get_label(fieldname), qty, completed_qty, self.name), StockOverProductionError)

			if fieldname == "material_transferred_for_manufacturing": #PjoB
				if not self.material_transferred_for_manufacturing:
					self.db_set(fieldname, qty)
			else:
				self.db_set(fieldname, qty)

			from erpnext.selling.doctype.sales_order.sales_order import update_produced_qty_in_so_item

			if self.sales_order and self.sales_order_item:
				update_produced_qty_in_so_item(self.sales_order, self.sales_order_item)

		if self.production_plan:
			self.update_production_plan_status()

	def update_required_items(self):
		'''
		update bin reserved_qty_for_production
		called from Stock Entry for production, after submit, cancel
		'''
		# calculate consumed qty based on submitted stock entries
		self.update_consumed_qty_for_required_items()

		if self.docstatus==1:
			# calculate transferred qty based on submitted stock entries
			self.update_transaferred_qty_for_required_items()
			self.update_remains_qty_for_required_items()

			# update in bin
			self.update_reserved_qty_for_production()

	def update_remains_qty_for_required_items(self):
		mstr = ""
		for d in self.required_items:
			returned_qty = frappe.db.sql('''select sum(qty)
				from `tabStock Entry` entry, `tabStock Entry Detail` detail
				where
					entry.work_order = "{name}" and entry.purpose = "Material Transfer"
					and entry.docstatus < 2
					and detail.parent = entry.name
					and detail.s_warehouse like "Work-in-Progress%"
					and (detail.item_code = "{item}" or detail.original_item = "{item}")'''.format(
						name = self.name,
						item = d.item_code
				))[0][0] or 0.0
			# returned_qty = returned_qty if returned_qty else 0.0

			# if returned_qty > 0 :
			mstr += d.item_code + " : " + str(returned_qty) + " \n"
			remains_qty = d.transferred_qty - d.consumed_qty - returned_qty
			if remains_qty < 0.000001:
				frappe.throw(d.item_code + " : " + str(remains_qty))

			d.db_set('returned_qty', returned_qty)
			d.db_set('remains_qty', remains_qty)
		frappe.msgprint(mstr)


def work_order_validate(doc, method):

	total_operating_cost = frappe.db.sql(""" select ifnull(sum(wo.total_operating_cost), 0) FROM `tabWork Order` wo WHERE wo.project = %s """, doc.project, as_list=1)

	frappe.db.set_value('Project', doc.project, 'total_operating_cost', total_operating_cost)

@frappe.whitelist()
def create_pick_list(source_name, target_doc=None, for_qty=None):
	for_qty = for_qty or json.loads(target_doc).get('for_qty')
	def update_item_quantity(source, target, source_parent):
		qty = flt(for_qty)
		if qty:
			target.qty = qty
			target.stock_qty = qty
			target.uom = frappe.get_value('Item', source.item_code, 'stock_uom')
			target.stock_uom = target.uom
			target.conversion_factor = 1
			target.project = source_parent.project
		else:
			target.delete()
	doc = get_mapped_doc('Work Order', source_name, {
		'Work Order': {
			'doctype': 'Pick List',
			'validation': {
				'docstatus': ['=', 1]
			}
		},
		'Work Order Item': {
			'doctype': 'Pick List Item',
			'postprocess': update_item_quantity
		},
	}, target_doc)

	doc.for_qty = for_qty

	doc.set_item_locations()

	return doc