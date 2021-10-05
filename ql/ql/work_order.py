# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

import frappe, json
from frappe.model.document import Document
from frappe.utils import (flt, cint, time_diff_in_hours, get_datetime, getdate,
	get_time, add_to_date, time_diff, add_days, get_datetime_str, get_link_to_form, new_line_sep)

from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from frappe.model.mapper import get_mapped_doc
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details
from frappe import _

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
			self.update_reserve_remains_qty_for_required_items()

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

			mstr += d.item_code + " : " + str(returned_qty) + " \n"
			remains_qty = d.transferred_qty - d.consumed_qty - returned_qty
			if remains_qty < -0.00001:
				frappe.throw("Cannot have negative stock Item " + d.item_code + " : " + str(remains_qty))

			d.db_set('returned_qty', returned_qty)
			d.db_set('remains_qty', remains_qty)

	def get_remains_qty_for_required_items(self):
		mstr = ""
		result = []
		ql_settings = frappe.get_doc('QL Settings')
		mfg_settings = frappe.get_doc('Manufacturing Settings')
		for d in self.required_items:
			if d.remains_qty > 0:

				returned_qty = frappe.db.sql('''
				SELECT item_code,item_name, sum(qty) as qty, batch_no from (select detail.item_code, detail.item_name, detail.qty, detail.batch_no
					from `tabStock Entry` entry, `tabStock Entry Detail` detail
					where
						entry.work_order = "{name}" and entry.purpose IN ('Material Transfer for Manufacture', 'Material Transfer')
						and entry.docstatus = 1
						and detail.parent = entry.name
						and detail.t_warehouse = "{default_wip_warehouse}"
						and (detail.item_code = "{item}" or detail.original_item = "{item}")
				union all
				select detail.item_code, detail.item_name, detail.qty * -1 as qty, detail.batch_no
					from `tabStock Entry` entry, `tabStock Entry Detail` detail
					where
						entry.work_order = "{name}" and entry.purpose IN ("Material Consumption for Manufacture", "Material Transfer")
						and entry.docstatus < 2
						and detail.parent = entry.name
						and detail.s_warehouse = "{default_wip_warehouse}"
						and (detail.item_code = "{item}" or detail.original_item = "{item}")
				) t GROUP BY batch_no	'''.format(
							name = self.name,
							item = d.item_code,
							default_wip_warehouse = mfg_settings.default_wip_warehouse
					), as_dict=True)

				if returned_qty:
					[result.append(rq) for rq in returned_qty]

			# remains_qty = d.transferred_qty - d.consumed_qty - returned_qty
		frappe.msgprint(repr(result))

		return result



	def update_reserve_remains_qty_for_required_items(self):
		mstr = ""
		ql_settings = frappe.get_doc('QL Settings')
		for d in self.required_items:
			transferred_qty = frappe.db.sql('''select sum(qty)
				from `tabStock Entry` entry, `tabStock Entry Detail` detail
				where
					entry.work_order = "{name}" and entry.purpose = "Material Transfer"
					and entry.docstatus = 1
					and detail.parent = entry.name
					and detail.t_warehouse = "{wip_reserve_warehouse}"
					and (detail.item_code = "{item}" or detail.original_item = "{item}")'''.format(
						name = self.name,
						item = d.item_code,
						wip_reserve_warehouse = ql_settings.wip_reserve_warehouse
				))[0][0] or 0.0

			returned_qty = frappe.db.sql('''select sum(qty)
				from `tabStock Entry` entry, `tabStock Entry Detail` detail
				where
					entry.work_order = "{name}" and entry.purpose IN ('Material Transfer for Manufacture', 'Material Transfer')
					and entry.docstatus = 1
					and detail.parent = entry.name
					and detail.s_warehouse = "{wip_reserve_warehouse}"
					and (detail.item_code = "{item}" or detail.original_item = "{item}")'''.format(
						name = self.name,
						item = d.item_code,
						wip_reserve_warehouse = ql_settings.wip_reserve_warehouse
				))[0][0] or 0.0

			mstr += d.item_code + " : " + str(returned_qty) + " \n"
			reserved_qty = transferred_qty - returned_qty
			if reserved_qty < -0.00001:
				frappe.throw("Cannot have negative stock Item " + d.item_code + " : " + str(reserved_qty))

			d.db_set('reserved_qty', reserved_qty)


