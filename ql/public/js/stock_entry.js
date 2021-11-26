frappe.ui.form.on('Stock Entry', {
	onload(frm){
		frm.set_indicator_formatter('item_code',
			function(doc) {
				if (!doc.s_warehouse) {
					return 'blue';
				} else { //fix due to conversion factor rounding, introduce tolerance 0.002
					return (doc.qty<=doc.actual_qty + 0.002) ? "green" : "orange"
				}
			})

		// Remove QI on SE Target Duplicate
		$("span[data-label=Duplicate]").parent().remove();
		frm.page.add_menu_item(__('Duplicate'), function() {
			var newdoc = frappe.model.copy_doc(frm.doc);
			newdoc.idx = null;
			newdoc.items.forEach(o => {
				o.quality_inspection = ""
			})
			newdoc.__run_link_triggers = false;
			if(onload) {
				onload(newdoc);
			}
			frappe.set_route('Form', newdoc.doctype, newdoc.name);
		});
	},
	refresh(frm) {
		set_auto_batch_insp_btn(frm)
		set_vol_calc(frm)
	},
    validate(frm) {
		sum_volume(frm);
		if(frm.doc.stock_entry_type == "Material Consumption for Manufacture" )
			frm.set_value("to_warehouse", "")
		if(frm.doc.to_warehouse && frm.doc.to_warehouse.substr(0,16) == "Work-in-Progress"){
			frm.set_value("stock_entry_type", "Material Transfer for Manufacture")
			frm.set_value("purpose", "Material Transfer for Manufacture")
		}

		(async () => {
			await backdate_batch_no(frm)
		})();
    },
	onload_post_render(frm){
		if(frm.doc.pick_list && !frm.doc.work_order)
			frappe.db.get_doc("Pick List", frm.doc.pick_list).then(o =>{
				frm.set_value("batch_no", o.batch_no)
			})
	},
	work_order(frm){
		frappe.db.get_doc("Work Order", frm.doc.work_order).then(o =>{
			console.log(o)
		})
		// if(frm.doc.work_order){
		// 	this.frm.set_query("item_code", "items", function() {
		// 		return{
		// 			filters:{ 'is_sub_contracted_item': 1 }
		// 		}
		// 	});
		// }

	},
	pick_list(frm){
		frappe.db.get_doc("Pick List", frm.doc.pick_list).then(o =>{
			console.log(o)
		})
	},
	purpose(frm){
		if(frm.doc.purpose = "Manufacture")
			frm.set_value('inspection_required', 1)
		if(frm.doc.purpose = "Material Transfer for Manufacture")
			frm.set_value('inspection_required', 0)
		if(frm.doc.purpose = "Material Transfer")
			frm.set_value('inspection_required', 0)
	},
})



function set_auto_batch_insp_btn(frm){
    frm.add_custom_button(__('Auto'), function(){
		(async () => {
			await create_batch_inspection(frm)
			console.log('Finished created Batch & QI !!!! ')
		})();
	});
}


function set_vol_calc(frm){
    frm.add_custom_button(__('Vol'), async function(){
			counts = (await ql.get_carton_size())
			let str = ""
			var rests = 0
			volume_details = ""
			// counts = sizes
			frm.doc.items.forEach(i => {
				let nrof_dcarton = Math.ceil((i.volume_per_unit*i.qty)/counts[i.default_carton])
				let rest = (i.volume_per_unit*i.qty) % counts[i.default_carton]
				rests += rest
				str += '<tr><td>'+i.item_name  + '</td><td>'+ (i.volume_per_unit*i.qty) +'</td><td style="text-align:right">'+i.default_carton +'</td><td style="text-align:right">'+i.qty+'</td><td style="text-align:right">'+nrof_dcarton+'</td></tr>'
				volume_details += `${nrof_dcarton} Carton ${i.item_name}\n`
			});
			str = '<table class="table" id="prqty"><thead><tr><th>Item Name</th><th>Volume</th><th>Carton</th><th>Qty</th><th>Carton Qty</th></tr></thead><tbody>'+str+'</tbody></table>' + `<table class="table" id="calc"><thead><tr><th>Carton</th><th>Vol %</th><th>Qty</th></tr></thead><tbody id="tbodyCalc"></tbody></table><button class="btn btn-primary btn-sm primary-action" onclick="cur_frm.cscript.caculateBox(true, ${rests})" ><i class="visible-xs octicon octicon-lock"></i><span class="hidden-xs" data-label="Compute" >C<span class="alt-underline">o</span>mpute</span></button>`
			frappe.msgprint({
				"title": "Carton Calculator",
				"message": str,
				"indicator": "red"
			})
			setTimeout(function(){ frm.cscript.caculateBox(false, rests)}, 1000);
	});
}

