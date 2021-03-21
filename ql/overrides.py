import frappe
from frappe.utils import flt, get_link_to_form
from dateutil.parser._parser import ParserError
import operator
import re, datetime, math, time
from dateutil import parser
from six import iteritems, text_type, string_types, integer_types
from erpnext.utilities.transaction_base import TransactionBase
from frappe import _


def before_save(doc, method):
	TransactionBase.validate_rate_with_reference_doc = ql_validate_rate_with_reference_doc
	frappe.utils.money_in_words = money_in_words

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
	out = re.sub(r'(?<=Thousand).*', '', out)
	return out + '.'