let currentProjects = [];
let isQuickCaptureOpen = false;
let suggestionsPanelOpen = false;

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupKeyboardShortcuts();
    setupEventListeners();
    loadInitialData();
});

function initializeApp() {
    console.log('Focus app initialized');
    
    const firstColor = document.querySelector('label[for="color1"]');
    if (firstColor) {
        selectColor(firstColor);
    }
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openQuickCapture();
        }
        
        if (e.key === 'Escape') {
            closeQuickCapture();
            closeProjectModal();
            toggleSmartSuggestions(false);
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            toggleSmartSuggestions();
        }
    });
}

function setupEventListeners() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
    
    setupFormSubmissions();
    
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
            }
        });
    });
}

function setupFormSubmissions() {
    const taskForm = document.getElementById('quick-task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitQuickTask();
        });
    }
    
    const ideaForm = document.getElementById('quick-idea-form');
    if (ideaForm) {
        ideaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitQuickIdea();
        });
    }
    
    const linkForm = document.getElementById('quick-link-form');
    if (linkForm) {
        linkForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitQuickLink();
        });
    }

    const noteForm = document.getElementById('quick-note-form');
    if (noteForm) {
        noteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitQuickNote();
        });
    }
}

function loadInitialData() {
    loadProjects();
}

function loadProjects() {
    const projectCards = document.querySelectorAll('.project-card');
    currentProjects = Array.from(projectCards).map(card => ({
        id: card.onclick.toString().match(/project_detail\/(\d+)/)?.[1],
        name: card.querySelector('.project-title').textContent,
        color: card.style.getPropertyValue('--project-color') || '#1e40af'
    }));
    
    updateProjectSelects();
}

function updateProjectSelects() {
    const selects = ['task-project', 'idea-project', 'link-project', 'note-project'];
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            const currentValue = select.value;
            select.innerHTML = '<option value="">No Project</option>';
            
            currentProjects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = project.name;
                select.appendChild(option);
            });
            
            if (currentValue) {
                select.value = currentValue;
            }
        }
    });
}

function openQuickCapture(tab = 'task') {
    const modal = document.getElementById('quick-capture-modal');
    modal.classList.remove('hidden');
    
    switchTab(tab);
    isQuickCaptureOpen = true;
    
    setTimeout(() => {
        const firstInput = document.querySelector(`#${tab}-tab input, #${tab}-tab textarea`);
        if (firstInput) {
            firstInput.focus();
        }
    }, 100);
}

function closeQuickCapture() {
    const modal = document.getElementById('quick-capture-modal');
    modal.classList.add('hidden');
    isQuickCaptureOpen = false;
    
    const forms = ['quick-task-form', 'quick-idea-form', 'quick-link-form', 'quick-note-form'];
    forms.forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
        }
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    const targetPanel = document.getElementById(`${tabName}-tab`);
    if (targetPanel) {
        targetPanel.classList.add('active');
    }
}

function submitQuickTask() {
    const taskData = {
        title: document.getElementById('task-title').value.trim(),
        description: document.getElementById('task-description').value.trim(),
        priority: document.getElementById('task-priority').value,
        energy_level: document.getElementById('task-energy').value,
        estimated_time: document.getElementById('task-estimated-time').value.trim(),
        due_date: document.getElementById('task-due-date').value,
        project_id: document.getElementById('task-project').value || null
    };
    
    if (!taskData.title) {
        showToast('Please enter a task title', 'error');
        return;
    }
    
    fetch('/api/tasks/quick-add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Task added successfully!', 'success');
            closeQuickCapture();
            
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast('Error adding task', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error adding task', 'error');
    });
}

function submitQuickIdea() {
    const ideaData = {
        title: document.getElementById('idea-title').value.trim(),
        description: document.getElementById('idea-description').value.trim(),
        project_id: document.getElementById('idea-project').value || null
    };
    
    if (!ideaData.title) {
        showToast('Please enter an idea title', 'error');
        return;
    }
    
    fetch('/api/ideas/quick-add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(ideaData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Idea captured!', 'success');
            closeQuickCapture();
            
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast('Error capturing idea', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error capturing idea', 'error');
    });
}

function submitQuickLink() {
    const linkData = {
        url: document.getElementById('link-url').value.trim(),
        title: document.getElementById('link-title').value.trim(),
        description: document.getElementById('link-description').value.trim(),
        project_id: document.getElementById('link-project').value || null
    };
    
    if (!linkData.url) {
        showToast('Please enter a URL', 'error');
        return;
    }
    
    fetch('/api/links/quick-add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(linkData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Link saved to backburner!', 'success');
            closeQuickCapture();

            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast('Error saving link', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error saving link', 'error');
    });
}

function submitQuickNote() {
    const noteData = {
        title: document.getElementById('note-title').value.trim(),
        content: document.getElementById('note-content').value.trim(),
        project_id: document.getElementById('note-project').value || null
    };
    
    if (!noteData.content) {
        showToast('Please enter note content', 'error');
        return;
    }
    
    fetch('/api/notes/quick-add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(noteData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Note saved!', 'success');
            closeQuickCapture();
            
            if (window.location.pathname.includes('/project/')) {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showToast('Error saving note', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error saving note', 'error');
    });
}

