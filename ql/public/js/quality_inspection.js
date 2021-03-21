frappe.ui.form.on('Quality Inspection', {
	onload(frm) {
		frm.get_field("readings").grid.cannot_add_rows = true;
		// if(!frm.doc.quality_inspection_template)
		// 	frm.set_value("quality_inspection_template",frm.doc.item_code)
		if(frm.doc.batch_no && !frm.doc.expired_date){
			let ed = frappe.get_doc('Batch',frm.doc.batch_no)
			if(ed) frm.set_value('expired_date', ed.expiry_date)
		}
	},
	refresh(frm){
		set_reject_btn(frm)
	},
    validate(frm) {
		set_month_code(cur_frm)
		check_expiry_date(cur_frm)
		set_sample_size(cur_frm)
		auto_fill(cur_frm)
    },
	sample_type(frm) {
		set_sample_size(cur_frm)
	},
	received_qty(frm) {
		set_sample_size(cur_frm)
	},
	vat(frm) {
		set_sample_size(cur_frm)
	},
	vat_sample_qty(frm) {
		set_sample_size(cur_frm)
	},
	vat_sample(frm) {
		set_sample_size(cur_frm)
	},
	before_submit(frm){
		frm.set_value('completion_status', 'Completed')
	}
})

function set_reject_btn(frm){
    frm.add_custom_button(__('Reject'), function(){
        reject_item(frm);
	});
}

function reject_item(frm){
	{
		frm.set_value('status', 'Rejected')
		frappe.prompt([{
			fieldname: 'qty',
			label: __('Reject Qty'),
			fieldtype: 'Float',
			'default': frm.doc.received_qty
		},
		{
			fieldname: 'new_batch_id',
			label: __('Reject Batch ID'),
			fieldtype: 'Data',
			'default': frm.doc.batch_no + 'x'
		}],
		(data) => {
			if(data.qty <= 0 && data.qty > frm.doc.received_qty){
				frappe.msgprint('quantity cannot exceed received quantity')
				return
			}
			frappe.call({
				method: 'ql.ql.stock.qi_reject',
				args: {
					item_code: frm.doc.item_code,
					batch_no: frm.doc.batch_no,
					qty: data.qty,
					new_batch_id: data.new_batch_id
				},
				callback: (r) => {
					frappe.msgprint(`Stock Entry <a href= "#Form/Stock Entry/${r.message.name}">${r.message.name}</a> Created`)
					frm.refresh();
				},
			});
		},
		__('Reject Batch'),
		__('Reject')
		);
	}
}

function check_expiry_date(frm){
	if(!frm.doc.expired_date){
		frappe.confirm('No Expiry Date, proceed ?',
			() => {},
			() => {
				frappe.validated = false;
		})
	}
}

function set_month_code(frm){
    var a = ['A','B','C','D','E','F','G','H','J','K','L','N']
    frm.set_value('month_code',a[(new Date()).getMonth()])
}

frappe.ui.form.on('Quality Inspection Reading', {
	reading_1(frm){
	  test_criteria(cur_frm)
	},
	reading_2(frm){
	  test_criteria(cur_frm)
	},
	reading_3(frm){
	  test_criteria(cur_frm)
	},
	reading_4(frm){
	  test_criteria(cur_frm)
	},
	reading_5(frm){
	  test_criteria(cur_frm)
	},
	reading_6(frm){
	  test_criteria(cur_frm)
	},
	reading_7(frm){
	  test_criteria(cur_frm)
	},
	reading_8(frm){
	  test_criteria(cur_frm)
	},
	reading_9(frm){
	  test_criteria(cur_frm)
	},
	reading_10(frm){
	  test_criteria(cur_frm)
	}
})

function test_criteria(frm){
	frm.selected_doc.status = "Accepted"
    for(let i=0;i<10;i++){
        let reading = frm.selected_doc['reading_'+ cstr(i+1)]
        if(frm.selected_doc.status == "Accepted" && reading != undefined){
            let criteria = frm.selected_doc.value.replaceAll(' ','').replaceAll(/[a-zA-z]+?\d|[a-zA-z]+|%/g,'')
		    if(criteria.match(/^\<|^\>/)){
				criteria = reading + criteria.match(/[<>=]+[-+]?[0-9]*\.?[0-9]+/g)
            } else if(!isNaN(criteria)){
                criteria = reading +'==' + criteria
			} else if(criteria.match(/[<=>]/g)){
                criteria = criteria.replace('<<','<'+cstr(reading)+"&&"+cstr(reading)+'<').replace('<=<','<='+cstr(reading)+"&&"+cstr(reading)+'<')
            } else {
                criteria = null
            }

            if(criteria){
                let result = eval(criteria)
                if(!result)
                    debugger
                let status = result?"Accepted":"Rejected"
                frm.selected_doc.status = status
            }
        }
    }

	frm.doc.status = "Accepted"
	frm.doc.readings.forEach(o => {
		if(o.status == "Rejected")
			frm.doc.status = "Rejected"
	});
    frm.refresh()

}


