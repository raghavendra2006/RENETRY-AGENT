// ReTurn Platform Core JavaScript

// Global Toast Notification Helper
window.showToast = function(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-center justify-between p-3.5 rounded-lg shadow-lg border text-xs font-medium transition-all duration-300 transform translate-y-2 opacity-0';
    
    if (type === 'success') {
        toast.className += ' bg-emerald-900 text-white border-emerald-800';
    } else if (type === 'error' || type === 'danger') {
        toast.className += ' bg-rose-900 text-white border-rose-800';
    } else if (type === 'warning') {
        toast.className += ' bg-amber-900 text-white border-amber-800';
    } else {
        toast.className += ' bg-slate-900 text-white border-slate-800';
    }

    toast.innerHTML = `
        <div class="flex items-center gap-2">
            <span>${message}</span>
        </div>
        <button type="button" class="ml-3 text-white/60 hover:text-white font-bold">&times;</button>
    `;

    container.appendChild(toast);

    // Fade and slide in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    const closeBtn = toast.querySelector('button');
    const dismiss = () => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    };

    closeBtn.addEventListener('click', dismiss);
    setTimeout(dismiss, 4000);
};

document.addEventListener('DOMContentLoaded', () => {
    // Mobile navigation toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Login dropdown handling (User, Recruiter, Admin)
    const loginDropdownBtn = document.getElementById('login-dropdown-btn');
    const loginDropdownMenu = document.getElementById('login-dropdown-menu');
    const loginChevron = document.getElementById('login-chevron');
    const loginDropdownWrapper = document.getElementById('login-dropdown-wrapper');

    if (loginDropdownBtn && loginDropdownMenu) {
        function openLoginDropdown() {
            loginDropdownMenu.classList.remove('hidden');
            loginDropdownBtn.setAttribute('aria-expanded', 'true');
            if (loginChevron) loginChevron.style.transform = 'rotate(180deg)';
        }

        function closeLoginDropdown() {
            if (!loginDropdownMenu.classList.contains('hidden')) {
                loginDropdownMenu.classList.add('hidden');
                loginDropdownBtn.setAttribute('aria-expanded', 'false');
                if (loginChevron) loginChevron.style.transform = 'rotate(0deg)';
            }
        }

        loginDropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (loginDropdownMenu.classList.contains('hidden')) {
                openLoginDropdown();
            } else {
                closeLoginDropdown();
            }
        });

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (loginDropdownWrapper && !loginDropdownWrapper.contains(e.target)) {
                closeLoginDropdown();
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' || e.key === 'Esc') {
                closeLoginDropdown();
            }
        });
    }

    // Auto-dismiss alert notifications
    const alertCloses = document.querySelectorAll('.alert-close-btn');
    alertCloses.forEach(btn => {
        btn.addEventListener('click', () => {
            const alertBox = btn.closest('.alert-box');
            if (alertBox) {
                alertBox.style.opacity = '0';
                setTimeout(() => alertBox.remove(), 200);
            }
        });
    });

    // Auto-dismiss flash alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-box');
    alerts.forEach(box => {
        setTimeout(() => {
            if (box && box.parentElement) {
                box.style.transition = 'opacity 0.4s ease';
                box.style.opacity = '0';
                setTimeout(() => box.remove(), 400);
            }
        }, 6000);
    });

    // Bookmark opportunity buttons
    const bookmarkBtns = document.querySelectorAll('.bookmark-btn');
    bookmarkBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const itemType = btn.dataset.itemType;
            const itemId = btn.dataset.itemId;

            try {
                const response = await fetch('/api/bookmarks/toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ item_type: itemType, item_id: itemId })
                });
                const result = await response.json();
                if (result.success) {
                    if (result.is_bookmarked) {
                        btn.classList.add('bg-teal-50', 'text-teal-800', 'border-teal-300', 'font-semibold');
                        btn.classList.remove('text-slate-600', 'border-slate-200');
                        btn.innerHTML = '★ Saved';
                        window.showToast('Added to your saved items', 'success');
                    } else {
                        btn.classList.remove('bg-teal-50', 'text-teal-800', 'border-teal-300', 'font-semibold');
                        btn.classList.add('text-slate-600', 'border-slate-200');
                        btn.innerHTML = '☆ Save';
                        window.showToast('Removed from saved items', 'info');
                    }
                }
            } catch (err) {
                console.error('Bookmark error:', err);
                window.showToast('Failed to update bookmark', 'error');
            }
        });
    });

    // Form submission loading state handler
    const forms = document.querySelectorAll('form[method="POST"]:not([data-no-loader])');
    forms.forEach(form => {
        form.addEventListener('submit', () => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = `
                    <span class="inline-flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Processing...</span>
                    </span>
                `;
                // Allow fallback re-enable if submission didn't navigate away in 10s
                setTimeout(() => {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                }, 10000);
            }
        });
    });
});
