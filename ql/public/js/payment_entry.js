frappe.ui.form.on('Payment Entry', {
	validate(frm){
	    if(frm.doc.total_allocated_amount && !frm.doc.is_fixed_paid_amount){
			frm.set_value("paid_amount", frm.doc.total_allocated_amount)
		}
	}
})