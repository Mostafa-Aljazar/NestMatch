/**
 * profile.js — NestMatch Account Settings Page
 */

'use strict';

// ===========================================================================
// 1. TAB NAVIGATION
// ===========================================================================
const tabButtons = document.querySelectorAll('.tab-nav-btn');
const tabPanels = {
  info:      document.getElementById('tab-info'),
  lifestyle: document.getElementById('tab-lifestyle'),
  security:  document.getElementById('tab-security'),
  reviews:   document.getElementById('tab-reviews'),
  verification: document.getElementById('tab-verification'),
};

function activateTab(tabName) {
  const target = tabPanels[tabName] ? tabName : 'info';

  tabButtons.forEach((btn) => btn.classList.remove('active'));
  Object.values(tabPanels).forEach((p) => {
    if (p) p.classList.add('hidden');
  });

  const activeBtn = document.querySelector(`.tab-nav-btn[data-tab="${target}"]`);
  if (activeBtn) activeBtn.classList.add('active');
  if (tabPanels[target]) tabPanels[target].classList.remove('hidden');
}

tabButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const target = button.dataset.tab;
    activateTab(target);

    // Update the URL without reloading the page
    // ?tab=lifestyle → يبيّن للمستخدم وين هو، وبيشتغل لو شارك الرابط
    const url = new URL(window.location.href);
    url.searchParams.set('tab', target);
    window.history.pushState({tab: target}, '', url);
  });
});

// Restore tab from URL on page load (e.g. after refresh or shared link)
const initialTab = new URL(window.location.href).searchParams.get('tab') || 'info';
activateTab(initialTab);

// Handle browser back/forward buttons
window.addEventListener('popstate', (event) => {
  const tab = event.state?.tab || new URL(window.location.href).searchParams.get('tab') || 'info';
  activateTab(tab);
});

// ===========================================================================
// 2. OPTION CARDS (Lifestyle Tab)
// ===========================================================================
document.querySelectorAll('[data-target]').forEach((group) => {
  const targetField = group.dataset.target;
  const hiddenInput = document.getElementById(`input-${targetField}`);
  group.querySelectorAll('.option-card').forEach((card) => {
    card.addEventListener('click', () => {
      group.querySelectorAll('.option-card').forEach((c) => c.classList.remove('selected'));
      card.classList.add('selected');
      if (hiddenInput) hiddenInput.value = card.dataset.value;
      const errorEl = group.parentElement?.querySelector(`.field-error[data-field="${targetField}"]`);
      if (errorEl) errorEl.textContent = '';
    });
  });
});
// ===========================================================================
// 3. DOM REFERENCES
// ===========================================================================
const profilePicInput = document.getElementById('profile_pic_input');

const tabAvatarImage       = document.getElementById('tab-avatar-image');
const tabAvatarPlaceholder = document.getElementById('tab-avatar-placeholder');

const headerAvatarImage       = document.getElementById('header-avatar-image');
const headerAvatarPlaceholder = document.getElementById('header-avatar-placeholder');

const sidebarUserName = document.getElementById('sidebar-user-name');

const profileStrengthValueHeader = document.getElementById('profile-strength-value-header');
const profileStrengthBarHeader   = document.getElementById('profile-strength-bar-header');

let _pendingAvatarSrc = null;


// ===========================================================================
// 4. PROFILE STRENGTH
// ===========================================================================
const lifestyleFieldsTotal = parseInt(document.getElementById('strength-lifestyle-total')?.dataset.value || '0', 10);

const strengthState = {
  hasPhone:          document.getElementById('strength-has-phone')?.dataset.value === 'true',
  hasVerification: document.getElementById('strength-has-verification')?.dataset.value === 'true',
  hasPhoto:          document.getElementById('strength-has-photo')?.dataset.value === 'true',
  // Fraction (0.0-1.0), not a boolean — a partially-filled lifestyle
  // questionnaire should move the needle, not just an all-or-nothing check.
  lifestyleFraction: lifestyleFieldsTotal
    ? parseInt(document.getElementById('strength-lifestyle-filled')?.dataset.value || '0', 10) / lifestyleFieldsTotal
    : 0,
};

