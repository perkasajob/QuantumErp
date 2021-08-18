// Copyright (c) 2016, Perkasa JoB and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Project Manufacturing Cost"] = {
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
		}
	]
};
