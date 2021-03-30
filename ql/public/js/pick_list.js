// $("<button class='btn btn-default btn-xs btn-test' style='margin-left:10px;'>Test</button>").insertAfter($('.btn-split')[1])
// $($('.btn-split')[0]).attr('data-warehouse')
frappe.ui.form.on('Pick List', {
	onload_post_render(frm){
		// set_query_inspection(frm)
	},
	refresh(frm) {
		frm.add_custom_button(__('UoM'), function(){
			convertUom(frm);
		});
	}
})

function convertUom(frm) {
	// split - ask for new qty and batch ID (optional)
	// and make stock entry via batch.batch_split
	frappe.call({
		method: 'ql.ql.stock.get_bom_uom',
		args: {
			work_order: frm.doc.work_order,
		},
		callback: (r) => {
			console.log(r)
			r.message.forEach(o => {
				frm.doc.locations.forEach(l=>{
					if(o.item_code == l.item_code){
						l.uom = o.uom
						let row = l
						if (row.uom) {
							get_item_details(row.item_code, row.uom).then(data => {
								frappe.model.set_value(l.doctype, l.name, 'conversion_factor', data.conversion_factor);
							});
						}
					}
				})
			});
			frm.refresh_field("locations")
		},
	});
}