// Recomputes strengthState.lifestyleFraction by counting how many of the
// lifestyle form's own hidden inputs currently hold a non-empty value —
// mirrors LifestyleProfile.completeness_fraction server-side without
// duplicating the field list, since the form's hidden inputs already
// enumerate exactly those fields.
function recalcLifestyleFraction() {
  const form = document.getElementById('lifestyle-form');
  if (!form || !lifestyleFieldsTotal) return;
  const inputs = form.querySelectorAll('input[type="hidden"]:not([name="csrfmiddlewaretoken"])');
  const filled = Array.from(inputs).filter((el) => el.value !== '').length;
  strengthState.lifestyleFraction = Math.min(1, filled / lifestyleFieldsTotal);
  const fractionLabel = document.getElementById('lifestyle-fields-fraction');
  if (fractionLabel) fractionLabel.textContent = `(${filled}/${lifestyleFieldsTotal})`;
}

function recalcStrength() {
  const boolItems = [strengthState.hasPhone, strengthState.hasBio, strengthState.hasPhoto].filter(Boolean).length;
  const pct = Math.round(((boolItems + strengthState.lifestyleFraction) / 4) * 100);
  if (profileStrengthValueHeader) profileStrengthValueHeader.textContent = `${pct}%`;
  if (profileStrengthBarHeader)   profileStrengthBarHeader.style.width   = `${pct}%`;

  document.querySelectorAll('.strength-check').forEach((item) => {
    const key = item.dataset.key;
    // hasLifestyle is "done" once the fraction is complete (or nearly so);
    // partial progress still shows a partially-filled ring rather than a
    // hard on/off state, using the same emerald palette at reduced opacity.
    const done = key === 'hasLifestyle' ? strengthState.lifestyleFraction >= 1 : !!strengthState[key];
    const partial = key === 'hasLifestyle' && strengthState.lifestyleFraction > 0 && strengthState.lifestyleFraction < 1;
    const icon = item.querySelector('.check-icon');
    item.classList.toggle('text-slate-500', !done && !partial);
    item.classList.toggle('text-slate',     done || partial);
    if (icon) {
      icon.classList.toggle('border-slate-300',   !done && !partial);
      icon.classList.toggle('bg-white',           !done && !partial);
      icon.classList.toggle('border-emerald-500',  done);
      icon.classList.toggle('bg-emerald-500',      done);
      icon.classList.toggle('border-amber-400',    partial);
      icon.classList.toggle('bg-amber-400',        partial);
      icon.classList.toggle('text-white',          done || partial);
      icon.textContent = done ? '✓' : (partial ? '·' : '');
    }
    // النص لما يكون مكتمل يصير أبهت
    item.classList.toggle('text-white/50', done);
    item.classList.toggle('text-white', !done);
  });
}

recalcStrength();

if (profileStrengthBarHeader) {
  const target = profileStrengthBarHeader.style.width;
  profileStrengthBarHeader.style.width = '0%';
  requestAnimationFrame(() => requestAnimationFrame(() => {
    profileStrengthBarHeader.style.width = target;
  }));
}


// ===========================================================================
// 5. AVATAR HELPERS
// ===========================================================================
function setAvatarSrc(imgEl, placeholderEl, src) {
  if (!imgEl || !placeholderEl) return;
  if (src) {
    imgEl.src = src;
    imgEl.classList.remove('hidden');
    placeholderEl.classList.add('hidden');
    placeholderEl.classList.remove('flex');
  } else {
    imgEl.classList.add('hidden');
    placeholderEl.classList.remove('hidden');
    placeholderEl.classList.add('flex');
  }
}

