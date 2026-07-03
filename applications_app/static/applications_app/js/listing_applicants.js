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

  card.dataset.status = status;
}

/* ─────────────────────────────────────────
   Accept / Reject — shared request logic
───────────────────────────────────────── */
function nmDecide(pk, btn, action) {
  var card = btn.closest('[data-app-pk]');
  var actionsRow = card.querySelector('[data-actions]');
  var buttons = actionsRow ? actionsRow.querySelectorAll('button') : [];
  buttons.forEach(function (b) { b.disabled = true; });

  var origText = btn.textContent;
  btn.textContent = action === 'accept' ? 'Accepting…' : 'Rejecting…';

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
      }
    })
    .catch(function (err) {
      console.error('Decision network error:', err);
      nmToast('Network error — check your connection.', 'error');
      buttons.forEach(function (b) { b.disabled = false; });
      btn.textContent = origText;
    });
}

function nmAccept(pk, btn) { nmDecide(pk, btn, 'accept'); }
function nmReject(pk, btn) { nmDecide(pk, btn, 'reject'); }
