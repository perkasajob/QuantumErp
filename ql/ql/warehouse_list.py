import frappe
# from erpnext.accounts.doctype.sales_invoice.sales_invoice import Warehouse
from erpnext.stock.doctype.warehouse.warehouse.get_children import Warehouse

def shoutout(self):
	print("Yay!")

def before_cancel(self):
	self.shoutout()
	self.update_time_sheet(None)

def build_my_thing():
	Warehouse.shoutout = shoutout
	Warehouse.before_cancel = before_cancel