function applyAvatarEverywhere(src) {
  // Tab 1 avatar
  setAvatarSrc(tabAvatarImage, tabAvatarPlaceholder, src);
  // Page header avatar
  setAvatarSrc(headerAvatarImage, headerAvatarPlaceholder, src);

  // Navbar — desktop
  const navImg         = document.getElementById('nav-avatar-img');
  const navPlaceholder = document.getElementById('nav-avatar-placeholder');
  if (navImg && src) {
    navImg.src = src;
    navImg.classList.remove('hidden');
    if (navPlaceholder) navPlaceholder.classList.add('hidden');
  } else if (navPlaceholder && !src) {
    navPlaceholder.classList.remove('hidden');
    if (navImg) navImg.classList.add('hidden');
  }

  // Navbar — mobile drawer
  const navImgMobile         = document.getElementById('nav-avatar-img-mobile');
  const navPlaceholderMobile = document.getElementById('nav-avatar-placeholder-mobile');
  if (navImgMobile && src) {
    navImgMobile.src = src;
    navImgMobile.classList.remove('hidden');
    if (navPlaceholderMobile) navPlaceholderMobile.classList.add('hidden');
  } else if (navPlaceholderMobile && !src) {
    navPlaceholderMobile.classList.remove('hidden');
    if (navImgMobile) navImgMobile.classList.add('hidden');
  }
}

if (tabAvatarImage)    tabAvatarImage.addEventListener('error',    () => setAvatarSrc(tabAvatarImage,    tabAvatarPlaceholder,    null));
if (headerAvatarImage) headerAvatarImage.addEventListener('error', () => setAvatarSrc(headerAvatarImage, headerAvatarPlaceholder, null));


// ===========================================================================
// 6. PROFILE PICTURE PREVIEW
// ===========================================================================
// ===========================================================================
const MAX_PHOTO_SIZE_MB = 5;
const ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];

const profilePicFilenameEl = document.getElementById('profile_pic_filename');
const profilePicErrorEl    = document.querySelector('.field-error[data-field="profile_pic"]');

function clearProfilePicError() {
  if (profilePicErrorEl) profilePicErrorEl.textContent = '';
}

function setProfilePicError(message) {
  if (profilePicErrorEl) profilePicErrorEl.textContent = message;
}

function setProfilePicFilename(name) {
  if (profilePicFilenameEl) profilePicFilenameEl.textContent = name || '';
}

// تتحقق من صحة الملف المختار حالياً، ترجع true/false
function validateSelectedProfilePic() {
  clearProfilePicError();
  const file = profilePicInput?.files?.[0];
  if (!file) return true; // ما في ملف جديد = ما في شي نتحقق منه

  if (file.size > MAX_PHOTO_SIZE_MB * 1024 * 1024) {
    setProfilePicError('Profile picture must be smaller than 5MB!');
    return false;
  }

  if (!ALLOWED_PHOTO_TYPES.includes(file.type)) {
    setProfilePicError('Profile picture must be a JPEG, PNG, WEBP, or GIF image!');
    return false;
  }

  return true;
}

if (profilePicInput) {
  profilePicInput.addEventListener('change', (event) => {
    // فقط نظّفي الخطأ القديم واعرضي اسم الملف — بدون أي تحقق هون
    clearProfilePicError();

    const file = event.target.files && event.target.files[0];
    if (!file) {
      setProfilePicFilename('');
      return;
    }

    setProfilePicFilename(file.name);

    const reader = new FileReader();
    reader.onload = (e) => {
      _pendingAvatarSrc = e.target.result;
      setAvatarSrc(tabAvatarImage, tabAvatarPlaceholder, _pendingAvatarSrc);
    };
    reader.readAsDataURL(file);
  });
}
// ===========================================================================
// 7. FORM HELPERS
// ===========================================================================
function clearFormFeedback(form) {
  form.querySelectorAll('.field-error').forEach((el) => (el.textContent = ''));
  form.querySelectorAll('input, select, textarea').forEach((el) => el.classList.remove('border-rose-300'));
  const messageBox = form.querySelector('[id$="-form-message"]');
  if (messageBox) { messageBox.innerHTML = ''; messageBox.className = 'hidden'; }
}

