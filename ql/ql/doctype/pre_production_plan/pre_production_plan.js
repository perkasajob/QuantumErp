// Copyright (c) 2022, Perkasa JoB and contributors
// For license information, please see license.txt

var constConfidenceLvl = {"84%": 1, "90%":1.26, "95%":1.65, "99%": 2.33}

frappe.ui.form.on('Pre Production Plan', {
	onload: function(frm) {

	},
	refresh: function(frm) {
		frm.add_custom_button(__('Get Data'), function () {
			frm.trigger("get_data");
		});
	},
	target_date: function(frm){
		var datestr = frappe.datetime.str_to_obj(frm.doc.target_date).getMonth()
		frm.set_value("month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
		"Dec"][datestr])
		frm.set_value("year", frm.doc.target_date.substr(2,2))
	},
	rofo: function(frm){
		if(frm.doc.total_sales){
			frm.set_value("accuracy", flt(frm.doc.total_sales/frm.doc.rofo*100, 2))
		}
	},
	get_data: function(frm){
		let cols = ["ams3", "ams12", "total_sales", "forecast", "rofo", "prev_month_forecast", "prev_month_rofo", "accuracy",
		 "work_in_progress", "production_output", "apl", "ppg", "dnr", "tsj" ]
		cols.forEach(c =>{
			frm.set_value(c, null)
		})

		var month = frappe.datetime.str_to_obj(frm.doc.target_date).getMonth()
		frappe.call({
			method: "ql.ql.doctype.pre_production_plan.pre_production_plan.get_data",
			args: {
				target_date: frm.doc.target_date,
				item_group: frm.doc.item_group,
				month: month,
				year: frm.doc.year
			},
			callback: function(r) {
				if(!r.exc) {
					if(r.message) {
						const regex = /D ([A-Z]{3}) - /gm;
						let d = r.message
						console.log(r.message)
						let total_stock_dist = 0
						let total_stock = 0
						let recommend_prod_qty = 0
						let production_output = 0
						let confidence_level = constConfidenceLvl[frm.doc.confidence_level]
						let min_safety_stock_qty= d.ams.ams12 + d.ams.std_val * confidence_level

						frm.set_value("ams3", flt(d.ams.ams3, 2))
						frm.set_value("ams12", flt(d.ams.ams12, 2))

						frm.set_value("min_safety_stock_qty", Math.round(min_safety_stock_qty))

						frm.set_value("total_sales", flt(d.ams.total_sales))
						if(d.nextFcRofo){
							frm.set_value("forecast", flt(d.nextFcRofo.forecast, 2))
							frm.set_value("rofo", flt(d.nextFcRofo.rofo, 2))
						}
						if(d.prevFcRofo){
							frm.set_value("prev_month_forecast", flt(d.prevFcRofo.forecast, 2))
							frm.set_value("prev_month_rofo", flt(d.prevFcRofo.rofo, 2))
						}
						if(frm.doc.rofo){
							frm.set_value("accuracy", flt(d.ams.total_sales/frm.doc.rofo*100, 2))
						}

						frm.set_value("production_output", d.stock_qty)
						frm.set_value("work_in_progress", d.wip_qty)
						if(d.stock_dist){
							d.stock_dist.forEach(o => {
								let warehouse = getFirstGroup(regex, o.warehouse)[0].toLowerCase()
								total_stock_dist += o.qty
								frm.set_value(warehouse, o.qty)
							});
						}
						total_stock = total_stock_dist + production_output
						frm.set_value("total_stock", total_stock)
						frm.set_value("safety_stock", flt(total_stock/frm.doc.rofo, 2))
						frm.set_value("safety_stock_ams3", flt(total_stock/frm.doc.ams3, 2))
						if (frm.doc.ref_safety_stock - (total_stock/frm.doc.ams3) > 0)
							recommend_prod_qty = (frm.doc.ref_safety_stock - (total_stock/frm.doc.ams3)) * frm.doc.ams3 - d.wip_qty

						frm.set_value("recommend_prod_qty", flt(recommend_prod_qty, 2))
					}
				}
			}
		});

	}
});

function getFirstGroup(regexp, str) {
	const array = [...str.matchAll(regexp)];
	return array.map(m => m[1]);
  }

