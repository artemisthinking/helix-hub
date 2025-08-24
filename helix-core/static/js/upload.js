// 📤 Helix Upload - Multi-file upload with routing

class HelixUpload {
    constructor() {
        this.selectedFiles = new Map();
        this.routingData = {};
        this.departmentProcessMap = {
            'FINANCE': ['PAYMENT', 'RECONCILIATION', 'REPORTING'],
            'TREASURY': ['LIQUIDITY', 'INVESTMENT', 'HEDGING'],
            'RISK': ['ASSESSMENT', 'MONITORING', 'REPORTING'],
            'COMPLIANCE': ['AML', 'KYC', 'REPORTING'],
            'OPERATIONS': ['SETTLEMENT', 'PROCESSING', 'MONITORING']
        };
        this.processFileTypeMap = {
            'PAYMENT': ['MT940', 'CAMT.053', 'BAI2'],
            'RECONCILIATION': ['MT940', 'CAMT.053', 'CSV'],
            'REPORTING': ['CSV', 'XML'],
            'LIQUIDITY': ['MT940', 'CAMT.053'],
            'INVESTMENT': ['CSV', 'XML'],
            'HEDGING': ['CSV', 'XML'],
            'ASSESSMENT': ['CSV', 'XML'],
            'MONITORING': ['MT940', 'CAMT.053', 'CSV'],
            'AML': ['CSV', 'XML'],
            'KYC': ['CSV', 'XML'],
            'SETTLEMENT': ['MT940', 'CAMT.053', 'BAI2'],
            'PROCESSING': ['MT940', 'CAMT.053', 'BAI2', 'CSV']
        };
        this.fileTypeValidation = {
            'MT940': ['.mt940', '.txt'],
            'CAMT.053': ['.xml'],
            'BAI2': ['.bai', '.bai2', '.txt'],
            'CSV': ['.csv'],
            'XML': ['.xml']
        };
    }
    
    initialize() {
        this.bindElements();
        this.bindEvents();
        this.setupDragDrop();
        console.log('📤 Helix Upload initialized with Swiss precision!');
    }
    
    bindElements() {
        this.elements = {
            departmentSelect: document.getElementById('departmentSelect'),
            processSelect: document.getElementById('processSelect'),
            fileTypeSelect: document.getElementById('fileTypeSelect'),
            prioritySelect: document.getElementById('prioritySelect'),
            uploadNotes: document.getElementById('uploadNotes'),
            fileUploadArea: document.getElementById('fileUploadArea'),
            fileInput: document.getElementById('fileInput'),
            fileQueue: document.getElementById('fileQueue'),
            fileList: document.getElementById('fileList'),
            clearFilesBtn: document.getElementById('clearFilesBtn'),
            validateBtn: document.getElementById('validateBtn'),
            uploadBtn: document.getElementById('uploadBtn')
        };
    }
    
