// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cash Adv', {
	refresh: function(frm) {
		if(frm.doc.docstatus==1) {
			if(frm.doc.workflow_state = "Approved"){
				frm.add_custom_button(__('Create Journal Entry'), function() {
					frappe.model.with_doctype('Journal Entry', function() {
						var je = frappe.model.get_new_doc('Journal Entry');
						je.remark = frm.doc.description
						je.cheque_no = frm.doc.cheque_no
						je.cheque_date = frm.doc.cheque_date
						je.cash_adv = frm.doc.name
						je.user_remark = frm.doc.user_remark

						// var accounts = frm.get_field('accounts').grid.get_selected_children();
						var je_account = frappe.model.add_child(je, 'accounts');
						je_account.credit_in_account_currency = Math.abs(frm.doc.credit_in_account_currency)
						je_account.account = frm.doc.account
						je_account.bank_account = frm.doc.bank_account
						je_account.cost_center = frm.doc.cost_center
						je_account.is_advance = frm.doc.is_advance
						je_account.reference_due_date = frm.doc.req_date
						frappe.set_route('Form', 'Journal Entry', je.name);
					});
				});
			} else if (frm.doc.workflow_state = "Booked") {
				frm.add_custom_button(__('Create Recap'), function() {
					frappe.model.with_doctype('Cash Adv Recap', function() {
						var car = frappe.model.get_new_doc('Cash Adv Recap');
						car.remark = frm.doc.description
						car.cheque_no = frm.doc.cheque_no
						car.cheque_date = frm.doc.cheque_date
						car.cash_adv = frm.doc.name
						car.user_remark = frm.doc.user_remark

						// var accounts = frm.get_field('accounts').grid.get_selected_children();
						var car_account = frappe.model.add_child(car, 'accounts');
						var items = frm.get_field('items').grid.get_selected_children();
						if(!items.length) {
							items = frm.doc.items;
						}
						items.forEach(function(item) {
							var car_item = frappe.model.add_child(car, 'items');
							car_item.item = item.item;
							car_item.qty = item.qty;
							car_item.uom = item.uom;
							car_item.rate = item.rate;
							car_item.note = item.note;
						});
						car_account.cash_advance_request = frm.doc.credit_in_account_currency
						car_account.account = frm.doc.account
						car_account.bank_account = frm.doc.bank_account
						car_account.cost_center = frm.doc.cost_center
						car_account.is_advance = frm.doc.is_advance
						frappe.set_route('Form', 'Cash Adv Recap', car.name);
					});
				});
			}
		}
	}
});
