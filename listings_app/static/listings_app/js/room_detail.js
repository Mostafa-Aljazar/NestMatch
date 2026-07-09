/* ─────────────────────────────────────────────────────────
   room_detail.js  —  NestMatch room detail page
   Expects window.NM (config object) injected inline by the
   Django template before this script loads.
───────────────────────────────────────────────────────── */

/* ── LIGHTBOX ─────────────────────────────────────────── */
var _nmLbSwiper = null;

function nmLbOpen(i) {
  var el = document.getElementById('nm-lb');
  if (!el) return;
  el.classList.add('open');
  document.body.style.overflow = 'hidden';

  if (!_nmLbSwiper) {
    _nmLbSwiper = new Swiper('#nm-lb-swiper', {
      initialSlide: i,
      loop: true,
      speed: 380,
      grabCursor: true,
      zoom: { maxRatio: 4, minRatio: 1 },
      keyboard: { enabled: true },
      pagination: {
        el: '.nm-lb-swiper-wrap .swiper-pagination',
        clickable: true,
        dynamicBullets: false
      },
      navigation: {
        nextEl: '.nm-lb-swiper-wrap .swiper-button-next',
        prevEl: '.nm-lb-swiper-wrap .swiper-button-prev'
      },
      on: {
        slideChange: function (s) { nmLbCount(s.realIndex); }
      }
    });

    /* zoom hint — mobile only */
    var hint = document.getElementById('nm-lb-zoom-hint');
    if (hint) {
      if ('ontouchstart' in window) {
        setTimeout(function () { hint.classList.add('hide'); }, 2200);
      } else {
        hint.style.display = 'none';
      }
    }
  } else {
    _nmLbSwiper.slideToLoop(i, 0);
  }

  nmLbCount(i);
}

function nmLbCount(i) {
  var total = window.NM ? parseInt(window.NM.imageCount, 10) || 0 : 0;
  var el = document.getElementById('nm-lb-count');
  if (el) el.textContent = (i + 1) + ' / ' + total;
}

function nmLbClose() {
  var el = document.getElementById('nm-lb');
  if (el) el.classList.remove('open');
  document.body.style.overflow = '';
}

/* keyboard nav */
document.addEventListener('keydown', function (e) {
  var lb = document.getElementById('nm-lb');
  if (!lb || !lb.classList.contains('open')) return;
  if (e.key === 'Escape') nmLbClose();
});

/* close on tap outside image */
(function () {
  var lb = document.getElementById('nm-lb');
  if (!lb) return;
  lb.addEventListener('click', function (e) {
    var t = e.target;
    if (t === lb) { nmLbClose(); return; }
    if (t.classList.contains('swiper-slide') ||
        t.classList.contains('swiper-zoom-container')) {
      nmLbClose();
    }
  });
})();


/* ── MOBILE GALLERY SWIPER ────────────────────────────── */
(function () {
  if (!document.getElementById('nm-mob-swiper')) return;
  var mobSwiper = new Swiper('#nm-mob-swiper', {
    loop: true,
    speed: 500,
    grabCursor: true,
    autoplay: {
      delay: 3500,
      disableOnInteraction: false,
      pauseOnMouseEnter: true
    },
    pagination: {
      el: '#nm-mob-swiper .swiper-pagination',
      clickable: true,
      dynamicBullets: false
    },
    keyboard: { enabled: true },
    a11y: { enabled: true }
  });

  var prevBtn = document.getElementById('nm-mob-prev');
  var nextBtn = document.getElementById('nm-mob-next');
  if (prevBtn) prevBtn.addEventListener('click', function () { mobSwiper.slidePrev(); });
  if (nextBtn) nextBtn.addEventListener('click', function () { mobSwiper.slideNext(); });
})();


