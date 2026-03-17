/**
 * Odoo Helpdesk Pre-fill Snippet
 *
 * HOW TO INSTALL:
 * 1. Log into mysticfoxxo.odoo.com
 * 2. Go to Website → Configuration → Settings
 * 3. Scroll down and paste this script into the <head> or <body> custom code section
 *    (Or: Website editor → Themes → Customize → HTML/JS Editor)
 * 4. Save
 *
 * This reads URL parameters (prefill_name, prefill_email, prefill_description)
 * and fills in the helpdesk form fields automatically.
 */
 <script>
  (function () {
    'use strict';
    function prefillHelpdeskForm() {
      var params = new URLSearchParams(window.location.search);
      var name = params.get('prefill_name');
      var email = params.get('prefill_email');
      var description = params.get('prefill_description');
      if (!name && !email && !description) return;
      var fieldMap = [
        { param: name, selectors: ['input[name="name"]', 'input[name="subject"]', 'input[name="ticket_name"]'] },
        { param: email, selectors: ['input[name="email"]', 'input[name="partner_email"]', 'input[name="email_from"]'] },
        { param: description, selectors: ['textarea[name="description"]', 'textarea[name="message"]',
  'textarea[name="ticket_description"]'] }
      ];
      fieldMap.forEach(function (entry) {
        if (!entry.param) return;
        for (var i = 0; i < entry.selectors.length; i++) {
          var el = document.querySelector(entry.selectors[i]);
          if (el) {
            el.value = entry.param;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new Event('blur', { bubbles: true }));
            break;
          }
        }
      });
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () {
        prefillHelpdeskForm();
        setTimeout(prefillHelpdeskForm, 1500);
        setTimeout(prefillHelpdeskForm, 3000);
      });
    } else {
      prefillHelpdeskForm();
      setTimeout(prefillHelpdeskForm, 1500);
      setTimeout(prefillHelpdeskForm, 3000);
    }
  })();
  </script>