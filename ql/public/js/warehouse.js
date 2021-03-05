frappe.ui.form.on('Warehouse', {
	refresh(frm){
		if(frappe.user.has_role("Accounts Manager") == undefined){
			frm.add_custom_button(__("Stock Balance QL"), function() {
				frappe.route_options = {
					"account": frm.doc.__onload.account,
					"company": frm.doc.company
				}
				frappe.set_route("query-report", "Stock Balance QL");
			});
			setTimeout(() => {
				// $("[data-label='Stock%20Balance']").remove()
				frm.remove_custom_button('Stock Balance')
			}, 3);

		}
	},
})