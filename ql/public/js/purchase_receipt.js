// erpnext.stock.PurchaseReceiptController.prototype.show_stock_ledger = function() {
// 		var me = this;
// 		if(this.frm.doc.docstatus===1) {
// 			cur_frm.add_custom_button(__("Stock Ledger QL2"), function() {
// 				frappe.route_options = {
// 					voucher_no: me.frm.doc.name,
// 					from_date: me.frm.doc.posting_date,
// 					to_date: me.frm.doc.posting_date,
// 					company: me.frm.doc.company
// 				};
// 				frappe.set_route("query-report", "Stock Ledger QL");
// 			}, __("View"));
// 		}

// 	}


frappe.ui.form.on('Purchase Receipt', {
	onload(frm){
		// Store the unchanged items qty
		frm.originItems = {}
		frm.doc.items.forEach(o=>frm.originItems[o.purchase_order_item]= o.qty)
	},
	onload_post_render(frm){
		set_query_inspection(frm)
	},
	refresh(frm) {
		set_POQty_btn(frm)
		if(frappe.user.has_role('WH') ||frappe.user.has_role('QC')){
			set_auto_batch_insp_btn(frm)
		}
		show_stock_ledger(frm)
	},
	validate(frm) {
		let project = ""
	    frm.doc.items.forEach((o,i)=>{
			if(!o.purchase_order_item)frm.doc.items.splice(i);
			set_batch_freeitem(frm, o);
			if(!project)project=o.project
		}) // remove items without PO reference
		if (!frm.doc.is_return)
			check_POqty(frm, true)
		frm.set_value('project', project)
		check_expiry_date(cur_frm)
		create_freeitem_stock(frm)
	},
	before_submit(frm){
		if (!frm.doc.is_return)
	   		check_POqty(frm, true)
	},

})



function show_stock_ledger(frm){
	var me = this;
	if(frm.doc.docstatus===1) {
		if(frappe.user.has_role("Accounts Manager") == undefined){
			cur_frm.add_custom_button(__("Stock Ledger QL"), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company
				};
				frappe.set_route("query-report", "Stock Ledger QL");
			}, __("View"));
			cur_frm.add_custom_button(__("General Ledger QL"), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.available_for_use_date,
					"to_date": frm.doc.available_for_use_date,
					"company": frm.doc.company
				};
				frappe.set_route("query-report", "General Ledger QL");
			}, __("View"));
			setTimeout(() => {
				$("[data-label='Stock%20Ledger']").remove()
				$("[data-label='General%20Ledger']").remove()
			}, 3);
		}
	}
}

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
		    	    } else {
		    	        var pri_qty = lqty[e[0].purchase_order_item] - frm.originItems[e[0].purchase_order_item] + e[0].pri_qty
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
	let processed_items = []
	for (let o of  cur_frm.doc.items){
		console.log('Item: ' + o.item_name)
		let prev_item = processed_items.find(item=>item.item_code == o.item_code)
		if(prev_item){
			let idx = prev_item.idx - 1
			frappe.model.set_value(o.doctype, o.name, 'batch_no', frm.doc.items[idx].batch_no)
			frappe.model.set_value(o.doctype, o.name, 'quality_inspection', frm.doc.items[idx].quality_inspection)
			cur_frm.refresh_field("items")
		} else if((!Object.keys(o).includes("batch_no") || !o.batch_no)){
			let has_batch_no = (await frappe.db.get_value('Item',o.item_code,'has_batch_no')).message.has_batch_no
			// let batch_count = (await frappe.db.count('Batch'))
			if(has_batch_no){
				let a = await ql.get_month_code()
				let batch_pre = a[(new Date()).getMonth()]+moment().format('YYDD')
				let batch_count = (await frappe.db.count('Batch', {filters:{'batch_id': ['like',batch_pre+'%']}}))
				let doc = (await frappe.db.insert({
					doctype: 'Batch',
					item: o.item_code,
					batch_id: batch_pre + genNum(batch_count+1, 3),
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
		if(o.batch_no || o.quality_inspection){
			processed_items.push(o)
		}
		set_batch_freeitem(frm, o)
	}
}


function set_batch_freeitem(frm, o){
	if (!frm.doc.hasOwnProperty("free_items"))
		return
	for (let fri of  frm.doc.free_items){
		if(o.item_code == fri.item_code){
			frappe.model.set_value(fri.doctype, fri.name, 'batch_no', o.batch_no)
			frappe.model.set_value(fri.doctype, fri.name, 'quality_inspection', o.quality_inspection)
		}
	}
}

function create_freeitem_stock(frm){
	if (!frm.doc.hasOwnProperty("free_items"))
		return
	for (let fri of  frm.doc.free_items){

	}
}


async function create_inspection(frm, o){
    if(!Object.keys(o).includes("quality_inspection") || !o.quality_inspection){
		let inspection_required = (await frappe.db.get_value('Item',o.item_code,'inspection_required_before_purchase')).message.inspection_required_before_purchase;
		if(inspection_required){
			// let a = ['PR_A','PR_B','PR_C','PR_D','PR_E','PR_F','PR_G','PR_H','PR_J','PR_K','PR_L','PR_N']
			let doc = (await frappe.db.insert({
				doctype: 'Quality Inspection',
				item_code: o.item_code,
				inspection_type: 'Incoming',
				reference_type: 'Purchase Receipt',
				reference_name: frm.doc.name,
				inspected_by: frappe.user.name,
				received_qty: o.received_qty * o.conversion_factor,
				uom: o.stock_uom,
				vat: o.vat,
				vat_qty: o.vat_qty,
				sample_size: 0,
				uom: o.uom,
				batch_no: o.batch_no
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