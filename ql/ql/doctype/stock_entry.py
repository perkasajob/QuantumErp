

from erpnext.controllers.stock_controller import StockController
import frappe

class QLStockEntry(StockController):
	def validate_fg_completed_qty(self):
		if self.purpose == "Manufacture" and self.work_order:
			pass
			# production_item = frappe.get_value('Work Order', self.work_order, 'production_item')