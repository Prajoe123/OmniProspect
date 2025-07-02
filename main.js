// Main JavaScript functionality for LinkedIn Scraper

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('button[onclick*="confirm"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Dynamic form field updates
    const searchQueryField = document.getElementById('search_query');
    if (searchQueryField) {
        searchQueryField.addEventListener('input', function() {
            // Provide real-time feedback on search query
            const value = this.value.trim();
            const feedback = document.querySelector('.search-feedback');
            
            if (feedback) {
                if (value.length < 3) {
                    feedback.textContent = 'Enter at least 3 characters for better results';
                    feedback.className = 'form-text text-warning';
                } else if (value.length > 50) {
                    feedback.textContent = 'Keep search query under 50 characters for best results';
                    feedback.className = 'form-text text-warning';
                } else {
                    feedback.textContent = 'Good search query length';
                    feedback.className = 'form-text text-success';
                }
            }
        });
    }

    // Progress tracking for long operations
    function showProgress(message) {
        const progressAlert = document.createElement('div');
        progressAlert.className = 'alert alert-info d-flex align-items-center';
        progressAlert.innerHTML = `
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            ${message}
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(progressAlert, container.firstChild);
        }
        
        return progressAlert;
    }

    // Enhanced table functionality
    const tables = document.querySelectorAll('.table');
    tables.forEach(function(table) {
        // Add sorting capability (basic)
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(function(header) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const sortKey = this.dataset.sort;
                sortTable(table, sortKey);
            });
        });
    });

    // Basic table sorting function
    function sortTable(table, column) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const columnIndex = Array.from(table.querySelectorAll('th')).findIndex(th => th.dataset.sort === column);
        
        if (columnIndex === -1) return;
        
        const sortedRows = rows.sort((a, b) => {
            const aText = a.cells[columnIndex].textContent.trim();
            const bText = b.cells[columnIndex].textContent.trim();
            
            // Try numeric sort first
            const aNum = parseFloat(aText);
            const bNum = parseFloat(bText);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return aNum - bNum;
            }
            
            // Fall back to string sort
            return aText.localeCompare(bText);
        });
        
        // Reorder rows
        sortedRows.forEach(row => tbody.appendChild(row));
    }

    // Real-time search filtering (for client-side filtering)
    const searchInputs = document.querySelectorAll('[data-search-target]');
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const target = document.querySelector(this.dataset.searchTarget);
            const searchTerm = this.value.toLowerCase();
            
            if (target) {
                const items = target.querySelectorAll('[data-searchable]');
                items.forEach(function(item) {
                    const text = item.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }
        });
    });

    // Batch operations
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('input[name="selected_items"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateBatchActions();
        });
    }

    // Update batch action buttons based on selection
    function updateBatchActions() {
        const selectedCount = document.querySelectorAll('input[name="selected_items"]:checked').length;
        const batchActions = document.querySelectorAll('.batch-action');
        
        batchActions.forEach(function(action) {
            action.disabled = selectedCount === 0;
            const countSpan = action.querySelector('.selected-count');
            if (countSpan) {
                countSpan.textContent = selectedCount;
            }
        });
    }

    // Individual checkbox change handlers
    const itemCheckboxes = document.querySelectorAll('input[name="selected_items"]');
    itemCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', updateBatchActions);
    });

    // Initialize batch actions state
    updateBatchActions();

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K: Quick search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[placeholder*="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-save form data to localStorage
    const autoSaveForms = document.querySelectorAll('form[data-auto-save]');
    autoSaveForms.forEach(function(form) {
        const formId = form.id || 'form_' + Date.now();
        
        // Load saved data
        const savedData = localStorage.getItem('form_data_' + formId);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(function(name) {
                    const field = form.querySelector(`[name="${name}"]`);
                    if (field) {
                        if (field.type === 'checkbox') {
                            field.checked = data[name];
                        } else {
                            field.value = data[name];
                        }
                    }
                });
            } catch (e) {
                console.warn('Failed to load form data:', e);
            }
        }
        
        // Save data on change
        form.addEventListener('input', function() {
            const formData = new FormData(form);
            const data = {};
            for (let [name, value] of formData.entries()) {
                data[name] = value;
            }
            localStorage.setItem('form_data_' + formId, JSON.stringify(data));
        });
        
        // Clear saved data on successful submit
        form.addEventListener('submit', function() {
            localStorage.removeItem('form_data_' + formId);
        });
    });
});

// Utility functions
window.LinkedInScraper = {
    // Show loading state
    showLoading: function(element, message = 'Loading...') {
        element.disabled = true;
        element.dataset.originalHtml = element.innerHTML;
        element.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>${message}`;
    },
    
    // Hide loading state
    hideLoading: function(element) {
        element.disabled = false;
        if (element.dataset.originalHtml) {
            element.innerHTML = element.dataset.originalHtml;
            delete element.dataset.originalHtml;
        }
    },
    
    // Format numbers with commas
    formatNumber: function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    
    // Copy text to clipboard
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                console.log('Text copied to clipboard');
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        }
    },
    
    // Validate email address
    isValidEmail: function(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },
    
    // Debounce function
    debounce: function(func, wait) {
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
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.LinkedInScraper;
}
