frappe.listview_settings['Purchase Order'].refresh = function (listview) {
	if(!frappe.user.has_role(["Purchase User","Purchase Manager", "Accounts Manager", "Accounts User", "System Manager"])){
		$( "span[title*='Grand Total:']").remove()
	}
}