/* ── LEAFLET MAP ──────────────────────────────────────── */
(function () {
  var el = document.getElementById('nm-detail-map');
  if (!el || typeof L === 'undefined') return;

  var popup    = document.getElementById('nm-map-popup');
  var lat      = parseFloat(el.dataset.lat);
  var lng      = parseFloat(el.dataset.lng);
  var city     = el.dataset.city     || '';
  var district = el.dataset.district || '';
  var country  = el.dataset.country  || '';
  var hasPin   = !isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0;

  var pinIcon = L.divIcon({
    className: '',
    html: '<div style="width:36px;height:36px;background:var(--brand-600);border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:3px solid #fff;box-shadow:0 2px 8px rgba(124,58,237,.5)"></div>',
    iconSize: [36, 36],
    iconAnchor: [18, 36]
  });

  var approxIcon = L.divIcon({
    className: '',
    html: '<div style="width:44px;height:44px;background:rgba(124,58,237,.18);border:2.5px dashed var(--brand-600);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:20px">📍</div>',
    iconSize: [44, 44],
    iconAnchor: [22, 22]
  });

  function initMap(clat, clng, exact) {
    var zoom = exact ? 15 : 12;
    var map = L.map('nm-detail-map', {
      zoomControl: true,
      scrollWheelZoom: false
    }).setView([clat, clng], zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
      maxZoom: 19
    }).addTo(map);

    var popupHtml = popup ? popup.innerHTML : '';
    if (!exact) {
      popupHtml += '<div style="margin-top:8px;font-size:11px;color:#9CA3AF;font-style:italic">📌 Approximate location — exact pin not set</div>';
    }
    L.marker([clat, clng], { icon: exact ? pinIcon : approxIcon })
      .addTo(map)
      .bindPopup(popupHtml, { maxWidth: 280 })
      .openPopup();
  }

  if (hasPin) {
    initMap(lat, lng, true);
  } else {
    var q = [district, city, country].filter(Boolean).join(', ');
    fetch('https://nominatim.openstreetmap.org/search?q=' + encodeURIComponent(q) + '&format=json&limit=1', {
      headers: { 'Accept-Language': 'en' }
    })
      .then(function (r) { return r.json(); })
      .then(function (results) {
        if (results && results.length) {
          initMap(parseFloat(results[0].lat), parseFloat(results[0].lon), false);
        } else {
          initMap(30.0444, 31.2357, false);
        }
      })
      .catch(function () {
        initMap(30.0444, 31.2357, false);
      });
  }
})();

 
/* ── APPLY MODAL ──────────────────────────────────────── */
function nmOpenModal() {
  var banner = document.getElementById('nm-verify-required-banner');
  var msgBox = document.getElementById('nm-apply-msg');
  var sendBtn = document.getElementById('nm-apply-btn');
  if (banner) banner.classList.add('hidden');
  if (msgBox) msgBox.closest('.mb-4').classList.remove('hidden');
  if (sendBtn) sendBtn.classList.remove('hidden');

  document.getElementById('nm-apply-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function nmCloseModal() {
  document.getElementById('nm-apply-modal').classList.remove('open');
  document.body.style.overflow = '';
}

function nmGetCookie(name) {
  var value = '; ' + document.cookie;
  var parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function nmSubmitApply() {
  var msg = document.getElementById('nm-apply-msg');
  if (msg && !msg.value.trim()) {
    msg.style.borderColor = '#E11D48';
    msg.focus();
    return;
  } 
  var btn = document.getElementById('nm-apply-btn');
  if (btn) {
    btn.textContent = 'Sending…';
    btn.disabled = true;
    btn.style.opacity = '.8';
  }

  var csrf = nmGetCookie('csrftoken');

  fetch(window.NM.applyUrl, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrf || '',
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: 'message=' + encodeURIComponent(msg ? msg.value.trim() : '')
  })
    .then(function (r) {
      return r.json().then(function (data) { return { ok: r.ok, data: data }; });
    })
    .then(function (result) {
      if (btn) {
        btn.textContent = 'Send Application ✈️';
        btn.disabled = false;
        btn.style.opacity = '1';
      }
      if (result.ok) {
        nmCloseModal();
        nmShowToast(null, null);   /* uses default toast state */
        if (msg) msg.value = '';

        var applyNowBtn = document.getElementById('nm-apply-now-btn');
        if (applyNowBtn) {
          var appId = result.data.application_id;
          var cancelBtn = document.createElement('button');
          cancelBtn.id = 'nm-cancel-apply-btn';
          cancelBtn.className = 'block w-full py-3.5 text-sm font-bold text-white bg-rose-600 border-none rounded-xl cursor-pointer text-center transition-all hover:bg-rose-700 active:scale-[.98] font-sans mb-2.5';
          cancelBtn.textContent = 'Cancel Application ✕';
          cancelBtn.addEventListener('click', function () { nmCancelApply(appId, cancelBtn); });
          applyNowBtn.replaceWith(cancelBtn);
        }
       } else if (result.data.code === 'id_not_verified') {
        var banner = document.getElementById('nm-verify-required-banner');
        var titleEl = document.getElementById('nm-verify-required-title');
        var textEl = document.getElementById('nm-verify-required-text');
        var msgBox = document.getElementById('nm-apply-msg');
        var sendBtn = document.getElementById('nm-apply-btn');

        if (result.data.id_status === 'pending') {
          if (titleEl) titleEl.textContent = 'ID verification pending';
          if (textEl) textEl.textContent = "Your ID is under review by our team. You'll be able to apply once it's approved.";
        } else if (result.data.id_status === 'rejected') {
          if (titleEl) titleEl.textContent = 'ID verification rejected';
          if (textEl) textEl.textContent = 'Your ID submission was rejected. Please resubmit a valid document.';
        } else {
          if (titleEl) titleEl.textContent = 'Verify your ID to apply';
          if (textEl) textEl.textContent = 'You need to verify your identity before applying to a room.';
        }

        if (banner) banner.classList.remove('hidden');
        if (msgBox) msgBox.closest('.mb-4').classList.add('hidden');
        if (sendBtn) sendBtn.classList.add('hidden');
      } else {
        nmShowToast('#E11D48', result.data.error || 'Could not send application.');
      }
    })
    .catch(function (err) {
      console.error('Apply network error:', err);
      if (btn) {
        btn.textContent = 'Send Application ✈️';
        btn.disabled = false;
        btn.style.opacity = '1';
      }
      nmShowToast('#E11D48', 'Network error — please try again.');
    });
}

function nmCancelApply(appPk, btn) {
  if (btn) {
    btn.disabled = true;
    btn.style.opacity = '.8';
    btn.textContent = 'Cancelling…';
  }

  var csrf = nmGetCookie('csrftoken');

  fetch('/applications/withdraw/' + appPk + '/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf || '' }
  })
    .then(function (r) {
      return r.json().then(function (data) { return { ok: r.ok, data: data }; });
    })
    .then(function (result) {
      if (result.ok) {
        nmShowToast('#374151', 'Application cancelled.');
        if (btn) {
          var applyNowBtn = document.createElement('button');
          applyNowBtn.id = 'nm-apply-now-btn';
          applyNowBtn.className = 'block w-full py-3.5 text-sm font-bold text-white bg-violet-700 border-none rounded-xl cursor-pointer text-center transition-all hover:bg-violet-800 active:scale-[.98] font-sans mb-2.5';
          applyNowBtn.textContent = 'Apply Now ';
          applyNowBtn.addEventListener('click', function () { nmOpenModal(); });
          btn.replaceWith(applyNowBtn);
        }
      } else {
        if (btn) {
          btn.disabled = false;
          btn.style.opacity = '1';
          btn.textContent = 'Cancel Application ✕';
        }
        nmShowToast('#E11D48', result.data.error || 'Could not cancel application.');
      }
    })
    .catch(function (err) {
      console.error('Cancel application network error:', err);
      if (btn) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.textContent = 'Cancel Application ✕';
      }
      nmShowToast('#E11D48', 'Network error — please try again.');
    });
}

