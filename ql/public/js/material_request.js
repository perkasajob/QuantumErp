frappe.ui.form.on('Material Request', {
	refresh(frm) {
		if(!frm.doc.requestee){
			frm.set_value("requestee", frappe.user.full_name())
		}
	},
	validate(frm){
	    if(!frm.doc.department){
	        var msg = "Department must be filled"
			frappe.msgprint(msg);
            throw msg;
		}
	},
	onload(frm){
		if(!frm.doc.requestee){
			frm.set_value("requestee", frappe.user.full_name())
		}

	    if(frm.doc.department)
	        return
		var dept_list = []
        frappe.db.get_single_value('QL Settings', 'dept_abbr')
    	.then(value => {
    		dept_list = value.split(",");
			var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
    		if(!frappe.user.has_role("System Manager") && !frappe.user.has_role("Purchase Manager"))
				frm.set_df_property("department", "read_only", dept ? 1 : 0);
			frm.set_value("department", dept)
		});
	}
})

frappe.ui.form.on('Purchase Invoice', {
	refresh(frm) {
		// your code here
	},
	validate(frm){
	    if(!frm.doc.department){
	        var msg = "Department must be filled"
	        frappe.msgprint(msg);
            throw msg;
	    }
	},
	onload(frm){
	    if(frm.doc.department)
	        return
	    var dept_list = []
        frappe.db.get_single_value('QL Settings', 'dept_abbr')
    	.then(value => {
    		dept_list = value.split(",");
    		var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
    		if(!frappe.user.has_role("System Manager") && !frappe.user.has_role("Purchase Manager") && !frappe.user.has_role("Purchase User"))
    	        frm.set_df_property("department", "read_only", dept ? 1 : 0);
    		frm.set_value("department", dept)
        });
	}
})


function dept_list_func(frm){
    var dept_list = []
    frappe.db.get_single_value('QL Settings', 'dept_abbr')
	.then(value => {
		dept_list = value.split(",");
		var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
		console.log(dept)
		if (!frm.doc.__islocal)
	        frm.set_df_property("department", "read_only", dept ? 1 : 0);
    });
}