function toggleTask(taskId) {
    const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
    const checkbox = taskItem.querySelector('.task-checkbox');
    const isCompleted = checkbox.classList.contains('checked');
    
    const endpoint = isCompleted ? 
        `/api/tasks/${taskId}/uncomplete` : 
        `/api/tasks/${taskId}/complete`;
    
    fetch(endpoint, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (isCompleted) {
                    checkbox.classList.remove('checked');
                    checkbox.textContent = '';
                    showToast('Task marked incomplete', 'success');

                    taskItem.style.opacity = '1';
                    setTimeout(() => {
                        updateCompletedCount();
                    }, 500);

                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    checkbox.classList.add('checked');
                    checkbox.textContent = '✓';
                    showToast('Task completed!', 'success');
                    
                    taskItem.style.opacity = '0.6';
                    setTimeout(() => {
                        updateCompletedCount();
                    }, 500);

                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                showToast('Error updating task', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error updating task', 'error');
        });
}

function updateCompletedCount() {
    const completedTasks = document.querySelectorAll('.task-checkbox.checked').length;
    const countElement = document.getElementById('completed-count');
    if (countElement) {
        countElement.textContent = completedTasks;
    }
}

function toggleSmartSuggestions(forceState = null) {
    const panel = document.getElementById('smart-suggestions');
    
    if (forceState !== null) {
        suggestionsPanelOpen = forceState;
    } else {
        suggestionsPanelOpen = !suggestionsPanelOpen;
    }
    
    if (suggestionsPanelOpen) {
        panel.classList.remove('hidden');
        loadSmartSuggestions();
    } else {
        panel.classList.add('hidden');
    }
}

function loadSmartSuggestions() {
    const content = document.getElementById('suggestions-content');
    content.innerHTML = '<div class="loading">Finding your next best move...</div>';
    
    fetch('/api/smart-suggestions')
        .then(response => response.json())
        .then(suggestions => {
            if (suggestions.length === 0) {
                content.innerHTML = `
                    <div style="text-align: center; padding: var(--space-lg); color: var(--color-text-muted);">
                        <div>All caught up!</div>
                    </div>
                `;
                return;
            }
            
            content.innerHTML = suggestions.map(task => `
                <div class="task-item" data-task-id="${task.id}" onclick="toggleTask(${task.id})" style="margin: 0 -var(--space-md); border-bottom: 1px solid var(--color-border-soft);">
                    <div class="task-checkbox"></div>
                    <div class="task-content">
                        <div class="task-title">${task.title}</div>
                        <div class="task-meta">
                            <span class="task-priority ${task.priority}">${task.priority}</span>
                            <span class="task-energy ${task.energy_level}">${task.energy_level} energy</span>
                            ${task.project_name ? `<span>${task.project_name}</span>` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error loading suggestions:', error);
            content.innerHTML = `
                <div style="text-align: center; padding: var(--space-lg); color: var(--color-urgent);">
                    Error loading suggestions
                </div>
            `;
        });
}

function createProject() {
    const modal = document.getElementById('new-project-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.getElementById('project-name').focus();
    }
}

function closeProjectModal() {
    const modal = document.getElementById('new-project-modal');
    if (modal) {
        modal.classList.add('hidden');
        const form = document.getElementById('new-project-form');
        if (form) form.reset();
        
        const firstColor = document.querySelector('label[for="color1"]');
        if (firstColor) {
            selectColor(firstColor);
        }
    }
}

function selectColor(label) {
    document.querySelectorAll('label[for^="color"]').forEach(l => {
        l.style.border = '3px solid transparent';
    });
    
    label.style.border = '3px solid var(--color-text)';
    
    const radioId = label.getAttribute('for');
    const radio = document.getElementById(radioId);
    if (radio) radio.checked = true;
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, 3000);
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

function setupAutoSave() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                const formData = new FormData(form);
                const data = Object.fromEntries(formData.entries());
                localStorage.setItem(`focus-form-${form.id}`, JSON.stringify(data));
            }, 500));
        });
    });
}

function restoreFormData() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const saved = localStorage.getItem(`focus-form-${form.id}`);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                Object.entries(data).forEach(([name, value]) => {
                    const field = form.querySelector(`[name="${name}"]`);
                    if (field) field.value = value;
                });
            } catch (e) {
                console.error('Error restoring form data:', e);
            }
        }
    });
}

function clearAutoSave(formId) {
    localStorage.removeItem(`focus-form-${formId}`);
}

function manageFocus() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    document.addEventListener('mousedown', () => {
        document.body.classList.remove('keyboard-navigation');
    });
}

function deleteProject(projectId, projectName) {
    if (!confirm(`Are you sure you want to delete the project "${projectName}"?\n\nThis will:\n• Move all tasks, ideas, notes, and links to "No Project"\n• This action cannot be undone.`)) {
        return;
    }
    
    showToast('Deleting project...', 'info');
    
    fetch(`/api/projects/${projectId}/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Project deleted successfully', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            showToast(data.error || 'Error deleting project', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error deleting project', 'error');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    setupAutoSave();
    restoreFormData();
    manageFocus();
    
    setInterval(updateCompletedCount, 30000);
});

window.openQuickCapture = openQuickCapture;
window.closeQuickCapture = closeQuickCapture;
window.toggleTask = toggleTask;
window.toggleSmartSuggestions = toggleSmartSuggestions;
window.createProject = createProject;
window.closeProjectModal = closeProjectModal;
window.selectColor = selectColor;
window.showToast = showToast;
window.submitQuickNote = submitQuickNote;
window.deleteProject = deleteProject;