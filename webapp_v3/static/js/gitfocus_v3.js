/**
 * GitFocus Planner V3 - JavaScript
 * Interface simplifiée reprenant V2 avec backend V3
 */

// ============================================================================
// STATE
// ============================================================================

const state = {
    currentDate: null,
    planningStartTime: null,
    pomodoroTasks: [],
    pauseTasks: [],
    recurrentTasks: [],
    selectedPomodoroIds: [],
    selectedPauseIds: [],
    currentPlanning: [],
    currentTab: 'pomodoro'
};

// ============================================================================
// API CALLS
// ============================================================================

const API_BASE = '/api/planning';

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'API error');
        }

        return data;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

async function loadPomodoroTasks() {
    try {
        const data = await apiCall('/tasks/pomodoro');
        state.pomodoroTasks = data.data || [];
        renderPomodoroTasks();
    } catch (error) {
        console.error('Failed to load Pomodoro tasks:', error);
        state.pomodoroTasks = [];
        renderPomodoroTasks();
    }
}

async function loadPauseTasks() {
    try {
        // En V3, les "pauses" sont dans les tâches récurrentes
        const data = await apiCall('/tasks/recurrent');
        // Filtrer pour garder seulement celles qui sont courtes (< 30 min)
        state.pauseTasks = (data.data || []).filter(t => t.duration_min <= 30);
        renderPauseTasks();
    } catch (error) {
        console.error('Failed to load pause tasks:', error);
        state.pauseTasks = [];
        renderPauseTasks();
    }
}

async function loadRecurrentTasks() {
    try {
        const data = await apiCall('/tasks/recurrent');
        state.recurrentTasks = data.data || [];
        renderRecurrentTasks();
    } catch (error) {
        console.error('Failed to load recurrent tasks:', error);
        state.recurrentTasks = [];
        renderRecurrentTasks();
    }
}

async function generatePlanning() {
    const selectedIds = state.selectedPomodoroIds;

    if (selectedIds.length === 0) {
        alert('Veuillez sélectionner au moins une tâche Pomodoro');
        return;
    }

    try {
        const data = await apiCall('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: state.currentDate,
                planningStartTime: state.planningStartTime,
                selectedPomodoroIds: selectedIds,
                selectedPauseIds: state.selectedPauseIds
            })
        });

        state.currentPlanning = data.data || [];
        renderPlanning();
        document.getElementById('btn-export').style.display = 'inline-block';

    } catch (error) {
        console.error('Error generating planning:', error);
        alert('Erreur lors de la génération du planning: ' + error.message);
    }
}

async function exportPlanning() {
    if (state.currentPlanning.length === 0) {
        return;
    }

    try {
        await apiCall('/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: state.currentDate,
                timeline: state.currentPlanning
            })
        });

        alert('Planning exporté avec succès');

    } catch (error) {
        console.error('Error exporting planning:', error);
        alert('Erreur lors de l\'export: ' + error.message);
    }
}

// ============================================================================
// RENDERING
// ============================================================================

function renderPomodoroTasks() {
    const container = document.getElementById('pomodoro-task-list');
    const count = document.getElementById('pomodoro-count');

    if (state.pomodoroTasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Aucune tâche Pomodoro</p></div>';
        count.textContent = '0 tâches';
        return;
    }

    container.innerHTML = state.pomodoroTasks.map(task => `
        <div class="task-item" onclick="toggleTaskSelection('${task.id}')">
            <input type="checkbox"
                   id="task-${task.id}"
                   ${state.selectedPomodoroIds.includes(task.id) ? 'checked' : ''}
                   onclick="event.stopPropagation(); toggleTaskSelection('${task.id}')">
            <div class="task-item-content">
                <div class="task-item-header">
                    <span class="task-item-name">${task.name}</span>
                    <span class="task-item-duration">${task.remaining_min || task.duration_min} min</span>
                </div>
                <div class="task-item-details">${task.category || ''} › ${task.sub_category || ''}</div>
            </div>
        </div>
    `).join('');

    count.textContent = `${state.pomodoroTasks.length} tâches`;
}