var volume_details

var counts = {}

$.extend(cur_frm.cscript,{
	caculateBox : (isCartonRandom, goal)=>{
		let str = ""
		let boxes
		// let output = counts.reduce((prev, curr) => Math.abs(curr - goal) < Math.abs(prev - goal) ? curr : prev);
		if (isCartonRandom){
			boxes = cur_frm.cscript.findBoxRandom(goal)
		}else{
			boxes = cur_frm.cscript.findBox(goal)
		}
		const groupSimilar = arr => {
			return arr.reduce((acc, val) => {
			   const { data, map } = acc;
			   const ind = map.get(val.output);
			   if(map.has(val.output)){
				  data[ind][1] = val.occupation;
				  data[ind][2]++;
			   } else {
				  map.set(val.output, data.push([val.output, val.occupation, 1])-1);
			   }
			   return { data, map };
			}, {
			   data: [],
			   map: new Map()
			}).data;
		 };
		//  const groupSimilar = arr => {
		// 	return arr.reduce((acc, val) => {
		// 	   const { data, map } = acc;
		// 	   const ind = map.get(val);
		// 	   if(map.has(val)){
		// 		  data[ind][1]++;
		// 	   } else {
		// 		  map.set(val, data.push([val, 1])-1);
		// 	   }
		// 	   return { data, map };
		// 	}, {
		// 	   data: [],
		// 	   map: new Map()
		// 	}).data;
		//  };

		let header = "------- Mixed Content -------\n"
		volume_details = volume_details.replace(/------- Mixed Content -------\n(.*\n)+/gmi,'')
		volume_details += header
		groupSimilar(boxes).forEach((o, i)=>{
			str += '<tr><td>'+o[0]  + '</td><td>'+ o[1] +'</td><td>'+ o[2] +'</td></tr>'
			volume_details += `${o[2]} Carton ${o[0]}, Volume ${o[1]}%\n`
		})
		$('#tbodyCalc').html(str)
		cur_frm.set_value('volume_details', volume_details)
	},
	findBox : (goal)=>{

		let output = []
		let outkey = Object.keys(counts).reduce((prev, curr) => Math.abs(counts[curr] - goal) < Math.abs(counts[prev] - goal) ? curr : prev);

		let delta = goal - counts[outkey];
		if(delta > 0){
			output.push({'output': outkey, 'occupation':100})
			goal = delta;
			output = output.concat(cur_frm.cscript.findBox(goal))
		} else	{
			output.push({'output': outkey, 'occupation':Math.round(goal/counts[outkey]*100)})
		}
		return output
	},
	findBoxRandom : (goal)=>{
		let keys = Object.keys(counts)
		let idx = Math.floor(Math.random() * keys.length)
		let outkey = keys[idx]
		let output = []

		let delta = goal - counts[outkey];
		debugger
		if(delta > 0){
			output.push({'output': outkey, 'occupation':100})
			goal = delta;
			output = output.concat(cur_frm.cscript.findBoxRandom(goal))
		} else	{
			output.push({'output': outkey, 'occupation':Math.round(goal/counts[outkey]*100)})
		}
		return output
	}
})


