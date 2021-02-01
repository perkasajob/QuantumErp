from __future__ import unicode_literals
from frappe import _
import frappe, math
from frappe.utils.background_jobs import enqueue
from frappe.utils import nowdate, date_diff, add_months, today, getdate, add_days, flt, get_last_day
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification,\
	get_title, get_title_html
from datetime import datetime

def daily():
	quality_inspection_scheduler()

@frappe.whitelist()
def quality_inspection_scheduler(today=nowdate()):
	month_map = {'Monthly': 30, 'Quarterly': 3*30, 'Half-yearly': 6*30, 'Yearly': 12*30}

	qis = frappe.db.sql("""select `tabQuality Inspection`.name as qi, `tabQuality Inspection`.retest_period as retest_period, `tabQuality Inspection`.modified as date, \
		batch_id, sum(`tabStock Ledger Entry`.actual_qty) as qty \
		from `tabBatch` \
			join `tabStock Ledger Entry` ignore index (item_code, warehouse) \
				on (`tabBatch`.batch_id = `tabStock Ledger Entry`.batch_no ) \
			join `tabQuality Inspection` ignore index (item_code) \
				on (`tabBatch`.batch_id = `tabQuality Inspection`.batch_no ) \
		where (`tabBatch`.expiry_date >= CURDATE()) and `tabStock Ledger Entry`.actual_qty > 0 and `tabQuality Inspection`.retest_period > '' \
		group by batch_id \
		order by `tabBatch`.expiry_date ASC, `tabBatch`.creation ASC;""", as_dict=True)

	for qi in qis:
		datediff = datetime.today() - qi.date
		days_offset = math.floor(month_map[qi.retest_period] * 0.25)
		# return {'datediff': datediff, 'days_offset': days_offset}
		if  (datediff.days + days_offset) % month_map[qi.retest_period] == 0 :
			qi_doc = frappe.get_doc('Quality Inspection', qi.qi)
			cnt = frappe.db.count('Quality Inspection', filters={'batch_no': qi_doc.batch_no})
			new_qi_doc = frappe.copy_doc(qi_doc)
			new_qi_doc.update({"completion_status": "Not Started", "status": "Rejected", "retest": cnt, "report_date":add_days(datetime.now(), days_offset).date() })
			try:
				new_qi_doc.insert()
				new_qi_doc.add_comment('Comment', text=qi_doc.name + ' scheduled retest #' + str(cnt))
				frappe.db.commit()
			except frappe.DuplicateEntryError:
				pass
			except Exception:
				frappe.db.rollback()



def expire_dx_adv(today=nowdate()):
	for i in range(2):
		adv_idx = str(i)
		# advs = frappe.get_list('Adv Item', filters=[['parentfield','=','adv'+ adv_idx],['date','<=',today], ['type','in',['AC','AT']]], fields=['*'])
		advs = frappe.get_list('Adv Item', filters=[['parentfield','=','adv'+ adv_idx], ['date','<=',today]], fields=['*'])

		for adv in advs:
			# idx = frappe.db.count('SP', {'parent': adv.parent, 'parentfield': 'loan' + suffix })
			# adv = frappe.get_doc("Adv Item", adv.name)
			dx = frappe.get_doc(adv.parenttype, adv.parent)
			dx.append('mkt'+adv.line ,{'date':adv.date,'number': adv.number, 'dppu': adv.dppu, 'type':adv.type, 'line': adv.line, 'note': adv.note, 'territory': adv.territory})
			dx.validate()
			dx.save()
			dppu = frappe.get_doc('DPPU', adv.dppu)
			mkt = frappe.get_doc({'doctype': 'Mkt','date':adv.date,'number': adv.number, 'dppu': adv.dppu, 'line': adv.line, 'note': adv.note, 'territory': adv.territory, 'dx': dx.name, 'dm': dppu.dm_user, 'sm': dppu.sm_user, 'mr': dppu.mr_user}).insert(ignore_permissions=True)
			mkt.submit()
			Event_doc, message = make_to_do(adv.parent, adv.owner, adv.dppu)
			#frappe.delete_doc("SP", adv.name)
			notification_doc = {
				'type': 'To Do',
				'document_type': "",
				'document_name': Event_doc.name,
				'subject': message,
				'from_user': "Administrator",
				'email_content': '<div>{}</div>'.format(message)
			}

			enqueue_create_notification(adv.owner, notification_doc)

	frappe.db.commit()

	return {"status" : "success"}

def make_to_do(dx, user, dppu):
	message = "Dx {} Installment from DPPU {} is overdue".format(dx, dppu)
	Event_doc=frappe.new_doc("ToDo")
	Event_doc.status="Open"
	Event_doc.priority="Medium"
	Event_doc.allocated_to=user
	Event_doc.date=nowdate()
	Event_doc.description=(message)
	Event_doc.flags.ignore_mandatory = True
	Event_doc.save()
	return Event_doc, message