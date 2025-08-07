// Multi-Clinic Appointment System - Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializeFormValidation();
    initializeSearchFilters();
    initializeDateTimeHandlers();
    setupAjaxErrorHandling();
    
    // Add loading states to forms
    setupLoadingStates();
    
    // Initialize auto-refresh for certain pages
    setupAutoRefresh();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Form validation enhancements
function initializeFormValidation() {
    // Add real-time validation to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Add input event listeners for real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });
}

// Field validation function
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const isRequired = field.hasAttribute('required');
    
    // Clear previous validation
    field.classList.remove('is-valid', 'is-invalid');
    
    // Check if required field is empty
    if (isRequired && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Skip validation if field is empty and not required
    if (!value && !isRequired) {
        return true;
    }
    
    // Type-specific validation
    switch (type) {
        case 'email':
            if (!isValidEmail(value)) {
                showFieldError(field, 'Please enter a valid email address');
                return false;
            }
            break;
            
        case 'password':
            if (value.length < 6) {
                showFieldError(field, 'Password must be at least 6 characters long');
                return false;
            }
            break;
            
        case 'tel':
            if (!isValidPhone(value)) {
                showFieldError(field, 'Please enter a valid phone number');
                return false;
            }
            break;
            
        case 'number':
            const min = field.getAttribute('min');
            const max = field.getAttribute('max');
            const numValue = parseFloat(value);
            
            if (isNaN(numValue)) {
                showFieldError(field, 'Please enter a valid number');
                return false;
            }
            
            if (min && numValue < parseFloat(min)) {
                showFieldError(field, `Value must be at least ${min}`);
                return false;
            }
            
            if (max && numValue > parseFloat(max)) {
                showFieldError(field, `Value must not exceed ${max}`);
                return false;
            }
            break;
            
        case 'date':
            if (!isValidDate(value)) {
                showFieldError(field, 'Please enter a valid date');
                return false;
            }
            break;
            
        case 'time':
            if (!isValidTime(value)) {
                showFieldError(field, 'Please enter a valid time');
                return false;
            }
            break;
    }
    
    // Show success state
    field.classList.add('is-valid');
    return true;
}

// Show field error
function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    // Find or create error message element
    let errorElement = field.parentNode.querySelector('.invalid-feedback');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'invalid-feedback';
        field.parentNode.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
}

// Validation helper functions
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    const digitsOnly = phone.replace(/\D/g, '');
    return digitsOnly.length >= 10 && digitsOnly.length <= 15;
}

function isValidDate(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date);
}

function isValidTime(timeString) {
    const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
    return timeRegex.test(timeString);
}

// Search and filter functionality
function initializeSearchFilters() {
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const target = this.getAttribute('data-search');
            const filter = this.value.toLowerCase();
            const items = document.querySelectorAll(target);
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                const shouldShow = text.includes(filter);
                item.style.display = shouldShow ? '' : 'none';
            });
        });
    });
}

// Date and time handlers
function initializeDateTimeHandlers() {
    // Set minimum date to today for date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    
    dateInputs.forEach(input => {
        if (input.hasAttribute('data-min-today')) {
            input.min = today;
        }
    });
    
    // Time slot conflict detection
    const timeInputs = document.querySelectorAll('input[type="time"]');
    timeInputs.forEach(input => {
        input.addEventListener('change', checkTimeConflicts);
    });
}

// Check for time conflicts
function checkTimeConflicts() {
    const form = this.closest('form');
    if (!form) return;
    
    const startTime = form.querySelector('input[name="start_time"]');
    const endTime = form.querySelector('input[name="end_time"]');
    
    if (startTime && endTime && startTime.value && endTime.value) {
        if (startTime.value >= endTime.value) {
            showFieldError(endTime, 'End time must be after start time');
        } else {
            endTime.classList.remove('is-invalid');
            endTime.classList.add('is-valid');
        }
    }
}

// Loading states for forms
function setupLoadingStates() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            const spinner = this.querySelector('.spinner-border');
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('loading');
            }
            
            if (spinner) {
                spinner.classList.remove('d-none');
            }
        });
    });
}

// Auto-refresh for dashboards
function setupAutoRefresh() {
    const autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');
    
    autoRefreshElements.forEach(element => {
        const interval = parseInt(element.getAttribute('data-auto-refresh')) * 1000;
        if (interval > 0) {
            setInterval(() => {
                refreshElement(element);
            }, interval);
        }
    });
}

// Refresh element content
function refreshElement(element) {
    const url = element.getAttribute('data-refresh-url') || window.location.href;
    
    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromEntries(html, 'text/html');
        const newContent = doc.querySelector(`[data-auto-refresh="${element.getAttribute('data-auto-refresh')}"]`);
        
        if (newContent) {
            element.innerHTML = newContent.innerHTML;
        }
    })
    .catch(error => {
        console.log('Auto-refresh failed:', error);
    });
}

// AJAX error handling
function setupAjaxErrorHandling() {
    // Global error handler for fetch requests
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response;
            })
            .catch(error => {
                console.error('Fetch error:', error);
                showNotification('An error occurred. Please try again.', 'error');
                throw error;
            });
    };
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
    
    return notification;
}

// Utility functions
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatTime(time) {
    return new Date(`2000-01-01T${time}`).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in templates
window.MedicalSystem = {
    showNotification,
    formatDate,
    formatTime,
    debounce,
    validateField
};

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const href = this.getAttribute('href');
        if (href && href !== '#') {
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Back to top button
function addBackToTopButton() {
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    backToTopBtn.className = 'btn btn-primary position-fixed';
    backToTopBtn.style.cssText = `
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: none;
    `;
    
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    document.body.appendChild(backToTopBtn);
    
    // Show/hide based on scroll position
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.display = 'block';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });
}

// Initialize back to top button
addBackToTopButton();

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+/ or Cmd+/ for search
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[data-search]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape key to close modals
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            if (modal) {
                modal.hide();
            }
        }
    }
});

// Print functionality
function printPage() {
    window.print();
}

// Export data functionality
function exportToCSV(data, filename) {
    const csvContent = "data:text/csv;charset=utf-8," 
        + data.map(row => row.join(",")).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Local storage helpers
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
        return false;
    }
}

function loadFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return null;
    }
}

// Session timeout warning
function setupSessionTimeout() {
    let sessionWarningShown = false;
    const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
    const WARNING_TIME = 5 * 60 * 1000; // 5 minutes before timeout
    
    let lastActivity = Date.now();
    
    // Track user activity
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, () => {
            lastActivity = Date.now();
            sessionWarningShown = false;
        });
    });
    
    // Check session timeout
    setInterval(() => {
        const timeSinceLastActivity = Date.now() - lastActivity;
        
        if (timeSinceLastActivity > SESSION_TIMEOUT - WARNING_TIME && !sessionWarningShown) {
            sessionWarningShown = true;
            showNotification(
                'Your session will expire in 5 minutes. Please save your work.',
                'warning',
                10000
            );
        }
        
        if (timeSinceLastActivity > SESSION_TIMEOUT) {
            showNotification('Session expired. Redirecting to login...', 'error');
            setTimeout(() => {
                window.location.href = '/auth/login';
            }, 3000);
        }
    }, 60000); // Check every minute
}

// Initialize session timeout for authenticated users
if (document.querySelector('.navbar .dropdown-toggle')) {
    setupSessionTimeout();
}
