frappe.ui.form.on('Purchase Order', {
	onload(frm){
	    // if(frm.doc.department){
	    //     if (!(frappe.user.has_role("System Manager") || frappe.user.name =="Administrator") ){
    	//         frm.set_df_property("department", "read_only", 1);
	    //     }
	    //     return
	    // }
	    // var dept_list = []
			// frappe.db.get_single_value('QL Settings', 'dept_abbr')
			// .then(value => {
			// 	dept_list = value.split(",");
			// 	var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
			// 	if (!frm.doc.__islocal)
			// 				frm.set_df_property("department", "read_only", dept ? 1 : 0);
			// });

		frappe.db.get_single_value('QL Settings', 'pi_po_same_rate')
		.then(pi_po_same_rate => {
			if (pi_po_same_rate){
				frappe.db.get_list('Supplier', {
						fields: ['name'],
						filters: {
							allow_different_purchase_rate: 1,
						}
				}).then(s => {
					if( s.map((a)=>{return a.name}).includes(frm.doc.supplier)){
						frappe.call({
							method: 'erpnext.buying.doctype.purchase_order.purchase_order.get_pi_price',
							args: {
									'purchase_order': frm.doc.name
							},
							callback: function(r) {
								if (!r.exc) {
									let o = r.message
									let total = 0
									for(var i=0; i< o.length; i++) {
										frm.doc.items.forEach(item => {
											if(item.name == o[i].po_detail){
												item.rate = o[i].rate
												item.price_list_rate = o[i].rate
												item.amount = flt(item.rate * item.qty, 2)
											}
											total += item.amount
										});
									}
									frm.doc.total =  total
									frm.refresh_field("items");
									frm.refresh_field("total");
								}
							}
						});
					}
				})
			}
		})
	},
	// validate(frm){
	// 	if(!frm.doc.department){
	//         var msg = "Department must be filled"
	//         frappe.msgprint(msg);
  //           throw msg;
	//     }
	// 	check_supplier_release(frm)
	// 	if (frm.doc.__islocal && !frm.doc.orderer){
	// 		frm.set_value("orderer", frappe.user.full_name())
	// 	}
	// },
	// before_submit(frm){
	// 	frm.set_value("submitter", frappe.user.full_name())
	// },
	// set_warehouse(frm){
	// 	frm.set_value("shipping_address", frm.doc.set_warehouse)
	// }
})


frappe.ui.form.on("Purchase Order Item", {
	item_code: function(frm, cdt, cdn) {
		console.log("item_code selected")
		var row = locals[cdt][cdn];
			if (row.item_code) {
				frm.set_query("supplier", function() {
					return {
						query: "ql.ql.purchase.get_allow_suppliers",
						filters: {
							"item_code": row.item_code,
						}
					}
				});
			}
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