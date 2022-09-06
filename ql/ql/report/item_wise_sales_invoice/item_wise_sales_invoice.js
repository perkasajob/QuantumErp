frappe.query_reports["Item Wise Sales Invoice"] = {
	"filters": [
	  {
		"fieldname":"from_date",
		"label": "From Date",
		"fieldtype": "Date",
		"width": "80",
		"reqd": 1,
		"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
	  },
	  {
		"fieldname":"to_date",
		"label": "To Date",
		"fieldtype": "Date",
		"width": "80",
		"reqd": 1,
		"default": frappe.datetime.get_today(),
	  }
	]
  };