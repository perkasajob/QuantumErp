// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cash Expense Claim', {
	refresh: function(frm) {
		if(frm.doc.workflow_state === "Approved"){
			frm.add_custom_button(__('Create Journal Entry'), function() {
				frappe.model.with_doctype('Journal Entry', function() {
					var je = frappe.model.get_new_doc('Journal Entry');
					je.remark = frm.doc.description
					je.cheque_no = frm.doc.cheque_no
					je.cheque_date = frm.doc.cheque_date
					je.cash_expense_claim = frm.doc.name
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
		if(frm.doc.cash_adv){
			frm.add_custom_button("Show CAReq", function () {
				cash_adv_request(frm)
			});
		}

	},
	cash_adv: function(frm){
		frappe.db.get_doc('Cash Adv', frm.doc.cash_adv).then(ca =>{
			if(!["Approved","Booked"].includes(ca.workflow_state)){
				frappe.msgprint("status must be either Approved or Booked")
				return
			}

			frm.set_value('items', [])
			let tableTemplate = frappe.meta.get_docfield(frm.doc.doctype, 'item_request', frm.doc.name).options
			let item_request = ""

			ca.items.forEach(e => {
				var c = frm.add_child("items");
				c.item = e.item
				c.qty = e.qty
				c.uom = e.uom
				c.rate = e.rate
				c.amount = e.amount
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

			refresh_field("items");
			refresh_field("item_request");
			frappe.meta.get_docfield(frm.doc.doctype, 'item_request', frm.doc.name).options = item_request
			// frm.set_value('item_request_content', item_request)

			frm.set_value('description', ca.description)
			frm.set_value('cash_advance_request', ca.credit_in_account_currency)
			frm.set_value('user_remark', ca.user_remark)
			frm.set_value('cost_center', ca.cost_center)
			cash_adv_request(frm)
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


function cash_adv_request (frm) {
	frappe.db.get_doc('Cash Adv', frm.doc.cash_adv).then(ca =>{
		if(!["Approved","Booked"].includes(ca.workflow_state)){
			frappe.msgprint("status must be either Approved or Booked")
			return
		}
		let tableTemplate = frappe.meta.get_docfield(frm.doc.doctype, 'item_request', frm.doc.name).options
		// let tableTemplate = "<table><tr><th>Planned Item|</th><th>Qty|</th><th>UoM|</th><th>Rate|</th><th>Note|</th></tr><tbody>"
		let item_request = ""


		ca.items.forEach(e => {
			// item_request += `<tr><td>${e.item}</td><td>${e.qty}</td><td>${e.uom??""}</td><td>${e.rate}</td><td>${e.note??""}</td></tr>`
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
		// item_request = tableTemplate + item_request + "</tbody></table>"
		// frappe.msgprint(item_request,"Cash Adv Request")
	})
}