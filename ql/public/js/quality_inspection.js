frappe.ui.form.on('Quality Inspection', {
	onload(frm) {
		frm.get_field("readings").grid.cannot_add_rows = true;
		if(!frm.doc.quality_inspection_template)
			frm.set_value("quality_inspection_template",frm.doc.item_code)
	},
    validate(frm) {
		set_month_code(cur_frm)
		check_expiry_date(cur_frm)
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
	before_submit(frm){
		frm.set_value('completion_status', 'Completed')
	}
})

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
            let criteria = frm.selected_doc.value.replaceAll(' ','').replaceAll('%','')
            if(criteria.match(/\<=x|\<x/)){
                criteria = criteria.replace('<x<','<'+cstr(reading)+"&&"+cstr(reading)+'<').replace('<=x<','<='+cstr(reading)+"&&"+cstr(reading)+'<')
            } else if(criteria.match(/^\<|^\>/)){
                criteria = reading + criteria
            } else if(!isNaN(criteria)){
                criteria = reading +'==' + criteria
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

function set_sample_size(frm){
	if(frm.doc.sample_type == 'N'){
		if(frm.doc.received_qty > 4)
			frm.set_value('sample_size', Math.round(Math.sqrt(frm.doc.received_qty)+1)*frm.doc.vat)
		else
			frm.set_value('sample_size', frm.doc.received_qty)
	}else if(frm.doc.sample_type == 'P'){
		frm.set_value('sample_size', Math.ceil(0.4*Math.sqrt(frm.doc.received_qty)*frm.doc.vat))
	}else if(frm.doc.sample_type == 'R'){
		frm.set_value('sample_size', Math.ceil(1.5*Math.sqrt(frm.doc.received_qty)*frm.doc.vat))
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
	frm.set_value('sample_size', size*frm.doc.vat)
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
	frm.set_value('sample_size', size*frm.doc.vat)
}