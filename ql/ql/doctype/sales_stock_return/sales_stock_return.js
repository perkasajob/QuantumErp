// Copyright (c) 2021, Perkasa JoB and contributors
// For license information, please see license.txt

{% include 'erpnext/selling/sales_common.js' %};

cur_frm.add_fetch('customer', 'tax_id', 'tax_id');

frappe.provide("erpnext.stock");
frappe.provide("ql.sales_stock_return");


frappe.ui.form.on('Sales Stock Return', {
	validate: function(frm) {
		if(frm.doc.warehouse){
			frm.doc.items.forEach(e => {
				if(!e.warehouse){
					e.warehouse = frm.doc.warehouse
				}
			});
		}
		frm.doc.items.forEach(i => {
			if(i.qty > 0){
				i.qty = -1 * i.qty
			}
		});


	},
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Packing Slip': 'Packing Slip',
			'Installation Note': 'Installation Note',
			'Sales Invoice': 'Invoice',
			'Stock Entry': 'Return',
		},
		frm.set_indicator_formatter('item_code',
			function(doc) {
				return (doc.docstatus==1 || doc.qty<=doc.actual_qty) ? "green" : "orange"
			})

		erpnext.queries.setup_queries(frm, "Warehouse", function() {
			return erpnext.queries.warehouse(frm.doc);
		});
		erpnext.queries.setup_warehouse_query(frm);

		frm.set_query('project', function(doc) {
			return {
				query: "erpnext.controllers.queries.get_project_name",
				filters: {
					'customer': doc.customer
				}
			}
		})

		frm.set_query('transporter', function() {
			return {
				filters: {
					'is_transporter': 1
				}
			}
		});

		frm.set_query('driver', function(doc) {
			return {
				filters: {
					'transporter': doc.transporter
				}
			}
		});


		frm.set_query('expense_account', 'items', function(doc, cdt, cdn) {
			if (erpnext.is_perpetual_inventory_enabled(doc.company)) {
				return {
					filters: {
						"report_type": "Profit and Loss",
						"company": doc.company,
						"is_group": 0
					}
				}
			}
		});

		frm.set_query('cost_center', 'items', function(doc, cdt, cdn) {
			if (erpnext.is_perpetual_inventory_enabled(doc.company)) {
				return {
					filters: {
						'company': doc.company,
						"is_group": 0
					}
				}
			}
		});


	},

	print_without_amount: function(frm) {
		ql.sales_stock_return.set_print_hide(frm.doc);
	},

	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.is_return === 1 && frm.doc.per_billed !== 100) {
			frm.add_custom_button(__('Credit Note'), function() {
				frappe.model.open_mapped_doc({
					method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
					frm: cur_frm,
				})
			}, __('Create'));
			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	}
});

frappe.ui.form.on("Sales Stock Return Item", {
	expense_account: function(frm, dt, dn) {
		var d = locals[dt][dn];
		frm.update_in_all_rows('items', 'expense_account', d.expense_account);
	},
	cost_center: function(frm, dt, dn) {
		var d = locals[dt][dn];
		frm.update_in_all_rows('items', 'cost_center', d.cost_center);
	}
});

