frappe.ui.form.on('BOM', {
	validate(frm){
		// set_query_inspection(frm)
		if(isNaN(frm.doc.formula_code)
			|| isNaN(frm.doc.batch_size_code)
			|| isNaN(frm.doc.supplier_code)){
				frappe.validated = 0;
				frappe.msgprint("Check Coding, must be number")
		} else {
			frm.set_value("coding",frm.doc.formula_code + frm.doc.batch_size_code + "-" + frm.doc.supplier_code)
		}
	}
})