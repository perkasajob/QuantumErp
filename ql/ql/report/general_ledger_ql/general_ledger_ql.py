# Copyright (c) 2013, Perkasa JoB and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from erpnext import get_company_currency, get_default_company
from erpnext.accounts.report.utils import get_currency, convert_to_presentation_currency
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.report.financial_statements import get_cost_centers_with_children
from six import iteritems
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions, get_dimension_with_children
from collections import OrderedDict

def execute(filters=None):
	if not filters:
		return [], []

	account_details = {}

	if filters and filters.get('print_in_account_currency') and \
		not filters.get('account'):
		frappe.throw(_("Select an account to print in account currency"))

	for acc in frappe.db.sql("""select name, is_group from tabAccount""", as_dict=1):
		account_details.setdefault(acc.name, acc)

	if filters.get('party'):
		filters.party = frappe.parse_json(filters.get("party"))

	validate_filters(filters, account_details)

	validate_party(filters)

	filters = set_account_currency(filters)

	columns = get_columns(filters)

	res = get_result(filters, account_details)

	return columns, res


def validate_filters(filters, account_details):
	if not filters.get("company"):
		frappe.throw(_("{0} is mandatory").format(_("Company")))

	if not filters.get("from_date") and not filters.get("to_date"):
		frappe.throw(_("{0} and {1} are mandatory").format(frappe.bold(_("From Date")), frappe.bold(_("To Date"))))

	if filters.get("account") and not account_details.get(filters.account):
		frappe.throw(_("Account {0} does not exists").format(filters.account))

	if (filters.get("account") and filters.get("group_by") == _('Group by Account')
		and account_details[filters.account].is_group == 0):
		frappe.throw(_("Can not filter based on Account, if grouped by Account"))

	if (filters.get("voucher_no")
		and filters.get("group_by") in [_('Group by Voucher')]):
		frappe.throw(_("Can not filter based on Voucher No, if grouped by Voucher"))

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

	if filters.get('project'):
		filters.project = frappe.parse_json(filters.get('project'))

	if filters.get('cost_center'):
		filters.cost_center = frappe.parse_json(filters.get('cost_center'))


def validate_party(filters):
	party_type, party = filters.get("party_type"), filters.get("party")

	if party:
		if not party_type:
			frappe.throw(_("To filter based on Party, select Party Type first"))
		else:
			for d in party:
				if not frappe.db.exists(party_type, d):
					frappe.throw(_("Invalid {0}: {1}").format(party_type, d))

def set_account_currency(filters):
	if filters.get("account") or (filters.get('party') and len(filters.party) == 1):
		filters["company_currency"] = frappe.get_cached_value('Company',  filters.company,  "default_currency")
		account_currency = None

		if filters.get("account"):
			account_currency = get_account_currency(filters.account)
		elif filters.get("party"):
			gle_currency = frappe.db.get_value(
				"GL Entry", {
					"party_type": filters.party_type, "party": filters.party[0], "company": filters.company
				},
				"account_currency"
			)

			if gle_currency:
				account_currency = gle_currency
			else:
				account_currency = (None if filters.party_type in ["Employee", "Student", "Shareholder", "Member"] else
					frappe.db.get_value(filters.party_type, filters.party[0], "default_currency"))

		filters["account_currency"] = account_currency or filters.company_currency
		if filters.account_currency != filters.company_currency and not filters.presentation_currency:
			filters.presentation_currency = filters.account_currency

	return filters

def get_result(filters, account_details):
	gl_entries = get_gl_entries(filters)

	data = get_data_with_opening_closing(filters, account_details, gl_entries)

	result = get_result_as_list(data, filters)

	return result

def get_gl_entries(filters):
	currency_map = get_currency(filters)
	select_fields = """, debit, credit, debit_in_account_currency,
		credit_in_account_currency """

	order_by_statement = "order by posting_date, account, creation"

	if filters.get("group_by") == _("Group by Voucher"):
		order_by_statement = "order by posting_date, voucher_type, voucher_no"

	if filters.get("include_default_book_entries"):
		filters['company_fb'] = frappe.db.get_value("Company",
			filters.get("company"), 'default_finance_book')

	gl_entries = frappe.db.sql(
		"""
		select
			name as gl_entry, posting_date, account, party_type, party,
			voucher_type, voucher_no, cost_center, project,
			against_voucher_type, against_voucher, account_currency,
			remarks, against, is_opening {select_fields}
		from `tabGL Entry`
		where company=%(company)s {conditions}
		{order_by_statement}
		""".format(
			select_fields=select_fields, conditions=get_conditions(filters),
			order_by_statement=order_by_statement
		),
		filters, as_dict=1)

	if filters.get('presentation_currency'):
		return convert_to_presentation_currency(gl_entries, currency_map)
	else:
		return gl_entries


