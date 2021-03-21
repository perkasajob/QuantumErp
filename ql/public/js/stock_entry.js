frappe.ui.form.on('Stock Entry', {
	refresh(frm) {
		set_auto_batch_insp_btn(frm)
		set_vol_calc(frm)
	},
    validate(frm) {
		sum_volume(frm)
    }
})


function set_auto_batch_insp_btn(frm){
    frm.add_custom_button(__('Auto'), function(){
		(async () => {
			await create_batch_inspection(frm)
			cur_frm.save();
		})();
	});
}


function set_vol_calc(frm){
    frm.add_custom_button(__('Vol'), function(){
		frappe.db.get_single_value('QL Settings', 'carton_sizes')
		.then(r => {
			let str = ""
			volume_details = ""
			var sizes = JSON.parse("{"+r+"}")
			counts = sizes
			frm.doc.items.forEach(i => {
				let nrof_dcarton = Math.ceil((i.volume_per_unit*i.qty)/sizes[i.default_carton])
				let rest = (i.volume_per_unit*i.qty) % sizes[i.default_carton]
				rests += rest
				str += '<tr><td>'+i.item_name  + '</td><td>'+ (i.volume_per_unit*i.qty) +'</td><td style="text-align:right">'+i.default_carton +'</td><td style="text-align:right">'+i.qty+'</td><td style="text-align:right">'+nrof_dcarton+'</td></tr>'
				volume_details += `${nrof_dcarton} Carton ${i.item_name}\n`
			});
			str = '<table class="table" id="prqty"><thead><tr><th>Item Name</th><th>Volume</th><th>Carton</th><th>Qty</th><th>Carton Qty</th></tr></thead><tbody>'+str+'</tbody></table>' + '<table class="table" id="calc"><thead><tr><th>Carton</th><th>Vol %</th><th>Qty</th></tr></thead><tbody id="tbodyCalc"></tbody></table><button class="btn btn-primary btn-sm primary-action" onclick="cur_frm.cscript.caculateBox(true)" ><i class="visible-xs octicon octicon-lock"></i><span class="hidden-xs" data-label="Compute" >C<span class="alt-underline">o</span>mpute</span></button>'
			frappe.msgprint({
				"title": "Carton Calculator",
				"message": str,
				"indicator": "red"
			})
			setTimeout(function(){ frm.cscript.caculateBox(false)}, 1000);

		})
	});
}

var volume_details
var rests = 0
var counts = {"a":1, "b":2, "c":3, "d":4, "e":5, "f":6, "g":7, "h":8,"i":9};

$.extend(cur_frm.cscript,{
	caculateBox : (isCartonRandom)=>{
		let goal = rests;
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
		debugger
		volume_details = volume_details.replace(/------- Mixed Content -------\n(.*\n)+/gmi,'')
		volume_details += "------- Mixed Content -------\n"
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
	let o = frm.doc.items[frm.doc.items.length - 1]
	let batch_no = (await frappe.db.get_value('Work Order', frm.doc.work_order, 'batch_no')).message.batch_no
	let qi_inspected_by_default = (await frappe.db.get_single_value ("QL Settings","qi_inspected_by_default"))

	frappe.model.set_value(o.doctype, o.name, 'batch_no', batch_no)

	if(!Object.keys(o).includes("quality_inspection") || !o.quality_inspection){
		let a = ['SE_A','SE_B','SE_C','SE_D','SE_E','SE_F','SE_G','SE_H','SE_J','SE_K','SE_L','SE_N']
		let doc = (await frappe.db.insert({
			doctype: 'Quality Inspection',
			item_code: o.item_code,
			inspection_type: 'In Process',
			reference_type: 'Stock Entry',
			reference_name: frm.doc.name,
			inspected_by: qi_inspected_by_default,
			received_qty: o.received_qty,
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

function sum_volume(frm){
	let vol = frm.doc.items.map((o)=>{ return o.qty * o.volume_per_unit * o.conversion_factor }).reduce((total,o)=>{return total + o})
	frm.set_value('total_net_volume', vol)
}