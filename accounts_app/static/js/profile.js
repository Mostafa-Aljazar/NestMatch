/**
 * profile.js — NestMatch Account Settings Page
 * =============================================
*/

'use strict';

// ===========================================================================
// 1. TAB NAVIGATION
// Handles switching between page tabs (Personal Info / Lifestyle / Security)
// ===========================================================================
const tabButtons = document.querySelectorAll('.tab-nav-btn');
const tabPanels = {
  info:      document.getElementById('tab-info'),
  lifestyle: document.getElementById('tab-lifestyle'),
  security:  document.getElementById('tab-security'),
};

tabButtons.forEach((button) => {
  button.addEventListener('click', () => {
    // Remove active class from all buttons and hide all panels
    tabButtons.forEach((btn) => btn.classList.remove('active'));
    Object.values(tabPanels).forEach((p) => p.classList.add('hidden'));

    // Activate the clicked button and show the corresponding panel
    button.classList.add('active');
    const target = button.dataset.tab;
    if (tabPanels[target]) tabPanels[target].classList.remove('hidden');
  });
});


// ===========================================================================
// 2. OPTION CARDS (Lifestyle Tab)
// Each group of cards has a data-target matching a hidden input.
// Clicking a card updates the hidden input with the correct value.
// ===========================================================================
document.querySelectorAll('[data-target]').forEach((group) => {
  const targetField = group.dataset.target;
  const hiddenInput = document.getElementById(`input-${targetField}`);

  group.querySelectorAll('.option-card').forEach((card) => {
    card.addEventListener('click', () => {
      // Remove 'selected' from all and apply to clicked
      group.querySelectorAll('.option-card').forEach((c) => c.classList.remove('selected'));
      card.classList.add('selected');

      // Update the hidden input value
      if (hiddenInput) hiddenInput.value = card.dataset.value;

      // Clear any errors for this field
      const errorEl = group.parentElement?.querySelector(`.field-error[data-field="${targetField}"]`);
      if (errorEl) errorEl.textContent = '';
    });
  });
});


// ===========================================================================
// 3. DOM REFERENCES
// References to elements used in multiple places
// ===========================================================================
const profilePicInput          = document.getElementById('profile_pic_input');
const profileAvatarImage       = document.getElementById('profile-avatar-image');
const profileAvatarPlaceholder = document.getElementById('profile-avatar-placeholder');
const sidebarUserName          = document.getElementById('sidebar-user-name');
const profileStrengthValue     = document.getElementById('profile-strength-value');
const profileStrengthBar       = document.getElementById('profile-strength-bar');


// ===========================================================================
// 4. PROFILE STRENGTH
// Calculates profile completion percentage based on real server data.
// The strengthState updates after each successful save without a reload.
// Initial values are pulled from hidden spans in the HTML.
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
  if (profileStrengthValue) profileStrengthValue.textContent = `${pct}%`;
  if (profileStrengthBar) profileStrengthBar.style.width = `${pct}%`;
}

recalcStrength();


// ===========================================================================
// 5. PROFILE PICTURE PREVIEW
// When the user selects a new image, it displays immediately in the sidebar.
// Actual uploading occurs when the user clicks 'Save'.
// ===========================================================================
function showAvatarInitials() {
  // If the image fails to load, fallback to displaying initials
  const nameSource = sidebarUserName?.textContent || '';
  const initials = nameSource
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('') || 'U';

  if (profileAvatarImage) profileAvatarImage.classList.add('hidden');
  if (profileAvatarPlaceholder) {
    profileAvatarPlaceholder.textContent = initials;
    profileAvatarPlaceholder.classList.remove('hidden');
    profileAvatarPlaceholder.classList.add('flex');
  }
}

// Handle broken or failed image loads
if (profileAvatarImage) {
  profileAvatarImage.addEventListener('error', () => showAvatarInitials());
}

// Instant preview when a new image is selected
if (profilePicInput) {
  profilePicInput.addEventListener('change', (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      if (profileAvatarImage) {
        profileAvatarImage.src = e.target.result;
        profileAvatarImage.classList.remove('hidden');
      } else {
        // First time adding an image (didn't have one before)
        const img = document.createElement('img');
        img.id = 'profile-avatar-image';
        img.src = e.target.result;
        img.alt = 'Profile preview';
        img.className = 'h-16 w-16 rounded-full border border-brand-200 object-cover';
        document.getElementById('profile-avatar-wrapper').appendChild(img);
      }
      if (profileAvatarPlaceholder) profileAvatarPlaceholder.classList.add('hidden');
    };
    reader.readAsDataURL(file);
  });
}


// ===========================================================================
// 6. FORM HELPERS
// Helper functions for AJAX forms
// ===========================================================================

/**
 * Clears all errors and success messages from the form
 * Called before every new submission
 */
function clearFormFeedback(form) {
  form.querySelectorAll('.field-error').forEach((el) => (el.textContent = ''));
  form.querySelectorAll('input, select, textarea').forEach((el) => el.classList.remove('border-rose-300'));
  const messageBox = form.querySelector('[id$="-form-message"]');
  if (messageBox) {
    messageBox.innerHTML = '';
    messageBox.className = 'hidden';
  }
}

