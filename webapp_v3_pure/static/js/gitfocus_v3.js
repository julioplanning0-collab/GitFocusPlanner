// V3 PURE - NO V2 LOGIC
// GitFocus V3 Pure - Timeline Linear Interface
// Architecture: 2-Step (ORDERING → TIME CALCULATION)

// ============================================
// STATE MANAGEMENT
// ============================================
const state = {
    // Planning config
    planningStartTime: null,  // Date object
    currentDate: null,        // YYYY-MM-DD

    // Tasks data
    pomodoroTasks: [],
    recurrentTasks: [],       // All recurrent tasks (no pauses separation)
    obstacles: [],

    // User selections
    selectedPomodoroIds: [],       // ["TASK001", "TASK002"]
    selectedRecurrentIds: [],      // ["REC001", "REC003", "REC001"] - ORDERED with duplicates (right panel)

    // Options
    calinEnabled: true,
    clopeEnabled: false,
    clopeInterval: 120,

    // Generated planning
    currentPlanning: null,

    // Server status
    serverOnline: false,

    // Modal state
    editingTaskId: null  // Task being edited in modal, null for new task
};

// ============================================
// INITIALIZATION
// ============================================
window.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 GitFocus V3 Pure - Initializing...');

    // Initialize planning start time (now + 15min, rounded to 5min)
    initPlanningStartTime();

    // Setup event listeners
    setupEventListeners();

    // Check server health
    checkServerHealth();

    // Load tasks
    loadAllTasks();
});

function initPlanningStartTime() {
    const now = new Date();
    const future = new Date(now.getTime() + 15 * 60000); // +15 minutes
    const roundedMin = Math.ceil(future.getMinutes() / 5) * 5; // Round up to next 5min
    future.setMinutes(roundedMin);
    future.setSeconds(0);
    future.setMilliseconds(0);

    state.planningStartTime = future;
    state.currentDate = formatDate(future);

    // Set input value
    const timeInput = document.getElementById('planningStartTime');
    timeInput.value = formatTime(future);

    console.log(`⏰ Planning start time: ${formatTime(future)}`);
}

// ============================================
// EVENT LISTENERS
// ============================================
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Planning start time change
    document.getElementById('planningStartTime').addEventListener('change', (e) => {
        const [hours, minutes] = e.target.value.split(':').map(Number);
        state.planningStartTime.setHours(hours);
        state.planningStartTime.setMinutes(minutes);
        console.log(`⏰ Planning start time updated: ${e.target.value}`);
    });
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `tab-${tabName}`);
    });
}

// ============================================
// API CALLS
// ============================================
async function checkServerHealth() {
    try {
        const response = await fetch('/api/v3/health');
        const data = await response.json();

        if (data.success) {
            state.serverOnline = true;
            document.getElementById('statusDot').classList.add('online');
            document.getElementById('statusText').textContent = `Server online - ${data.service} v${data.version}`;
        } else {
            throw new Error('Server returned error');
        }
    } catch (error) {
        console.error('❌ Server health check failed:', error);
        document.getElementById('statusText').textContent = 'Server offline';
        showToast('Erreur: Serveur inaccessible', 'error');
    }
}

async function loadAllTasks() {
    console.log('📥 Loading tasks from API...');

    try {
        // Load in parallel
        const [pomodoroRes, recurrentRes, obstaclesRes] = await Promise.all([
            fetch('/api/v3/tasks/pomodoro'),
            fetch('/api/v3/tasks/recurrent'),  // Load ALL recurrent tasks (including pauses)
            fetch(`/api/v3/temps-morts?date=${state.currentDate}`)
        ]);

        const pomodoroData = await pomodoroRes.json();
        const recurrentData = await recurrentRes.json();
        const obstaclesData = await obstaclesRes.json();

        if (pomodoroData.success) {
            state.pomodoroTasks = pomodoroData.tasks;
            renderPomodoroTasks();
            console.log(`✅ Loaded ${state.pomodoroTasks.length} Pomodoro tasks`);
        }

        if (recurrentData.success) {
            state.recurrentTasks = recurrentData.tasks;
            renderRecurrentTasksGrouped();
            console.log(`✅ Loaded ${state.recurrentTasks.length} Recurrent tasks`);
        }

        if (obstaclesData.success) {
            state.obstacles = obstaclesData.temps_morts;
            console.log(`✅ Loaded ${state.obstacles.length} obstacles`);
        }

        updateSelectionSummary();

    } catch (error) {
        console.error('❌ Error loading tasks:', error);
        showToast('Erreur lors du chargement des tâches', 'error');
    }
}