def work_order_validate(doc, method):

	total_operating_cost = frappe.db.sql(""" select ifnull(sum(wo.total_operating_cost), 0) FROM `tabWork Order` wo WHERE wo.project = %s """, doc.project, as_list=1)

	frappe.db.set_value('Project', doc.project, 'total_operating_cost', total_operating_cost)


@frappe.whitelist()
def raise_work_orders(material_request):
	mr= frappe.get_doc("Material Request", material_request)
	errors =[]
	work_orders = []
	default_wip_warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_wip_warehouse")

	for d in mr.items:
		if (d.stock_qty - d.ordered_qty) > 0:
			if frappe.db.exists("BOM", {"item": d.item_code, "is_default": 1}):
				wo_order = frappe.new_doc("Work Order")
				wo_order.update({
					"production_item": d.item_code,
					"qty": d.stock_qty - d.ordered_qty,
					"fg_warehouse": d.warehouse,
					"wip_warehouse": default_wip_warehouse,
					"description": d.description,
					"stock_uom": d.stock_uom,
					"expected_delivery_date": d.schedule_date,
					"sales_order": d.sales_order,
					"bom_no": get_item_details(d.item_code).bom_no,
					"material_request": mr.name,
					"material_request_item": d.name,
					"planned_start_date": mr.transaction_date,
					"company": mr.company,
					"project": d.project,
					"batch_no": mr.batch_no,
				})

				wo_order.set_work_order_operations()
				wo_order.save()

				work_orders.append(wo_order.name)
			else:
				errors.append(_("Row {0}: Bill of Materials not found for the Item {1}").format(d.idx, d.item_code))

	if work_orders:
		message = ["""<a href="#Form/Work Order/%s" target="_blank">%s</a>""" % \
			(p, p) for p in work_orders]
		frappe.msgprint(_("The following Work Orders were created:") + '\n' + new_line_sep(message))

	if errors:
		frappe.throw(_("Work Order cannot be created for following reason:") + '\n' + new_line_sep(errors))

	return work_orders


@frappe.whitelist()
def make_return_remain(work_order_id, purpose, qty=None):
	work_order = frappe.get_doc("Work Order", work_order_id)
	if not frappe.db.get_value("Warehouse", work_order.wip_warehouse, "is_group") \
			and not work_order.skip_transfer:
		wip_warehouse = work_order.wip_warehouse
	else:
		wip_warehouse = None

	return work_order.get_remains_qty_for_required_items()


	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = purpose
	stock_entry.work_order = work_order_id
	stock_entry.company = work_order.company
	stock_entry.from_bom = 1
	stock_entry.bom_no = work_order.bom_no
	stock_entry.use_multi_level_bom = work_order.use_multi_level_bom
	stock_entry.fg_completed_qty = qty or (flt(work_order.qty) - flt(work_order.produced_qty))
	if work_order.bom_no:
		stock_entry.inspection_required = frappe.db.get_value('BOM',
			work_order.bom_no, 'inspection_required')

	if purpose=="Material Transfer for Manufacture":
		stock_entry.to_warehouse = wip_warehouse
		stock_entry.project = work_order.project
	else:
		stock_entry.from_warehouse = wip_warehouse
		stock_entry.to_warehouse = work_order.fg_warehouse
		stock_entry.project = work_order.project

	stock_entry.set_stock_entry_type()
	stock_entry.get_items()
	return stock_entry.as_dict()


@frappe.whitelist()
def create_pick_list(source_name, target_doc=None, for_qty=None):
	for_qty = for_qty or json.loads(target_doc).get('for_qty')
	max_finished_goods_qty = frappe.db.get_value('Work Order', source_name, 'qty')
	def update_item_quantity(source, target, source_parent):
		qty = flt(source.required_qty) / max_finished_goods_qty * flt(for_qty)
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


@frappe.whitelist()
def close_work_order(work_order):
	work_order = frappe.get_doc(json.loads(work_order))
	total_reserved_items = 0.0
	for ri in work_order.required_items:
		total_reserved_items += (ri.reserved_qty + ri.remains_qty )
	if(total_reserved_items < 0.01)	:
		work_order.db_set("status", "Completed")
	return work_order