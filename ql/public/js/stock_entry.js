frappe.ui.form.on('Stock Entry', {
	refresh(frm) {
		set_auto_batch_insp_btn(frm)
	},
    validate(frm) {
		sum_volume(frm)
    }
})


function set_auto_batch_insp_btn(frm){
    frm.add_custom_button(__('Auto'), function(){
		(async () => {
			await create_batch_inspection(frm)
			cur_frm.save();
		})();
	});
}

async function create_batch_inspection(frm){
	let o = frm.doc.items[frm.doc.items.length - 1]
	let batch_no = (await frappe.db.get_value('Work Order', frm.doc.work_order, 'batch_no')).message.batch_no
	let qi_inspected_by_default = (await frappe.db.get_single_value ("QL Settings","qi_inspected_by_default"))

	frappe.model.set_value(o.doctype, o.name, 'batch_no', batch_no)

	if(!Object.keys(o).includes("quality_inspection") || !o.quality_inspection){
		let a = ['SE_A','SE_B','SE_C','SE_D','SE_E','SE_F','SE_G','SE_H','SE_J','SE_K','SE_L','SE_N']
		let doc = (await frappe.db.insert({
			doctype: 'Quality Inspection',
			item_code: o.item_code,
			inspection_type: 'In Process',
			reference_type: 'Stock Entry',
			reference_name: frm.doc.name,
			inspected_by: qi_inspected_by_default,
			received_qty: o.received_qty,
			sample_size: 0,
			batch_no: o.batch_no,
			month_code:a[(new Date()).getMonth()]
		}))
		o.quality_inspection = doc.name
		frappe.model.set_value(o.doctype, o.name, 'quality_inspection', doc.name)
		cur_frm.refresh_field("items")
		frappe.msgprint(`Quality Inspection ${doc.name} is Created`)
	}
}

function sum_volume(frm){
	let vol = frm.doc.items.map((o)=>{ return o.qty * o.volume_per_unit * o.conversion_factor }).reduce((total,o)=>{return total + o})
	frm.set_value('total_net_volume', vol)
}