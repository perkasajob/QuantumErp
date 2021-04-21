frappe.ui.form.on('Purchase Invoice', {
	validate(frm) {
		let project = ""
	    frm.doc.items.forEach((o,i)=>{
			if(!project)project=o.project
		})
		frm.set_value('project', project)
	},
})