async function create_batch_inspection(frm){
	let a = await ql.get_month_code()
	let qi_inspected_by_default = (await frappe.db.get_doc('QL Settings')).qi_inspected_by_default
	if(frm.doc.purpose == "Manufacture"){
		let o = frm.doc.items[frm.doc.items.length - 1]
		await create_batch_inspection_item(frm, o, a, qi_inspected_by_default)
		cur_frm.save();
	} else {
		frappe.confirm('This will create batches & QI all items, Are you sure you want to proceed ?',
		() => {
			(async () => {
			for(let i=0;i< frm.doc.items.length;i++){
				try{
					await create_batch_inspection_item(frm,frm.doc.items[i], a, qi_inspected_by_default)
				} catch(e) {console.log(e)}
			}
			cur_frm.save();
			})();
		}, () => {
		})

	}
}

async function create_batch_inspection_item(frm, o, a, qi_inspected_by_default){
	if(frm.doc.batch_no)
		frappe.model.set_value(o.doctype, o.name, 'batch_no', frm.doc.batch_no)
	else {
		// let batch_no = (await frappe.db.get_value('Work Order', frm.doc.work_order, 'batch_no')).message.batch_no
		let shelf_life = (await frappe.db.get_value('BOM', frm.doc.bom_no, 'shelf_life_in_days')).message.shelf_life_in_days
		if(!shelf_life){
			shelf_life = (await frappe.db.get_value('Item', frm.doc.item_code, 'shelf_life_in_days')).message.shelf_life_in_days
		}
		var exp_date = frappe.datetime.add_days(frappe.datetime.now_date(), shelf_life)
		let batch_pre = o.item_code+moment().format('YY').substr(-1)+a[(new Date()).getMonth()]
		let batch_count = (await frappe.db.count('Batch', {filters:{'batch_id': ['like',batch_pre+'%']}}))

		let doc = (await frappe.db.insert({
			doctype: 'Batch',
			item: o.item_code,
			batch_id: batch_pre+genNum(batch_count+1, 3),
			expiry_date: exp_date
		}))
		o.batch_no = doc.name
		frappe.model.set_value(o.doctype, o.name, 'batch_no', doc.name)
	}

	if((!Object.keys(o).includes("quality_inspection") || !o.quality_inspection ) && frm.doc.inspection_required){
		let doc = (await frappe.db.insert({
			doctype: 'Quality Inspection',
			naming_series : 'SE-.batch_no.-.##',
			item_code: o.item_code,
			inspection_type: 'In Process',
			reference_type: 'Stock Entry',
			reference_name: frm.doc.name,
			inspected_by: qi_inspected_by_default,
			received_qty: o.qty,
			sample_size: 0,
			batch_no: o.batch_no
		}))
		o.quality_inspection = doc.name
		frappe.model.set_value(o.doctype, o.name, 'quality_inspection', doc.name)
		cur_frm.refresh_field("items")
		frappe.msgprint(`Quality Inspection ${doc.name} is Created`)
	}
}

function sum_volume(frm){
	let vol = frm.doc.items.map((o)=>{ return o.qty * o.volume_per_unit * o.conversion_factor }).reduce((total,o)=>{return total + o})
	frm.set_value('total_net_volume', vol)
}

async function backdate_batch_no(frm){
	if(frm.doc.batch_no && frm.doc.set_posting_time){
		let a = await ql.get_month_code()
		let month = a.indexOf(frm.doc.batch_no.charAt(0))
		let batch_date = new Date("20"+frm.doc.batch_no.substr(1,2), month-1, frm.doc.batch_no.substr(3,2))
		// uncomment this
		// if(new Date(cur_frm.doc.posting_date) < batch_date){
		// 	frappe.validated = false
		// 	frappe.msgprint("Posting date cannot be earlier than batch date")
		// }
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