// Copyright (c) 2022, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Forecast', {
	target_date: function(frm){
		var datestr = frappe.datetime.str_to_obj(frm.doc.target_date).getMonth()
		frm.set_value("month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
		"Dec"][datestr])
		frm.set_value("year", frm.doc.target_date.substr(2,2))
	}
});
