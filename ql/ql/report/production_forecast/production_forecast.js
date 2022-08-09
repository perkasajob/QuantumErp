// Copyright (c) 2016, Perkasa JoB and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Production Forecast"] = {
	"filters": [
		{
			"fieldname":"dstock",
			"label": __("D Stock"),
			"fieldtype": "Link",
			"options": "D Stock",
			"default": "",
			on_change: function() {
				console.log("TEST")
			}
		},
		{
			"fieldname":"report_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
	]
};
