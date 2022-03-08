// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cash Advance Request', {
	setup: function(frm) {
		if(!frm.doc.company){
			frappe.db.get_single_value('Global Defaults', 'default_company')
				.then(default_company => {
					frm.set_value("company", default_company)
				})
		}

		frm.set_query("advance_account", function() {
			return {
				filters: {
					"root_type": "Asset",
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});
	},
	refresh: function(frm) {
		if(frm.doc.workflow_state === "Approved"){
			frm.add_custom_button(__('Journal Entry'), function() {
				frappe.model.with_doctype('Journal Entry', function() {
					var je = frappe.model.get_new_doc('Journal Entry');
					je.remark = frm.doc.description
					je.cheque_no = frm.doc.cheque_no
					je.cheque_date = frm.doc.cheque_date
					je.user_remark = frm.doc.user_remark

					// var accounts = frm.get_field('accounts').grid.get_selected_children();
					var je_account = frappe.model.add_child(je, 'accounts');
					je_account.credit_in_account_currency = Math.abs(frm.doc.credit_in_account_currency)
					je_account.account = frm.doc.account
					je_account.bank_account = frm.doc.bank_account
					je_account.cost_center = frm.doc.cost_center
					je_account.reference_due_date = frm.doc.req_date
					je_account.reference_type = frm.doc.doctype
					je_account.reference_name = frm.doc.name
					je_account.is_advance = 'Yes'
					frappe.set_route('Form', 'Journal Entry', je.name);
				});
			}, __('Create'));
			// if ((flt(frm.doc.credit_in_account_currency) <= flt(frm.doc.requested_amount))
			// 	&& frappe.model.can_create("Payment Entry")) {
			// 	frm.add_custom_button(__('Payment'),
			// 		function() { frm.events.make_payment_entry(frm); }, __('Create'));
			// }
		} else if (frm.doc.workflow_state === "Booked") {
			frm.add_custom_button(__('Create Recap'), function() {
				frappe.model.with_doctype('Cash Expense Claim', function() {
					var cec = frappe.model.get_new_doc('Cash Expense Claim');
					cec.remark = frm.doc.description
					cec.cheque_no = frm.doc.cheque_no
					cec.cheque_date = frm.doc.cheque_date
					cec.cash_advance_request = frm.doc.name
					cec.user_remark = frm.doc.user_remark
					cec.department = frm.doc.department

					// var accounts = frm.get_field('accounts').grid.get_selected_children();
					var cec_account = frappe.model.add_child(cec, 'accounts');
					var items = frm.get_field('items').grid.get_selected_children();
					if(!items.length) {
						items = frm.doc.items;
					}
					items.forEach(function(item) {
						var cec_item = frappe.model.add_child(cec, 'items');
						cec_item.item = item.item;
						cec_item.qty = item.qty;
						cec_item.uom = item.uom;
						cec_item.rate = item.rate;
						cec_item.note = item.note;
					});
					cec_account.cash_advance_request = frm.doc.credit_in_account_currency
					cec_account.account = frm.doc.account
					cec_account.bank_account = frm.doc.bank_account
					cec_account.cost_center = frm.doc.cost_center
					frappe.set_route('Form', 'Cash Expense Claim', cec.name);
				});
			});
		}
	},
	is_fixed_amount: function(frm){
		frm.set_df_property("requested_amount", "read_only", frm.doc.is_fixed_amount ? 0 : 1);
	},
	validate(frm){
	    if(!frm.doc.department){
	        var msg = "Department must be filled"
			frappe.msgprint(msg);
            throw msg;
		}
	},
	onload(frm){
		frm.set_query("journal_entry", function() {
			return {
				filters: {
					reference_name: frm.doc.name
				}
			}
		})

	    if(!frm.doc.department){
			var dept_list = []
			frappe.db.get_single_value('QL Settings', 'dept_abbr')
			.then(value => {
				dept_list = value.split(",");
				var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
				if(!frappe.user.has_role("System Manager") && !frappe.user.has_role("Cash Advance Request Verificator"))
					frm.set_df_property("department", "read_only", dept ? 1 : 0);
				frm.set_value("department", dept)
			});
		}
	},
	make_payment_entry: function(frm) {

		if (!frm.doc.advance_account || !frm.doc.employee){
			frappe.throw("Advance Account & Employee field cannot be empty")
			return
		}
		var method = "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry";
		if(frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "ql.ql.doctype.cash_advance_request.cash_advance_request.make_bank_entry"
		}

		return frappe.call({
			method: method,
			args: {
				"dt": frm.doc.doctype,
				"dn": frm.doc.name
			},
			callback: function(r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	},
	before_workflow_action(frm){
		if(frm.selected_workflow_action == "Review"){
			frappe.db.set_value(frm.doc.doctype, frm.doc.name, 'verifier', frappe.user.full_name())
		}
	}
});
