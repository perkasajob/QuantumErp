// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Petty Cash Reimbursement', {
	onload(frm){
		frm.set_query("journal_entry", function() {
			return {
				filters: {
					reference_name: frm.doc.name
				}
			}
		})
		frappe.db.get_single_value('Global Defaults', 'default_company')
			.then(default_company => {
				frm.set_query("cash_account", function() {
					return {
						filters: {
							company: default_company,
							account_type: 'Cash',
							is_group: 0
						}
					}
				})
			})
	},
	refresh: function(frm) {
		if(frm.doc.workflow_state === "Approved"){
			frm.add_custom_button(__('Create Journal Entry'), function() {
				frappe.model.with_doctype('Journal Entry', function() {
					var je = frappe.model.get_new_doc('Journal Entry');
					je.cheque_no = frm.doc.cheque_no
					je.cheque_date = frm.doc.cheque_date
					je.user_remark = frm.doc.user_remark

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
					je_account.reference_type = frm.doc.doctype
					je_account.reference_name = frm.doc.name

					frappe.set_route('Form', 'Journal Entry', je.name);
				});
			});
		}
	},
	cash_account(frm){
		get_items(frm)
	},
	from_date(frm){
		get_items(frm)
	},
	to_date(frm){
		get_items(frm)
	},
	before_workflow_action(frm){
		if(frm.selected_workflow_action === "Submit"){
			frappe.db.set_value(frm.doc.doctype, frm.doc.name, 'verifier', frappe.user.full_name())
		}
	}
});


function get_items(frm){
	if(frm.doc.cash_account && frm.doc.from_date && frm.doc.to_date){
		frappe.xcall('ql.ql.doctype.petty_cash_reimbursement.petty_cash_reimbursement.get_items',
		{account: frm.doc.cash_account,
		from_date: frm.doc.from_date, to_date: frm.doc.to_date })
			.then(r => {
				frm.doc.cash_expense_claims = []
				frm.doc.expense_claims = []
				frm.doc.purchase_inv_payments = []
				if(r) {
					r.cec.forEach((d) => {
						let i = frm.add_child("cash_expense_claims");
						i.cash_expense_claim = d.name;
						i.date = d.date;
						i.amount = d.total;
						i.description = d.description;
						i.voucher = d.voucher;
					})
					refresh_field("cash_expense_claims");

					r.ec.forEach((d) => {
						let i = frm.add_child("expense_claims");
						i.expense_claim = d.name;
						i.posting_date = d.date;
						i.total_sanctioned_amount = d.total_sanctioned_amount;
						i.remark = d.remark;
						i.voucher = d.voucher;
					})
					refresh_field("expense_claims");

					r.pe.forEach((d) => {
						let p = frm.add_child("purchase_inv_payments");
						p.payment_entry = d.name;
						p.date = d.posting_date;
						p.amount = d.paid_amount;
						p.description = d.description;
					})
					refresh_field("purchase_inv_payments");
					frm.set_value('cec_total', r.cec_total)
					frm.set_value('ec_total', r.ec_total)
					frm.set_value('pip_total', r.pe_total)
					frm.set_value('total', r.cec_total + r.ec_total + r.pe_total)
				}
			});
	}
}
