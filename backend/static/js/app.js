/**
 * EduOrbit Core ES2025 Client-Side Framework & Interactivity Orchestrator
 */

export class EduOrbitApp {
  constructor() {
    this.initHTMXEvents();
    this.initToasts();
    console.log("EduOrbit client core initialized.");
  }

  /**
   * Configures global HTMX request/response overrides and custom indicators.
   */
  initHTMXEvents() {
    document.body.addEventListener('htmx:beforeRequest', (evt) => {
      // Add loading state or custom indicators here if needed
      const indicator = evt.detail.elt.getAttribute('hx-indicator');
      if (indicator) {
        const spinner = document.querySelector(indicator);
        if (spinner) spinner.classList.add('active');
      }
    });

    document.body.addEventListener('htmx:afterRequest', (evt) => {
      // Deactivate custom indicator spinners
      const indicator = evt.detail.elt.getAttribute('hx-indicator');
      if (indicator) {
        const spinner = document.querySelector(indicator);
        if (spinner) spinner.classList.remove('active');
      }
    });

    // Enforce standardized error notifications on client-side requests failing
    document.body.addEventListener('htmx:responseError', (evt) => {
      const status = evt.detail.xhr.status;
      let errorMsg = `Server returned an error status: ${status}`;
      
      try {
        const responseJson = JSON.parse(evt.detail.xhr.responseText);
        if (responseJson && responseJson.error && responseJson.error.message) {
          errorMsg = responseJson.error.message;
        }
      } catch (e) {
        // Fallback to generic message
      }
      
      this.showToast(errorMsg, "error");
    });
  }

  /**
   * Centralized UI Toast alert handling.
   */
  initToasts() {
    this.toastContainer = document.createElement('div');
    this.toastContainer.className = 'toast-container';
    document.body.appendChild(this.toastContainer);
    
    // Add essential toast container style block programmatically if not styling-injected
    const style = document.createElement('style');
    style.textContent = `
      .toast-container {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 1070;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .toast-item {
        background-color: var(--color-surface, #ffffff);
        color: var(--color-text-primary, #212121);
        border-left: 4px solid var(--color-primary, #2E7D32);
        padding: 12px 20px;
        border-radius: var(--radius-md, 8px);
        box-shadow: var(--shadow-md, 0 4px 6px rgba(0,0,0,0.1));
        font-family: var(--font-family);
        font-size: var(--font-size-sm, 14px);
        min-width: 250px;
        max-width: 350px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        opacity: 0;
        transform: translateY(20px);
        animation: toastFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
      }
      .toast-item.error {
        border-left-color: var(--color-error, #D32F2F);
      }
      .toast-item.warning {
        border-left-color: var(--color-warning, #F57C00);
      }
      .toast-item.info {
        border-left-color: var(--color-info, #0288D1);
      }
      @keyframes toastFadeIn {
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Displays a dynamic toast alert notification.
   */
  showToast(message, type = "success") {
    const toast = document.createElement('div');
    toast.className = `toast-item ${type}`;
    toast.innerHTML = `
      <span>${message}</span>
      <button style="background:none; border:none; color:inherit; font-size:16px; cursor:pointer; margin-left:12px;" onclick="this.parentElement.remove()">×</button>
    `;
    this.toastContainer.appendChild(toast);
    
    // Auto-remove toast after 4 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}

// Instantiate global app profile
document.addEventListener("DOMContentLoaded", () => {
  window.eduOrbit = new EduOrbitApp();
});
