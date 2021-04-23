
frappe.ui.form.on('Work Order', {
	refresh(frm){
		if(cur_frm.doc.status == "In Process"){
			var consumption_btn = frm.add_custom_button(__('Material Consumption'), function() {
				const backflush_raw_materials_based_on = frm.doc.__onload.backflush_raw_materials_based_on;
				erpnext.work_order.make_consumption_se(frm, backflush_raw_materials_based_on);
			});
			consumption_btn.addClass('btn-primary');
		}
	},
})
