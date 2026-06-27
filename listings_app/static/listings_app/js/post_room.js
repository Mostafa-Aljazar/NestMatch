/* post_room.js — Post a Room wizard logic */

window._parStep = 1;

function parStep(s) {
  if (s < 1 || s > 4) return;
  window._parStep = s;
  for (var i = 1; i <= 4; i++) {
    var el = document.getElementById('par-s' + i);
    if (el) { el.classList.toggle('hidden', i !== s); }
  }
  var hints = ['Basic Information', 'Title & Location', 'Photos & Description', 'Requirements & Publish'];
  var lbl = document.getElementById('nm-step-hint');
  if (lbl) lbl.textContent = 'Step ' + s + ' of 4 — ' + hints[s - 1];
  var stepLabels = ['Basic Info', 'Location', 'Photos', 'Requirements'];
  for (var i = 1; i <= 4; i++) {
    var num = document.getElementById('ps' + i + '-num');
    var lbl = document.getElementById('ps' + i + '-lbl');
    if (!num || !lbl) continue;
    var row   = num.parentElement;
    var lineL = row.children[0];
    var lineR = row.children[2];
    if (i < s) {
      num.className = 'w-7 h-7 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[11px] font-extrabold shrink-0 z-10';
      num.textContent = '✓';
      lineL.className = 'flex-1 h-0.5 bg-emerald-300';
      lineR.className = 'flex-1 h-0.5 bg-emerald-300';
      lbl.className   = 'text-[11px] font-bold text-emerald-600 text-center leading-tight';
    } else if (i === s) {
      num.className = 'w-7 h-7 rounded-full bg-violet-600 text-white flex items-center justify-center text-[11px] font-extrabold shrink-0 shadow-sm shadow-violet-200 z-10';
      num.textContent = i;
      lineL.className = i === 1 ? 'flex-1 h-0.5 bg-transparent' : 'flex-1 h-0.5 bg-emerald-300';
      lineR.className = i === 4 ? 'flex-1 h-0.5 bg-transparent' : 'flex-1 h-0.5 bg-gray-200';
      lbl.className   = 'text-[11px] font-bold text-violet-600 text-center leading-tight';
    } else {
      num.className = 'w-7 h-7 rounded-full bg-white text-gray-400 flex items-center justify-center text-[11px] font-extrabold shrink-0 border-2 border-gray-200 z-10';
      num.textContent = i;
      lineL.className = i === 1 ? 'flex-1 h-0.5 bg-transparent' : 'flex-1 h-0.5 bg-gray-200';
      lineR.className = i === 4 ? 'flex-1 h-0.5 bg-transparent' : 'flex-1 h-0.5 bg-gray-200';
      lbl.className   = 'text-[11px] font-medium text-gray-400 text-center leading-tight';
    }
  }
  var back = document.getElementById('par-back');
  var next = document.getElementById('par-next');
  if (back) back.classList.toggle('hidden', s <= 1);
  if (next) { next.textContent = s === 4 ? 'Publish Listing ✅' : 'Continue →'; next.classList.toggle('hidden', s === 4); }
}

// Listing Type: single-select with toggle (click selected card to deselect)
function parPickType(el) {
  var isSelected = el.classList.contains('sel');
  el.parentElement.querySelectorAll('.nm-type-card').forEach(function(c) { c.classList.remove('sel'); });
  if (!isSelected) el.classList.add('sel');
}

// Who Is This For: multi-select with toggle
function parPickTenant(el) {
  el.classList.toggle('sel');
}

var _parOcc = 3;
function parChangeOcc(d) {
  _parOcc = Math.max(1, Math.min(20, _parOcc + d));
  var el = document.getElementById('par-occ');
  if (el) el.textContent = _parOcc;
}

function parUpdateTitleCount(inp) {
  var count = document.getElementById('par-title-count');
  if (!count) return;
  var len = inp.value.length;
  count.textContent = len + ' / 80';
  count.style.color = len > 80 ? '#EF4444' : len > 60 ? '#D97706' : '#9CA3AF';
  inp.style.borderColor = len > 80 ? '#EF4444' : '';
}