    bindEvents() {
        // Routing cascade
        this.elements.departmentSelect.addEventListener('change', () => {
            this.updateProcessOptions();
        });
        
        this.elements.processSelect.addEventListener('change', () => {
            this.updateFileTypeOptions();
        });
        
        this.elements.fileTypeSelect.addEventListener('change', () => {
            this.updateFileValidation();
        });
        
        // File selection
        this.elements.fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });
        
        // Button events
        this.elements.clearFilesBtn.addEventListener('click', () => {
            this.clearAllFiles();
        });
        
        this.elements.validateBtn.addEventListener('click', () => {
            this.validateAllFiles();
        });
        
        this.elements.uploadBtn.addEventListener('click', () => {
            this.uploadFiles();
        });
        
        // Upload area click
        this.elements.fileUploadArea.addEventListener('click', () => {
            this.elements.fileInput.click();
        });
    }
    
    setupDragDrop() {
        const area = this.elements.fileUploadArea;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            area.addEventListener(eventName, () => {
                area.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, () => {
                area.classList.remove('dragover');
            }, false);
        });
        
        area.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFileSelection(files);
        }, false);
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    updateProcessOptions() {
        const department = this.elements.departmentSelect.value;
        const processSelect = this.elements.processSelect;
        
        // Clear existing options
        processSelect.innerHTML = '<option value="">Select Process...</option>';
        
        if (department && this.departmentProcessMap[department]) {
            processSelect.disabled = false;
            
            this.departmentProcessMap[department].forEach(process => {
                const option = document.createElement('option');
                option.value = process;
                option.textContent = process.charAt(0) + process.slice(1).toLowerCase();
                processSelect.appendChild(option);
            });
        } else {
            processSelect.disabled = true;
        }
        
        // Reset downstream selects
        this.elements.fileTypeSelect.innerHTML = '<option value="">Select File Type...</option>';
        this.elements.fileTypeSelect.disabled = true;
        this.updateButtons();
    }
    
    updateFileTypeOptions() {
        const process = this.elements.processSelect.value;
        const fileTypeSelect = this.elements.fileTypeSelect;
        
        // Clear existing options
        fileTypeSelect.innerHTML = '<option value="">Select File Type...</option>';
        
        if (process && this.processFileTypeMap[process]) {
            fileTypeSelect.disabled = false;
            
            this.processFileTypeMap[process].forEach(fileType => {
                const option = document.createElement('option');
                option.value = fileType;
                option.textContent = fileType;
                fileTypeSelect.appendChild(option);
            });
        } else {
            fileTypeSelect.disabled = true;
        }
        
        this.updateButtons();
    }
    
    updateFileValidation() {
        const fileType = this.elements.fileTypeSelect.value;
        
        if (fileType && this.fileTypeValidation[fileType]) {
            const extensions = this.fileTypeValidation[fileType];
            this.elements.fileInput.accept = extensions.join(',');
            
            // Update file types display
            const fileTypesElement = this.elements.fileUploadArea.querySelector('.file-types');
            if (fileTypesElement) {
                fileTypesElement.textContent = `Supported: ${fileType} files (${extensions.join(', ')})`;
            }
        }
        
        this.updateButtons();
    }
    
    handleFileSelection(files) {
        Array.from(files).forEach(file => {
            const fileId = this.generateFileId();
            const validation = this.validateFile(file);
            
            this.selectedFiles.set(fileId, {
                file: file,
                id: fileId,
                name: file.name,
                size: file.size,
                type: file.type,
                validation: validation,
                status: validation.valid ? 'ready' : 'error',
                progress: 0
            });
        });
        
        this.updateFileQueue();
        this.updateButtons();
    }
    
    validateFile(file) {
        const selectedFileType = this.elements.fileTypeSelect.value;
        
        if (!selectedFileType) {
            return {
                valid: false,
                errors: ['Please select a file type first']
            };
        }
        
        const errors = [];
        const allowedExtensions = this.fileTypeValidation[selectedFileType] || [];
        
        // Check file extension
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(fileExtension)) {
            errors.push(`Invalid file type. Expected: ${allowedExtensions.join(', ')}`);
        }
        
        // Check file size (max 50MB)
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            errors.push('File size exceeds 50MB limit');
        }
        
        // Basic file content validation
        if (selectedFileType === 'MT940' && !file.name.toLowerCase().includes('mt940') && !fileExtension.includes('.txt')) {
            errors.push('MT940 files should have .mt940 or .txt extension');
        }
        
        if (selectedFileType === 'CAMT.053' && fileExtension !== '.xml') {
            errors.push('CAMT.053 files must be XML format');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
    
    updateFileQueue() {
        if (this.selectedFiles.size === 0) {
            this.elements.fileQueue.style.display = 'none';
            return;
        }
        
        this.elements.fileQueue.style.display = 'block';
        
        const fileListHTML = Array.from(this.selectedFiles.values()).map(fileData => {
            const fileTypeIcon = this.getFileTypeIcon(fileData.name);
            const statusClass = fileData.validation.valid ? 'ready' : 'error';
            const statusText = fileData.validation.valid ? '✅ Ready' : '❌ Invalid';
            
            let errorMessages = '';
            if (!fileData.validation.valid) {
                errorMessages = `
                    <div class="file-errors">
                        ${fileData.validation.errors.map(error => `<div class="error-message">${error}</div>`).join('')}
                    </div>
                `;
            }
            
            return `
                <div class="file-item" data-file-id="${fileData.id}">
                    <div class="file-icon">${fileTypeIcon}</div>
                    <div class="file-info">
                        <div class="file-name">${fileData.name}</div>
                        <div class="file-meta">
                            ${this.formatFileSize(fileData.size)} • ${this.getSelectedRouting()}
                        </div>
                        ${errorMessages}
                        <div class="progress-bar" style="display: none;">
                            <div class="progress-fill" style="width: ${fileData.progress}%"></div>
                        </div>
                    </div>
                    <div class="file-status ${statusClass}">${statusText}</div>
                    <button class="btn btn-secondary btn-sm" onclick="upload.removeFile('${fileData.id}')">
                        🗑️
                    </button>
                </div>
            `;
        }).join('');
        
        this.elements.fileList.innerHTML = fileListHTML;
    }
    
    getFileTypeIcon(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'mt940': '💰',
            'xml': '💼',
            'bai': '🏛️',
            'bai2': '🏛️',
            'csv': '📊',
            'txt': '📄'
        };
        return iconMap[extension] || '📄';
    }
    
    getSelectedRouting() {
        const dept = this.elements.departmentSelect.value;
        const proc = this.elements.processSelect.value;
        const type = this.elements.fileTypeSelect.value;
        
        if (dept && proc && type) {
            return `${dept}-${proc}-${type}`;
        }
        return 'Routing not set';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    removeFile(fileId) {
        this.selectedFiles.delete(fileId);
        this.updateFileQueue();
        this.updateButtons();
        showNotification(`🗑️ File removed from queue`, 'info');
    }
    
    clearAllFiles() {
        this.selectedFiles.clear();
        this.elements.fileInput.value = '';
        this.updateFileQueue();
        this.updateButtons();
        showNotification('🗑️ All files cleared', 'info');
    }
    
    validateAllFiles() {
        let validCount = 0;
        let invalidCount = 0;
        
        this.selectedFiles.forEach(fileData => {
            const validation = this.validateFile(fileData.file);
            fileData.validation = validation;
            fileData.status = validation.valid ? 'ready' : 'error';
            
            if (validation.valid) {
                validCount++;
            } else {
                invalidCount++;
            }
        });
        
        this.updateFileQueue();
        
        if (invalidCount === 0) {
            showNotification(`✅ All ${validCount} files are valid and ready for upload`, 'success');
        } else {
            showNotification(`⚠️ ${validCount} valid, ${invalidCount} invalid files found`, 'warning');
        }
    }
    
    async uploadFiles() {
        const validFiles = Array.from(this.selectedFiles.values()).filter(f => f.validation.valid);
        
        if (validFiles.length === 0) {
            showNotification('❌ No valid files to upload', 'error');
            return;
        }
        
        const routingData = {
            department: this.elements.departmentSelect.value,
            process: this.elements.processSelect.value,
            file_type: this.elements.fileTypeSelect.value
        };
        
        const priority = this.elements.prioritySelect.value;
        const notes = this.elements.uploadNotes.value;
        
        showNotification(`🚀 Starting upload of ${validFiles.length} files...`, 'info');
        
        // Upload files one by one
        for (const fileData of validFiles) {
            try {
                await this.uploadSingleFile(fileData, routingData, priority, notes);
            } catch (error) {
                console.error('Upload error:', error);
                showNotification(`❌ Failed to upload ${fileData.name}: ${error.message}`, 'error');
            }
        }
        
        // Clear successful uploads
        this.clearAllFiles();
        showNotification('🎉 All files uploaded successfully!', 'success');
        
        // Refresh dashboard if available
        if (window.dashboard) {
            window.dashboard.fetchDashboardData();
        }
    }
    
    async uploadSingleFile(fileData, routingData, priority, notes) {
        const formData = new FormData();
        formData.append('file', fileData.file);
        formData.append('routing_code', JSON.stringify(routingData));
        formData.append('priority', priority);
        formData.append('notes', notes);
        
        // Update file status to uploading
        fileData.status = 'uploading';
        this.updateFileProgress(fileData.id, 0);
        
        const response = await fetch('/api/files/upload', {
            method: 'POST',
            body: formData,
            headers: {
                // JWT token would be added here if available
                // 'Authorization': `Bearer ${getJWTToken()}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Upload failed');
        }
        
        const result = await response.json();
        
        // Update file status to completed
        fileData.status = 'completed';
        this.updateFileProgress(fileData.id, 100);
        
        return result;
    }
    
    updateFileProgress(fileId, progress) {
        const fileElement = document.querySelector(`[data-file-id="${fileId}"]`);
        if (fileElement) {
            const progressBar = fileElement.querySelector('.progress-bar');
            const progressFill = fileElement.querySelector('.progress-fill');
            const statusElement = fileElement.querySelector('.file-status');
            
            if (progress > 0) {
                progressBar.style.display = 'block';
                progressFill.style.width = `${progress}%`;
            }
            
            if (progress === 100) {
                statusElement.textContent = '✅ Uploaded';
                statusElement.className = 'file-status completed';
            } else if (progress > 0) {
                statusElement.textContent = '📤 Uploading...';
                statusElement.className = 'file-status processing';
            }
        }
    }
    
    updateButtons() {
        const hasValidRouting = this.elements.departmentSelect.value && 
                              this.elements.processSelect.value && 
                              this.elements.fileTypeSelect.value;
        
        const hasFiles = this.selectedFiles.size > 0;
        const hasValidFiles = Array.from(this.selectedFiles.values()).some(f => f.validation.valid);
        
        this.elements.clearFilesBtn.disabled = !hasFiles;
        this.elements.validateBtn.disabled = !hasFiles;
        this.elements.uploadBtn.disabled = !hasValidRouting || !hasValidFiles;
    }
    
    generateFileId() {
        return 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// Global upload instance
let upload = null;

// Initialize upload functionality
function initializeUploadSection() {
    upload = new HelixUpload();
    upload.initialize();
}

// Make removeFile available globally
window.upload = upload;
