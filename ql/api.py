import frappe
import json
from frappe.utils import nowdate, flt
from erpnext import get_company_currency, get_default_company
from frappe import _

logger = frappe.logger("journal_api")



@frappe.whitelist(allow_guest=True)
def test_journal_entry():

	return frappe.request.get_data()

@frappe.whitelist()
def create_journal_entry(
	accounts,
	company=None,
	voucher_type="Journal Entry",
	remarks="",
	posting_date=None,
	submit=0
):
	"""
	API Endpoint to create a Journal Entry with robust logging.
	"""
	
	# --- LOGGING START: Track Incoming Request ---
	# We capture the raw arguments to debug what data was actually sent
	payload_debug = {
		"company": company,
		"accounts": accounts,
		"submit": submit,
		"user": frappe.session.user
	}
	logger.info(f"Incoming JE Request: {json.dumps(payload_debug)}")
	# ---------------------------------------------

	if frappe.request.method != "POST":
		msg = "Only POST requests are allowed."
		logger.error(msg)
		frappe.throw(_(msg), frappe.PermissionError)

	# 1. Parse Data
	if isinstance(accounts, str):
		try:
			accounts = json.loads(accounts)
		except json.JSONDecodeError:
			frappe.throw(_("Invalid JSON format for 'accounts'."))

	if isinstance(submit, str):
		submit = 1 if submit.lower() in ["true", "1"] else 0

	# 2. Set Defaults
	if not posting_date:
		posting_date = nowdate()
	
	if not company:
		company = frappe.defaults.get_user_default("Company") or \
				  frappe.db.get_single_value("Global Defaults", "default_company")

	# 3. Build Child Table
	if isinstance(accounts, str):
		try:
			accounts = json.loads(accounts)
		except json.JSONDecodeError:
			frappe.throw(_("Invalid JSON format for 'accounts'."))

	# If the user passed a single dict object, wrap it in a list
	if isinstance(accounts, dict):
		accounts = [accounts]

	# 3. Final Verification before loop
	if not isinstance(accounts, list):
		frappe.throw(_("'accounts' must be a list of dictionaries."))

	# 4. Loop
	je_accounts = []
	for row in accounts:
		# Safety Check: ensure the row is actually a dict
		if not isinstance(row, dict):
			frappe.throw(_("Each item in 'accounts' must be a Dictionary, found {0} instead. Item: {1}").format(type(row), row))

		# Now this line is safe
		if "cost_center" not in row:
			 row["cost_center"] = frappe.get_cached_value('Company', company, 'cost_center')
		
		je_accounts.append(row)        

	doc_data = {
		"doctype": "Journal Entry",
		"voucher_type": voucher_type,
		"posting_date": posting_date,
		"company": company,
		"user_remark": remarks,
		"accounts": je_accounts
	}

	# 4. Insert Document with Error Logging
	try:
		je_doc = frappe.get_doc(doc_data)
		je_doc.insert()

		if submit:
			je_doc.submit()
		
		# --- LOGGING SUCCESS ---
		logger.info(f"Success: Created JE {je_doc.name}")
		# -----------------------

		return {
			"status": "success",
			"name": je_doc.name
		}

	except Exception as e:
		# --- LOGGING FAILURE ---
		# This creates a visible record in 'Error Log' DocType in Desk
		error_message = f"Error creating Journal Entry.\nError: {str(e)}\nPayload: {json.dumps(payload_debug, indent=2)}"
		
		frappe.log_error(
			title="API Journal Entry Creation Failed", 
			message=error_message
		)
		
		# Also log to server file
		logger.error(f"Failed: {str(e)}")
		# -----------------------
		
		# Re-throw so the API caller knows it failed (returns 500)
		frappe.throw(str(e)) 


import frappe
from frappe.utils import flt

@frappe.whitelist(allow_guest=True)
def get_item_costs(from_date=None, to_date=None):
    """
    Extracts native valuation rate and calculates pure variable COGS 
    (materials + direct labor from Workstation) per manufactured piece in v12.
    """
    items = frappe.db.sql("""
        SELECT 
            item_code, 
            item_name, 
            valuation_rate, 
			apl_item_code,
            product_id 
        FROM 
            `tabItem`
        WHERE 
            is_sales_item = 1 
			AND is_active = 1
            AND item_group = 'Q1 : Generik'
    """, as_dict=True)

    if not items:
        return []

    item_codes = tuple([d.item_code for d in items])
    variable_cost_data = {}

    if from_date and to_date and item_codes:
        # Join Job Card to Workstation to fetch hour_rate_labour
        manufacture_entries = frappe.db.sql("""
            SELECT 
                sed.item_code, 
                SUM(sed.qty) as total_qty,
                SUM(sed.amount) as total_material_cost,
                (
                    SELECT SUM((jc.total_time_in_mins / 60) * IFNULL(w.hour_rate_labour, 0))
                    FROM `tabJob Card` jc
                    JOIN `tabWorkstation` w ON jc.workstation = w.name
                    WHERE jc.project = se.project AND jc.docstatus = 1
                ) as total_labor_cost
            FROM `tabStock Entry Detail` sed
            JOIN `tabStock Entry` se ON se.name = sed.parent
            WHERE se.purpose = 'Manufacture' 
              AND se.docstatus = 1 
              AND sed.is_finished_item = 1
              AND sed.item_code IN %s
              AND se.posting_date BETWEEN %s AND %s
            GROUP BY sed.item_code, se.project
        """, (item_codes, from_date, to_date), as_dict=True)

        aggregated_costs = {}
        for entry in manufacture_entries:
            ic = entry.item_code
            if ic not in aggregated_costs:
                aggregated_costs[ic] = {"qty": 0.0, "total_variable_cost": 0.0}
            
            aggregated_costs[ic]["qty"] += flt(entry.total_qty)
            aggregated_costs[ic]["total_variable_cost"] += (flt(entry.total_material_cost) + flt(entry.total_labor_cost))

        for ic, data in aggregated_costs.items():
            if data["qty"] > 0:
                variable_cost_data[ic] = data["total_variable_cost"] / data["qty"]

    payload = []
    for item in items:
        calc_var_cogs = variable_cost_data.get(item.item_code)
        final_var_cogs = calc_var_cogs if calc_var_cogs is not None else flt(item.valuation_rate)
        
        payload.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "product_id": item.product_id,
			"apl_item_code": item.apl_item_code,
            "statutory_valuation_rate": flt(item.valuation_rate),
            "variable_cogs_per_piece": final_var_cogs
        })

    return payload