// ============================================
// RENDER FUNCTIONS
// ============================================
function renderPomodoroTasks() {
    const container = document.getElementById('pomodoroList');

    if (state.pomodoroTasks.length === 0) {
        container.innerHTML = '<div class="empty-message">Aucune tâche Pomodoro disponible</div>';
        return;
    }

    container.innerHTML = state.pomodoroTasks.map(task => `
        <div class="task-item ${state.selectedPomodoroIds.includes(task.id) ? 'selected' : ''}" data-id="${task.id}">
            <input type="checkbox"
                   id="pomo-${task.id}"
                   ${state.selectedPomodoroIds.includes(task.id) ? 'checked' : ''}
                   onchange="app.togglePomodoro('${task.id}')">
            <div class="task-info">
                <div class="task-name">${escapeHtml(task.name)}</div>
                <div class="task-meta">
                    <span class="task-duration">⏱️ ${task.duration} min</span>
                    ${task.category ? `<span class="task-category">📁 ${escapeHtml(task.category)}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');

    document.getElementById('countPomodoro').textContent = state.selectedPomodoroIds.length;

    // Auto-generate timeline when selections change
    autoGenerateTimeline();
}

// Render LEFT panel: Available recurrent tasks (grouped by category)
function renderRecurrentTasksGrouped() {
    const container = document.getElementById('recurrentAvailable');

    if (state.recurrentTasks.length === 0) {
        container.innerHTML = '<div class="empty-message">Aucune tâche récurrente disponible</div>';
        return;
    }

    // Group tasks by category
    const tasksByCategory = {};
    state.recurrentTasks.forEach(task => {
        const category = task.category || 'Sans catégorie';
        if (!tasksByCategory[category]) {
            tasksByCategory[category] = [];
        }
        tasksByCategory[category].push(task);
    });

    // Sort categories alphabetically
    const sortedCategories = Object.keys(tasksByCategory).sort();

    // Render grouped tasks
    container.innerHTML = sortedCategories.map(category => `
        <div class="category-group">
            <div class="category-header">${escapeHtml(category)}</div>
            ${tasksByCategory[category].map(task => `
                <div class="recurrent-task-item" data-id="${task.id}" onclick="app.addTaskToSelected('${task.id}')">
                    <span class="recurrent-task-name">${escapeHtml(task.name)}</span>
                    <span class="recurrent-task-duration">${task.duration}min</span>
                    <button class="btn-edit" onclick="event.stopPropagation(); app.showEditTaskModal('${task.id}');" title="Modifier">✏️</button>
                </div>
            `).join('')}
        </div>
    `).join('');

    document.getElementById('countRecurrent').textContent = state.recurrentTasks.length;
}

// Render RIGHT panel: Selected recurrent tasks (reorderable)
function renderSelectedRecurrent() {
    const container = document.getElementById('recurrentSelected');
    const sendBtn = document.getElementById('sendToTimelineBtn');

    if (state.selectedRecurrentIds.length === 0) {
        container.innerHTML = `
            <div class="empty-message">
                Cliquez sur les tâches à gauche pour les ajouter.<br>
                Glissez-déposez pour réordonner.
            </div>
        `;
        // Disable button when empty
        if (sendBtn) sendBtn.disabled = true;
        return;
    }

    container.innerHTML = state.selectedRecurrentIds.map((taskId, index) => {
        const task = state.recurrentTasks.find(t => t.id === taskId);
        if (!task) return '';

        return `
            <div class="selected-task-item" draggable="true" data-id="${taskId}" data-index="${index}">
                <span class="drag-handle">☰</span>
                <span class="selected-task-index">${index + 1}.</span>
                <span class="selected-task-name">${escapeHtml(task.name)}</span>
                <span class="selected-task-duration">${task.duration}min</span>
                <button class="btn-remove" onclick="app.removeSelectedRecurrent(${index})" title="Retirer">❌</button>
            </div>
        `;
    }).join('');

    // Enable button when has items
    if (sendBtn) sendBtn.disabled = false;

    updateSelectionSummary();

    // Setup drag & drop for reordering
    setupRecurrentDragDrop();

    // Auto-generate timeline when selections change
    autoGenerateTimeline();
}

// ============================================
// DRAG & DROP FOR RECURRENT REORDERING (RIGHT PANEL)
// ============================================
let draggedRecurrentItem = null;
let draggedRecurrentIndex = null;

function setupRecurrentDragDrop() {
    const items = document.querySelectorAll('#recurrentSelected .selected-task-item[draggable="true"]');

    items.forEach(item => {
        item.addEventListener('dragstart', handleRecurrentDragStart);
        item.addEventListener('dragend', handleRecurrentDragEnd);
        item.addEventListener('dragover', handleRecurrentDragOver);
        item.addEventListener('drop', handleRecurrentDrop);
    });
}

function handleRecurrentDragStart(e) {
    draggedRecurrentItem = e.currentTarget;
    draggedRecurrentIndex = parseInt(draggedRecurrentItem.dataset.index);

    draggedRecurrentItem.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', draggedRecurrentIndex);

    console.log(`🎯 Drag start: index ${draggedRecurrentIndex}`);
}

function handleRecurrentDragEnd(e) {
    if (draggedRecurrentItem) {
        draggedRecurrentItem.classList.remove('dragging');
    }

    // Remove all drag-over classes
    document.querySelectorAll('.selected-task-item').forEach(item => {
        item.classList.remove('drag-over-top', 'drag-over-bottom');
    });

    draggedRecurrentItem = null;
    draggedRecurrentIndex = null;
}

function handleRecurrentDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    const targetItem = e.currentTarget;
    if (targetItem === draggedRecurrentItem) return;

    // Remove all drag-over classes first
    document.querySelectorAll('.selected-task-item').forEach(item => {
        item.classList.remove('drag-over-top', 'drag-over-bottom');
    });

    // Determine if dragging above or below middle
    const rect = targetItem.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;

    if (e.clientY < midpoint) {
        targetItem.classList.add('drag-over-top');
    } else {
        targetItem.classList.add('drag-over-bottom');
    }
}