function showFieldErrors(form, errors) {
  Object.entries(errors || {}).forEach(([field, message]) => {
    const errorEl = form.querySelector(`.field-error[data-field="${field}"]`);
    if (errorEl) errorEl.textContent = message;
    const inputEl = form.querySelector(`[name="${field}"]`);
    if (inputEl) inputEl.classList.add('border-rose-300');
  });
}

function showFormFeedback(form, message, isError = false) {
  const messageBox = form.querySelector('[id$="-form-message"]');
  if (!messageBox) return;
  const colorClasses = isError ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700';
  const iconBg    = isError ? 'bg-rose-100'  : 'bg-emerald-100';
  const iconColor = isError ? 'text-rose-700' : 'text-emerald-700';
  const icon      = isError ? '!'             : '✓';
  const title     = isError ? 'Something went wrong' : 'Success';
  messageBox.innerHTML = `
    <div class="fixed right-4 top-20 z-[60] flex max-w-sm items-start gap-3 rounded-2xl border ${colorClasses} px-4 py-3 shadow-soft">
      <div class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${iconBg}">
        <span class="text-sm font-bold ${iconColor}">${icon}</span>
      </div>
      <div class="flex-1">
        <p class="text-sm font-semibold">${title}</p>
        <p class="mt-1 text-sm">${message}</p>
      </div>
      <button type="button" class="ml-2 text-sm font-semibold ${iconColor}" onclick="this.closest('.fixed').remove()">✕</button>
    </div>`;
  messageBox.classList.remove('hidden');
  setTimeout(() => {
    if (messageBox.firstElementChild) messageBox.firstElementChild.remove();
    messageBox.classList.add('hidden');
  }, 5000);
}

function refreshSidebarName(form) {
  const first = form.querySelector('[name="first_name"]')?.value?.trim();
  const last  = form.querySelector('[name="last_name"]')?.value?.trim();
  if (sidebarUserName && first && last) sidebarUserName.textContent = `${first} ${last}`;
}


// ===========================================================================
// 8. AJAX — Personal info / Lifestyle / Security
// ===========================================================================
async function submitAjaxForm(form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearFormFeedback(form);
    const formData  = new FormData(form);
    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn?.textContent;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Saving...'; }

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      });
      const data = await response.json();

      if (data.success) {
        if (form.id === 'personal-info-form') {
          refreshSidebarName(form);
          strengthState.hasPhone = !!form.querySelector('[name="phone_number"]')?.value?.trim();
          strengthState.hasBio   = !!form.querySelector('[name="bio"]')?.value?.trim();
          if (_pendingAvatarSrc) {
            setAvatarSrc(headerAvatarImage, headerAvatarPlaceholder, _pendingAvatarSrc);
            strengthState.hasPhoto = true;
            _pendingAvatarSrc = null;
          } else if (profilePicInput?.files?.length) {
            strengthState.hasPhoto = true;
          }
          if (data.profile_pic_url) {
            applyAvatarEverywhere(data.profile_pic_url);
            strengthState.hasPhoto = true;
          }
        }
        if (form.id === 'lifestyle-form') recalcLifestyleFraction();
        recalcStrength();
        showFormFeedback(form, data.message || 'Saved successfully.', false);
        form.querySelectorAll('input[type="password"]').forEach((el) => (el.value = ''));
      } else {
        showFieldErrors(form, data.errors || {});
      }
    } catch {
      showFormFeedback(form, 'Something went wrong. Please try again.', true);
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = originalBtnText; }
    }
  });
}

['personal-info-form', 'lifestyle-form', 'security-form'].forEach((id) => {
  const form = document.getElementById(id);
  if (form) submitAjaxForm(form);
});


// ===========================================================================
// 9. REVIEW FORM — AJAX + live card inject
// ===========================================================================
const reviewForm = document.getElementById('review-form');

