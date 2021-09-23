// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cash Adv Recap', {
	refresh: function(frm) {
		if(frm.doc.workflow_state === "Approved"){
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
					frappe.set_route('Form', 'Journal Entry', je.name);
				});
			});
		}
	},
	cash_adv: function(frm){
		frappe.db.get_doc('Cash Adv', frm.doc.cash_adv).then(ca =>{
			if(!["Approved","Booked"].includes(ca.workflow_state)){
				frappe.msgprint("status must be either Approved or Booked")
				return
			}
			let tableTemplate = frappe.meta.get_docfield(frm.doc.doctype, 'item_request', frm.doc.name).options
			let item_request = ""

			frm.set_value('items', [])
			ca.items.forEach(e => {
				frm.add_child("items",e);
				item_request += `<div class="row-index sortable-handle col col-xs-1">
									<span class="hidden-xs">${e.idx}</span>
								</div>
									<div class="col grid-static-col col-xs-5  bold">
									${e.item}
								</div>
								<div class="col grid-static-col col-xs-1  text-right bold">
									<div style="text-align: right">${e.qty}</div>
								</div>
								<div class="col grid-static-col col-xs-1 ">
									${e.uom??""}
								</div>
								<div class="col grid-static-col col-xs-2  text-right">
									<div style="text-align: right">${e.rate}</div>
								</div>
								<div class="col grid-static-col col-xs-2  text-right">
									<div style="text-align: right">${e.note??""}</div>
								</div>`
			})

			item_request = tableTemplate.replace('[No Data]',item_request ) + '<div class="clearfix"></div>'
			frappe.meta.get_docfield(frm.doc.doctype, 'item_request', frm.doc.name).options = item_request
			refresh_field("item_request");
			refresh_field("items");

			frm.set_value('description', ca.description)
			frm.set_value('cash_advance_request', ca.credit_in_account_currency)
			frm.set_value('user_remark', ca.user_remark)
			frm.set_value('cost_center', ca.cost_center)
		})
	},
	purchase_date: function(frm){
		frm.doc.items.forEach(i =>{
			i.date = frm.doc.purchase_date
		})
		refresh_field("items")
	},
	before_workflow_action(frm){
		if(frm.selected_workflow_action === "Review"){
			frappe.db.set_value(frm.doc.doctype, frm.doc.name, 'verifier', frappe.user.full_name())
		} else if(frm.selected_workflow_action === "Finish"){
			if(!frm.doc.journal_entry)
				frappe.throw(__("Please set a Journal Entry"));
		}
	}
});