function handleRecurrentDrop(e) {
    e.preventDefault();

    const targetItem = e.currentTarget;
    const targetIndex = parseInt(targetItem.dataset.index);

    if (draggedRecurrentIndex === null || draggedRecurrentIndex === targetIndex) {
        return;
    }

    // Determine drop position
    const rect = targetItem.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;
    const dropAbove = e.clientY < midpoint;

    // Calculate new index
    let newIndex = targetIndex;
    if (!dropAbove && draggedRecurrentIndex < targetIndex) {
        newIndex = targetIndex;
    } else if (!dropAbove && draggedRecurrentIndex > targetIndex) {
        newIndex = targetIndex + 1;
    } else if (dropAbove && draggedRecurrentIndex > targetIndex) {
        newIndex = targetIndex;
    } else if (dropAbove && draggedRecurrentIndex < targetIndex) {
        newIndex = targetIndex - 1;
    }

    // Reorder array
    const taskId = state.selectedRecurrentIds[draggedRecurrentIndex];
    state.selectedRecurrentIds.splice(draggedRecurrentIndex, 1);
    state.selectedRecurrentIds.splice(newIndex, 0, taskId);

    console.log(`✅ Reordered: moved index ${draggedRecurrentIndex} → ${newIndex}`);

    // Re-render
    renderSelectedRecurrent();
}

