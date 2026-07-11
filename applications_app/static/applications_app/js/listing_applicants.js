/* ─────────────────────────────────────────
   CSRF cookie helper (Django standard)
───────────────────────────────────────── */
function getCookie(name) {
  var value = '; ' + document.cookie;
  var parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

/* ─────────────────────────────────────────
   Toast
───────────────────────────────────────── */
function nmToast(msg, type, duration) {
  type     = type     || 'success';
  duration = duration || 3500;

  var wrap = document.getElementById('nm-toast-wrap');
  var t    = document.createElement('div');
  t.className = 'nm-toast nm-toast-' + type;

  var icons = { success: '✅', error: '❌', info: '💜' };
  t.innerHTML =
    '<span style="font-size:15px;flex-shrink:0">' + (icons[type] || '') + '</span>' +
    '<span style="flex:1">' + msg + '</span>';

  wrap.appendChild(t);
  setTimeout(function () {
    t.style.animation = 'nmToastOut .3s ease forwards';
    setTimeout(function () { t.remove(); }, 300);
  }, duration);
}

/* ─────────────────────────────────────────
   Stats sync after accept/reject
───────────────────────────────────────── */
function nmUpdateStats(stats) {
  if (!stats) return;
  ['total', 'pending', 'accepted', 'rejected'].forEach(function (key) {
    var el = document.getElementById('nm-stat-' + key);
    if (el) el.textContent = stats[key];
  });
}

/* ─────────────────────────────────────────
   Apply the decided state to a card in place
───────────────────────────────────────── */
function nmApplyDecision(card, status, label, badgeClass) {
  var badge = card.querySelector('[data-status-badge]');
  if (badge) {
    badge.className = 'inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold shrink-0 self-start ' + badgeClass;
    badge.textContent = label;
  }
  var actions = card.querySelector('[data-actions]');
  if (actions) actions.classList.add('hidden');

  var agreementActions = card.querySelector('[data-agreement-actions]');
  if (agreementActions && status === 'accepted') agreementActions.classList.remove('hidden');

  card.dataset.status = status;
}

/* ─────────────────────────────────────────
   Accept / Reject — shared request logic
───────────────────────────────────────── */
function nmDecide(pk, btn, action) {
  var card = btn.closest('[data-app-pk]');
  var actionsRow = card.querySelector('[data-actions]');
  var agreementActions = card.querySelector('[data-agreement-actions]');
  var buttons = actionsRow ? actionsRow.querySelectorAll('button') : [];
  buttons.forEach(function (b) { b.disabled = true; });

  var origText = btn.textContent;
  btn.textContent = action === 'accept' ? 'Accepting…' : 'Rejecting…';

  if (action === 'accept' && agreementActions) {
    agreementActions.classList.remove('hidden');
    agreementActions.innerHTML =
      '<button disabled class="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold text-brand-400 bg-brand-100 border border-brand-200 transition-colors cursor-not-allowed font-jakarta">' +
        '<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12a9 9 0 0118 0 9 9 0 01-18 0Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M7 12h10"/></svg>' +
        'Generating Agreement…' +
      '</button>';
  }

  var csrf = getCookie('csrftoken');

  fetch('/applications/application/' + pk + '/' + action + '/', {
    method:  'POST',
    headers: { 'X-CSRFToken': csrf || '' }
  })
    .then(function (r) {
      return r.json().then(function (data) { return { ok: r.ok, status: r.status, data: data }; });
    })
    .then(function (result) {
      if (result.ok) {
        if (action === 'accept') {
          nmApplyDecision(card, 'accepted', 'Accepted', 'bg-emerald-100 text-emerald-700');
          nmToast('Applicant accepted.', 'success');
          if (agreementActions) {
            if (result.data.agreement_id) {
              agreementActions.innerHTML =
                '<a href="' + result.data.view_url + '" class="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold text-brand-700 bg-brand-50 border border-brand-200 hover:bg-brand-100 transition-colors">' +
                  '<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m5.231 13.481L15 17.25m-1.519-2.121L10.5 18.5m0 0-2.121-2.121M10.5 18.5V15m9-9v13.5A2.25 2.25 0 0 1 17.25 21H6.75A2.25 2.25 0 0 1 4.5 18.75V5.25A2.25 2.25 0 0 1 6.75 3h6.879a1.5 1.5 0 0 1 1.06.44l4.243 4.242a1.5 1.5 0 0 1 .44 1.061Z"/></svg>' +
                  'View Agreement' +
                '</a>';
            } else {
              agreementActions.innerHTML =
                '<button onclick="nmGenerateAgreement(' + pk + ', this)" class="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold text-brand-700 bg-brand-50 border border-brand-200 hover:bg-brand-100 transition-colors cursor-pointer font-jakarta">' +
                  '<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z"/></svg>' +
                  'Generate Agreement' +
                '</button>';
            }
          }
        } else {
          nmApplyDecision(card, 'rejected', 'Rejected', 'bg-rose-100 text-rose-600');
          nmToast('Applicant rejected.', 'info');
        }
        nmUpdateStats(result.data.stats);
      } else {
        console.error('Decision failed:', result.status, result.data);
        nmToast('Could not update applicant — please try again.', 'error');
        buttons.forEach(function (b) { b.disabled = false; });
        btn.textContent = origText;
        if (agreementActions) {
          agreementActions.classList.add('hidden');
        }
      }
    })
    .catch(function (err) {
      console.error('Decision network error:', err);
      nmToast('Network error — check your connection.', 'error');
      buttons.forEach(function (b) { b.disabled = false; });
      btn.textContent = origText;
      if (agreementActions) {
        agreementActions.classList.add('hidden');
      }
    });
}

function nmAccept(pk, btn) { nmDecide(pk, btn, 'accept'); }
function nmReject(pk, btn) { nmDecide(pk, btn, 'reject'); }

/* ─────────────────────────────────────────
   Generate Agreement — reload so the server
   re-renders the card with the real "View
   Agreement" link, rather than hand-building
   that markup here.
───────────────────────────────────────── */
function nmGenerateAgreement(pk, btn) {
  btn.textContent = 'Generating…';
  btn.disabled = true;
  var csrf = getCookie('csrftoken');

  fetch('/agreements/application/' + pk + '/generate/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf || '' }
  })
    .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
    .then(function (result) {
      if (result.ok) {
        window.location.reload();
      } else {
        console.error('Agreement generation failed:', result.status, result.data);
        nmToast('Could not generate agreement — please try again.', 'error');
        btn.textContent = '✨ Generate Agreement';
        btn.disabled = false;
      }
    })
    .catch(function (err) {
      console.error('Agreement network error:', err);
      nmToast('Network error — check your connection.', 'error');
      btn.textContent = '✨ Generate Agreement';
      btn.disabled = false;
    });
}