def get_conditions(filters):
	conditions = []
	if filters.get("account"):
		lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
		conditions.append("""account in (select name from tabAccount
			where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt))

	if filters.get("cost_center"):
		filters.cost_center = get_cost_centers_with_children(filters.cost_center)
		conditions.append("cost_center in %(cost_center)s")

	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")

	if filters.get("group_by") == "Group by Party" and not filters.get("party_type"):
		conditions.append("party_type in ('Customer', 'Supplier')")

	if filters.get("party_type"):
		conditions.append("party_type=%(party_type)s")

	if filters.get("party"):
		conditions.append("party in %(party)s")

	if not (filters.get("account") or filters.get("party") or
		filters.get("group_by") in ["Group by Account", "Group by Party"]):
		conditions.append("posting_date >=%(from_date)s")

	conditions.append("(posting_date <=%(to_date)s or is_opening = 'Yes')")

	if filters.get("project"):
		conditions.append("project in %(project)s")

	if filters.get("finance_book"):
		if filters.get("include_default_book_entries"):
			conditions.append("(finance_book in (%(finance_book)s, %(company_fb)s, '') OR finance_book IS NULL)")
		else:
			conditions.append("finance_book in (%(finance_book)s)")

	from frappe.desk.reportview import build_match_conditions
	match_conditions = build_match_conditions("GL Entry")

	if match_conditions:
		conditions.append(match_conditions)

	accounting_dimensions = get_accounting_dimensions(as_list=False)

	if accounting_dimensions:
		for dimension in accounting_dimensions:
			if filters.get(dimension.fieldname):
				if frappe.get_cached_value('DocType', dimension.document_type, 'is_tree'):
					filters[dimension.fieldname] = get_dimension_with_children(dimension.document_type,
						filters.get(dimension.fieldname))
					conditions.append("{0} in %({0})s".format(dimension.fieldname))
				else:
					conditions.append("{0} in (%({0})s)".format(dimension.fieldname))

	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_data_with_opening_closing(filters, account_details, gl_entries):
	data = []

	gle_map = initialize_gle_map(gl_entries, filters)

	totals, entries = get_accountwise_gle(filters, gl_entries, gle_map)

	# Opening for filtered account
	data.append(totals.opening)

	if filters.get("group_by") != _('Group by Voucher (Consolidated)'):
		for acc, acc_dict in iteritems(gle_map):
			# acc
			if acc_dict.entries:
				# opening
				data.append({})
				if filters.get("group_by") != _("Group by Voucher"):
					data.append(acc_dict.totals.opening)

				data += acc_dict.entries

				# totals
				data.append(acc_dict.totals.total)

				# closing
				if filters.get("group_by") != _("Group by Voucher"):
					data.append(acc_dict.totals.closing)
		data.append({})
	else:
		data += entries

	# totals
	data.append(totals.total)

	# closing
	data.append(totals.closing)

	return data

def get_totals_dict():
	def _get_debit_credit_dict(label):
		return _dict(
			account="'{0}'".format(label),
			debit=0.0,
			credit=0.0,
			debit_in_account_currency=0.0,
			credit_in_account_currency=0.0
		)
	return _dict(
		opening = _get_debit_credit_dict(_('Opening')),
		total = _get_debit_credit_dict(_('Total')),
		closing = _get_debit_credit_dict(_('Closing (Opening + Total)'))
	)

def group_by_field(group_by):
	if group_by == _('Group by Party'):
		return 'party'
	elif group_by in [_('Group by Voucher (Consolidated)'), _('Group by Account')]:
		return 'account'
	else:
		return 'voucher_no'

def initialize_gle_map(gl_entries, filters):
	gle_map = OrderedDict()
	group_by = group_by_field(filters.get('group_by'))

	for gle in gl_entries:
		gle_map.setdefault(gle.get(group_by), _dict(totals=get_totals_dict(), entries=[]))
	return gle_map


def get_accountwise_gle(filters, gl_entries, gle_map):
	totals = get_totals_dict()
	entries = []
	consolidated_gle = OrderedDict()
	group_by = group_by_field(filters.get('group_by'))

	def update_value_in_dict(data, key, gle):
		data[key].debit += flt(gle.debit)
		data[key].credit += flt(gle.credit)

		data[key].debit_in_account_currency += flt(gle.debit_in_account_currency)
		data[key].credit_in_account_currency += flt(gle.credit_in_account_currency)

		if data[key].against_voucher and gle.against_voucher:
			data[key].against_voucher += ', ' + gle.against_voucher

	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	for gle in gl_entries:
		if (gle.posting_date < from_date or
			(cstr(gle.is_opening) == "Yes" and not filters.get("show_opening_entries"))):
			update_value_in_dict(gle_map[gle.get(group_by)].totals, 'opening', gle)
			update_value_in_dict(totals, 'opening', gle)

			update_value_in_dict(gle_map[gle.get(group_by)].totals, 'closing', gle)
			update_value_in_dict(totals, 'closing', gle)

		elif gle.posting_date <= to_date:
			update_value_in_dict(gle_map[gle.get(group_by)].totals, 'total', gle)
			update_value_in_dict(totals, 'total', gle)
			if filters.get("group_by") != _('Group by Voucher (Consolidated)'):
				gle_map[gle.get(group_by)].entries.append(gle)
			elif filters.get("group_by") == _('Group by Voucher (Consolidated)'):
				key = (gle.get("voucher_type"), gle.get("voucher_no"),
					gle.get("account"), gle.get("cost_center"))
				if key not in consolidated_gle:
					consolidated_gle.setdefault(key, gle)
				else:
					update_value_in_dict(consolidated_gle, key, gle)

			update_value_in_dict(gle_map[gle.get(group_by)].totals, 'closing', gle)
			update_value_in_dict(totals, 'closing', gle)

	for key, value in consolidated_gle.items():
		entries.append(value)

	return totals, entries

def get_result_as_list(data, filters):
	balance, balance_in_account_currency = 0, 0
	inv_details = get_supplier_invoice_details()

	for d in data:
		if not d.get('posting_date'):
			balance, balance_in_account_currency = 0, 0

		balance = get_balance(d, balance, 'debit', 'credit')
		d['balance'] = balance

		d['account_currency'] = filters.account_currency
		d['bill_no'] = inv_details.get(d.get('against_voucher'), '')

	return data

def get_supplier_invoice_details():
	inv_details = {}
	for d in frappe.db.sql(""" select name, bill_no from `tabPurchase Invoice`
		where docstatus = 1 and bill_no is not null and bill_no != '' """, as_dict=1):
		inv_details[d.name] = d.bill_no

	return inv_details

def get_balance(row, balance, debit_field, credit_field):
	balance += (row.get(debit_field, 0) -  row.get(credit_field, 0))

	return balance

def get_columns(filters):
	if filters.get("presentation_currency"):
		currency = filters["presentation_currency"]
	else:
		if filters.get("company"):
			currency = get_company_currency(filters["company"])
		else:
			company = get_default_company()
			currency = get_company_currency(company)

	columns = [
		{
			"label": _("GL Entry"),
			"fieldname": "gl_entry",
			"fieldtype": "Link",
			"options": "GL Entry",
			"hidden": 1
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 90
		},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 180
		},
		{
			"label": _("Debit ({0})".format(currency)),
			"fieldname": "debit",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Credit ({0})".format(currency)),
			"fieldname": "credit",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Balance ({0})".format(currency)),
			"fieldname": "balance",
			"fieldtype": "Currency",
			"width": 130
		}
	]

	columns.extend([
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"width": 120
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 180
		},
		{
			"label": _("Against Account"),
			"fieldname": "against",
			"width": 120
		},
		{
			"label": _("Party Type"),
			"fieldname": "party_type",
			"width": 100
		},
		{
			"label": _("Party"),
			"fieldname": "party",
			"width": 100
		},
		{
			"label": _("Project"),
			"options": "Project",
			"fieldname": "project",
			"width": 100
		},
		{
			"label": _("Cost Center"),
			"options": "Cost Center",
			"fieldname": "cost_center",
			"width": 100
		},
		{
			"label": _("Against Voucher Type"),
			"fieldname": "against_voucher_type",
			"width": 100
		},
		{
			"label": _("Against Voucher"),
			"fieldname": "against_voucher",
			"fieldtype": "Dynamic Link",
			"options": "against_voucher_type",
			"width": 100
		},
		{
			"label": _("Supplier Invoice No"),
			"fieldname": "bill_no",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Remarks"),
			"fieldname": "remarks",
			"width": 400
		}
	])

	return columns

class ClosedAccountingPeriod(frappe.ValidationError): pass
class StockAccountInvalidTransaction(frappe.ValidationError): pass
class StockValueAndAccountBalanceOutOfSync(frappe.ValidationError): pass

def make_gl_entries(gl_map, cancel=False, adv_adj=False, merge_entries=True, update_outstanding='Yes', from_repost=False):
	if gl_map:
		if not cancel:
			validate_accounting_period(gl_map)
			gl_map = process_gl_map(gl_map, merge_entries)
			if gl_map and len(gl_map) > 1:
				save_entries(gl_map, adv_adj, update_outstanding, from_repost)
			else:
				frappe.throw(_("Incorrect number of General Ledger Entries found. You might have selected a wrong Account in the transaction."))
		else:
			delete_gl_entries(gl_map, adv_adj=adv_adj, update_outstanding=update_outstanding)

def validate_accounting_period(gl_map):
	accounting_periods = frappe.db.sql(""" SELECT
			ap.name as name
		FROM
			`tabAccounting Period` ap, `tabClosed Document` cd
		WHERE
			ap.name = cd.parent
			AND ap.company = %(company)s
			AND cd.closed = 1
			AND cd.document_type = %(voucher_type)s
			AND %(date)s between ap.start_date and ap.end_date
			""", {
				'date': gl_map[0].posting_date,
				'company': gl_map[0].company,
				'voucher_type': gl_map[0].voucher_type
			}, as_dict=1)

	if accounting_periods:
		frappe.throw(_("You cannot create or cancel any accounting entries within in the closed Accounting Period {0}")
			.format(frappe.bold(accounting_periods[0].name)), ClosedAccountingPeriod)

def process_gl_map(gl_map, merge_entries=True):
	if merge_entries:
		gl_map = merge_similar_entries(gl_map)
	for entry in gl_map:
		# toggle debit, credit if negative entry
		if flt(entry.debit) < 0:
			entry.credit = flt(entry.credit) - flt(entry.debit)
			entry.debit = 0.0

		if flt(entry.debit_in_account_currency) < 0:
			entry.credit_in_account_currency = \
				flt(entry.credit_in_account_currency) - flt(entry.debit_in_account_currency)
			entry.debit_in_account_currency = 0.0

		if flt(entry.credit) < 0:
			entry.debit = flt(entry.debit) - flt(entry.credit)
			entry.credit = 0.0

		if flt(entry.credit_in_account_currency) < 0:
			entry.debit_in_account_currency = \
				flt(entry.debit_in_account_currency) - flt(entry.credit_in_account_currency)
			entry.credit_in_account_currency = 0.0

	return gl_map

def merge_similar_entries(gl_map):
	merged_gl_map = []
	accounting_dimensions = get_accounting_dimensions()
	for entry in gl_map:
		# if there is already an entry in this account then just add it
		# to that entry
		same_head = check_if_in_list(entry, merged_gl_map, accounting_dimensions)
		if same_head:
			same_head.debit	= flt(same_head.debit) + flt(entry.debit)
			same_head.debit_in_account_currency	= \
				flt(same_head.debit_in_account_currency) + flt(entry.debit_in_account_currency)
			same_head.credit = flt(same_head.credit) + flt(entry.credit)
			same_head.credit_in_account_currency = \
				flt(same_head.credit_in_account_currency) + flt(entry.credit_in_account_currency)
		else:
			merged_gl_map.append(entry)

	company = gl_map[0].company if gl_map else erpnext.get_default_company()
	company_currency = erpnext.get_company_currency(company)
	precision = get_field_precision(frappe.get_meta("GL Entry").get_field("debit"), company_currency)

	# filter zero debit and credit entries
	merged_gl_map = filter(lambda x: flt(x.debit, precision)!=0 or flt(x.credit, precision)!=0, merged_gl_map)
	merged_gl_map = list(merged_gl_map)

	return merged_gl_map

def check_if_in_list(gle, gl_map, dimensions=None):
	account_head_fieldnames = ['party_type', 'party', 'against_voucher', 'against_voucher_type',
		'cost_center', 'project']

	if dimensions:
		account_head_fieldnames = account_head_fieldnames + dimensions

	for e in gl_map:
		same_head = True
		if e.account != gle.account:
			same_head = False

		for fieldname in account_head_fieldnames:
			if cstr(e.get(fieldname)) != cstr(gle.get(fieldname)):
				same_head = False

		if same_head:
			return e

def save_entries(gl_map, adv_adj, update_outstanding, from_repost=False):
	if not from_repost:
		validate_cwip_accounts(gl_map)

	round_off_debit_credit(gl_map)
	for entry in gl_map:
		make_entry(entry, adv_adj, update_outstanding, from_repost)

		# check against budget
		if not from_repost:
			validate_expense_against_budget(entry)

	if not from_repost:
		validate_account_for_perpetual_inventory(gl_map)


def make_entry(args, adv_adj, update_outstanding, from_repost=False):
	gle = frappe.new_doc("GL Entry")
	gle.update(args)
	gle.flags.ignore_permissions = 1
	gle.flags.from_repost = from_repost
	gle.validate()
	gle.db_insert()
	gle.run_method("on_update_with_args", adv_adj, update_outstanding, from_repost)
	gle.flags.ignore_validate = True
	gle.submit()

def validate_account_for_perpetual_inventory(gl_map):
	if cint(erpnext.is_perpetual_inventory_enabled(gl_map[0].company)):
		account_list = [gl_entries.account for gl_entries in gl_map]

		aii_accounts = [d.name for d in frappe.get_all("Account",
			filters={'account_type': 'Stock', 'is_group': 0, 'company': gl_map[0].company})]

		for account in account_list:
			if account not in aii_accounts:
				continue

			account_bal, stock_bal, warehouse_list = get_stock_and_account_balance(account,
				gl_map[0].posting_date, gl_map[0].company)

			if gl_map[0].voucher_type=="Journal Entry":
				# In case of Journal Entry, there are no corresponding SL entries,
				# hence deducting currency amount
				account_bal -= flt(gl_map[0].debit) - flt(gl_map[0].credit)
				if account_bal == stock_bal:
					frappe.throw(_("Account: {0} can only be updated via Stock Transactions")
						.format(account), StockAccountInvalidTransaction)

			# This has been comment for a temporary, will add this code again on release of immutable ledger
			# elif account_bal != stock_bal:
			# 	precision = get_field_precision(frappe.get_meta("GL Entry").get_field("debit"),
			# 		currency=frappe.get_cached_value('Company',  gl_map[0].company,  "default_currency"))

			# 	diff = flt(stock_bal - account_bal, precision)
			# 	error_reason = _("Stock Value ({0}) and Account Balance ({1}) are out of sync for account {2} and it's linked warehouses.").format(
			# 		stock_bal, account_bal, frappe.bold(account))
			# 	error_resolution = _("Please create adjustment Journal Entry for amount {0} ").format(frappe.bold(diff))
			# 	stock_adjustment_account = frappe.db.get_value("Company",gl_map[0].company,"stock_adjustment_account")

			# 	db_or_cr_warehouse_account =('credit_in_account_currency' if diff < 0 else 'debit_in_account_currency')
			# 	db_or_cr_stock_adjustment_account = ('debit_in_account_currency' if diff < 0 else 'credit_in_account_currency')

			# 	journal_entry_args = {
			# 	'accounts':[
			# 		{'account': account, db_or_cr_warehouse_account : abs(diff)},
			# 		{'account': stock_adjustment_account, db_or_cr_stock_adjustment_account : abs(diff) }]
			# 	}

			# 	frappe.msgprint(msg="""{0}<br></br>{1}<br></br>""".format(error_reason, error_resolution),
			# 		raise_exception=StockValueAndAccountBalanceOutOfSync,
			# 		title=_('Values Out Of Sync'),
			# 		primary_action={
			# 			'label': _('Make Journal Entry'),
			# 			'client_action': 'erpnext.route_to_adjustment_jv',
			# 			'args': journal_entry_args
			# 		})

def validate_cwip_accounts(gl_map):
	cwip_enabled = any([cint(ac.enable_cwip_accounting) for ac in frappe.db.get_all("Asset Category","enable_cwip_accounting")])

	if cwip_enabled and gl_map[0].voucher_type == "Journal Entry":
			cwip_accounts = [d[0] for d in frappe.db.sql("""select name from tabAccount
				where account_type = 'Capital Work in Progress' and is_group=0""")]

			for entry in gl_map:
				if entry.account in cwip_accounts:
					frappe.throw(
						_("Account: <b>{0}</b> is capital Work in progress and can not be updated by Journal Entry").format(entry.account))

def round_off_debit_credit(gl_map):
	precision = get_field_precision(frappe.get_meta("GL Entry").get_field("debit"),
		currency=frappe.get_cached_value('Company',  gl_map[0].company,  "default_currency"))

	debit_credit_diff = 0.0
	for entry in gl_map:
		entry.debit = flt(entry.debit, precision)
		entry.credit = flt(entry.credit, precision)
		debit_credit_diff += entry.debit - entry.credit

	debit_credit_diff = flt(debit_credit_diff, precision)

	if gl_map[0]["voucher_type"] in ("Journal Entry", "Payment Entry"):
		allowance = 5.0 / (10**precision)
	else:
		allowance = .5

	if abs(debit_credit_diff) >= allowance:
		frappe.throw(_("Debit and Credit not equal for {0} #{1}. Difference is {2}.")
			.format(gl_map[0].voucher_type, gl_map[0].voucher_no, debit_credit_diff))

	elif abs(debit_credit_diff) >= (1.0 / (10**precision)):
		make_round_off_gle(gl_map, debit_credit_diff, precision)

def make_round_off_gle(gl_map, debit_credit_diff, precision):
	round_off_account, round_off_cost_center = get_round_off_account_and_cost_center(gl_map[0].company)
	round_off_account_exists = False
	round_off_gle = frappe._dict()
	for d in gl_map:
		if d.account == round_off_account:
			round_off_gle = d
			if d.debit_in_account_currency:
				debit_credit_diff -= flt(d.debit_in_account_currency)
			else:
				debit_credit_diff += flt(d.credit_in_account_currency)
			round_off_account_exists = True

	if round_off_account_exists and abs(debit_credit_diff) <= (1.0 / (10**precision)):
		gl_map.remove(round_off_gle)
		return

	if not round_off_gle:
		for k in ["voucher_type", "voucher_no", "company",
			"posting_date", "remarks"]:
				round_off_gle[k] = gl_map[0][k]

	round_off_gle.update({
		"account": round_off_account,
		"debit_in_account_currency": abs(debit_credit_diff) if debit_credit_diff < 0 else 0,
		"credit_in_account_currency": debit_credit_diff if debit_credit_diff > 0 else 0,
		"debit": abs(debit_credit_diff) if debit_credit_diff < 0 else 0,
		"credit": debit_credit_diff if debit_credit_diff > 0 else 0,
		"cost_center": round_off_cost_center,
		"party_type": None,
		"party": None,
		"is_opening": "No",
		"against_voucher_type": None,
		"against_voucher": None
	})

	if not round_off_account_exists:
		gl_map.append(round_off_gle)

def get_round_off_account_and_cost_center(company):
	round_off_account, round_off_cost_center = frappe.get_cached_value('Company',  company,
		["round_off_account", "round_off_cost_center"]) or [None, None]
	if not round_off_account:
		frappe.throw(_("Please mention Round Off Account in Company"))

	if not round_off_cost_center:
		frappe.throw(_("Please mention Round Off Cost Center in Company"))

	return round_off_account, round_off_cost_center

def delete_gl_entries(gl_entries=None, voucher_type=None, voucher_no=None,
		adv_adj=False, update_outstanding="Yes"):

	from erpnext.accounts.doctype.gl_entry.gl_entry import validate_balance_type, \
		check_freezing_date, update_outstanding_amt, validate_frozen_account

	if not gl_entries:
		gl_entries = frappe.db.sql("""
			select account, posting_date, party_type, party, cost_center, fiscal_year,voucher_type,
			voucher_no, against_voucher_type, against_voucher, cost_center, company
			from `tabGL Entry`
			where voucher_type=%s and voucher_no=%s""", (voucher_type, voucher_no), as_dict=True)

	if gl_entries:
		validate_accounting_period(gl_entries)
		check_freezing_date(gl_entries[0]["posting_date"], adv_adj)

	frappe.db.sql("""delete from `tabGL Entry` where voucher_type=%s and voucher_no=%s""",
		(voucher_type or gl_entries[0]["voucher_type"], voucher_no or gl_entries[0]["voucher_no"]))

	for entry in gl_entries:
		validate_frozen_account(entry["account"], adv_adj)
		validate_balance_type(entry["account"], adv_adj)
		if not adv_adj:
			validate_expense_against_budget(entry)

		if entry.get("against_voucher") and update_outstanding == 'Yes' and not adv_adj:
			update_outstanding_amt(entry["account"], entry.get("party_type"), entry.get("party"), entry.get("against_voucher_type"),
				entry.get("against_voucher"), on_cancel=True)