ql.SalesStockReturnController = erpnext.selling.SellingController.extend({
	setup: function(doc) {
		this.setup_posting_date_time_check();
		this._super(doc);
		this.frm.make_methods = {
			'Delivery Trip': this.make_delivery_trip,
		};
	},
	refresh: function(doc, dt, dn) {
		var me = this;
		this._super();
		if ((!doc.is_return) && (doc.status!="Closed" || this.frm.is_new())) {
			if (this.frm.doc.docstatus===0) {
				this.frm.add_custom_button(__('Sales Order'),
					function() {
						if (!me.frm.doc.customer) {
							frappe.throw({
								title: __("Mandatory"),
								message: __("Please Select a Customer")
							});
						}
						erpnext.utils.map_current_doc({
							method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
							source_doctype: "Sales Order",
							target: me.frm,
							setters: {
								customer: me.frm.doc.customer,
							},
							get_query_filters: {
								docstatus: 1,
								status: ["not in", ["Closed", "On Hold"]],
								per_delivered: ["<", 99.99],
								company: me.frm.doc.company,
								project: me.frm.doc.project || undefined,
							}
						})
					}, __("Get items from"));
			}
		}

		if (!doc.is_return && doc.status!="Closed") {

			if (doc.docstatus==1) {
				this.frm.add_custom_button(__('Sales Return'), function(frm) {
					me.make_sales_return(me.frm) }, __('Create'));
			}

			if (!doc.__islocal && doc.docstatus==1) {
				this.frm.page.set_inner_btn_group_as_primary(__('Create'));
			}
		}

		if (doc.docstatus==1) {
			this.show_stock_ledger();
			if (erpnext.is_perpetual_inventory_enabled(doc.company)) {
				this.show_general_ledger();
			}
			if (this.frm.has_perm("submit") && doc.status !== "Closed") {
				me.frm.add_custom_button(__("Close"), function() { me.close_delivery_note() },
					__("Status"))
			}
		}

		// ql.sales_stock_return.set_print_hide(doc, dt, dn);

	},

	make_sales_return: function(frm) {
		// frappe.model.open_mapped_doc({
		// 	method: "ql.ql.doctype.sales_stock_return.sales_stock_return.make_sales_return",
		// 	frm: this.frm
		// })

		frappe.db.get_value("Company", {"name": frm.doc.company}, ["default_income_account", "default_warehouse_for_sales_return"], (r) => {
			frappe.model.with_doctype('Sales Invoice', function() {
				var si = frappe.model.get_new_doc('Sales Invoice');
				si.sales_stock_return = frm.doc.name
				si.customer = frm.doc.customer
				si.warehouse = frm.doc.warehouse
				si.is_return = 1
				si.update_stock = 1

				var items = frm.get_field('items').grid.get_selected_children();
				if(!items.length) {
					items = frm.doc.items;
				}
				items.forEach(function(item) {
					var si_item = frappe.model.add_child(si, 'items');
					si_item.item_code = item.item_code;
					si_item.item_name = item.item_name;
					si_item.description = item.description;
					si_item.customer_item_code = item.customer_item_code;
					si_item.qty = item.qty;
					si_item.uom = item.uom;
					si_item.warehouse = r.default_warehouse_for_sales_return;
					si_item.batch_no = item.batch_no;
					si_item.rate = item.rate;
					si_item.note = item.note;
					si_item.ssr_detail = frm.doc.name;
					si_item.income_account = item.return_account;
				});

				frappe.set_route('Form', 'Sales Invoice', si.name);
			});

		});




	},

	tc_name: function() {
		this.get_terms();
	},

	items_on_form_rendered: function(doc, grid_row) {
		erpnext.setup_serial_no();
	},

	packed_items_on_form_rendered: function(doc, grid_row) {
		erpnext.setup_serial_no();
	},

	close_delivery_note: function(doc){
		this.update_status("Closed")
	},

	reopen_delivery_note : function() {
		this.update_status("Submitted")
	},

	update_status: function(status) {
		var me = this;
		frappe.ui.form.is_saving = true;
		frappe.call({
			method:"erpnext.stock.doctype.delivery_note.delivery_note.update_delivery_note_status",
			args: {docname: me.frm.doc.name, status: status},
			callback: function(r){
				if(!r.exc)
					me.frm.reload_doc();
			},
			always: function(){
				frappe.ui.form.is_saving = false;
			}
		})
	},

	warehouse: function() {
		let packed_items_table = this.frm.doc["packed_items"];
		this.autofill_warehouse(this.frm.doc["items"], "source_warehouse", this.frm.doc.to_warehouse);
		if (packed_items_table && packed_items_table.length) {
			this.autofill_warehouse(packed_items_table, "source_warehouse", this.frm.doc.to_warehouse);
		}
	}

});

$.extend(cur_frm.cscript, new ql.SalesStockReturnController({frm: cur_frm}));

frappe.ui.form.on('Sales Stock Return', {
	setup: function(frm) {
		if(frm.doc.company) {
			frm.trigger("unhide_account_head");
		}
	},

	company: function(frm) {
		frm.trigger("unhide_account_head");
	},

	unhide_account_head: function(frm) {
		// unhide expense_account and cost_center if perpetual inventory is enabled in the company
		var aii_enabled = erpnext.is_perpetual_inventory_enabled(frm.doc.company)
		frm.fields_dict["items"].grid.set_column_disp(["expense_account", "cost_center"], aii_enabled);
	}
})


ql.sales_stock_return.set_print_hide = function(doc, cdt, cdn){
	var dn_fields = frappe.meta.docfield_map['Sales Stock Return'];
	var dn_item_fields = frappe.meta.docfield_map['Sales Stock Return Item'];
	var dn_fields_copy = dn_fields;
	var dn_item_fields_copy = dn_item_fields;
	if (doc.print_without_amount) {
		dn_fields['currency'].print_hide = 1;
		dn_item_fields['rate'].print_hide = 1;
		dn_item_fields['discount_percentage'].print_hide = 1;
		dn_item_fields['price_list_rate'].print_hide = 1;
		dn_item_fields['amount'].print_hide = 1;
		dn_item_fields['discount_amount'].print_hide = 1;
		dn_fields['taxes'].print_hide = 1;
	} else {
		if (dn_fields_copy['currency'].print_hide != 1)
			dn_fields['currency'].print_hide = 0;
		if (dn_item_fields_copy['rate'].print_hide != 1)
			dn_item_fields['rate'].print_hide = 0;
		if (dn_item_fields_copy['amount'].print_hide != 1)
			dn_item_fields['amount'].print_hide = 0;
		if (dn_item_fields_copy['discount_amount'].print_hide != 1)
			dn_item_fields['discount_amount'].print_hide = 0;
		if (dn_fields_copy['taxes'].print_hide != 1)
			dn_fields['taxes'].print_hide = 0;
	}
}