function parFeatureCheck(cb) {
  var label = cb.closest('label');
  if (!label) return;
  if (cb.checked) {
    label.style.borderColor = '#7C3AED';
    label.style.background  = '#F5F3FF';
    label.style.color       = '#7C3AED';
  } else {
    label.style.borderColor = '#E5E7EB';
    label.style.background  = '';
    label.style.color       = '#374151';
  }
}

function parFeatureLeave(label) {
  var cb = label.querySelector('input[type=checkbox]');
  if (cb && cb.checked) return;
  label.style.borderColor = '#E5E7EB';
}

function parGenerateAI() {
  var btn = document.getElementById('nm-ai-btn');
  if (btn) { btn.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite;font-size:14px">⏳</span> Generating...'; btn.disabled = true; }
  setTimeout(function() {
    var ta = document.getElementById('nm-desc-ta');
    if (ta) {
      ta.value = 'A bright, fully-furnished private room in a well-maintained 3-bedroom apartment. The room features a comfortable single bed, built-in wardrobe, study desk, and individual A/C unit. Shared spaces include a modern kitchen, spacious living room, and two clean bathrooms.\n\nLocated on the 4th floor with elevator access in a quiet residential building in Nasr City, just 5 minutes walk from Ain Shams University metro station. Ideal for university students or working professionals seeking a clean, peaceful environment.\n\nUtilities (water, electricity, internet) are included in the monthly rent.';
      ta.style.borderColor = '#7C3AED';
      ta.style.boxShadow   = '0 0 0 3px rgba(124,58,237,.12)';
    }
    var badge = document.getElementById('nm-ai-badge');
    if (badge) badge.classList.remove('hidden');
    if (btn) { btn.innerHTML = '<span>✨</span> Generate with AI'; btn.disabled = false; }
  }, 2000);
}

// Navbar scroll shadow
var nav = document.getElementById('nm-nav');
if (nav) {
  window.addEventListener('scroll', function() {
    nav.style.boxShadow = window.scrollY > 10 ? '0 4px 20px rgba(0,0,0,.1)' : 'none';
  }, { passive: true });
}

function nmToggleMenu() {
  document.getElementById('nm-mm')?.classList.toggle('nm-open');
  document.getElementById('nm-hbg')?.classList.toggle('nm-open');
}

// ── Landmark Autocomplete ─────────────────────────────────
var _landmarkTimer = null;
var _landmarkActive = -1;

function parLandmarkSearch(q) {
  clearTimeout(_landmarkTimer);
  var dd = document.getElementById('nm-landmark-dropdown');
  if (!q || q.length < 2) { dd.classList.add('hidden'); return; }
  _landmarkTimer = setTimeout(function() {
    var lat = document.getElementById('nm-lat').value || '30.0444';
    var lng = document.getElementById('nm-lng').value || '31.2357';
    var url = 'https://nominatim.openstreetmap.org/search?q='
      + encodeURIComponent(q)
      + '&format=json&limit=6&addressdetails=1'
      + '&viewbox=' + (parseFloat(lng)-0.3) + ',' + (parseFloat(lat)+0.3) + ',' + (parseFloat(lng)+0.3) + ',' + (parseFloat(lat)-0.3)
      + '&bounded=0';
    fetch(url)
      .then(function(r){ return r.json(); })
      .then(function(results){
        dd.innerHTML = '';
        _landmarkActive = -1;
        if (!results.length) {
          dd.innerHTML = '<div class="px-4 py-3 text-[13px] text-gray-400">No results found</div>';
          dd.classList.remove('hidden');
          return;
        }
        results.forEach(function(r, i) {
          var item = document.createElement('div');
          item.style.cssText = 'padding:10px 14px;font-size:13px;color:#111827;cursor:pointer;border-bottom:1px solid #F3F4F6;display:flex;align-items:center;gap:10px';
          var icon = r.type === 'mosque' ? '🕌'
            : r.type === 'university' || r.type === 'college' ? '🎓'
            : r.type === 'hospital'   || r.type === 'clinic'  ? '🏥'
            : r.type === 'school'     ? '🏫'
            : r.type === 'station'    || r.category === 'railway' ? '🚉'
            : r.type === 'bus_stop'   ? '🚌'
            : r.type === 'mall'       || r.type === 'supermarket' ? '🛒'
            : r.type === 'park'       ? '🌳'
            : r.type === 'pharmacy'   ? '💊'
            : r.type === 'bank'       ? '🏦'
            : '📍';
          var name = r.namedetails && r.namedetails.name ? r.namedetails.name : r.display_name.split(',')[0];
          var sub  = r.display_name.split(',').slice(1,3).join(',').trim();
          item.innerHTML = '<span style="font-size:16px;flex-shrink:0">'+icon+'</span>'
            + '<div><div style="font-weight:600;color:#111827">'+name+'</div>'
            + (sub ? '<div style="font-size:11px;color:#9CA3AF;margin-top:1px">'+sub+'</div>' : '')
            + '</div>';
          item.onmouseenter = function(){ parLandmarkHighlight(i); };
          item.onclick = function(){
            document.getElementById('nm-field-landmark').value = name;
            dd.classList.add('hidden');
          };
          dd.appendChild(item);
        });
        dd.classList.remove('hidden');
      }).catch(function(){ dd.classList.add('hidden'); });
  }, 350);
}

function parLandmarkHighlight(idx) {
  var items = document.getElementById('nm-landmark-dropdown').children;
  Array.from(items).forEach(function(el, i){
    el.style.background = i === idx ? '#F5F3FF' : '';
    el.style.color      = i === idx ? '#7C3AED' : '#111827';
  });
  _landmarkActive = idx;
}

function parLandmarkKey(e) {
  var dd = document.getElementById('nm-landmark-dropdown');
  if (dd.classList.contains('hidden')) return;
  var items = dd.children;
  if (e.key === 'ArrowDown')                    { e.preventDefault(); parLandmarkHighlight(Math.min(_landmarkActive+1, items.length-1)); }
  else if (e.key === 'ArrowUp')                 { e.preventDefault(); parLandmarkHighlight(Math.max(_landmarkActive-1, 0)); }
  else if (e.key === 'Enter' && _landmarkActive >= 0) { e.preventDefault(); items[_landmarkActive].click(); }
  else if (e.key === 'Escape')                  { dd.classList.add('hidden'); }
}

document.addEventListener('click', function(e) {
  var dd  = document.getElementById('nm-landmark-dropdown');
  var inp = document.getElementById('nm-field-landmark');
  if (dd && inp && !dd.contains(e.target) && e.target !== inp) dd.classList.add('hidden');
});

// ── Leaflet Map ───────────────────────────────────────────
var _map    = null;
var _marker = null;

function parInitMap() {
  if (_map) return;
  _map = L.map('nm-map', { zoomControl: true }).setView([30.0444, 31.2357], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
    maxZoom: 19
  }).addTo(_map);

  var pinIcon = L.divIcon({
    className: '',
    html: '<div style="font-size:32px;line-height:1;filter:drop-shadow(0 2px 4px rgba(0,0,0,.3))">📍</div>',
    iconSize: [32, 32], iconAnchor: [16, 32]
  });

  _map.on('click', function(e) {
    parSetPin(e.latlng.lat, e.latlng.lng, null, pinIcon);
  });
}

