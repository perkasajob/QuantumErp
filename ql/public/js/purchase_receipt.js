frappe.ui.form.on('Purchase Receipt', {
	onload_post_render(frm){
		set_query_inspection(frm)
	},
	refresh(frm) {
		set_POQty_btn(frm)
		if(frappe.user.has_role('WH') ||frappe.user.has_role('QC')){
			set_auto_batch_insp_btn(frm)
		}
	},
	validate(frm) {
	    frm.doc.items.forEach((o,i)=>{if(!o.purchase_order_item)frm.doc.items.splice(i)}) // remove items without PO reference
		check_POqty(frm, true)
		check_expiry_date(cur_frm)
	},
	before_submit(frm){
	   check_POqty(frm, true)
	}
})

function set_query_inspection(frm){
	frm.set_query("quality_inspection",'items', function(doc, cdt, cdn){
		var d =locals[cdt][cdn]
		return {
			"filters": {
				"inspection_type": "Incoming",
				"reference_name": frm.doc.name,
				"item_code": d.item_code
			}
		};
	})
}


function set_POQty_btn(frm){
    frm.add_custom_button(__('PO Qty'), function(){
        check_POqty(frm, false);
	});
}

function set_auto_batch_insp_btn(frm){
    frm.add_custom_button(__('Auto'), function(){
		(async () => {
			await create_batch_inspection(frm)
			cur_frm.save();
			console.log('Finished created Batch & QI !!!! ')
		})();
	});
}

function check_expiry_date(frm){
	let batchesNoED = []
	for(let item of frm.doc.items){
		if(item.batch_no)
			frappe.db.get_value('Batch', item.batch_no, ['name', 'expiry_date'])
			.then(doc => {
				batchesNoED.push(doc.message.name)
			})
	}

	if(batchesNoED.length > 0){
		frappe.confirm('Batch '+ batchesNoED.join() +' Expiry date not set, proceed ?',
			() => {},
			() => {
				frappe.validated = false;
		})
	}
}



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

async function create_batch_inspection(frm){
    if(frm.doc.__islocal)
		return
	for (let o of  cur_frm.doc.items){
		console.log('Item: ' + o.item_name)
		if(!Object.keys(o).includes("batch_no") || !o.batch_no){
			let has_batch_no = (await frappe.db.get_value('Item',o.item_code,'has_batch_no')).message.has_batch_no
			let batch_count = (await frappe.db.count('Batch'))
			if(has_batch_no){
				let a = ['A','B','C','D','E','F','G','H','J','K','L','N']
				let doc = (await frappe.db.insert({
					doctype: 'Batch',
					item: o.item_code,
					batch_id: a[(new Date()).getMonth()]+moment().format('YYMM')+genNum(batch_count+1, 3),
					// inspection: inspection_nr,
					month_code:a[(new Date()).getMonth()]
				}))
				o.batch_no = doc.name
				// frappe.model.set_value(v.doctype,
				frappe.model.set_value(o.doctype, o.name, 'batch_no', doc.name)
				cur_frm.refresh_field("items")
				// frappe.msgprint(`Batch ${doc.name} is Created`)
				await create_inspection(cur_frm, o)

			} else {
				await create_inspection(cur_frm, o)
			}
		} else { // create inspection only
			await create_inspection(cur_frm, o)
		}
	}
}


async function create_inspection(frm, o){
    if(!Object.keys(o).includes("quality_inspection") || !o.quality_inspection){
		let inspection_required = (await frappe.db.get_value('Item',o.item_code,'inspection_required_before_purchase')).message.inspection_required_before_purchase;
		if(inspection_required){
			let a = ['PR_A','PR_B','PR_C','PR_D','PR_E','PR_F','PR_G','PR_H','PR_J','PR_K','PR_L','PR_N']
			let doc = (await frappe.db.insert({
				doctype: 'Quality Inspection',
				item_code: o.item_code,
				inspection_type: 'Incoming',
				reference_type: 'Purchase Receipt',
				reference_name: frm.doc.name,
				inspected_by: frappe.user.name,
				received_qty: o.received_qty,
				vat: o.vat,
				vat_qty: o.vat_qty,
				sample_size: 0,
				batch_no: o.batch_no,
				month_code:a[(new Date()).getMonth()]
			}))
			o.quality_inspection = doc.name
			frappe.model.set_value(o.doctype, o.name, 'quality_inspection', doc.name)
			cur_frm.refresh_field("items")
			frappe.msgprint(`Quality Inspection ${doc.name} is Created`)
		}
    }
}


function genNum(number, length)
{
    var str = '' + number%Math.pow(10,length);
    while (str.length < length) {
        str = '0' + str;
    }
    return str;
}


async function stall(stallTime = 3000) {
	await new Promise(resolve => setTimeout(resolve, stallTime));
  }