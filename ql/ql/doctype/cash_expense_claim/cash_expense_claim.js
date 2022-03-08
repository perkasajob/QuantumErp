// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cash Expense Claim', {
	setup: function(frm) {
		frappe.db.get_single_value('Global Defaults', 'default_company')
			.then(default_company => {
				frm.set_value("company", default_company)
			})
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
					if(frm.doc.outstanding_amount < 0){
						je_account.credit_in_account_currency = -1 * frm.doc.outstanding_amount
					} else if (frm.doc.outstanding_amount > 0) {
						je_account.debit_in_account_currency = frm.doc.outstanding_amount
					}
					je_account.account = frm.doc.account
					je_account.bank_account = frm.doc.bank_account
					je_account.cost_center = frm.doc.cost_center
					je_account.reference_type = frm.doc.doctype
					je_account.reference_name = frm.doc.name
					frappe.set_route('Form', 'Journal Entry', je.name);
				});
			}, __('Create'));
			if ((flt(frm.doc.cash_advance_request_amount) <= flt(frm.doc.total))
				&& frappe.model.can_create("Payment Entry")) {
				frm.add_custom_button(__('Payment'),
					function() { frm.events.make_payment_entry(frm); }, __('Create'));
			}
		}
		if(frm.doc.cash_advance_request){
			frm.add_custom_button("Show CAReq", function () {
				cash_adv_request(frm)
			});
		}

	},
	// set_query_for_payable_account: function(frm) {
	// 	frm.fields_dict["account"].get_query = function() {
	// 		return {
	// 			filters: {
	// 				"report_type": "Balance Sheet",
	// 				"account_type": "Payable",
	// 				"is_group": 0
	// 			}
	// 		};
	// 	};
	// },
	cash_advance_request: function(frm){
		frappe.db.get_doc('Cash Advance Request', frm.doc.cash_advance_request).then(ca =>{
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
			frm.set_value('cash_advance_request_amount', ca.credit_in_account_currency)
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
	make_payment_entry: function(frm) {

		if (!frm.doc.account || !frm.doc.employee){
			frappe.throw("Account & Employee field cannot be empty")
			return
		}
		var method = "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry";
		if(frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "ql.ql.doctype.cash_expense_claim.cash_expense_claim.make_bank_entry"
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
		if(frm.selected_workflow_action === "Review"){
			frappe.db.set_value(frm.doc.doctype, frm.doc.name, 'verifier', frappe.user.full_name())
		}
	}
});


function cash_adv_request (frm) {
	frappe.db.get_doc('Cash Advance Request', frm.doc.cash_advance_request).then(ca =>{
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