/**
 * Displays errors under each corresponding field
 * errors = { field_name: "error message" }
 * Each field must have <p class="field-error" data-field="field_name">
 */
function showFieldErrors(form, errors) {
  Object.entries(errors || {}).forEach(([field, message]) => {
    const errorEl = form.querySelector(`.field-error[data-field="${field}"]`);
    if (errorEl) errorEl.textContent = message;
    const inputEl = form.querySelector(`[name="${field}"]`);
    if (inputEl) inputEl.classList.add('border-rose-300');
  });
}

/**
 * Shows a toast message after success
 * isError = true  → Clears message box (errors appear inline)
 * isError = false → Shows green toast that disappears after 5 seconds
 */
function showFormFeedback(form, message, isError = false) {
  const messageBox = form.querySelector('[id$="-form-message"]');
  if (!messageBox) return;

  // بنحدد الألوان والنص حسب نوع الرسالة (نجاح أو خطأ)
  const colorClasses = isError
    ? 'border-rose-200 bg-rose-50 text-rose-700'      // أحمر
    : 'border-emerald-200 bg-emerald-50 text-emerald-700'; // أخضر

  const iconBg = isError ? 'bg-rose-100' : 'bg-emerald-100';
  const iconColor = isError ? 'text-rose-700' : 'text-emerald-700';
  const icon = isError ? '!' : '✓';
  const title = isError ? 'Something went wrong' : 'Success';

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

  // التوست بيختفي تلقائيًا بعد 5 ثواني بالحالتين (نجاح أو خطأ)
  setTimeout(() => {
    if (messageBox.firstElementChild) messageBox.firstElementChild.remove();
    messageBox.classList.add('hidden');
  }, 5000);
}

/**
 * Updates the user's name in the sidebar after saving Personal Info
 */
function refreshSidebarName(form) {
  const first = form.querySelector('[name="first_name"]')?.value?.trim();
  const last  = form.querySelector('[name="last_name"]')?.value?.trim();
  if (sidebarUserName && first && last) {
    sidebarUserName.textContent = `${first} ${last}`;
  }
}


// ===========================================================================
// 7. AJAX FORM SUBMISSION
// Handles submission for all forms without reloading
// Works on: personal-info-form / lifestyle-form / security-form
// ===========================================================================
async function submitAjaxForm(form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Clear old errors before submitting
    clearFormFeedback(form);

    const formData  = new FormData(form);
    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';

    // Disable the submit button while the request is in flight, to
    // prevent double-submits (e.g. double-clicking "Save changes").
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn?.textContent;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Saving...';
    }

    try {
      const response = await fetch(form.action, {
        method:  'POST',
        headers: {
          'X-CSRFToken':      csrfToken,
          'X-Requested-With': 'XMLHttpRequest', // Important: Tells Django to return JSON
        },
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        //  Successful save

        if (form.id === 'personal-info-form') {
          refreshSidebarName(form);
          strengthState.hasPhone = !!form.querySelector('[name="phone_number"]')?.value?.trim();
          strengthState.hasBio   = !!form.querySelector('[name="bio"]')?.value?.trim();
          strengthState.hasPhoto = strengthState.hasPhoto || !!profilePicInput?.files?.length;
        }

        if (form.id === 'lifestyle-form') {
          strengthState.hasLifestyle = true;
        }

        recalcStrength();
        showFormFeedback(form, data.message || 'Saved successfully.', false);
        form.querySelectorAll('input[type="password"]').forEach((input) => (input.value = ''));

      } else {
        //  Validation errors — display inline only, no toast
        showFieldErrors(form, data.errors || {});
      }

    } catch (err) {
      // Network or server error
      showFormFeedback(form, 'Something went wrong. Please try again.', true);
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
      }
    }
  });
}


// Initialize AJAX submission for the three forms
['personal-info-form', 'lifestyle-form', 'security-form'].forEach((formId) => {
  const form = document.getElementById(formId);
  if (form) submitAjaxForm(form);
});


// ===========================================================================
// 8. DELETE ACCOUNT MODAL
// Modern popup to replace the browser's default confirm()
// ===========================================================================

/**
 * Opens the modal
 * Called via: onclick="openDeleteModal()" in the HTML
 */
function openDeleteModal() {
  const modal = document.getElementById('delete-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

/**
 * Closes the modal
 * Called via Cancel button or clicking outside the modal
 */
function closeDeleteModal() {
  const modal = document.getElementById('delete-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

// Close if the user clicks on the background
document.getElementById('delete-modal')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeDeleteModal();
});


const deleteAccountForm = document.getElementById('delete-account-form');
if (deleteAccountForm) {
  deleteAccountForm.addEventListener('submit', async (event) => {
    event.preventDefault();   // يمنع الفورم من عمل reload عادي

    const csrfToken = deleteAccountForm.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
    // ... تعطيل الزر وقت الإرسال

    const response = await fetch(deleteAccountForm.action, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest',   // يطلب JSON من الـ view
      },
      body: new FormData(deleteAccountForm),
    });

    const data = await response.json();

    if (data.success) {
      window.location.href = data.redirect_url || '/auth/register/';  // الحساب انحذف، روح لصفحة جديدة
    } else {
      closeDeleteModal();
      // عرض رسالة خطأ
    }
  });
}  