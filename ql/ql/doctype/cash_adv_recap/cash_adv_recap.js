// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cash Adv Recap', {
	refresh: function(frm) {
		if(frm.doc.docstatus==1) {
			if(frm.doc.workflow_state = "Approved"){
				frm.add_custom_button(__('Create Journal Entry'), function() {
					frappe.model.with_doctype('Journal Entry', function() {
						var je = frappe.model.get_new_doc('Journal Entry');
						je.remark = frm.doc.description
						je.cheque_no = frm.doc.cheque_no
						je.cheque_date = frm.doc.cheque_date
						je.cash_adv_recap = frm.doc.name
						je.user_remark = frm.doc.user_remark

						// var accounts = frm.get_field('accounts').grid.get_selected_children();
						var je_account = frappe.model.add_child(je, 'accounts');
						if(frm.doc.outstanding_amount < 0){
							je_account.credit_in_account_currency = -1 * frm.doc.outstanding_amount
						} else if (frm.doc.outstanding_amount > 0) {
							je_account.debit_in_account_currency = frm.doc.outstanding_amount
						}
						je_account.account = frm.doc.account
						je_account.bank_account = frm.doc.bank_account
						je_account.cost_center = frm.doc.cost_center
						je_account.is_advance = frm.doc.is_advance
						frappe.set_route('Form', 'Journal Entry', je.name);
					});
				});
			}
		}
	},
	cash_adv: function(frm){
		frappe.db.get_doc('Cash Adv', frm.doc.cash_adv).then(ca =>{
			if(!["Approved","Booked"].includes(ca.workflow_state)){
				frappe.msgprint("status must be either Approved or Booked")
				return
			}
			ca.items.forEach(e => {
				frm.add_child("items",e);
			})
			refresh_field("items");
			frm.set_value('cash_advance_request', ca.credit_in_account_currency)
			frm.set_value('is_advance', ca.is_advance)
			frm.set_value('user_remark', ca.user_remark)
			frm.set_value('cost_center', ca.cost_center)
		})
	}
});

