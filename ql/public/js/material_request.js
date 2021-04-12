frappe.ui.form.on('Material Request', {
	refresh(frm) {
		if(!frm.doc.requestee){
			frm.set_value("requestee", frappe.user.full_name())
		}
		mr_set_buttons(frm)
	},
	validate(frm){
	    if(!frm.doc.department){
	        var msg = "Department must be filled"
			frappe.msgprint(msg);
            throw msg;
		}
	},
	onload(frm){
		if(!frm.doc.requestee){
			frm.set_value("requestee", frappe.user.full_name())
		}

	    if(frm.doc.department)
	        return
		var dept_list = []
        frappe.db.get_single_value('QL Settings', 'dept_abbr')
    	.then(value => {
    		dept_list = value.split(",");
			var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
    		if(!frappe.user.has_role("System Manager") && !frappe.user.has_role("Purchase Manager"))
				frm.set_df_property("department", "read_only", dept ? 1 : 0);
			frm.set_value("department", dept)
		});
	},
	get_items_from_bom(frm){
		var d = new frappe.ui.Dialog({
			title: __("Get Items from BOM"),
			fields: [
				{"fieldname":"bom", "fieldtype":"Link", "label":__("BOM"),
					options:"BOM", reqd: 1, get_query: function() {
						return {filters: { docstatus:1 }};
					}},
				{"fieldname":"warehouse", "fieldtype":"Link", "label":__("Warehouse"),
					options:"Warehouse", reqd: 1},
				{"fieldname":"qty", "fieldtype":"Float", "label":__("Quantity"),
					reqd: 1, "default": 1},
				{"fieldname":"fetch_exploded", "fieldtype":"Check",
					"label":__("Fetch exploded BOM (including sub-assemblies)"), "default":1},
				{fieldname:"fetch", "label":__("Get Items from BOM"), "fieldtype":"Button"}
			]
		});

		d.get_input("fetch").on("click", function() {
			var values = d.get_values();
			frm.set_value('bom_no', values.bom)
			if(!values) return;
			values["company"] = frm.doc.company;
			if(!frm.doc.company) frappe.throw(__("Company field is required"));
			frappe.call({
				method: "erpnext.manufacturing.doctype.bom.bom.get_bom_items",
				args: values,
				callback: function(r) {
					if (!r.message) {
						frappe.throw(__("BOM does not contain any stock item"));
					} else {
						erpnext.utils.remove_empty_first_row(frm, "items");
						$.each(r.message, function(i, item) {
							console.log(item)
							var d = frappe.model.add_child(cur_frm.doc, "Material Request Item", "items");
							d.item_code = item.item_code;
							d.item_name = item.item_name;
							d.description = item.description;
							d.warehouse = values.warehouse;
							d.uom = item.stock_uom;
							d.stock_uom = item.stock_uom;
							d.conversion_factor = 1;
							d.qty = item.qty;
							d.project = item.project;
						});
					}
					d.hide();
					refresh_field("items");
				}
			});
		});
		d.show();
	}
})


function mr_set_buttons(frm){
	if (frm.doc.docstatus == 1 && frm.doc.status != 'Stopped') {
			if (frm.doc.material_request_type === "Purchase") {
				frm.add_custom_button(__('BAST'),
					() => frm.events.make_purchase_order(frm), __('Create'));
			}
		}
	if (frm.doc.docstatus == 0 && frm.doc.status != 'Stopped') {
		frm.add_custom_button(__('Set Rq Date'),
			() => {frappe.prompt({
						label: 'Required Date',
						fieldname: 'date',
						fieldtype: 'Date'
					}, (values) => {
						frm.set_value("schedule_date", values.date)
						set_schedule_date(frm)
					})
				}
			);
	}
}

frappe.ui.form.on('Purchase Invoice', {
	refresh(frm) {
		// your code here
	},
	validate(frm){
	    if(!frm.doc.department){
	        var msg = "Department must be filled"
	        frappe.msgprint(msg);
            throw msg;
	    }
	},
	onload(frm){
	    if(frm.doc.department)
	        return
	    var dept_list = []
        frappe.db.get_single_value('QL Settings', 'dept_abbr')
    	.then(value => {
    		dept_list = value.split(",");
    		var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
    		if(!frappe.user.has_role("System Manager") && !frappe.user.has_role("Purchase Manager") && !frappe.user.has_role("Purchase User"))
    	        frm.set_df_property("department", "read_only", dept ? 1 : 0);
    		frm.set_value("department", dept)
        });
	}
})


function dept_list_func(frm){
    var dept_list = []
    frappe.db.get_single_value('QL Settings', 'dept_abbr')
	.then(value => {
		dept_list = value.split(",");
		var dept = dept_list.find((e)=>{return frappe.user.has_role(e)})
		console.log(dept)
		if (!frm.doc.__islocal)
	        frm.set_df_property("department", "read_only", dept ? 1 : 0);
    });
}

function convertUom(frm) {
	// split - ask for new qty and batch ID (optional)
	// and make stock entry via batch.batch_split
	frappe.call({
		method: 'ql.ql.stock.get_bom_uom',
		args: {
			work_order: "",
			material_request: frm.doc.name
		},
		callback: (r) => {
			r.message.forEach(o => {
				frm.doc.items.forEach(row =>{
					if(o.item_code == row.item_code){
						row.uom = o.uom
						if (row.uom) {
							get_item_details(row.item_code, row.uom).then(data => {
								row.qty =  row.qty/data.conversion_factor
								frappe.model.set_value(row.doctype, row.name, 'conversion_factor', data.conversion_factor);
							});
						}
					}
				})
			});
			frm.refresh_field("locations")
		},
	});
}

function get_item_details(item_code, uom=null) {
	if (item_code) {
		return frappe.xcall('erpnext.stock.doctype.pick_list.pick_list.get_item_details', {
			item_code,
			uom
		});
	}
}

function set_schedule_date(frm) {
	if(frm.doc.schedule_date){
		copy_value_in_all_rows(frm.doc, frm.doc.doctype, frm.doc.name, "items", "schedule_date");
	}
}

function copy_value_in_all_rows(doc, dt, dn, table_fieldname, fieldname) {
	var d = locals[dt][dn];
	if(d[fieldname]){
		var cl = doc[table_fieldname] || [];
		for(var i = 0; i < cl.length; i++) {
			cl[i][fieldname] = d[fieldname];
		}
	}
	refresh_field(table_fieldname);
}