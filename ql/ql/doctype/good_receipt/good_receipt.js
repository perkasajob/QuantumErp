// Copyright (c) 2022, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.provide("ql");

frappe.ui.form.on('Good Receipt', {
	// refresh: function(frm) {

	// }
});

ql.GoodReceipt = erpnext.stock.StockController.extend({
	setup: function() {
		this.setup_posting_date_time_check();
	},
})

$.extend(cur_frm.cscript, new ql.GoodReceipt({frm: cur_frm}));