import frappe
from frappe.utils import flt, get_link_to_form
from dateutil.parser._parser import ParserError
import operator
import re, datetime, math, time
from dateutil import parser
from six import iteritems, text_type, string_types, integer_types
from erpnext.utilities.transaction_base import TransactionBase
from frappe import _


def ql_validate_rate_with_reference_doc(self, ref_details):
	buying_doctypes = ["Purchase Order", "Purchase Invoice", "Purchase Receipt"]

	if self.doctype in buying_doctypes:
		to_disable = "Maintain same rate throughout Purchase cycle"
		settings_page = "Buying Settings"
	else:
		to_disable = "Maintain same rate throughout Sales cycle"
		settings_page = "Selling Settings"

	for ref_dt, ref_dn_field, ref_link_field in ref_details:
		for d in self.get("items"):
			if d.get(ref_link_field):
				ref_rate = frappe.db.get_value(ref_dt + " Item", d.get(ref_link_field), "rate")

				if abs(flt(d.rate - ref_rate, d.precision("rate"))) >= 10:
					frappe.msgprint(_("Row #{0}: Rate must be same as {1}: {2} ({3} / {4}) ")
						.format(d.idx, ref_dt, d.get(ref_dn_field), d.rate, ref_rate))
					frappe.throw(_("To allow different rates, disable the {0} checkbox in {1}.")
						.format(frappe.bold(_(to_disable)),
						get_link_to_form(settings_page, settings_page, frappe.bold(settings_page))))

def money_in_words(number, main_currency = None, fraction_currency=None):
	"""
	Returns string in words with currency and fraction currency.
	"""
	from frappe.utils import get_defaults, cint
	from frappe.utils.data import get_number_format_info, in_words
	_ = frappe._

	try:
		# note: `flt` returns 0 for invalid input and we don't want that
		number = float(number)
	except ValueError:
		return ""

	number = flt(number)
	if number < 0:
		return ""

	d = get_defaults()
	if not main_currency:
		main_currency = d.get('currency', 'INR')
	if not fraction_currency:
		fraction_currency = frappe.db.get_value("Currency", main_currency, "fraction", cache=True) or _("Cent")

	number_format = frappe.db.get_value("Currency", main_currency, "number_format", cache=True) or \
		frappe.db.get_default("number_format") or "#,###.##"

	fraction_length = get_number_format_info(number_format)[2]

	n = "%.{0}f".format(fraction_length) % number

	numbers = n.split('.')
	main, fraction =  numbers if len(numbers) > 1 else [n, '00']

	if len(fraction) < fraction_length:
		zeros = '0' * (fraction_length - len(fraction))
		fraction += zeros

	in_million = True
	if number_format == "#,##,###.##": in_million = False

	# 0.00
	if main == '0' and fraction in ['00', '000']:
		out = "{0} {1}".format(main_currency, _('Zero'))
	# 0.XX
	elif main == '0':
		out = _(in_words(fraction, in_million).title())
	else:
		out = main_currency + ' ' + _(in_words(main, in_million).title())
		if cint(fraction):
			out = out + ' ' + _('and') + ' ' + _(in_words(fraction, in_million).title())
	# out = re.sub(r'(?<=Thousand).*', '', out)
	out = out[0:139] #140 characters is max
	return out + '.'


def validate_multiple_billing(self, ref_dt, item_ref_dn, based_on, parentfield):
	from erpnext.controllers.status_updater import get_allowance_for
	item_allowance = {}
	global_qty_allowance, global_amount_allowance = None, None

	for item in self.get("items"):
		if item.get(item_ref_dn):
			ref_amt = flt(frappe.db.get_value(ref_dt + " Item",
				item.get(item_ref_dn), based_on), self.precision(based_on, item))
			if not ref_amt:
				frappe.msgprint(
					_("Warning: System will not check overbilling since amount for Item {0} in {1} is zero")
						.format(item.item_code, ref_dt))
			else:
				already_billed = frappe.db.sql("""
					select sum(%s)
					from `tab%s`
					where %s=%s and docstatus=1 and parent != %s
				""" % (based_on, self.doctype + " Item", item_ref_dn, '%s', '%s'),
					(item.get(item_ref_dn), self.name))[0][0]

				total_billed_amt = flt(flt(already_billed) + flt(item.get(based_on)),
					self.precision(based_on, item))

				allowance, item_allowance, global_qty_allowance, global_amount_allowance = \
					get_allowance_for(item.item_code, item_allowance, global_qty_allowance, global_amount_allowance, "amount")

				max_allowed_amt = flt(ref_amt * (100 + allowance) / 100)

				if total_billed_amt < 0 and max_allowed_amt < 0:
					# while making debit note against purchase return entry(purchase receipt) getting overbill error
					total_billed_amt = abs(total_billed_amt)
					max_allowed_amt = abs(max_allowed_amt)

				if total_billed_amt - max_allowed_amt > 5:
					frappe.throw(_("Cannot overbill for Item {0} in row {1} more than {2}. To allow over-billing, please set allowance in Accounts Settings")
						.format(item.item_code, item.idx, max_allowed_amt))