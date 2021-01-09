frappe.listview_settings['Purchase Order'].refresh = function (listview) {
	if(frappe.user.has_role(["WH","Stock User"])){
		$( "span[title*='Grand Total:']").remove()
	}
}