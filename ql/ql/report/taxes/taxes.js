// Copyright (c) 2016, Perkasa JoB and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Taxes"] = {
	"filters": [
		{
			fieldname: "account_head",
			label: __("Account Head"),
			fieldtype: "Link",
			options: "Account Head",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_start_date"),
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_end_date"),
		},
	]
}
