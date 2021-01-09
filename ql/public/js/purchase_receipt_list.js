frappe.listview_settings['Purchase Receipt'].refresh = function (listview) {
	if(frappe.user.has_role(["WH","Stock User"])){
		$( "span[title*='Grand Total:']").remove()
	}
}