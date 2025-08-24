// 🎯 Helix Base - Common functionality for all pages

// Global utilities
window.Helix = {
    version: '1.0.0',
    initialized: false,
    
    // Common initialization
    init() {
        if (this.initialized) return;
        
        console.log('🎛️ Helix Base System initializing...');
        this.setupGlobalErrorHandler();
        this.setupCommonEvents();
        this.initialized = true;
        console.log('✅ Helix Base System ready!');
    },
    
    // Global error handling
    setupGlobalErrorHandler() {
        window.addEventListener('error', (event) => {
            console.error('🚨 Global error:', event.error);
            this.showNotification('An unexpected error occurred', 'error');
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            console.error('🚨 Unhandled promise rejection:', event.reason);
            this.showNotification('A network error occurred', 'error');
        });
    },
    
    // Common event bindings
    setupCommonEvents() {
        // Smooth scrolling for all anchor links
        $(document).on('click', 'a[href^="#"]', function(e) {
            e.preventDefault();
            const target = $(this.getAttribute('href'));
            if (target.length) {
                $('html, body').animate({
                    scrollTop: target.offset().top - 80
                }, 500);
            }
        });
        
        // Auto-hide notifications after 5 seconds
        $(document).on('click', '.notification-close', function() {
            $(this).closest('.notification').fadeOut();
        });
        
        // Form validation helpers
        $(document).on('submit', 'form[data-validate]', function(e) {
            if (!Helix.validateForm(this)) {
                e.preventDefault();
            }
        });
    },
    
    // Show notification
    showNotification(message, type = 'info', duration = 5000) {
        const notification = $(`
            <div class="notification notification-${type}">
                <span class="notification-message">${message}</span>
                <button class="notification-close" type="button">&times;</button>
            </div>
        `);
        
        $('body').append(notification);
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                notification.fadeOut(() => notification.remove());
            }, duration);
        }
        
        // Remove on click
        notification.find('.notification-close').on('click', () => {
            notification.fadeOut(() => notification.remove());
        });
        
        return notification;
    },
    
    // Form validation
    validateForm(form) {
        const $form = $(form);
        let isValid = true;
        
        // Clear previous errors
        $form.find('.form-error').remove();
        $form.find('.form-input, .form-select').removeClass('error');
        
        // Check required fields
        $form.find('[required]').each(function() {
            const $field = $(this);
            const value = $field.val().trim();
            
            if (!value) {
                isValid = false;
                $field.addClass('error');
                $field.after('<div class="form-error">This field is required</div>');
            }
        });
        
        // Check email fields
        $form.find('input[type="email"]').each(function() {
            const $field = $(this);
            const value = $field.val().trim();
            
            if (value && !Helix.isValidEmail(value)) {
                isValid = false;
                $field.addClass('error');
                $field.after('<div class="form-error">Please enter a valid email address</div>');
            }
        });
        
        return isValid;
    },
    
    // Utility functions
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    },
    
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    timeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = now - time;
        
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (seconds < 60) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    },
    
    // API helpers
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        // Add JWT token if available
        const token = localStorage.getItem('jwt_token');
        if (token) {
            defaultOptions.headers.Authorization = `Bearer ${token}`;
        }
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },
    
    // Loading state management
    showLoading(element, message = 'Loading...') {
        const $element = $(element);
        $element.addClass('loading');
        
        if (message) {
            $element.attr('data-loading-message', message);
        }
    },
    
    hideLoading(element) {
        const $element = $(element);
        $element.removeClass('loading');
        $element.removeAttr('data-loading-message');
    },
    
    // Local storage helpers
    storage: {
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.warn('Failed to save to localStorage:', e);
            }
        },
        
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.warn('Failed to read from localStorage:', e);
                return defaultValue;
            }
        },
        
        remove(key) {
            try {
                localStorage.removeItem(key);
            } catch (e) {
                console.warn('Failed to remove from localStorage:', e);
            }
        }
    },
    
    // Theme management
    theme: {
        current: 'light',
        
        init() {
            const saved = Helix.storage.get('theme', 'light');
            this.set(saved);
        },
        
        set(theme) {
            this.current = theme;
            document.documentElement.setAttribute('data-theme', theme);
            Helix.storage.set('theme', theme);
        },
        
        toggle() {
            const newTheme = this.current === 'light' ? 'dark' : 'light';
            this.set(newTheme);
            return newTheme;
        }
    }
};

// Auto-initialize when DOM is ready
$(document).ready(function() {
    Helix.init();
    Helix.theme.init();
});

// Global helper functions for backward compatibility
function showNotification(message, type, duration) {
    return Helix.showNotification(message, type, duration);
}

function formatFileSize(bytes) {
    return Helix.formatFileSize(bytes);
}

function timeAgo(timestamp) {
    return Helix.timeAgo(timestamp);
}
