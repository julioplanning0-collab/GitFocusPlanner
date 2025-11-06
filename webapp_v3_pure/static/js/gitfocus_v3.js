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
    pauseTasks: [],
    recurrentTasks: [],
    obstacles: [],

    // User selections
    selectedPomodoroIds: [],       // ["TASK001", "TASK002"]
    selectedPauseIds: [],          // ["REC001", "REC003", "REC001"] - ORDERED with duplicates
    enabledRecurrentIds: [],       // ["REC006", "REC008"]

    // Options
    calinEnabled: true,
    clopeEnabled: false,
    clopeInterval: 120,

    // Generated planning
    currentPlanning: null,

    // Server status
    serverOnline: false
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

    // Options checkboxes
    document.getElementById('calinEnabled').addEventListener('change', (e) => {
        state.calinEnabled = e.target.checked;
    });

    document.getElementById('clopeEnabled').addEventListener('change', (e) => {
        state.clopeEnabled = e.target.checked;
    });

    document.getElementById('clopeInterval').addEventListener('change', (e) => {
        state.clopeInterval = parseInt(e.target.value);
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
        const [pomodoroRes, pauseRes, recurrentRes, obstaclesRes] = await Promise.all([
            fetch('/api/v3/tasks/pomodoro'),
            fetch('/api/v3/tasks/recurrent?pause_only=true'),
            fetch('/api/v3/tasks/recurrent?exclude_pauses=true'),
            fetch(`/api/v3/temps-morts?date=${state.currentDate}`)
        ]);

        const pomodoroData = await pomodoroRes.json();
        const pauseData = await pauseRes.json();
        const recurrentData = await recurrentRes.json();
        const obstaclesData = await obstaclesRes.json();

        if (pomodoroData.success) {
            state.pomodoroTasks = pomodoroData.tasks;
            renderPomodoroTasks();
            console.log(`✅ Loaded ${state.pomodoroTasks.length} Pomodoro tasks`);
        }

        if (pauseData.success) {
            state.pauseTasks = pauseData.tasks;
            renderPauseTasks();
            console.log(`✅ Loaded ${state.pauseTasks.length} Pause tasks`);
        }

        if (recurrentData.success) {
            state.recurrentTasks = recurrentData.tasks;
            renderRecurrentTasks();
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
}

function renderPauseTasks() {
    const container = document.getElementById('pausesAvailable');

    if (state.pauseTasks.length === 0) {
        container.innerHTML = '<div class="empty-message">Aucune pause disponible</div>';
        return;
    }

    container.innerHTML = state.pauseTasks.map(task => `
        <div class="pause-item" draggable="true" data-id="${task.id}">
            <div class="pause-item-info">
                <div class="pause-item-name">${escapeHtml(task.name)}</div>
                <div class="pause-item-duration">${task.duration} min</div>
            </div>
        </div>
    `).join('');

    // Setup drag & drop
    setupDragAndDrop();
}

function renderRecurrentTasks() {
    const container = document.getElementById('recurrentList');

    if (state.recurrentTasks.length === 0) {
        container.innerHTML = '<div class="empty-message">Aucune tâche récurrente disponible</div>';
        return;
    }

    container.innerHTML = state.recurrentTasks.map(task => `
        <div class="task-item recurrent-item ${state.enabledRecurrentIds.includes(task.id) ? 'active' : ''}" data-id="${task.id}">
            <label class="toggle-switch">
                <input type="checkbox"
                       ${state.enabledRecurrentIds.includes(task.id) ? 'checked' : ''}
                       onchange="app.toggleRecurrent('${task.id}')">
                <span class="toggle-slider"></span>
            </label>
            <div class="task-info">
                <div class="task-name">${escapeHtml(task.name)}</div>
                <div class="task-meta">
                    <span class="task-duration">⏱️ ${task.duration} min</span>
                    ${task.recurrence_type ? `<span class="task-category">🔁 ${task.recurrence_type}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');

    document.getElementById('countRecurrent').textContent = state.enabledRecurrentIds.length;
}

function renderSelectedPauses() {
    const container = document.getElementById('pausesSelected');

    if (state.selectedPauseIds.length === 0) {
        container.innerHTML = `
            <div class="empty-message">
                Glissez les pauses ici pour construire votre séquence.
                <br>Ordre important : les pauses seront insérées dans cet ordre.
            </div>
        `;
        return;
    }

    container.innerHTML = state.selectedPauseIds.map((pauseId, index) => {
        const task = state.pauseTasks.find(t => t.id === pauseId);
        if (!task) return '';

        return `
            <div class="pause-item" draggable="true" data-id="${pauseId}" data-index="${index}">
                <div class="pause-item-info">
                    <div class="pause-item-name">${index + 1}. ${escapeHtml(task.name)}</div>
                    <div class="pause-item-duration">${task.duration} min</div>
                </div>
                <div class="pause-item-actions">
                    <button class="btn-icon" onclick="app.removeSelectedPause(${index})" title="Retirer">❌</button>
                </div>
            </div>
        `;
    }).join('');

    document.getElementById('countPauses').textContent = state.selectedPauseIds.length;
    updateSelectionSummary();

    // Re-setup drag & drop for selected zone
    setupDragAndDrop();
}

// ============================================
// DRAG & DROP (HTML5 API)
// ============================================
function setupDragAndDrop() {
    const availableZone = document.getElementById('pausesAvailable');
    const selectedZone = document.getElementById('pausesSelected');

    // Draggable items
    document.querySelectorAll('.pause-item[draggable="true"]').forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
    });

    // Drop zones
    [availableZone, selectedZone].forEach(zone => {
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('drop', handleDrop);
        zone.addEventListener('dragleave', handleDragLeave);
    });
}

let draggedItem = null;
let draggedFromZone = null;

function handleDragStart(e) {
    draggedItem = e.target.closest('.pause-item');
    draggedFromZone = e.target.closest('.drag-zone').id;

    draggedItem.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('text/html', draggedItem.innerHTML);

    console.log(`🎯 Drag start: ${draggedItem.dataset.id} from ${draggedFromZone}`);
}

function handleDragEnd(e) {
    if (draggedItem) {
        draggedItem.classList.remove('dragging');
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';

    const dropZone = e.currentTarget;
    if (dropZone.id === 'pausesSelected') {
        dropZone.classList.add('drag-over');
    }
}

function handleDragLeave(e) {
    const dropZone = e.currentTarget;
    if (dropZone.id === 'pausesSelected') {
        dropZone.classList.remove('drag-over');
    }
}

function handleDrop(e) {
    e.preventDefault();

    const dropZone = e.currentTarget;
    dropZone.classList.remove('drag-over');

    // Only allow drop on selected zone
    if (dropZone.id !== 'pausesSelected') {
        return;
    }

    if (!draggedItem) return;

    const pauseId = draggedItem.dataset.id;

    // If dragged from selected zone (reordering)
    if (draggedFromZone === 'pausesSelected') {
        const oldIndex = parseInt(draggedItem.dataset.index);
        // TODO: Implement reordering (would require drop position detection)
        console.log('⚠️ Reordering not yet implemented');
        return;
    }

    // Add to selected pauses (allows duplicates)
    state.selectedPauseIds.push(pauseId);
    renderSelectedPauses();

    console.log(`✅ Added pause ${pauseId} to selection`);
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

    // Pause actions
    removeSelectedPause(index) {
        state.selectedPauseIds.splice(index, 1);
        renderSelectedPauses();
    },

    clearSelectedPauses() {
        state.selectedPauseIds = [];
        renderSelectedPauses();
        showToast('Séquence de pauses effacée', 'success');
    },

    // Recurrent actions
    toggleRecurrent(taskId) {
        const index = state.enabledRecurrentIds.indexOf(taskId);
        if (index > -1) {
            state.enabledRecurrentIds.splice(index, 1);
        } else {
            state.enabledRecurrentIds.push(taskId);
        }
        renderRecurrentTasks();
        updateSelectionSummary();
    },

    toggleAllRecurrent(enable) {
        if (enable) {
            state.enabledRecurrentIds = state.recurrentTasks.map(t => t.id);
            showToast('Toutes les tâches récurrentes activées', 'success');
        } else {
            state.enabledRecurrentIds = [];
            showToast('Toutes les tâches récurrentes désactivées', 'success');
        }
        renderRecurrentTasks();
        updateSelectionSummary();
    },

    // Planning actions
    async generatePlanning() {
        console.log('⚡ Generating planning...');

        // Validation
        if (state.selectedPomodoroIds.length === 0) {
            showToast('Veuillez sélectionner au moins une tâche Pomodoro', 'warning');
            return;
        }

        if (state.selectedPauseIds.length === 0) {
            showToast('Veuillez sélectionner au moins une pause', 'warning');
            return;
        }

        // Prepare request
        const payload = {
            date: state.currentDate,
            planning_start_time: formatTime(state.planningStartTime),
            pomodoro_ids: state.selectedPomodoroIds,
            pause_ids: state.selectedPauseIds,  // ORDERED with duplicates
            recurrent_ids: state.enabledRecurrentIds,
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
// UTILITIES
// ============================================
function updateSelectionSummary() {
    const summary = document.getElementById('selectionSummary');
    summary.innerHTML = `
        <span>Pomodoros: <strong>${state.selectedPomodoroIds.length}</strong></span>
        <span>Pauses: <strong>${state.selectedPauseIds.length}</strong></span>
        <span>Récurrentes: <strong>${state.enabledRecurrentIds.length}</strong></span>
    `;
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
