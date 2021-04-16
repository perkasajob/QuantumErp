import frappe
from frappe.utils import flt, get_link_to_form
from dateutil.parser._parser import ParserError
import operator
import re, datetime, math, time
from dateutil import parser
from six import iteritems, text_type, string_types, integer_types
from erpnext.utilities.transaction_base import TransactionBase
from frappe.model.base_document import BaseDocument
from frappe.modules import load_doctype_module
from frappe import _
from erpnext.controllers.buying_controller import get_items_from_bom
from erpnext.stock.stock_ledger import get_valuation_rate
from erpnext.stock.doctype.stock_entry.stock_entry import get_used_alternative_items


_classes = {}

def get_controller(doctype):
	"""Returns the **class** object of the given DocType.
	For `custom` type, returns `frappe.model.document.Document`.

	:param doctype: DocType name as string."""
	from frappe.model.document import Document
	from frappe.utils.nestedset import NestedSet
	global _classes

	if not doctype in _classes:
		module_name, custom = frappe.db.get_value("DocType", doctype, ("module", "custom"), cache=True) \
			or ["Core", False]

		if custom:
			if frappe.db.field_exists("DocType", "is_tree"):
				is_tree = frappe.db.get_value("DocType", doctype, "is_tree", cache=True)
			else:
				is_tree = False
			_class = NestedSet if is_tree else Document
		else: #PJOB: replacement ===
			class_overrides = frappe.get_hooks('override_doctype_class')
			if class_overrides and class_overrides.get(doctype):
				import_path = class_overrides[doctype][-1]
				module_path, classname = import_path.rsplit('.', 1)
				module = frappe.get_module(module_path)
				if not hasattr(module, classname):
					raise ImportError('{0}: {1} does not exist in module {2}'.format(doctype, classname, module_path))
			else:
				module = load_doctype_module(doctype, module_name)
				classname = doctype.replace(" ", "").replace("-", "")

			if hasattr(module, classname):
				_class = getattr(module, classname)
				if issubclass(_class, BaseDocument):
					_class = getattr(module, classname)
				else:
					raise ImportError(doctype)
			else:
				raise ImportError(doctype)
		return _class

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


def update_raw_materials_supplied_based_on_bom(self, item, raw_material_table):
		exploded_item = 1
		print("Override update_raw_materials_supplied_based_on_bom")
		if hasattr(item, 'include_exploded_items'):
			exploded_item = item.get('include_exploded_items')

		bom_items = get_items_from_bom(item.item_code, item.bom, exploded_item)
		bom = frappe.get_doc('BOM', item.bom)
		# quantity

		used_alternative_items = []
		if self.doctype == 'Purchase Receipt' and item.purchase_order:
			used_alternative_items = get_used_alternative_items(purchase_order = item.purchase_order)

		raw_materials_cost = 0
		items = list(set([d.item_code for d in bom_items]))
		item_wh = frappe._dict(frappe.db.sql("""select i.item_code, id.default_warehouse
			from `tabItem` i, `tabItem Default` id
			where id.parent=i.name and id.company=%s and i.name in ({0})"""
			.format(", ".join(["%s"] * len(items))), [self.company] + items))

		for bom_item in bom_items:
			if self.doctype == "Purchase Order":
				reserve_warehouse = bom_item.source_warehouse or item_wh.get(bom_item.item_code)
				if frappe.db.get_value("Warehouse", reserve_warehouse, "company") != self.company:
					reserve_warehouse = None

			conversion_factor = item.conversion_factor
			if (self.doctype == 'Purchase Receipt' and item.purchase_order and
				bom_item.item_code in used_alternative_items):
				alternative_item_data = used_alternative_items.get(bom_item.item_code)
				bom_item.item_code = alternative_item_data.item_code
				bom_item.item_name = alternative_item_data.item_name
				bom_item.stock_uom = alternative_item_data.stock_uom
				conversion_factor = alternative_item_data.conversion_factor
				bom_item.description = alternative_item_data.description

			# check if exists
			exists = 0
			for d in self.get(raw_material_table):
				if d.main_item_code == item.item_code and d.rm_item_code == bom_item.item_code \
					and d.reference_name == item.name:
						rm, exists = d, 1
						break

			if not exists:
				rm = self.append(raw_material_table, {})

			returned_qty = 0.0 if not hasattr(rm, "returned_qty") or rm.returned_qty is None  else rm.returned_qty

			required_qty = flt(flt(bom_item.qty_consumed_per_unit) * bom.quantity *
				flt(conversion_factor), rm.precision("required_qty")) -  returned_qty
			rm.reference_name = item.name
			rm.bom_detail_no = bom_item.name
			rm.main_item_code = item.item_code
			rm.rm_item_code = bom_item.item_code
			rm.stock_uom = bom_item.stock_uom
			rm.required_qty = required_qty
			if self.doctype == "Purchase Order" and not rm.reserve_warehouse:
				rm.reserve_warehouse = reserve_warehouse

			rm.conversion_factor = conversion_factor

			if self.doctype in ["Purchase Receipt", "Purchase Invoice"]:
				rm.consumed_qty = required_qty
				rm.description = bom_item.description
				if item.batch_no and frappe.db.get_value("Item", rm.rm_item_code, "has_batch_no") and not rm.batch_no:
					rm.batch_no = item.batch_no

			# get raw materials rate
			if self.doctype == "Purchase Receipt":
				from erpnext.stock.utils import get_incoming_rate
				rm.rate = get_incoming_rate({
					"item_code": bom_item.item_code,
					"warehouse": self.supplier_warehouse,
					"posting_date": self.posting_date,
					"posting_time": self.posting_time,
					"qty": -1 * required_qty,
					"serial_no": rm.serial_no
				})
				if not rm.rate:
					rm.rate = get_valuation_rate(bom_item.item_code, self.supplier_warehouse,
						self.doctype, self.name, currency=self.company_currency, company = self.company)
			else:
				rm.rate = bom_item.rate

			rm.amount = required_qty * flt(rm.rate)
			raw_materials_cost += flt(rm.amount)

		if self.doctype in ("Purchase Receipt", "Purchase Invoice"):
			item.rm_supp_cost = raw_materials_cost