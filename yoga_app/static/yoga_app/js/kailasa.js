/**
 * Yoga Kailasa — Shared JavaScript Utilities
 * Loaded once via base.html.
 */
'use strict';

/* ─── CSRF ───────────────────────────────────────────────────────────────────── */
function getCookie(name) {
  if (!document.cookie) return null;
  const match = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith(name + '='));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

/* ─── AJAX POST ──────────────────────────────────────────────────────────────── */
window.ajaxPost = async function ajaxPost(url, body = {}) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify(body),
  });
  if (response.status === 401 || response.status === 403) {
    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
    return;
  }
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
};

/* ─── Like Buttons ───────────────────────────────────────────────────────────── */
function initLikeButtons() {
  document.querySelectorAll('[data-like-btn]').forEach(button => {
    button.addEventListener('click', async function () {
      if (this.dataset.pending === 'true') return;
      this.dataset.pending = 'true';
      const icon = this.querySelector('i');
      const countEl = this.querySelector('.likes-count');
      if (icon) icon.style.opacity = '0.4';

      const { type, id, courseId, topicId, postSlug } = this.dataset;
      let url;
      if (type === 'topic')     url = `/courses/${courseId}/discussion/${id}/like/`;
      else if (type === 'post') url = `/courses/${courseId}/discussion/${topicId}/posts/${id}/like/`;
      else if (type === 'blog') url = `/blog/${postSlug}/like/`;
      else { this.dataset.pending = 'false'; if (icon) icon.style.opacity = ''; return; }

      try {
        const data = await window.ajaxPost(url);
        if (!data) return;
        const liked = data.liked;
        if (icon) {
          icon.style.opacity = '';
          icon.classList.toggle('fas', liked);
          icon.classList.toggle('far', !liked);
          icon.style.color = liked ? '#a73a00' : '';
        }
        if (countEl) countEl.textContent = data.likes_count;
      } catch (err) {
        if (icon) icon.style.opacity = '';
        window.showToast('Could not update like. Please try again.', 'error');
      } finally {
        this.dataset.pending = 'false';
      }
    });
  });
}

/* ─── Comment Form Loading State ─────────────────────────────────────────────── */
function initCommentForms() {
  document.querySelectorAll('form[data-comment-form]').forEach(form => {
    form.addEventListener('submit', function () {
      const btn = this.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Posting\u2026'; }
    });
  });
}

/* ─── Toast ──────────────────────────────────────────────────────────────────── */
window.showToast = function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const colours = { success: 'bg-green-100 text-green-800', error: 'bg-red-100 text-red-800', info: 'bg-amber-100 text-amber-800' };
  const toast = document.createElement('div');
  toast.className = `px-5 py-3 rounded-lg shadow text-sm font-medium transition-all duration-300 ${colours[type] || colours.info}`;
  toast.setAttribute('role', 'alert');
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
};

/* ─── Notification Pagination ────────────────────────────────────────────────── */
function initNotificationPagination() {
  const btn = document.getElementById('load-more-notifications');
  if (!btn) return;
  let page = 2;
  btn.addEventListener('click', async function () {
    this.textContent = 'Loading\u2026';
    this.disabled = true;
    try {
      const res = await fetch(`/notifications/api/?page=${page}&per_page=10`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      const list = document.getElementById('notification-list');
      if (list && data.notifications && data.notifications.length > 0) {
        data.notifications.forEach(n => {
          const item = document.createElement('div');
          item.className = 'rs-surface-container-lowest p-4 rounded-xl mb-2';
          item.innerHTML = `<p class="rs-on-surface text-sm">${n.message}</p><span class="text-xs rs-on-surface-variant">${n.created_at}</span>`;
          list.appendChild(item);
        });
        page++;
        if (!data.has_next) { this.remove(); return; }
      } else { this.remove(); return; }
      this.textContent = 'Load more';
      this.disabled = false;
    } catch (err) {
      this.textContent = 'Load more';
      this.disabled = false;
      window.showToast('Could not load more notifications.', 'error');
    }
  });
}

/* ─── Delegated data-action dispatcher ──────────────────────────────────────── */
/* Replaces inline onclick="" handlers so the site can run without CSP
   'unsafe-inline' for scripts. Templates use:
     <button data-action="toggle-mobile-menu">
     <button data-action="toggle-mobile-section" data-target="mobile-practice">
     <button data-action="toggle-module" data-target="module-3">
     <button data-action="scroll-to" data-target="curriculum-section">
     <button data-action="toggle-aside">
     <button data-action="toggle-password">
     <button data-action="pick-profile-picture" data-target="id_profile_picture">
     <div data-action="toggle-class-active">
     <button data-action="alert-message" data-message="...">
 */
function initDataActions() {
  document.addEventListener('click', function (e) {
    const el = e.target.closest('[data-action]');
    if (!el) return;

    const actions = {
      'toggle-mobile-menu': () => window.toggleBaseMobileMenu && window.toggleBaseMobileMenu(),
      'toggle-mobile-section': () => window.toggleMobileSection && window.toggleMobileSection(el.dataset.target),
      'toggle-module': () => window.toggleModule && window.toggleModule(el.dataset.target),
      'scroll-to': () => document.getElementById(el.dataset.target)?.scrollIntoView({ behavior: 'smooth' }),
      'toggle-aside': () => {
        const aside = document.querySelector('aside');
        if (aside) ['hidden', 'fixed', 'z-50'].forEach(cls => aside.classList.toggle(cls));
      },
      'toggle-password': () => window.togglePasswordVisibility && window.togglePasswordVisibility(),
      'pick-profile-picture': () => document.getElementById(el.dataset.target)?.click(),
      'toggle-class-active': () => el.classList.toggle('active'),
      'alert-message': () => alert(el.dataset.message || ''),
      'load-video-embed': () => {
        const slot = el.closest('.rs-embed-slot');
        if (!slot || slot.dataset.loaded === 'true') return;
        const embed = slot.dataset.embed || el.dataset.embed;
        if (!embed) return;
        const iframe = document.createElement('iframe');
        iframe.src = embed + (embed.includes('?') ? '&' : '?') + 'autoplay=1';
        iframe.title = slot.getAttribute('aria-label') || 'Highlighted session video';
        iframe.className = 'absolute inset-0 w-full h-full';
        iframe.setAttribute('allow', 'autoplay; encrypted-media; picture-in-picture; fullscreen');
        iframe.setAttribute('allowfullscreen', '');
        slot.style.background = '#000';
        slot.textContent = '';
        slot.appendChild(iframe);
        slot.dataset.loaded = 'true';
      },
    };
    const handler = actions[el.dataset.action];
    if (handler) {
      e.preventDefault();
      handler();
    }
  });
}

/* ─── Init ───────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  initLikeButtons();
  initCommentForms();
  initNotificationPagination();
  initDataActions();
});
