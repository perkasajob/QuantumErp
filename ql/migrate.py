import os
import shutil

def before_migrate():
	shutil.copyfile('../apps/ql/ql/ql/base_document.py', '../apps/frappe/frappe/model/base_document.py')

