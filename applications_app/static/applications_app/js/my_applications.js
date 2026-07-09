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
  type = type || 'success';
  duration = duration || 3500;

  var wrap = document.getElementById('nm-toast-wrap');
  var t = document.createElement('div');
  t.className = 'nm-toast nm-toast-' + type;

 
  var svgs = {
    success: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',
    error: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
    info: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
    warning: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01"/></svg>'
  };

  t.innerHTML = 
    '<div class="nm-toast-icon">' + (svgs[type] || '') + '</div>' +
    '<div class="nm-toast-msg">' + msg + '</div>';

  wrap.appendChild(t);
  
  setTimeout(function () {
    t.style.animation = 'nmToastOut .3s ease forwards';
    setTimeout(function () { t.remove(); }, 300);
  }, duration);
}

/* ─────────────────────────────────────────
   Filter tabs
───────────────────────────────────────── */
window.nmAppTab = function (btn, filter) {
  document.querySelectorAll('#nm-tabs .nm-tab').forEach(function (b) {
    b.classList.remove('bg-brand-600', 'text-white', 'border-brand-600');
    b.classList.add('text-gray-500', 'bg-transparent');
  });
  btn.classList.remove('text-gray-500', 'bg-transparent');
  btn.classList.add('bg-brand-600', 'text-white', 'border-brand-600');

  document.querySelectorAll('#nm-app-list [data-status]').forEach(function (card) {
    card.style.display =
      (filter === 'all' || card.dataset.status === filter) ? '' : 'none';
  });
};

/* ─────────────────────────────────────────
   Card removal animation
───────────────────────────────────────── */
function nmRemoveCard(card) {
  if (!card) return;
  card.style.transition   = 'opacity .3s ease, transform .3s ease';
  card.style.opacity      = '0';
  card.style.transform    = 'translateX(28px)';
  setTimeout(function () {
    card.style.transition = 'max-height .3s ease, margin .3s ease, padding .3s ease';
    card.style.overflow   = 'hidden';
    card.style.maxHeight  = '0';
    card.style.margin     = '0';
    card.style.padding    = '0';
    setTimeout(function () { card.remove(); }, 320);
  }, 280);
}

/* ─────────────────────────────────────────
   Withdraw modal — open / close
───────────────────────────────────────── */
function nmOpenWithdrawModal(title, onConfirm) {
  document.getElementById('nm-withdraw-title').textContent =
    title ? '“' + title + '”' : '';

  var modal   = document.getElementById('nm-withdraw-modal');
  var confirm = document.getElementById('nm-withdraw-confirm');

  /* reset button state */
  confirm.textContent = 'Yes, Withdraw';
  confirm.disabled    = false;

  /* assign the specific confirm action for this call */
  confirm.onclick = function () { onConfirm(confirm); };

  modal.classList.add('open');
  setTimeout(function () { confirm.focus(); }, 60);
}

function nmCloseWithdraw() {
  document.getElementById('nm-withdraw-modal').classList.remove('open');
  var confirm      = document.getElementById('nm-withdraw-confirm');
  confirm.onclick  = null;
  confirm.textContent = 'Yes, Withdraw';
  confirm.disabled    = false;
}

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') nmCloseWithdraw();
});

/* ─────────────────────────────────────────
   Withdraw — demo mode  (no network)
───────────────────────────────────────── */
function nmWithdrawDemo(btn, title) {
  var card = btn.closest('[data-status]');

  nmOpenWithdrawModal(title, function (confirmBtn) {
    nmCloseWithdraw();
    nmRemoveCard(card);
    nmToast('Application withdrawn.', 'info');
  });
}

/* ─────────────────────────────────────────
   Timeline + stats sync after withdraw
───────────────────────────────────────── */
function nmRemoveTimelineEntry(pk) {
  var row = document.querySelector('[data-timeline-pk="' + pk + '"]');
  if (row) row.remove();

  var list = document.getElementById('nm-timeline-list');
  var section = document.getElementById('nm-timeline-section');
  if (list && section && !list.children.length) section.remove();
}

function nmUpdateStats(stats) {
  if (!stats) return;
  var fields = ['total', 'pending', 'accepted', 'rejected'];
  fields.forEach(function (key) {
    var stat = document.getElementById('nm-stat-' + key);
    var tab  = document.getElementById('nm-tab-' + key);
    if (stat) stat.textContent = stats[key];
    if (tab)  tab.textContent  = stats[key];
  });
}

/* ─────────────────────────────────────────
   Withdraw — real DB users
───────────────────────────────────────── */
function nmWithdraw(pk, btn) {
  var card    = btn.closest('[data-status]');
  var titleEl = card.querySelector('[data-card-title]');
  var title   = titleEl ? titleEl.textContent.trim() : '';

  nmOpenWithdrawModal(title, function (confirmBtn) {
    confirmBtn.textContent = '⏳ Withdrawing…';
    confirmBtn.disabled    = true;

    var csrf = getCookie('csrftoken');

    fetch('/applications/withdraw/' + pk + '/', {
      method:  'POST',
      headers: { 'X-CSRFToken': csrf || '' }
    })
      .then(function (r) {
        return r.json().then(function (data) { return { ok: r.ok, status: r.status, data: data }; });
      })
      .then(function (result) {
        nmCloseWithdraw();
        if (result.ok) {
          if (result.data.stats && result.data.stats.total === 0) {
            nmToast('Application withdrawn successfully.', 'info');
            setTimeout(function () { window.location.reload(); }, 500);
            return;
          }
          nmRemoveCard(card);
          nmRemoveTimelineEntry(pk);
          nmUpdateStats(result.data.stats);
          nmToast('Application withdrawn successfully.', 'info');
        } else {
          console.error('Withdraw failed:', result.status, result.data);
          nmToast('Could not withdraw — please try again.', 'error');
        }
      })
      .catch(function (err) {
        console.error('Withdraw network error:', err);
        nmCloseWithdraw();
        nmToast('Network error — check your connection.', 'error');
      });
  });
}

/* ─────────────────────────────────────────
   Download Agreement (demo card — no backing Application row)
───────────────────────────────────────── */
function nmDownloadAgreementDemo(btn, title) {
  var orig  = btn.innerHTML;
  btn.innerHTML = '⏳ Generating…';
  btn.disabled  = true;
  setTimeout(function () {
    btn.innerHTML = orig;
    btn.disabled  = false;
    nmToast('Agreement for “' + title + '” downloaded!', 'success');
  }, 1800);
}

/* ─────────────────────────────────────────
   Generate Agreement (real) — generates the agreement, then
   reloads so the server re-renders the card with a real
   "View & Sign Agreement" link, rather than jumping straight
   to a PDF download (the seeker needs to reach the view page
   to sign it, same as the poster-side flow).
───────────────────────────────────────── */
function nmDownloadAgreement(btn, title, applicationPk) {
  var orig = btn.innerHTML;
  btn.innerHTML = '⏳ Generating…';
  btn.disabled = true;

  var csrf = getCookie('csrftoken');
  fetch('/agreements/application/' + applicationPk + '/generate/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf || '' }
  })
    .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
    .then(function (result) {
      if (result.ok) {
        window.location.reload();
      } else {
        console.error('Agreement generation failed:', result.data);
        nmToast('Could not generate agreement — please try again.', 'error');
        btn.innerHTML = orig;
        btn.disabled = false;
      }
    })
    .catch(function (err) {
      console.error('Agreement network error:', err);
      nmToast('Network error — check your connection.', 'error');
      btn.innerHTML = orig;
      btn.disabled = false;
    });
}
