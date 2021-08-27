// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Distributor Warehouse', {
	refresh: function(frm) {
		frm.toggle_display(['address_html','contact_html'], !frm.doc.__islocal);


		if(!frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(frm);

		} else {
			frappe.contacts.clear_address_and_contact(frm);
		}
		frappe.dynamic_link = {doc: frm.doc, fieldname: 'name', doctype: 'Distributor Warehouse'};

	}
});