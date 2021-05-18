frappe.ui.form.on('Sales Invoice', {
	validate(frm){

	    frm.set_value('discount_amount', frm.doc.mdp_discount_amount + Math.ceil(frm.doc.mdp_discount_margin/100 * (frm.doc.total - frm.doc.mdp_discount_amount)))
	}
})