if (reviewForm) {
  reviewForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    reviewForm.querySelectorAll('.field-error').forEach((el) => (el.textContent = ''));
    reviewForm.querySelectorAll('input, select, textarea').forEach((el) => el.classList.remove('border-rose-300'));

    const formData  = new FormData(reviewForm);
    const csrfToken = reviewForm.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
    const submitBtn = reviewForm.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Submitting...'; }

    try {
      const response = await fetch(reviewForm.action, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      });
      let data;
      try {
        data = await response.json();
      } catch (err) {
        const text = await response.text();
        throw new Error(text || 'Server returned an invalid response.');
      }

      if (!response.ok) {
        throw new Error(data?.message || 'Server error.');
      }

      if (data.success) {
        const reviewerName = formData.get('reviewer_name') || '';
        const roleVal      = formData.get('role') || '';
        const locationVal  = formData.get('location') || '';
        const reviewText   = formData.get('review_text') || '';
        const today        = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        const roleLabel    = roleVal === 'seeker' ? 'Room Seeker' : roleVal === 'poster' ? 'Room Poster' : roleVal;

        const card = document.createElement('div');
        card.className = 'bg-slate-50 p-4 border border-slate-200 rounded-xl';
        card.style.animation = 'tabFadeIn 0.25s ease';
        card.innerHTML = `
          <div class="flex justify-between items-center gap-3">
            <div>
              <p class="font-semibold text-brand-900">${_escHtml(reviewerName)}</p>
              <p class="text-slate-500 text-xs">${_escHtml(roleLabel)}</p>
            </div>
            <span class="rounded-full px-3 py-1 text-[11px] font-semibold bg-yellow-50 text-yellow-700">Pending approval</span>
          </div>
          <p class="mt-3 text-slate-600 text-sm leading-6">${_escHtml(reviewText.substring(0, 140))}${reviewText.length > 140 ? '…' : ''}</p>
          <div class="flex flex-wrap items-center gap-2 mt-3 text-slate-500 text-xs">
            ${locationVal ? `<span>${_escHtml(locationVal)}</span>` : ''}
            <span>· ${today}</span>
          </div>`;

        const reviewsPanel = document.getElementById('tab-reviews');
        let listContainer  = reviewsPanel.querySelector('.space-y-4');
        if (!listContainer) {
          const emptyMsg = reviewsPanel.querySelector('.space-y-6 p.text-slate-500');
          if (emptyMsg) emptyMsg.remove();
          listContainer = document.createElement('div');
          listContainer.className = 'space-y-4';
          const reviewsBox = reviewsPanel.querySelector('.space-y-6 .rounded-2xl');
          if (reviewsBox) reviewsBox.appendChild(listContainer);
        }
        listContainer.prepend(card);
        reviewForm.reset();
        _showToast('Review submitted! It will appear publicly once approved.', false);
      } else {
        Object.entries(data.errors || {}).forEach(([field, message]) => {
          const errorEl = reviewForm.querySelector(`.field-error[data-field="${field}"]`);
          if (errorEl) errorEl.textContent = message;
          const inputEl = reviewForm.querySelector(`[name="${field}"]`);
          if (inputEl) inputEl.classList.add('border-rose-300');
        });
        if (data.message) _showToast(data.message, true);
      }
    } catch (error) {
      const message = error?.message || 'Something went wrong. Please try again.';
      _showToast(message, true);
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = originalText; }
    }
  });
}

const deleteReviewForms = document.querySelectorAll('form[data-ajax-review-delete]');

deleteReviewForms.forEach((form) => {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Deleting...'; }

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: new FormData(form),
      });

      let data;
      try {
        data = await response.json();
      } catch (err) {
        const text = await response.text();
        throw new Error(text || 'Server returned an invalid response.');
      }

      if (!response.ok) {
        throw new Error(data?.message || 'Server error.');
      }

      if (data.success) {
        const card = form.closest('.bg-slate-50');
        if (card) card.remove();
        _showToast(data.message || 'Review deleted.', false);
      } else {
        throw new Error(data.message || 'Could not delete review.');
      }
    } catch (error) {
      const message = error?.message || 'Something went wrong. Please try again.';
      _showToast(message, true);
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = originalText; }
    }
  });
});

