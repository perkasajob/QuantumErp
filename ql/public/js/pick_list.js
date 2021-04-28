// $("<button class='btn btn-default btn-xs btn-test' style='margin-left:10px;'>Test</button>").insertAfter($('.btn-split')[1])
// $($('.btn-split')[0]).attr('data-warehouse')
frappe.ui.form.on('Pick List', {
	onload_post_render(frm){
		// set_query_inspection(frm)
	},
	refresh(frm) {
		// if(frm.doc.docstatus == 1)
		// 	frm.add_custom_button(__('Stock Entry'), () => frm.trigger('create_stock_entry'), __('Create'));
	}
})

function convertUom(frm) {
	// split - ask for new qty and batch ID (optional)
	// and make stock entry via batch.batch_split
	frappe.call({
		method: 'ql.ql.stock.get_bom_uom',
		args: {
			work_order: frm.doc.work_order || "",
			material_request: frm.doc.material_request || ""
		},
		callback: (r) => {
			console.log(r)
			r.message.forEach(o => {
				frm.doc.locations.forEach(row =>{
					if(o.item_code == row.item_code){
						row.uom = o.uom
						if (row.uom) {
							get_item_details(row.item_code, row.uom).then(data => {
								frappe.model.set_value(row.doctype, row.name, 'conversion_factor', data.conversion_factor);
								frappe.model.set_value(row.doctype, row.name, 'qty', row.qty/data.conversion_factor);
							});
						}
					}
				})
			});
			frm.refresh_field("locations")
		},
	});
}

function get_item_details(item_code, uom=null) {
	if (item_code) {
		return frappe.xcall('erpnext.stock.doctype.pick_list.pick_list.get_item_details', {
			item_code,
			uom
		});
	}
}