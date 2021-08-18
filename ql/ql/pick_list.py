# -*- coding: utf-8 -*-
# Copyright (c) 2020, Perkasa JoB and Contributors
# License: QL. See license.txt

from __future__ import unicode_literals
from erpnext.stock.doctype.pick_list.pick_list import PickList
import frappe
import json
from six import iteritems
from frappe.model.document import Document
from frappe import _
from collections import OrderedDict
from frappe.utils import floor, flt, today, cint
from frappe.model.mapper import get_mapped_doc, map_child_doc
from erpnext.stock.get_item_details import get_conversion_factor
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note as create_delivery_note_from_sales_order
from erpnext.stock.doctype.pick_list.pick_list import update_stock_entry_based_on_work_order,update_stock_entry_based_on_material_request,update_stock_entry_items_with_no_reference,validate_item_locations,stock_entry_exists
from erpnext.stock.doctype.pick_list.pick_list import get_available_item_locations, get_items_with_location_and_quantity


class QLPickList(PickList):
	def set_item_locations(self, save=False):
		items = self.aggregate_item_qty()
		self.item_location_map = frappe._dict()

		from_warehouses = None
		if self.parent_warehouse:
			from_warehouses = frappe.db.get_descendants('Warehouse', self.parent_warehouse)

		# reset
		self.delete_key('locations')
		for item_doc in items:
			item_code = item_doc.item_code

			self.item_location_map.setdefault(item_code,
				get_available_item_locations(item_code, from_warehouses, self.item_count_map.get(item_code), self.company))

			locations = get_items_with_location_and_quantity(item_doc, self.item_location_map)

			item_doc.idx = None
			item_doc.name = None

			for row in locations:
				row.update({
					'picked_qty': row.stock_qty
				})
				if item_doc.batch_no:
					row.update({
						'batch_no': item_doc.batch_no
					})


				location = item_doc.as_dict()
				location.update(row)
				self.append('locations', location)

		if save:
			self.save()

@frappe.whitelist()
def create_stock_entry(pick_list):
	pick_list = frappe.get_doc(json.loads(pick_list))
	validate_item_locations(pick_list)

	# if stock_entry_exists(pick_list.get('name')): #pjob
	# 	return frappe.msgprint(_('Stock Entry has been already created against this Pick List'))

	stock_entry = frappe.new_doc('Stock Entry')
	stock_entry.pick_list = pick_list.get('name')
	stock_entry.purpose = pick_list.get('purpose')
	stock_entry.set_stock_entry_type()

	if pick_list.get('work_order'):
		stock_entry = update_stock_entry_based_on_work_order(pick_list, stock_entry)
	elif pick_list.get('material_request'):
		stock_entry = update_stock_entry_based_on_material_request(pick_list, stock_entry)
	else:
		stock_entry = update_stock_entry_items_with_no_reference(pick_list, stock_entry)

	stock_entry.set_incoming_rate()
	stock_entry.set_actual_qty()
	stock_entry.calculate_rate_and_amount(update_finished_item_rate=False)

	return stock_entry.as_dict()