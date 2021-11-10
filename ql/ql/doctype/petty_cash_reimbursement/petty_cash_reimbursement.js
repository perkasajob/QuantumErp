// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Petty Cash Reimbursement', {
	refresh: function(frm) {
		frm.add_custom_button(__('Get CEC'), function() {
			// frappe.db.get_list("Cash Expense Claim", {
			// 	filters: { 'workflow_state': 'Approved'},
			// 	fields: ['name', 'purchase_date', 'total', 'description'],
			// 	order_by: 'purchase_date desc'
			// }).then((r) => {
			// 	if(r) {
			// 		r.forEach((d) => {
			// 			let i = frm.add_child("items");
			// 			i.cash_expense_claim = d.name;
			// 			i.date = d.purchase_date;
			// 			i.amount = d.total;
			// 			i.description = d.description;
			// 		})
			// 		refresh_field("items");
			// 	}
			// })

			frappe.xcall('ql.ql.doctype.petty_cash_reimbursement.petty_cash_reimbursement.get_items')
			.then(r => {
				console.log(r)
				if(r) {
					r.forEach((d) => {
						let i = frm.add_child("items");
						i.cash_expense_claim = d.name;
						i.date = d.purchase_date;
						i.amount = d.total;
						i.description = d.description;
					})
					refresh_field("items");
				}
			});
		})

		if(frm.doc.workflow_state === "Approved"){
			frm.add_custom_button(__('Create Journal Entry'), function() {
				frappe.model.with_doctype('Journal Entry', function() {
					var je = frappe.model.get_new_doc('Journal Entry');
					je.cheque_no = frm.doc.cheque_no
					je.cheque_date = frm.doc.cheque_date
					je.user_remark = frm.doc.user_remark
					je.reference_type = frm.doc.doctype
					je.reference_name = frm.doc.name

					// var accounts = frm.get_field('accounts').grid.get_selected_children();
					var je_account = frappe.model.add_child(je, 'accounts');
					if(frm.doc.total < 0){
						je_account.credit_in_account_currency = -1 * frm.doc.total
					} else if (frm.doc.total > 0) {
						je_account.debit_in_account_currency = frm.doc.total
					}
					je_account.account = frm.doc.account
					je_account.bank_account = frm.doc.bank_account
					je_account.cost_center = frm.doc.cost_center
					frappe.set_route('Form', 'Journal Entry', je.name);
				});
			});
		}
	},
	before_workflow_action(frm){
		if(frm.selected_workflow_action === "Submit"){
			frappe.db.set_value(frm.doc.doctype, frm.doc.name, 'verifier', frappe.user.full_name())
		} else if(frm.selected_workflow_action === "Finish"){
			if(!frm.doc.journal_entry)
				frappe.throw(__("Please set a Journal Entry"));
		}
	}
});