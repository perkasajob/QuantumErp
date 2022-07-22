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
						"name": "Stock Balance QL",
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
					},
					{
						"type": "report",
						"is_query_report": True,
						"name": "WO - Remain Qty",
						"doctype": "Work Order",
						"onboard": 1,
						"dependencies": ["Stock Ledger Entry","Work Order Item"],
					},
					{
						"type": "report",
						"is_query_report": True,
						"name": "MR-MT Fullfillment",
						"doctype": "Material Request",
						"onboard": 1,
						"dependencies": ["Material Request Item"],
					}
				]
			},{
				"label": _("Purchasing"),
				"items": [
					{
						"type": "doctype",
						"name": "Cash Advance Request",
					},
					{
						"type": "doctype",
						"name": "Cash Expense Claim",
					},
					{
						"type": "doctype",
						"name": "Petty Cash Reimbursement",
					}
				]
			},{
				"label": _("Stock"),
				"items": [
					{
						"type": "doctype",
						"name": "Sales Stock Return",
					},
					{
						"type": "doctype",
						"name": "Pre Production Plan",
					},
					{
						"type": "doctype",
						"name": "Forecast ROFO",
					}
				]
			}
		]