/* close modal on backdrop click */
(function () {
  var modal = document.getElementById('nm-apply-modal');
  if (!modal) return;
  modal.addEventListener('click', function (e) {
    if (e.target === this) nmCloseModal();
  });
})();


/* ── TOAST ────────────────────────────────────────────── */
function nmShowToast(bg, text) {
  var t = document.getElementById('nm-toast');
  if (!t) return;
  if (bg)   t.style.background = bg;
  if (text) t.textContent = text;
  t.classList.add('show');
  setTimeout(function () { t.classList.remove('show'); }, 4500);
}


/* ── SHARE ────────────────────────────────────────────── */
function nmShare() {
  var title = (window.NM && window.NM.title) ? window.NM.title : document.title;
  var url   = window.location.href;
  if (navigator.share) {
    navigator.share({ title: title, url: url });
  } else {
    navigator.clipboard.writeText(url).then(function () {
      var t = document.getElementById('nm-toast');
      if (!t) return;
      var origBg   = t.style.background;
      var origText = t.textContent;
      t.style.background = '#374151';
      t.textContent = 'Link copied to clipboard!';
      t.classList.add('show');
      setTimeout(function () {
        t.classList.remove('show');
        t.style.background = origBg;
        t.textContent = origText;
      }, 3000);
    });
  }
}


/* ── REVIEW STAR PICKER ──────────────────────────────────── */
function nmSetRating(val) {
  var input = document.getElementById('nm-rating-input');
  if (input) input.value = val;
  document.querySelectorAll('#nm-star-picker .nm-star-btn').forEach(function (star) {
    var starVal = parseInt(star.dataset.val, 10);
    star.style.color = starVal <= val ? '#F59E0B' : '#D1D5DB';
  });
}
