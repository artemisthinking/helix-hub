// 🔐 Helix Authentication - Enterprise login system with precise timestamps

class HelixAuth {
    constructor() {
        this.currentUser = null;
        this.loginTime = null;
        this.sessionTimer = null;
        this.token = null;
    }
    
    initialize() {
        this.bindEvents();
        this.setupTimestamps();
        this.checkExistingSession();
        console.log('🔐 Helix Authentication initialized');
    }
    
    bindEvents() {
        // Login form submission
        $('#loginForm').on('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        // Logout button
        $(document).on('click', '#logoutBtn', () => {
            this.handleLogout();
        });
        
        // Profile button
        $(document).on('click', '#userProfileBtn', () => {
            this.showUserProfile();
        });
        
        // Enter key shortcut for login
        $('#loginPassword').on('keypress', (e) => {
            if (e.which === 13) {
                this.handleLogin();
            }
        });
    }
    
    setupTimestamps() {
        // Update system time display every second
        setInterval(() => {
            const now = new Date();
            const utcTime = now.toISOString().replace('T', ' ').slice(0, 23) + ' UTC';
            $('#currentSystemTime').text(utcTime);
            
            // Update session duration if logged in
            if (this.loginTime) {
                this.updateSessionDuration();
            }
        }, 1000);
    }
    
    async handleLogin() {
        const username = $('#loginUsername').val().trim();
        const password = $('#loginPassword').val().trim();
        
        if (!username || !password) {
            this.showError('Please enter both username and password');
            return;
        }
        
        this.showLoading('#loginBtn', 'Authenticating...');
        this.hideError();
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.handleLoginSuccess(data);
            } else {
                this.showError(data.message || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.hideLoading('#loginBtn');
        }
    }
    
    handleLoginSuccess(data) {
        // Store authentication data
        this.token = data.access_token;
        this.currentUser = data.user_info;
        this.loginTime = new Date(data.user_info.last_login);
        
        // Store in localStorage for session persistence
        Helix.storage.set('auth_token', this.token);
        Helix.storage.set('current_user', this.currentUser);
        Helix.storage.set('login_time', this.loginTime.toISOString());
        
        // Log successful authentication
        console.log('🎉 Authentication successful:', this.currentUser);
        
        // Hide login form and show dashboard
        this.showDashboard();
        
        // Show success notification
        Helix.showNotification(
            `🎉 Welcome back, ${this.currentUser.full_name}!`,
            'success'
        );
        
        // Start session monitoring
        this.startSessionMonitoring();
    }
    
    showDashboard() {
        // Hide login container
        $('#loginContainer').fadeOut(300);
        
        // Show user display
        this.updateUserDisplay();
        $('#userDisplay').fadeIn(300);
        
        // Show main dashboard content
        $('.main-content').show();
        
        // Initialize dashboard if available
        if (window.dashboard) {
            window.dashboard.fetchDashboardData();
        }
    }
    
    updateUserDisplay() {
        if (!this.currentUser) return;
        
        const permissions = this.currentUser.permissions;
        
        // Update user info
        $('#userEmoji').text(permissions.emoji);
        $('#userFullName').text(this.currentUser.full_name);
        $('#userRole').text(this.currentUser.role.toUpperCase())
                     .css('background', permissions.color);
        $('#roleDescription').text(this.getRoleDescription(this.currentUser.role));
        
        // Update timestamps
        this.updateTimestamps();
        
        // Update permissions display
        this.updatePermissionsDisplay();
        
        // Apply role-based UI changes
        this.applyRoleBasedUI();
    }
    
    updateTimestamps() {
        if (!this.loginTime) return;
        
        const loginUtc = this.loginTime.toISOString().replace('T', ' ').slice(0, 23) + ' UTC';
        const loginLocal = this.loginTime.toLocaleString();
        
        $('#loginTimestamp').text(loginUtc);
        $('#localTimestamp').text(loginLocal);
        
        this.updateSessionDuration();
    }
    
    updateSessionDuration() {
        if (!this.loginTime) return;
        
        const now = new Date();
        const diff = now - this.loginTime;
        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        
        $('#sessionDuration').text(`${minutes}m ${seconds}s`);
    }
    
    updatePermissionsDisplay() {
        if (!this.currentUser) return;
        
        const permissions = this.currentUser.permissions;
        const permissionsHtml = Object.entries(permissions)
            .filter(([key, value]) => key.startsWith('can_'))
            .map(([key, value]) => {
                const label = key.replace('can_', '').replace('_', ' ');
                const icon = value ? '✅' : '❌';
                const className = value ? 'allowed' : 'denied';
                return `
                    <div class="permission-item ${className}">
                        <span>${icon}</span>
                        <span>${label}</span>
                    </div>
                `;
            }).join('');
        
        $('#permissionsGrid').html(permissionsHtml);
    }
    
    applyRoleBasedUI() {
        if (!this.currentUser) return;
        
        const permissions = this.currentUser.permissions;
        const role = this.currentUser.role;
        
        // Hide/show elements based on permissions
        if (!permissions.can_manage_users) {
            $('.admin-only').hide();
        }
        
        if (!permissions.can_upload_files) {
            $('.upload-section').hide();
        }
        
        if (!permissions.can_modify_settings) {
            $('.settings-controls').hide();
        }
        
        // Show role-specific dashboard sections
        $('.dashboard-section').hide();
        permissions.dashboard_sections.forEach(section => {
            if (section === 'all') {
                $('.dashboard-section').show();
            } else {
                $(`.dashboard-section.${section}`).show();
            }
        });
        
        // Add role-specific styling
        $('body').removeClass('role-admin role-dev role-auditor')
                 .addClass(`role-${role}`);
    }
    
    getRoleDescription(role) {
        const descriptions = {
            'admin': 'Full system administrator',
            'dev': 'Development & file processing',
            'auditor': 'Read-only audit access'
        };
        return descriptions[role] || 'Unknown role';
    }
    
    startSessionMonitoring() {
        // Check session validity every 5 minutes
        this.sessionTimer = setInterval(() => {
            this.validateSession();
        }, 5 * 60 * 1000);
        
        // Auto-logout after 8 hours
        setTimeout(() => {
            this.handleAutoLogout();
        }, 8 * 60 * 60 * 1000);
    }
    
    async validateSession() {
        if (!this.token) return;
        
        try {
            const response = await fetch('/api/auth/validate', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (!response.ok) {
                this.handleSessionExpired();
            }
        } catch (error) {
            console.warn('Session validation failed:', error);
        }
    }
    
    handleLogout() {
        Helix.showNotification('👋 Logging out...', 'info');
        
        setTimeout(() => {
            this.clearSession();
            this.showLoginForm();
        }, 1000);
    }
    
    handleAutoLogout() {
        Helix.showNotification('⏰ Session expired - please login again', 'warning');
        
        setTimeout(() => {
            this.clearSession();
            this.showLoginForm();
        }, 3000);
    }
    
    handleSessionExpired() {
        Helix.showNotification('🔒 Session expired - please login again', 'warning');
        this.clearSession();
        this.showLoginForm();
    }
    
    clearSession() {
        // Clear authentication data
        this.token = null;
        this.currentUser = null;
        this.loginTime = null;
        
        // Clear localStorage
        Helix.storage.remove('auth_token');
        Helix.storage.remove('current_user');
        Helix.storage.remove('login_time');
        
        // Stop session monitoring
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
            this.sessionTimer = null;
        }
        
        // Reset UI
        $('body').removeClass('role-admin role-dev role-auditor');
        $('.dashboard-section').show();
        $('.admin-only, .upload-section, .settings-controls').show();
    }
    
    showLoginForm() {
        // Hide dashboard elements
        $('#userDisplay').hide();
        $('.main-content').hide();
        
        // Show login form
        $('#loginContainer').fadeIn(300);
        
        // Clear form
        $('#loginForm')[0].reset();
        this.hideError();
        
        // Focus on username field
        setTimeout(() => {
            $('#loginUsername').focus();
        }, 300);
    }
    
    checkExistingSession() {
        const token = Helix.storage.get('auth_token');
        const user = Helix.storage.get('current_user');
        const loginTimeStr = Helix.storage.get('login_time');
        
        if (token && user && loginTimeStr) {
            this.token = token;
            this.currentUser = user;
            this.loginTime = new Date(loginTimeStr);
            
            // Check if session is still valid (less than 8 hours old)
            const sessionAge = (new Date() - this.loginTime) / (1000 * 60 * 60);
            
            if (sessionAge < 8) {
                console.log('🔄 Restoring previous session');
                this.showDashboard();
                this.startSessionMonitoring();
                return;
            }
        }
        
        // No valid session, show login form
        this.showLoginForm();
    }
    
    showUserProfile() {
        if (!this.currentUser) return;
        
        const profileHtml = `
            <div class="user-profile-modal">
                <h3>${this.currentUser.permissions.emoji} User Profile</h3>
                <div class="profile-info">
                    <p><strong>Name:</strong> ${this.currentUser.full_name}</p>
                    <p><strong>Username:</strong> ${this.currentUser.username}</p>
                    <p><strong>Email:</strong> ${this.currentUser.email}</p>
                    <p><strong>Role:</strong> ${this.currentUser.role}</p>
                    <p><strong>Login Time:</strong> ${this.loginTime.toLocaleString()}</p>
                    <p><strong>Session Duration:</strong> ${$('#sessionDuration').text()}</p>
                </div>
            </div>
        `;
        
        // Would show in a modal - for now just log it
        console.log('User Profile:', this.currentUser);
        Helix.showNotification('👤 Profile info logged to console', 'info');
    }
    
    // Utility methods
    showError(message) {
        $('#loginError').text(message).fadeIn();
    }
    
    hideError() {
        $('#loginError').fadeOut();
    }
    
    showLoading(selector, text) {
        $(selector).prop('disabled', true).text(text);
    }
    
    hideLoading(selector) {
        $(selector).prop('disabled', false).text('🚀 Login to Dashboard');
    }
    
    // Get current user for other components
    getCurrentUser() {
        return this.currentUser;
    }
    
    // Get auth token for API calls
    getAuthToken() {
        return this.token;
    }
    
    // Check if user has specific permission
    hasPermission(permission) {
        return this.currentUser?.permissions?.[permission] || false;
    }
}

// Global authentication instance
let auth = null;

// Initialize authentication
function initializeAuthentication() {
    auth = new HelixAuth();
    auth.initialize();
}

// Helper function for demo user buttons
function fillLoginForm(username, password) {
    $('#loginUsername').val(username);
    $('#loginPassword').val(password);
    $('#loginUsername, #loginPassword').addClass('demo-filled');
    
    // Remove highlight after 2 seconds
    setTimeout(() => {
        $('#loginUsername, #loginPassword').removeClass('demo-filled');
    }, 2000);
}

// Auto-initialize when DOM is ready
$(document).ready(() => {
    initializeAuthentication();
});

// Make auth available globally
window.auth = auth;
