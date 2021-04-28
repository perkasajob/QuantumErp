
frappe.ui.form.on('Work Order', {
	refresh(frm){
		if(cur_frm.doc.status == "In Process"){
			// WO allows to add Material Consumption after Manufacture, once Material Consumption is submitted, WO will complete
			var consumption_btn = frm.add_custom_button(__('Material Consumption'), function() {
				const backflush_raw_materials_based_on = frm.doc.__onload.backflush_raw_materials_based_on;
				erpnext.work_order.make_consumption_se(frm, backflush_raw_materials_based_on);
			});
			consumption_btn.addClass('btn-primary');
			frm.add_custom_button(__('Create Pick List'), function() {
				create_pick_list(frm);
			});
			// this.frm.add_custom_button(__('Material Request'),
			// 	function() {
			// 		erpnext.utils.map_current_doc({
			// 			method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order",
			// 			source_doctype: "Material Request",
			// 			target: me.frm,
			// 			setters: {
			// 				company: me.frm.doc.company
			// 			},
			// 			get_query_filters: {
			// 				material_request_type: "Material Transfer",
			// 				docstatus: 1,
			// 				status: ["!=", "Stopped"],
			// 				per_ordered: ["<", 99.99],
			// 			}
			// 		})
			// 	});
		}
	},
})

function create_pick_list(frm) {  // , purpose='Material Transfer for Manufacture'
	    frappe.xcall('ql.ql.work_order.create_pick_list', {
				'source_name': frm.doc.name,
				'for_qty': frm.doc.qty
		}).then(pick_list => {
			frappe.model.sync(pick_list);
			frappe.set_route('Form', pick_list.doctype, pick_list.name);
		});
}


function create_stock_entry(frm) {
	frappe.xcall('erpnext.stock.doctype.pick_list.pick_list.create_stock_entry', {
		'pick_list': frm.doc,
	}).then(stock_entry => {
		frappe.model.sync(stock_entry);
		frappe.set_route("Form", 'Stock Entry', stock_entry.name);
	});
}

function make_se(frm, purpose) {
	this.show_prompt_for_qty_input(frm, purpose)
		.then(data => {
			return frappe.xcall('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry', {
				'work_order_id': frm.doc.name,
				'purpose': purpose,
				'qty': data.qty
			});
		}).then(stock_entry => {
			frappe.model.sync(stock_entry);
			frappe.set_route('Form', stock_entry.doctype, stock_entry.name);
		});

}

