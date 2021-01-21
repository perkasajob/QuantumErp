frappe.ui.form.on('Stock Entry', {
    validate(frm) {
		sum_volume(frm)
    }
})

function sum_volume(frm){
	let vol = frm.doc.items.map((o)=>{ return o.qty * o.volume_per_unit * o.conversion_factor }).reduce((total,o)=>{return total + o})
	frm.set_value('total_net_volume', vol)
}