// ============================================
// USER ACTIONS
// ============================================
const app = {
    // Pomodoro actions
    togglePomodoro(taskId) {
        const index = state.selectedPomodoroIds.indexOf(taskId);
        if (index > -1) {
            state.selectedPomodoroIds.splice(index, 1);
        } else {
            state.selectedPomodoroIds.push(taskId);
        }
        renderPomodoroTasks();
        updateSelectionSummary();
    },

    selectAllPomodoros() {
        state.selectedPomodoroIds = state.pomodoroTasks.map(t => t.id);
        renderPomodoroTasks();
        updateSelectionSummary();
        showToast('Toutes les tâches Pomodoro sélectionnées', 'success');
    },

    clearPomodoros() {
        state.selectedPomodoroIds = [];
        renderPomodoroTasks();
        updateSelectionSummary();
        showToast('Sélection Pomodoro effacée', 'success');
    },

    // Recurrent actions (LEFT → RIGHT)
    addTaskToSelected(taskId) {
        // Allow duplicates (same task can be added multiple times)
        state.selectedRecurrentIds.push(taskId);
        renderSelectedRecurrent();
        console.log(`✅ Added recurrent task ${taskId} to selection`);
    },

    removeSelectedRecurrent(index) {
        state.selectedRecurrentIds.splice(index, 1);
        renderSelectedRecurrent();
        console.log(`✅ Removed recurrent task at index ${index}`);
    },

    clearSelectedRecurrent() {
        state.selectedRecurrentIds = [];
        renderSelectedRecurrent();
        showToast('Séquence de tâches récurrentes vidée', 'success');
    },

    sendToTimeline() {
        if (state.selectedRecurrentIds.length === 0) {
            showToast('Aucune tâche sélectionnée à envoyer', 'warning');
            return;
        }

        // Switch to Pomodoro tab to trigger planning generation
        switchTab('pomodoro');

        // Scroll to planning section
        setTimeout(() => {
            showToast(`${state.selectedRecurrentIds.length} tâches envoyées vers le planning`, 'success');
            console.log('📤 Tasks sent to timeline:', state.selectedRecurrentIds);
        }, 300);
    },

    // Modal actions
    showAddTaskModal() {
        state.editingTaskId = null;
        document.getElementById('modalTitle').textContent = 'Ajouter une tâche récurrente';
        document.getElementById('taskId').value = '';
        document.getElementById('taskName').value = '';
        document.getElementById('taskCategory').value = '';
        document.getElementById('taskDescription').value = '';
        document.getElementById('taskDuration').value = '5';

        populateCategoryDatalist();

        document.getElementById('taskModal').style.display = 'flex';
    },

    showEditTaskModal(taskId) {
        state.editingTaskId = taskId;
        const task = state.recurrentTasks.find(t => t.id === taskId);

        if (!task) {
            showToast('Tâche introuvable', 'error');
            return;
        }

        document.getElementById('modalTitle').textContent = 'Modifier la tâche récurrente';
        document.getElementById('taskId').value = task.id;
        document.getElementById('taskName').value = task.name;
        document.getElementById('taskCategory').value = task.category || '';
        document.getElementById('taskDescription').value = task.description || '';
        document.getElementById('taskDuration').value = task.duration;

        populateCategoryDatalist();

        document.getElementById('taskModal').style.display = 'flex';
    },

    closeTaskModal() {
        document.getElementById('taskModal').style.display = 'none';
        state.editingTaskId = null;
    },

    async saveTask() {
        const name = document.getElementById('taskName').value.trim();
        const category = document.getElementById('taskCategory').value.trim();
        const description = document.getElementById('taskDescription').value.trim();
        const duration = parseInt(document.getElementById('taskDuration').value);

        if (!name || !category || duration < 1) {
            showToast('Veuillez remplir tous les champs obligatoires', 'warning');
            return;
        }

        // TODO: Implement API call to save task
        console.log('⚠️ Save task not yet implemented (API endpoint needed)');
        showToast('Fonctionnalité en cours de développement', 'warning');
        app.closeTaskModal();
    },

    // Planning actions
    async generatePlanning() {
        console.log('⚡ Generating planning...');

        // Validation
        if (state.selectedPomodoroIds.length === 0) {
            showToast('Veuillez sélectionner au moins une tâche Pomodoro', 'warning');
            return;
        }

        if (state.selectedRecurrentIds.length === 0) {
            showToast('Veuillez sélectionner au moins une tâche récurrente (utilisée comme pause)', 'warning');
            return;
        }

        // Prepare request - selectedRecurrentIds serves as pause sequence
        const payload = {
            date: state.currentDate,
            planning_start_time: formatTime(state.planningStartTime),
            pomodoro_ids: state.selectedPomodoroIds,
            pause_ids: state.selectedRecurrentIds,  // ORDERED with duplicates
            recurrent_ids: [],  // Empty for now (no separate recurrent injection)
            calin_enabled: state.calinEnabled,
            clope_enabled: state.clopeEnabled,
            clope_interval_min: state.clopeInterval
        };

        console.log('📤 Request payload:', payload);

        // Disable button
        const btn = document.getElementById('generateBtn');
        btn.disabled = true;
        btn.textContent = '⏳ Génération en cours...';

        try {
            const response = await fetch('/api/v3/planning/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erreur lors de la génération');
            }

            if (data.success) {
                state.currentPlanning = data.planning;
                displayPlanning(data);
                showToast(`Planning généré avec succès (${data.planning.length} slots)`, 'success');

                // Enable export button
                document.getElementById('exportBtn').disabled = false;
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }

        } catch (error) {
            console.error('❌ Error generating planning:', error);
            showToast(`Erreur: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '⚡ Générer Planning';
        }
    },

    async exportPlanning() {
        if (!state.currentPlanning) {
            showToast('Aucun planning à exporter', 'warning');
            return;
        }

        console.log('💾 Exporting planning...');

        const btn = document.getElementById('exportBtn');
        btn.disabled = true;
        btn.textContent = '⏳ Export en cours...';

        try {
            const response = await fetch('/api/v3/planning/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: state.currentDate,
                    planning: state.currentPlanning
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erreur lors de l\'export');
            }

            if (data.success) {
                showToast(`Planning exporté: ${data.file_path}`, 'success');
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }

        } catch (error) {
            console.error('❌ Error exporting planning:', error);
            showToast(`Erreur: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '💾 Export CSV';
        }
    },

    hidePlanning() {
        document.getElementById('planningSection').style.display = 'none';
    }
};

