

frappe.ui.form.on('Item', {
  refresh: function(frm) {
      // Target the input element by fieldname
      let $inputWrapper = $(frm.fields_dict['msds_document'].wrapper);
      let $input = $inputWrapper.find('input[data-fieldname="msds_document"]');

      if ($input.length) {
          let $button = $('<button>', {
              html: '<i class="fa fa-link"></i>',
              class: 'btn btn-primary btn-sm',
              css: {
                  'margin-left': '5px',
                  'display': 'inline-block',
                  'vertical-align': 'middle'
              }
          });

          // Apply flexbox to the control-input div
          let $controlInput = $input.closest('.control-input');
          $controlInput.css({
              'display': 'flex',
              'align-items': 'center',
              'flex-wrap': 'nowrap'
          });

          // Insert the button after the input
          $input.after($button);

          $button.on('click', function() {
              let url = $input.val().trim();
              if (!url) {
                  url = $inputWrapper.find('.control-value').text().trim();
              }
              if (url) {
                  if (!/^https?:\/\//i.test(url)) {
                      url = 'https://' + url;
                  }
                  window.open(url, '_blank');
              } else {
                  frappe.msgprint('Please enter a URL in the MSDS Document field.');
              }
          });
      }
  }
})