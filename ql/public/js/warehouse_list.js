frappe.treeview_settings['Warehouse'].onrender = function(node) {
	if (node.data && node.data.balance!==undefined && frappe.user.has_role('Administrator')||!frappe.user_roles.includes('WH')) {
		$('<span class="balance-area pull-right text-muted small">'
		+ format_currency(Math.abs(node.data.balance), node.data.company_currency)
		+ '</span>').insertBefore(node.$ul);
	}
}