function parSetPin(lat, lng, label, icon) {
  if (_marker) _map.removeLayer(_marker);
  icon = icon || L.divIcon({
    className: '',
    html: '<div style="font-size:32px;line-height:1;filter:drop-shadow(0 2px 4px rgba(0,0,0,.3))">📍</div>',
    iconSize: [32, 32], iconAnchor: [16, 32]
  });
  _marker = L.marker([lat, lng], { icon: icon, draggable: true }).addTo(_map);
  _map.setView([lat, lng], 16);

  _marker.on('dragend', function(e) {
    var pos = e.target.getLatLng();
    parReverseGeocode(pos.lat, pos.lng);
    document.getElementById('nm-lat').value = pos.lat.toFixed(6);
    document.getElementById('nm-lng').value = pos.lng.toFixed(6);
  });

  document.getElementById('nm-lat').value = lat.toFixed(6);
  document.getElementById('nm-lng').value = lng.toFixed(6);

  var info   = document.getElementById('nm-map-info');
  var coords = document.getElementById('nm-map-coords');
  if (info)   info.classList.remove('hidden');
  if (coords) coords.textContent = '(' + lat.toFixed(5) + ', ' + lng.toFixed(5) + ')';

  if (label) {
    var addr = document.getElementById('nm-map-address');
    if (addr) addr.textContent = label;
  } else {
    parReverseGeocode(lat, lng);
  }
}