function _showToast(message, isError = false) {
  const existing = document.getElementById('_global-toast');
  if (existing) existing.remove();
  const colorClasses = isError ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700';
  const iconBg    = isError ? 'bg-rose-100'  : 'bg-emerald-100';
  const iconColor = isError ? 'text-rose-700' : 'text-emerald-700';
  const icon      = isError ? '!'             : '✓';
  const title     = isError ? 'Something went wrong' : 'Success';
  const toast = document.createElement('div');
  toast.id = '_global-toast';
  toast.className = `fixed right-4 top-20 z-[60] flex max-w-sm items-start gap-3 rounded-2xl border ${colorClasses} px-4 py-3 shadow-soft`;
  toast.innerHTML = `
    <div class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${iconBg}">
      <span class="text-sm font-bold ${iconColor}">${icon}</span>
    </div>
    <div class="flex-1">
      <p class="text-sm font-semibold">${title}</p>
      <p class="mt-1 text-sm">${message}</p>
    </div>
    <button type="button" class="ml-2 text-sm font-semibold ${iconColor}" onclick="this.closest('#_global-toast').remove()">✕</button>`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

function _escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}


// ===========================================================================
// 10. DELETE ACCOUNT MODAL
// ===========================================================================
function openDeleteModal() {
  const modal = document.getElementById('delete-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeDeleteModal() {
  const modal = document.getElementById('delete-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

document.getElementById('delete-modal')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeDeleteModal();
});

const deleteAccountForm = document.getElementById('delete-account-form');
if (deleteAccountForm) {
  deleteAccountForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const csrfToken = deleteAccountForm.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
    const response = await fetch(deleteAccountForm.action, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
      body: new FormData(deleteAccountForm),
    });
    const data = await response.json();
    if (data.success) {
      window.location.href = data.redirect_url || '/auth/register/';
    } else {
      alert(data.message || 'Could not delete account. Please try again.');
    }
  });
}

// ===========================================================================
// 11. VERIFICATION DOCUMENT UPLOAD — AJAX
// ===========================================================================
document.querySelectorAll('.verification-doc-form').forEach((form) => {
  const fileInput = form.querySelector('input[type="file"]');
  const filenameEl = form.querySelector('.verif-filename');
  const errorEl = form.querySelector('.field-error[data-field="file"]');

  // اظهار اسم الملف فوراً بعد الاختيار
  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (errorEl) errorEl.textContent = '';
      const file = fileInput.files && fileInput.files[0];
      if (filenameEl) filenameEl.textContent = file ? file.name : '';
    });
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (errorEl) errorEl.textContent = '';
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Uploading...'; }

    const formData  = new FormData(form);
    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      });
      const data = await response.json();

      if (data.success) {
        _showToast(data.message || 'Document submitted for review.', false);

        // حدّثي الـ badge بنفس الكارد
        const card = form.closest('.rounded-2xl, .min-w-0.flex-1');
        const badgeContainer = card?.querySelector('.flex.items-center.justify-between');
        if (badgeContainer) {
          const oldBadge = badgeContainer.querySelector('span');
          if (oldBadge) {
            oldBadge.outerHTML = `<span class="inline-flex items-center gap-1.5 rounded-full bg-yellow-50 px-3 py-1 text-xs font-semibold text-yellow-700">Pending review</span>`;
          }
        }
        const btn = form.querySelector('button[type="button"]');
        if (btn) btn.textContent = 'Replace file';
      } else {
        const firstError = Object.values(data.errors || {})[0];
        if (errorEl) errorEl.textContent = firstError || 'Something went wrong.';
      }
    } catch {
      if (errorEl) errorEl.textContent = 'Something went wrong. Please try again.';
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = originalText; }
      if (filenameEl) filenameEl.textContent = '';
      fileInput.value = '';
    }
  });
});