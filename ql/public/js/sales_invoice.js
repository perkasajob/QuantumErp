frappe.ui.form.on('Sales Invoice', {
	validate(frm){
		if(frm.doc.is_return){
			frm.set_value('taxes', [])
			frm.set_value('taxes_and_charges', '')
			// frm.set_value('mdp_discount_amount', 0)
			frm.set_value('mdp_discount_margin', 0)
			const default_company = frappe.defaults.get_default('company');
			frappe.db.get_value('Company', default_company, 'abbr').then(r=>{
				const abbr = r.message.abbr
				debugger
				frm.set_value('taxes_and_charges', `PPN - ${abbr}`)
			})

		} else {
			frm.set_value('discount_amount', frm.doc.mdp_discount_amount + Math.ceil(frm.doc.mdp_discount_margin/100 * (frm.doc.total - frm.doc.mdp_discount_amount)))
		}

		if(frm.doc.warehouse){
			frm.doc.items.forEach(e => {
				if(!e.warehouse){
					e.warehouse = frm.doc.warehouse
				}
			});
		}
	}
})