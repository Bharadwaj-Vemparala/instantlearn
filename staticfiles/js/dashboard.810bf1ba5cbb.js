/**
 * Instant Learn — Dashboard JS
 * Tab switching, sidebar toggle, micro-interactions
 */

(function () {
  'use strict';

  // ── Sidebar Toggle (mobile) ────────────────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
    // Close on outside click
    document.addEventListener('click', function (e) {
      if (
        window.innerWidth <= 768 &&
        sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        !sidebarToggle.contains(e.target)
      ) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ── Tab Switching ──────────────────────────────────────────────────────────
  function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const tabName = this.dataset.tab;
        if (!tabName) return;

        // Deactivate all tabs in same group
        const parentNav = this.closest('.tab-nav');
        if (parentNav) {
          parentNav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        }
        // Deactivate all panes
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

        // Activate this button and its pane
        this.classList.add('active');
        const pane = document.getElementById('tab-' + tabName);
        if (pane) pane.classList.add('active');
      });
    });
  }

  // ── Auto-dismiss Alerts ────────────────────────────────────────────────────
  function initAlerts() {
    document.querySelectorAll('.alert.fade.show').forEach(function (alert) {
      setTimeout(function () {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      }, 4500);
    });
  }

  // ── Stat cards entrance animation ─────────────────────────────────────────
  function animateStatCards() {
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach(function (card, i) {
      card.style.opacity = '0';
      card.style.transform = 'translateY(16px)';
      setTimeout(function () {
        card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }, i * 60);
    });
  }

  // ── Perf rings animate in ─────────────────────────────────────────────────
  function animatePerfRings() {
    document.querySelectorAll('.perf-ring-fill').forEach(function (path) {
      const target = path.getAttribute('stroke-dasharray');
      path.setAttribute('stroke-dasharray', '0, 100');
      setTimeout(function () {
        path.style.transition = 'stroke-dasharray 1s ease';
        path.setAttribute('stroke-dasharray', target);
      }, 100);
    });
  }

  // ── Invite code auto-uppercase ─────────────────────────────────────────────
  function initInviteCode() {
    const inviteInput = document.querySelector('[name="invite_code"]');
    if (inviteInput) {
      inviteInput.addEventListener('input', function () {
        const pos = this.selectionStart;
        this.value = this.value.toUpperCase();
        this.setSelectionRange(pos, pos);
      });
    }
  }

  // ── Course card hover tilt ─────────────────────────────────────────────────
  function initCardTilt() {
    document.querySelectorAll('.course-card').forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;
        const rotX = ((y - cy) / cy) * -4;
        const rotY = ((x - cx) / cx) * 4;
        card.style.transform = `translateY(-3px) rotateX(${rotX}deg) rotateY(${rotY}deg)`;
      });
      card.addEventListener('mouseleave', function () {
        card.style.transform = '';
      });
    });
  }

  // ── Marks input live feedback ─────────────────────────────────────────────
  function initMarksInput() {
    const marksInput = document.querySelector('[name="graded_marks"]');
    if (!marksInput) return;
    const maxAttr = marksInput.getAttribute('max');
    if (!maxAttr) return;
    const maxMarks = parseInt(maxAttr);
    const bar = document.getElementById('marksBar');
    const pct = document.getElementById('marksPct');
    if (!bar || !pct) return;

    function updateBar() {
      const val = parseInt(marksInput.value) || 0;
      const p = Math.min(100, Math.round((val / maxMarks) * 100));
      bar.style.width = p + '%';
      bar.style.background = p >= 60 ? 'var(--color-emerald)' : p >= 40 ? 'var(--color-amber)' : 'var(--color-red)';
      pct.textContent = marksInput.value ? `${p}% · ${val}/${maxMarks}` : 'Enter marks to see percentage';
    }
    marksInput.addEventListener('input', updateBar);
  }

  // ── Tooltip bootstrap init ────────────────────────────────────────────────
  function initTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
      document.querySelectorAll('[title]').forEach(function (el) {
        new bootstrap.Tooltip(el, { trigger: 'hover' });
      });
    }
  }

  // ── Init on DOM ready ─────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    initTabs();
    initAlerts();
    animateStatCards();
    animatePerfRings();
    initInviteCode();
    initCardTilt();
    initMarksInput();
    initTooltips();
  });

})();
