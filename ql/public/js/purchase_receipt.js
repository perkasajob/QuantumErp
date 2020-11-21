frappe.ui.form.on('Purchase Receipt', {
	refresh(frm) {
		set_POQty_btn(frm)
	},
	validate(frm) {
	    frm.doc.items.forEach((o,i)=>{if(!o.purchase_order_item)frm.doc.items.splice(i)}) // remove items without PO reference
	   // frm.refresh_field("items")
	    check_POqty(frm, true)
	},
	before_submit(frm){
	   check_POqty(frm, true)
	}
})


function set_POQty_btn(frm){
    frm.add_custom_button(__('PO Qty'), function(){
        check_POqty(frm, false);
	});
};

async function check_POqty(frm, validation){
    var lqty = {}
    frm.doc.items.forEach((o,i)=>{if(!o.purchase_order_item)frm.doc.items.splice(i)}) // remove items without PO reference
	frm.refresh_field("items")
    // frm.doc.items.forEach(o=>lqty[o.item_name]= o.item_name in lqty?lqty[o.item_name]+o.qty:o.qty)
    frm.doc.items.forEach(o=>lqty[o.purchase_order_item]= o.qty)
    frappe.call({
			method: "ql.ql.purchase.check_PO_qty",
			args: {
				"docname": frm.doc.name,
				"item_names": frm.doc.items.map((o)=>{return o.item_name}), //Object.keys(lqty),
				"purchase_order_item": frm.doc.items.map((o)=>{return o.purchase_order_item})
			},
			callback: function(r) {
				if (r.message) {
			    	var str = ""
			    	var fail = false
			    	r.message.forEach(e => {
			    	    
			    	    if(frm.doc.__islocal){
			    	        var pri_qty = lqty[e[0].purchase_order_item] + e[0].pri_qty
			    	    } else{
			    	        var pri_qty = e[0].pri_qty
			    	    }
    					str += '<tr><td>'+e[0].poi_idx  + '</td><td>'+e[0].item_name + '['+ e[0].schedule_date+']</td><td style="text-align:right">'+e[0].poi_qty +'</td><td style="text-align:right">'+ pri_qty
    					var percentage =Math.floor(pri_qty/e[0].poi_qty*100)
    					if(percentage > 105){
    					    str += '<td style="color:red">'
    					    fail = true
    					} else {
    					    str += '<td>'
    					}    
    					str += percentage +'</td></tr>'
    				});
    				
					str = '<table class="table" id="prqty"><thead><tr><th>PO Idx</th><th>Item Name</th><th>PO qty</th><th>PR qty</th><th>%</th></tr></thead><tbody>'+str+'</tbody></table>'
					if(validation){
					    if(fail){
    					    frappe.msgprint({
        						"title": "Please check qty must < 105% of PO",
        						"message": str,
        						"indicator": "red"
        					})
        					frappe.validated = false;
					    }
					} else {
    					frappe.msgprint({
    						"title": "Purchase Order vs Purchase Receipt",
    						"message": str,
    						"indicator": "blue"
    					})
					}
					return fail;
				}
			}
		});
}