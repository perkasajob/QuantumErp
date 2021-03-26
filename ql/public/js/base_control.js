
var ql = {
	get_month_code: function() { return new Promise(res => {frappe.db.get_single_value("QL Settings","month_code").then(r=>res(r.split(",")))});},
	get_carton_size: function(){ return new Promise(res => {frappe.db.get_single_value("QL Settings","carton_sizes").then(r=>res(this.parseJson(r)))});},
	parseJson: function(c){let x = {};c.split(",").forEach(o=>{let p = o.split(":");x[p[0].trim()]=isNaN(p[1])?p[1]:Number(p[1])}); return x}
}