function parReverseGeocode(lat, lng) {
  fetch('https://nominatim.openstreetmap.org/reverse?lat='+lat+'&lon='+lng+'&format=json&addressdetails=1')
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (!d || !d.address) return;
      var a = d.address;
      function setField(id, val) {
        var el = document.getElementById(id);
        if (el && val) el.value = val;
      }
      setField('nm-field-country',  a.country);
      setField('nm-field-city',     a.city || a.town || a.village || a.municipality);
      setField('nm-field-district', a.suburb || a.neighbourhood || a.quarter || a.district);
      setField('nm-field-street',   a.road || a.pedestrian || a.footway);
      var parts = [];
      if (a.house_number) parts.push(a.house_number);
      if (a.road)         parts.push(a.road);
      if (a.suburb || a.neighbourhood) parts.push(a.suburb || a.neighbourhood);
      if (a.city || a.town || a.village) parts.push(a.city || a.town || a.village);
      if (a.country)      parts.push(a.country);
      setField('nm-field-address', parts.join(', '));
      var addrEl = document.getElementById('nm-map-address');
      if (addrEl) addrEl.textContent = d.display_name;
      var coords = document.getElementById('nm-map-coords');
      if (coords) coords.textContent = '(' + parseFloat(lat).toFixed(5) + ', ' + parseFloat(lng).toFixed(5) + ')';
    }).catch(function(){});
}

function parMapSearch() {
  var q   = document.getElementById('nm-map-search').value.trim();
  if (!q) return;
  var btn = document.querySelector('#nm-map-search + button');
  if (btn) { btn.textContent = '...'; btn.disabled = true; }
  fetch('https://nominatim.openstreetmap.org/search?q='+encodeURIComponent(q)+'&format=json&limit=1')
    .then(function(r){ return r.json(); })
    .then(function(results){
      if (btn) { btn.textContent = 'Search'; btn.disabled = false; }
      if (!results || !results.length) { alert('Location not found. Try a more specific address.'); return; }
      parSetPin(parseFloat(results[0].lat), parseFloat(results[0].lon), results[0].display_name);
    })
    .catch(function(){
      if (btn) { btn.textContent = 'Search'; btn.disabled = false; }
      alert('Search failed. Check your connection.');
    });
}

function parMapLocate() {
  if (!navigator.geolocation) { alert('Geolocation is not supported by your browser.'); return; }
  navigator.geolocation.getCurrentPosition(
    function(pos) { parSetPin(pos.coords.latitude, pos.coords.longitude, null); },
    function()    { alert('Could not get your location. Please allow location access.'); }
  );
}

// Init map when step 2 becomes visible
var _origParStep = parStep;
parStep = function(s) {
  _origParStep(s);
  if (s === 2) { setTimeout(parInitMap, 100); }
};

// ── Photo upload ──────────────────────────────────────────
var _photos = [];

function parHandleFiles(files) {
  for (var i = 0; i < files.length; i++) {
    if (_photos.length >= 10) { alert('Maximum 10 photos allowed.'); break; }
    var file = files[i];
    if (!file.type.match('image.*')) continue;
    if (file.size > 10 * 1024 * 1024) { alert(file.name + ' exceeds 10MB limit.'); continue; }
    (function(f) {
      var reader = new FileReader();
      reader.onload = function(e) {
        _photos.push({ name: f.name, src: e.target.result });
        parRenderPreviews();
      };
      reader.readAsDataURL(f);
    })(file);
  }
}