function auto_fill(frm){
	let fill_data = 0
	if(!frm.doc.received_qty){
		fill_data = 1
	}

	if(frm.doc.reference_type == "Purchase Receipt" && fill_data){
		frappe.db.get_doc("Purchase Receipt", frm.doc.reference_name).then(r=>{
			r.items.every(o=>{
				if(o.quality_inspection == frm.doc.name){
					["received_qty","vat","vat_qty","batch_no"].forEach(e=>{
						frm.set_value(e, o[e])
					})
					return false
				}
			})
		})
	}
}

function set_sample_size(frm){
	if(frm.doc.sample_type == 'N'){
		if(frm.doc.vat > 16){
			frm.set_value('vat_sample', Math.round(Math.sqrt(frm.doc.vat)+1))
		}else if(frm.doc.vat < 5){
			frm.set_value('vat_sample', frm.doc.vat)
		}else{
			frm.set_value('vat_sample', 4)
		}
		frm.set_value('sample_size', frm.doc.vat_sample*frm.doc.vat_sample_qty)
	}else if(frm.doc.sample_type == 'P'){
		frm.set_value('vat_sample', Math.ceil(0.4*Math.sqrt(frm.doc.vat)))
		frm.set_value('sample_size', frm.doc.vat_sample*frm.doc.vat_sample_qty)
	}else if(frm.doc.sample_type == 'R'){
		frm.set_value('vat_sample', Math.ceil(1.5*Math.sqrt(frm.doc.vat)))
		frm.set_value('sample_size', frm.doc.vat_sample*frm.doc.vat_sample_qty)
	}else if(frm.doc.sample_type == 'Military General'){
		ISO2859milGeneral(frm)
	}else if(frm.doc.sample_type == 'Military Special'){
		ISO2859milSpecial(frm)
	}
}

function ISO2859milGeneral(frm){
	let n = parseFloat(frm.doc.received_qty)
	let size = 1
	if(2<=n && n<=8){
		size = 2
	} else if (9<=n && n<=15){
		size = 3
	} else if (16<=n && n<=25){
		size = 5
	} else if (26<=n && n<=50){
		size = 8
	} else if (51<=n && n<=90){
		size = 20
	} else if (91<=n && n<=150){
		size = 20
	} else if (151<=n && n<=280){
		size = 32
	} else if (281<=n && n<=500){
		size = 50
	} else if (501<=n && n<=1200){
		size = 80
	} else if (1201<=n && n<=3200){
		size = 125
	} else if (3201<=n && n<=10000){
		size = 200
	} else if (10001<=n && n<=35000){
		size = 315
	} else if (35001<=n && n<=150000){
		size = 500
	} else if (150001<=n && n<=500000){
		size = 800
	} else {
		size = 1250
	}
	frm.set_value('sample_size', size)
}

function ISO2859milSpecial(frm){
	let n = parseFloat(frm.doc.received_qty)
	let size = 1
	if(2<=n && n<=8){
		size = 2
	} else if (9<=n && n<=15){
		size = 2
	} else if (16<=n && n<=25){
		size = 2
	} else if (26<=n && n<=50){
		size = 3
	} else if (51<=n && n<=90){
		size = 3
	} else if (91<=n && n<=150){
		size = 3
	} else if (151<=n && n<=280){
		size = 5
	} else if (281<=n && n<=500){
		size = 5
	} else if (501<=n && n<=1200){
		size = 5
	} else if (1201<=n && n<=3200){
		size = 8
	} else if (3201<=n && n<=10000){
		size = 8
	} else if (10001<=n && n<=35000){
		size = 8
	} else if (35001<=n && n<=150000){
		size = 13
	} else if (150001<=n && n<=500000){
		size = 13
	} else {
		size = 13
	}
	frm.set_value('sample_size', size)
}