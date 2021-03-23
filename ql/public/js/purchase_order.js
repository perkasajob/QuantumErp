frappe.listview_settings['Purchase Order'].refresh = function (listview) {
	if(frappe.user.has_role(["WH","Stock User"])){
		$( "span[title*='Grand Total:']").remove()
	}
}

frappe.ui.form.on('Purchase Order', {
	validate(frm){
		check_supplier_release(frm)
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