function parRenderPreviews() {
  var list  = document.getElementById('nm-preview-list');
  var count = document.getElementById('nm-photo-count');
  if (!list) return;
  list.innerHTML = '';
  _photos.forEach(function(p, idx) {
    var div = document.createElement('div');
    div.style.cssText = 'width:72px;height:72px;border-radius:10px;position:relative;overflow:hidden;flex-shrink:0;animation:fadeUp .25s ease both';
    div.innerHTML = '<img src="'+p.src+'" style="width:100%;height:100%;object-fit:cover" alt="">'
      + '<div onclick="parRemovePhoto('+idx+')" style="position:absolute;top:3px;right:3px;width:18px;height:18px;background:rgba(239,68,68,.9);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff;cursor:pointer;line-height:1">✕</div>';
    list.appendChild(div);
  });
  if (_photos.length < 10) {
    var add = document.createElement('div');
    add.onclick = function(){ document.getElementById('nm-file-input').click(); };
    add.style.cssText = 'width:72px;height:72px;border-radius:10px;background:#F3F4F6;display:flex;align-items:center;justify-content:center;font-size:22px;border:2px dashed #E5E7EB;cursor:pointer;color:#9CA3AF;flex-shrink:0';
    add.textContent = '+';
    list.appendChild(add);
  }
  if (count) { count.classList.remove('hidden'); count.textContent = _photos.length + ' / 10 photos added'; }
}

function parRemovePhoto(idx) {
  _photos.splice(idx, 1);
  parRenderPreviews();
  if (_photos.length === 0) {
    var count = document.getElementById('nm-photo-count');
    if (count) count.classList.add('hidden');
  }
}

function parDragOver(e) {
  e.preventDefault();
  var z = document.getElementById('nm-dropzone');
  if (z) { z.style.borderColor = '#7C3AED'; z.style.background = '#F5F3FF'; }
}

function parDragLeave(e) {
  var z = document.getElementById('nm-dropzone');
  if (z) { z.style.borderColor = '#DDD6FE'; z.style.background = '#FAF5FF'; }
}

function parDrop(e) {
  e.preventDefault();
  parDragLeave(e);
  parHandleFiles(e.dataTransfer.files);
}

// ── Custom Requirements ───────────────────────────────────
var _customCount  = 0;
var _emojiOptions = ['✅','🚫','⭐','🏠','🔑','📌','💬','🎯','⚠️','🙏','👍','🛑','📎','🔔','💡'];

function parAddCustom() {
  _customCount++;
  var id    = 'custom-' + _customCount;
  var list  = document.getElementById('nm-custom-list');
  var empty = document.getElementById('nm-custom-empty');
  if (empty) empty.style.display = 'none';

  var row = document.createElement('div');
  row.id  = id;
  row.style.cssText = 'display:flex;align-items:center;gap:10px;background:#F9FAFB;border:1.5px solid #E5E7EB;border-radius:10px;padding:12px 14px;animation:fadeUp .3s ease both';
  row.innerHTML = '<select onchange="parCustomEmoji(this)" style="font-size:18px;border:none;background:transparent;cursor:pointer;padding:2px;outline:none;flex-shrink:0">'
    + _emojiOptions.map(function(e){ return '<option value="'+e+'">'+e+'</option>'; }).join('')
    + '</select>'
    + '<input type="text" placeholder="e.g. Must water the plants on Fridays" style="flex:1;border:none;background:transparent;font-size:14px;font-weight:500;color:#111827;outline:none;font-family:inherit" />'
    + '<label style="position:relative;display:inline-block;width:44px;height:24px;flex-shrink:0"><input type="checkbox" checked style="opacity:0;width:0;height:0"><span style="position:absolute;cursor:pointer;inset:0;background:#7C3AED;border-radius:24px;transition:.3s" onclick="this.style.background=this.previousElementSibling.checked?\'#E5E7EB\':\'#7C3AED\'"><span style="position:absolute;height:18px;width:18px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.3s;transform:translateX(20px);box-shadow:0 1px 4px rgba(0,0,0,.2)"></span></span></label>'
    + '<button onclick="parRemoveCustom(\''+id+'\')" style="width:26px;height:26px;border-radius:50%;background:#FEE2E2;border:none;cursor:pointer;font-size:13px;color:#EF4444;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-family:inherit">✕</button>';
  list.appendChild(row);
}

function parRemoveCustom(id) {
  var el = document.getElementById(id);
  if (el) el.remove();
  var list  = document.getElementById('nm-custom-list');
  var empty = document.getElementById('nm-custom-empty');
  if (list && empty && list.children.length === 0) empty.style.display = 'block';
}
