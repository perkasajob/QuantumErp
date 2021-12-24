frappe.ui.form.on('Purchase Order', {
	onload(frm){
	    if(frm.doc.department){
	        if (!(frappe.user.has_role("System Manager") || frappe.user.name =="Administrator") ){
    	        frm.set_df_property("department", "read_only", 1);
	        }
	        return
	    }
	    var dept_list = []
        frappe.db.get_single_value('QL Settings', 'dept_abbr')
    	.then(value => {
    		dept_list = value.split(",");
    		var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
    		if (!frm.doc.__islocal)
    	        frm.set_df_property("department", "read_only", dept ? 1 : 0);
        });
	},
	validate(frm){
		if(!frm.doc.department){
	        var msg = "Department must be filled"
	        frappe.msgprint(msg);
            throw msg;
	    }
		check_supplier_release(frm)
		debugger
		if (frm.doc.__islocal && !frm.doc.orderer){
			frm.set_value("orderer", frappe.user.full_name())
		}
	},
	before_submit(frm){
		frm.set_value("submitter", frappe.user.full_name())
	},
	set_warehouse(frm){
		frm.set_value("shipping_address", frm.doc.set_warehouse)
	}
})

function check_supplier_release(frm){

	frappe.call({
		method: 'frappe.model.db_query.get_list',
		async: false,
		args: {
			doctype: "Supplier Release",
			filters:{
				'supplier': frm.doc.supplier,
				'released': 0
			},
			fields:['item']
		},
		type: 'GET',
		callback: function(o) {
			var item_codes = frm.doc.items.map(o=>{return o.item_code})
			let lock_items = ""
			o.message.forEach(e => {
				if(item_codes.includes(e.item)){
					frappe.validated = false;
					lock_items += e.item + ","
				}
				if(!frappe.validated){
					frappe.msgprint(lock_items + " not yet released by QA")
				}
			});
		}
	});
}