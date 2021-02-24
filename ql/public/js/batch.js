// $("<button class='btn btn-default btn-xs btn-test' style='margin-left:10px;'>Test</button>").insertAfter($('.btn-split')[1])
// $($('.btn-split')[0]).attr('data-warehouse')
frappe.ui.form.on('Batch', {
	make_dashboard: function(frm) {
		$('.btn-split').each((i, e) => {
			let btn = $(`<button class='btn btn-default btn-xs btn-move-qi' style='margin-left:10px;' data-warehouse='${$(e).attr('data-warehouse')}' data-qty='${$(e).attr('data-qty')}'>Inspect</button>`).insertAfter(e)
			btn.on('click', function() {
				var $btn = $(this);
				frappe.prompt([{
					fieldname: 'qty',
					label: __('Inspect Qty'),
					fieldtype: 'Float',
					'default': $btn.attr('data-qty')
				}],
				(data) => {
					frappe.call({
						method: 'ql.ql.stock.create_inspection',
						args: {
							item_code: frm.doc.item,
							batch_no: frm.doc.name,
							qty: data.qty,
							warehouse: $btn.attr('data-warehouse'),
							// new_batch_id: data.new_batch_id
						},
						callback: (r) => {
							if(r?.message)
								frappe.msgprint(`Quality Inspection <a href= "#Form/Quality Inspection/${r.message.name}">${r.message.name}</a> Created`)
							frm.refresh();
						},
					});
				},
				__('Inspect Batch'),
				__('Inspect')
				);
			})
		});
	}
})

function batch_inspect(e) {
	debugger
	// split - ask for new qty and batch ID (optional)
	// and make stock entry via batch.batch_split
	rows.find('.btn-split').on('click', function() {
		var $btn = $(this);
		frappe.prompt([{
			fieldname: 'qty',
			label: __('Inspect Qty'),
			fieldtype: 'Float',
			'default': $btn.attr('data-qty')
		},
		{
			fieldname: 'new_batch_id',
			label: __('Inspect ID (Optional)'),
			fieldtype: 'Data',
		}],
		(data) => {
			frappe.call({
				method: 'erpnext.stock.doctype.batch.batch.split_batch',
				args: {
					item_code: frm.doc.item,
					batch_no: frm.doc.name,
					qty: data.qty,
					warehouse: $btn.attr('data-warehouse'),
					new_batch_id: data.new_batch_id
				},
				callback: (r) => {
					frm.refresh();
				},
			});
		},
		__('Inspect Batch'),
		__('Inspect')
		);
	})
}