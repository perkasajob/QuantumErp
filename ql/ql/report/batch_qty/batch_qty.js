// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Batch Qty"] = {
	"filters": [
	  {
		"fieldname":"start_date",
		"label": "Start Date",
		"fieldtype": "Date",
		"width": "80",
		"reqd": 1,
		"default": frappe.datetime.get_today(),
	  },
	  {
		"fieldname":"end_date",
		"label": "End Date",
		"fieldtype": "Date",
		"width": "80",
		"reqd": 1,
		"default": frappe.datetime.get_today(),
	  },
	  {
		"fieldname":"batch_no_flt",
		"label": "Batch No",
		"fieldtype": "Link",
		"options": "Batch",
		"width": "80"
	  }
	]
  };