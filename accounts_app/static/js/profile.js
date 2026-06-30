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
};

tabButtons.forEach((button) => {
  button.addEventListener('click', () => {
    tabButtons.forEach((btn) => btn.classList.remove('active'));
    Object.values(tabPanels).forEach((p) => p.classList.add('hidden'));
    button.classList.add('active');
    const target = button.dataset.tab;
    const panel = tabPanels[target];
    if (panel) {
      panel.classList.remove('hidden');
      panel.classList.remove('tab-panel');
      void panel.offsetWidth;
      panel.classList.add('tab-panel');
    }
    button.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  });
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
const strengthState = {
  hasPhone:     document.getElementById('strength-has-phone')?.dataset.value === 'true',
  hasBio:       document.getElementById('strength-has-bio')?.dataset.value === 'true',
  hasPhoto:     document.getElementById('strength-has-photo')?.dataset.value === 'true',
  hasLifestyle: document.getElementById('strength-has-lifestyle')?.dataset.value === 'true',
};

function recalcStrength() {
  const filled = Object.values(strengthState).filter(Boolean).length;
  const pct = Math.round((filled / 4) * 100);
  if (profileStrengthValueHeader) profileStrengthValueHeader.textContent = `${pct}%`;
  if (profileStrengthBarHeader)   profileStrengthBarHeader.style.width   = `${pct}%`;

  document.querySelectorAll('.strength-check').forEach((item) => {
    const key  = item.dataset.key;
    const done = !!strengthState[key];
    const icon = item.querySelector('.check-icon');
    item.classList.toggle('text-slate-500', !done);
    item.classList.toggle('text-slate',     done);
    if (icon) {
      icon.classList.toggle('border-slate-300',   !done);
      icon.classList.toggle('bg-white',           !done);
      icon.classList.toggle('border-emerald-500',  done);
      icon.classList.toggle('bg-emerald-500',      done);
      icon.classList.toggle('text-white',          done);
      icon.textContent = done ? '✓' : '';
    }
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
if (profilePicInput) {
  profilePicInput.addEventListener('change', (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
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
        if (form.id === 'lifestyle-form') strengthState.hasLifestyle = true;
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
        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      });
      const data = await response.json();

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
              <p class="font-semibold text-slate-900">${_escHtml(reviewerName)}</p>
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
    } catch {
      _showToast('Something went wrong. Please try again.', true);
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = originalText; }
    }
  });
}

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