// ============================================
// PLANNING DISPLAY
// ============================================
function displayPlanning(data) {
    const section = document.getElementById('planningSection');
    const statsContainer = document.getElementById('planningStats');
    const timelineContainer = document.getElementById('timelineDisplay');

    // Show section
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth' });

    // Display statistics
    if (data.statistics) {
        const stats = data.statistics;
        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-label">Total Pomodoros</div>
                <div class="stat-value">${stats.total_pomodoros || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Pauses</div>
                <div class="stat-value">${stats.total_pauses || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Temps de Travail</div>
                <div class="stat-value">${stats.total_work_min || 0} min</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Temps de Pause</div>
                <div class="stat-value">${stats.total_pause_min || 0} min</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Début</div>
                <div class="stat-value">${stats.planning_start || 'N/A'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Fin</div>
                <div class="stat-value">${stats.planning_end || 'N/A'}</div>
            </div>
        `;
    }

    // Display timeline
    timelineContainer.innerHTML = data.planning.map(slot => {
        let badge = '';
        if (slot.type === 'pomodoro' && slot.pomodoro_index && slot.pomodoro_total) {
            badge = `<span class="slot-badge badge-pomodoro">${slot.pomodoro_index}/${slot.pomodoro_total}</span>`;
        }
        if (slot.rescheduled) {
            badge += '<span class="slot-badge">⚠️ Décalé</span>';
        }

        return `
            <div class="timeline-slot type-${slot.type}">
                <span class="slot-time">${slot.heure_debut} - ${slot.heure_fin}</span>
                <span class="slot-name">${escapeHtml(slot.task_name)}</span>
                ${badge}
            </div>
        `;
    }).join('');

    console.log(`✅ Planning displayed: ${data.planning.length} slots`);
}

// ============================================
// AUTO-GENERATION TIMELINE DYNAMIQUE (POMODORO TAB)
// ============================================

// Debounce timer to avoid excessive API calls
let timelineGenerationTimer = null;

async function autoGenerateTimeline() {
    // Clear previous timer
    if (timelineGenerationTimer) {
        clearTimeout(timelineGenerationTimer);
    }

    // Check if we have minimum required data
    if (state.selectedPomodoroIds.length === 0 || state.selectedRecurrentIds.length === 0) {
        showEmptyTimeline();
        return;
    }

    // Debounce: wait 300ms before generating
    timelineGenerationTimer = setTimeout(async () => {
        console.log('🔄 Auto-generating timeline...');

        const payload = {
            date: state.currentDate,
            planning_start_time: formatTime(state.planningStartTime),
            pomodoro_ids: state.selectedPomodoroIds,
            pause_ids: state.selectedRecurrentIds,  // ORDERED with duplicates
            recurrent_ids: [],
            calin_enabled: state.calinEnabled,
            clope_enabled: state.clopeEnabled,
            clope_interval_min: state.clopeInterval
        };

        try {
            const response = await fetch('/api/v3/planning/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erreur génération timeline');
            }

            if (data.success) {
                state.currentPlanning = data.planning;
                renderTimelineDynamic(data.planning, data.statistics);
                console.log(`✅ Timeline auto-generated: ${data.planning.length} slots`);
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }

        } catch (error) {
            console.error('❌ Auto-generation failed:', error);
            showTimelineError(error.message);
        }
    }, 300);
}

function showEmptyTimeline() {
    const container = document.getElementById('timelineDisplay');
    const infoSpan = document.getElementById('timelineInfo');

    container.innerHTML = `
        <div class="empty-message">
            La timeline s'affichera automatiquement<br>
            quand vous sélectionnez des tâches.
        </div>
    `;

    infoSpan.textContent = 'Sélectionnez des tâches';

    // Disable export button
    document.getElementById('exportBtn').disabled = true;
}

function showTimelineError(message) {
    const container = document.getElementById('timelineDisplay');
    const infoSpan = document.getElementById('timelineInfo');

    container.innerHTML = `
        <div class="empty-message" style="color: var(--error-color);">
            ❌ Erreur lors de la génération<br>
            ${escapeHtml(message)}
        </div>
    `;

    infoSpan.textContent = 'Erreur';

    // Disable export button
    document.getElementById('exportBtn').disabled = true;
}

function renderTimelineDynamic(planning, statistics) {
    const container = document.getElementById('timelineDisplay');
    const infoSpan = document.getElementById('timelineInfo');

    if (!planning || planning.length === 0) {
        showEmptyTimeline();
        return;
    }

    // Group slots by date
    const byDate = {};
    planning.forEach(slot => {
        // Extract date from heure_debut (format: "HH:MM" or "YYYY-MM-DD HH:MM")
        let date;
        if (slot.date) {
            date = slot.date;
        } else if (slot.heure_debut && slot.heure_debut.includes(' ')) {
            date = slot.heure_debut.split(' ')[0];
        } else {
            date = state.currentDate;
        }

        if (!byDate[date]) {
            byDate[date] = [];
        }
        byDate[date].push(slot);
    });

    // Sort dates
    const sortedDates = Object.keys(byDate).sort();

    // Render timeline with date separators
    let html = '';
    sortedDates.forEach(date => {
        // Add date separator (sticky header)
        html += `<div class="timeline-date-separator">${formatDateFr(date)}</div>`;

        // Add slots for this date
        byDate[date].forEach(slot => {
            const timeDisplay = slot.heure_debut && slot.heure_fin
                ? `${slot.heure_debut} - ${slot.heure_fin}`
                : `${slot.duration || '?'}min`;

            html += `
                <div class="timeline-slot type-${slot.type || 'unknown'}">
                    <span class="slot-time">${timeDisplay}</span>
                    <span class="slot-name">${escapeHtml(slot.task_name || slot.name || 'Tâche')}</span>
                </div>
            `;
        });
    });

    container.innerHTML = html;

    // Update info span
    if (statistics) {
        const start = statistics.planning_start || '?';
        const end = statistics.planning_end || '?';
        infoSpan.textContent = `${planning.length} slots, de ${start} à ${end}`;
    } else {
        infoSpan.textContent = `${planning.length} slots`;
    }

    // Enable export button
    document.getElementById('exportBtn').disabled = false;
}

function formatDateFr(dateStr) {
    // Convert YYYY-MM-DD to "Lundi 6 novembre 2025"
    const date = new Date(dateStr + 'T12:00:00');  // Force midday to avoid timezone issues

    const options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };

    const formatted = date.toLocaleDateString('fr-FR', options);
    // Capitalize first letter
    return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

// ============================================
// UTILITIES
// ============================================
function updateSelectionSummary() {
    const summary = document.getElementById('selectionSummary');

    // Count pauses in selected recurrents
    const pauseCount = state.selectedRecurrentIds.filter(id => {
        const task = state.recurrentTasks.find(t => t.id === id);
        return task && task.isPause;
    }).length;

    const recurrentCount = state.selectedRecurrentIds.length - pauseCount;

    summary.innerHTML = `
        <span>Pomodoros: <strong>${state.selectedPomodoroIds.length}</strong></span>
        <span>Pauses: <strong>${pauseCount}</strong></span>
        <span>Récurrentes: <strong>${recurrentCount}</strong></span>
    `;
}

function populateCategoryDatalist() {
    const datalist = document.getElementById('categoriesList');

    // Get unique categories from existing tasks
    const categories = [...new Set(state.recurrentTasks.map(t => t.category).filter(Boolean))];
    categories.sort();

    datalist.innerHTML = categories.map(cat =>
        `<option value="${escapeHtml(cat)}">`
    ).join('');
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.className = 'toast';
    }, 4000);
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatTime(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// EXPOSE APP GLOBALLY
// ============================================
window.app = app;
