// Copyright (c) 2020, Perkasa JoB and Contributors
// License: QL. See license.txt

frappe.ui.form.on('Job Card', {
	refresh(frm) {
		frm.add_custom_button(__('convert'), function(){
			uom_convert(frm);
		});
	},

})

function uom_convert(frm){
	frappe.prompt([{
		fieldname: 'density',
		label: __('Density'),
		fieldtype: 'Float',
		'default': 1
	}],
	(data) => {
		frm.doc.time_logs.forEach(o => {
			o.completed_qty = o.completed_qty / (data.density||1)
		});
		frm.refresh()
		frm.scroll_to_field("time_logs");
	},
	__('Convert Weight to pcs'),
	__('Convert')
	);

}