function renderPauseTasks() {
    const container = document.getElementById('pause-task-list');
    const count = document.getElementById('pause-count');

    if (state.pauseTasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Aucune tâche de pause</p></div>';
        count.textContent = '0 tâches';
        return;
    }

    container.innerHTML = state.pauseTasks.map(task => {
        const selectionCount = state.selectedPauseIds.filter(id => id === task.id).length;
        const countBadge = selectionCount > 0 ? `<span class="selection-count">x${selectionCount}</span>` : '';

        return `
            <div class="task-item clickable ${selectionCount > 0 ? 'selected' : ''}"
                 onclick="togglePauseSelection('${task.id}')"
                 title="Cliquez pour ajouter (permet duplicatas)">
                <div class="task-item-header">
                    <span class="task-item-icon">🟢</span>
                    <span class="task-item-name">${task.name}</span>
                    <span class="task-item-duration">${task.duration_min} min</span>
                    ${countBadge}
                </div>
                <div class="task-item-details">${task.category || ''} › ${task.sub_category || ''}</div>
            </div>
        `;
    }).join('');

    const totalSelected = state.selectedPauseIds.length;
    const uniqueSelected = new Set(state.selectedPauseIds).size;
    const countText = totalSelected > 0
        ? `${uniqueSelected} tâches (${totalSelected} sélections)`
        : `${state.pauseTasks.length} tâches`;

    count.textContent = countText;
}

function renderRecurrentTasks() {
    const container = document.getElementById('recurrent-task-list');
    const count = document.getElementById('recurrent-count');

    if (state.recurrentTasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Aucune tâche récurrente</p></div>';
        count.textContent = '0 tâches';
        return;
    }

    container.innerHTML = state.recurrentTasks.map(task => `
        <div class="task-item clickable" title="Cliquez pour ajouter au planning">
            <div class="task-item-header">
                <span class="task-item-icon">🟣</span>
                <span class="task-item-name">${task.name}</span>
                <span class="task-item-duration">${task.duration_min} min</span>
            </div>
            <div class="task-item-details">${task.category || ''} › ${task.sub_category || ''}</div>
        </div>
    `).join('');

    count.textContent = `${state.recurrentTasks.length} tâches`;
}

function renderPlanning() {
    const container = document.getElementById('planning-container');

    if (!state.currentPlanning || state.currentPlanning.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Aucun planning généré</p></div>';
        return;
    }

    container.innerHTML = state.currentPlanning.map(item => {
        const typeClass = `type-${item.type}`;
        return `
            <div class="timeline-item ${typeClass}">
                <div class="timeline-time">${item.start_time} - ${item.end_time}</div>
                <div class="timeline-name">${item.name}</div>
                <div class="timeline-duration">${item.duration} min</div>
            </div>
        `;
    }).join('');
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

function toggleTaskSelection(taskId) {
    const index = state.selectedPomodoroIds.indexOf(taskId);
    if (index > -1) {
        state.selectedPomodoroIds.splice(index, 1);
    } else {
        state.selectedPomodoroIds.push(taskId);
    }
    renderPomodoroTasks();
}

function togglePauseSelection(taskId) {
    // Add to selection (allows duplicates)
    state.selectedPauseIds.push(taskId);
    renderPauseTasks();
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.task-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });

    state.currentTab = tabName;
}

function initializeDate() {
    const dateInput = document.getElementById('planning-date');
    const timeInput = document.getElementById('planning-start-time');

    const today = new Date();
    state.currentDate = today.toISOString().split('T')[0];
    dateInput.value = state.currentDate;

    const hours = today.getHours();
    const minutes = today.getMinutes();
    state.planningStartTime = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    timeInput.value = state.planningStartTime;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize date and time
    initializeDate();

    // Setup tab switching
    document.querySelectorAll('.task-tab').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Setup action buttons
    document.getElementById('btn-generate').addEventListener('click', generatePlanning);
    document.getElementById('btn-export').addEventListener('click', exportPlanning);
    document.getElementById('btn-refresh').addEventListener('click', () => {
        loadPomodoroTasks();
        loadPauseTasks();
        loadRecurrentTasks();
    });

    // Load initial data
    loadPomodoroTasks();
    loadPauseTasks();
    loadRecurrentTasks();
});
