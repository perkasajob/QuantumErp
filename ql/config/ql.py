from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
			{
				"label": _("QL Reports"),
				"items": [
					{
						"type": "report",
						"is_query_report": True,
						"name": "Stock Ledger QL",
						"doctype": "Stock Ledger Entry",
						"onboard": 1,
						"dependencies": ["Item"],
					},
					{
						"type": "report",
						"is_query_report": True,
						"name": "Procurement Tracker QL",
						"doctype": "Purchase Order",
						"onboard": 1,
						"dependencies": ["Item","Material Request"],
					},
					{
						"type": "report",
						"is_query_report": True,
						"name": "Batch Qty",
						"doctype": "Stock Ledger Entry",
						"onboard": 1,
						"dependencies": ["Item"],
					}
				]
			}
		]