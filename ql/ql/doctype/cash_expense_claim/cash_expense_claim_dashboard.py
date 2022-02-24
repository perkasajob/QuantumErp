from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'cash_expense_claim',
        'non_standard_fieldnames': {
            'Payment Entry': 'reference_name',
            'Journal Entry': 'reference_name'
        },
		'transactions': [
			{
				'items': ['Payment Entry']
			},
			{
				'items': ['Journal Entry']
			}
		]
	}
