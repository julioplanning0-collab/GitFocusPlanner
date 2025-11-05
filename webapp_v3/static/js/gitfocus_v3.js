/**
 * GITFOCUS PLANNER V3 - JAVASCRIPT
 * Interface web pour gestion de planning avec tâches récurrentes
 */

// ===================================================================
// ÉTAT GLOBAL
// ===================================================================

const state = {
    currentTab: 'planning',
    recurrentTasks: [],
    selectedTasks: [],
    planning: null,
    categories: {}
};

// ===================================================================
// INITIALISATION
// ===================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeDate();
    initializeEventListeners();
    loadRecurrentTasks();
});

// ===================================================================
// GESTION DES ONGLETS
// ===================================================================

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });

    state.currentTab = tabName;
}

// ===================================================================
// INITIALISATION DE LA DATE
// ===================================================================

function initializeDate() {
    const dateInput = document.getElementById('planning-date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
}

// ===================================================================
// EVENT LISTENERS
// ===================================================================

function initializeEventListeners() {
    // Planning tab
    document.getElementById('btn-generate-planning').addEventListener('click', generatePlanning);
    document.getElementById('btn-export-planning').addEventListener('click', exportPlanning);

    // Recurrent tab
    document.getElementById('btn-add-task').addEventListener('click', showAddTaskModal);
    document.getElementById('btn-generate-from-recurrent').addEventListener('click', generatePlanningFromRecurrent);

    // Modal
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('btn-cancel').addEventListener('click', closeModal);
    document.getElementById('btn-save-task').addEventListener('click', saveTask);
}

// ===================================================================
// CHARGEMENT DES TÂCHES RÉCURRENTES
// ===================================================================

async function loadRecurrentTasks() {
    try {
        const response = await fetch('/api/planning/tasks/recurrent');
        const data = await response.json();

        if (data.success) {
            state.recurrentTasks = data.data.filter(task => task.is_active === 1);
            renderLibraryTree();
        } else {
            showToast('Erreur: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Erreur lors du chargement des tâches: ' + error.message, 'error');
    }
}

// ===================================================================
// RENDU DE LA BIBLIOTHÈQUE
// ===================================================================

function renderLibraryTree() {
    const container = document.getElementById('library-tree');

    // Group by category and subcategory
    const grouped = {};
    state.recurrentTasks.forEach(task => {
        const cat = task.category || 'Sans catégorie';
        const subcat = task.sub_category || 'Général';

        if (!grouped[cat]) grouped[cat] = {};
        if (!grouped[cat][subcat]) grouped[cat][subcat] = [];
        grouped[cat][subcat].push(task);
    });

    // Render tree
    let html = '';
    Object.keys(grouped).sort().forEach(category => {
        html += `<div class="category-group">
            <div class="category-header" onclick="toggleCategory(this)">
                <span class="category-icon">📁</span>
                <span>${category}</span>
            </div>`;

        Object.keys(grouped[category]).sort().forEach(subcategory => {
            html += `<div class="subcategory-group">
                <div class="subcategory-header">📁 ${subcategory}</div>`;

            grouped[category][subcategory].forEach(task => {
                html += `<div class="task-item" data-task-id="${task.id}" onclick="addTaskToSelected('${task.id}')">
                    <div class="task-info">
                        <div class="task-name">${task.name}</div>
                        <div class="task-duration">${task.duration_min} min</div>
                    </div>
                </div>`;
            });

            html += `</div>`;
        });

        html += `</div>`;
    });

    container.innerHTML = html;
}

// ===================================================================
// GESTION CATÉGORIES
// ===================================================================

function toggleCategory(element) {
    const group = element.parentElement;
    group.classList.toggle('collapsed');
}

// ===================================================================
// AJOUT DE TÂCHES À LA SÉLECTION
// ===================================================================

function addTaskToSelected(taskId) {
    const task = state.recurrentTasks.find(t => t.id === taskId);
    if (!task) return;

    state.selectedTasks.push({
        id: taskId,
        name: task.name,
        duration: task.duration_min,
        category: task.category
    });

    renderSelectedTasks();
    showToast(`"${task.name}" ajoutée`, 'success');
}

// ===================================================================
// RENDU DES TÂCHES SÉLECTIONNÉES
// ===================================================================

function renderSelectedTasks() {
    const container = document.getElementById('selected-list');
    const countElement = document.getElementById('selected-count');

    countElement.textContent = state.selectedTasks.length;

    if (state.selectedTasks.length === 0) {
        container.innerHTML = `<div class="empty-state-small">
            <p>Aucune tâche sélectionnée</p>
            <p class="hint">Cliquez sur une tâche dans la bibliothèque pour l'ajouter</p>
        </div>`;
        return;
    }

    let html = '';
    state.selectedTasks.forEach((task, index) => {
        html += `<div class="selected-task" draggable="true" data-index="${index}">
            <span class="selected-task-number">${index + 1}.</span>
            <div class="selected-task-info">
                <div class="task-name">${task.name}</div>
                <div class="task-duration">${task.duration} min</div>
            </div>
            <button class="selected-task-remove" onclick="removeSelectedTask(${index})">×</button>
        </div>`;
    });

    container.innerHTML = html;

    // Add drag & drop
    initializeDragAndDrop();
}

// ===================================================================
// SUPPRESSION D'UNE TÂCHE SÉLECTIONNÉE
// ===================================================================

function removeSelectedTask(index) {
    const task = state.selectedTasks[index];
    state.selectedTasks.splice(index, 1);
    renderSelectedTasks();
    showToast(`"${task.name}" supprimée`, 'success');
}

// ===================================================================
// DRAG & DROP
// ===================================================================

let draggedIndex = null;

function initializeDragAndDrop() {
    const tasks = document.querySelectorAll('.selected-task');

    tasks.forEach(task => {
        task.addEventListener('dragstart', handleDragStart);
        task.addEventListener('dragover', handleDragOver);
        task.addEventListener('drop', handleDrop);
        task.addEventListener('dragend', handleDragEnd);
    });
}

function handleDragStart(e) {
    draggedIndex = parseInt(e.target.dataset.index);
    e.target.classList.add('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
}

function handleDrop(e) {
    e.preventDefault();
    const dropIndex = parseInt(e.target.closest('.selected-task').dataset.index);

    if (draggedIndex !== dropIndex) {
        // Swap tasks
        const task = state.selectedTasks.splice(draggedIndex, 1)[0];
        state.selectedTasks.splice(dropIndex, 0, task);
        renderSelectedTasks();
    }
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
    draggedIndex = null;
}

// ===================================================================
// GÉNÉRATION DU PLANNING
// ===================================================================

async function generatePlanning() {
    const date = document.getElementById('planning-date').value;
    const startTime = document.getElementById('planning-start-time').value;

    if (!date || !startTime) {
        showToast('Veuillez renseigner la date et l\'heure', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/planning/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                planningStartTime: startTime
            })
        });

        const data = await response.json();

        if (data.success) {
            state.planning = data.data;
            renderPlanning();
            switchTab('planning');
            showToast('Planning généré avec succès', 'success');
        } else {
            showToast('Erreur: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Erreur: ' + error.message, 'error');
    }
}

async function generatePlanningFromRecurrent() {
    if (state.selectedTasks.length === 0) {
        showToast('Veuillez sélectionner au moins une tâche', 'warning');
        return;
    }

    const date = document.getElementById('planning-date').value;
    const startTime = document.getElementById('planning-start-time').value;

    try {
        const response = await fetch('/api/planning/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                planningStartTime: startTime,
                selectedRecurrentIds: state.selectedTasks.map(t => t.id)
            })
        });

        const data = await response.json();

        if (data.success) {
            state.planning = data.data;
            renderPlanning();
            switchTab('planning');
            showToast('Planning généré avec succès', 'success');
        } else {
            showToast('Erreur: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Erreur: ' + error.message, 'error');
    }
}

// ===================================================================
// RENDU DU PLANNING
// ===================================================================

function renderPlanning() {
    const container = document.getElementById('timeline-container');

    if (!state.planning || !state.planning.timeline || state.planning.timeline.length === 0) {
        container.innerHTML = `<div class="empty-state">
            <p>Aucun planning généré</p>
        </div>`;
        return;
    }

    let html = '';
    state.planning.timeline.forEach(item => {
        const typeClass = `type-${item.type}`;
        html += `<div class="timeline-item ${typeClass}">
            <div class="timeline-time">${item.start_time} - ${item.end_time}</div>
            <div>
                <div class="timeline-name">${item.name}</div>
                ${item.category ? `<div class="timeline-category">${item.category}</div>` : ''}
            </div>
            <div class="timeline-duration">${item.duration} min</div>
        </div>`;
    });

    container.innerHTML = html;
}

// ===================================================================
// EXPORT CSV
// ===================================================================

async function exportPlanning() {
    if (!state.planning) {
        showToast('Veuillez d\'abord générer un planning', 'warning');
        return;
    }

    try {
        const date = document.getElementById('planning-date').value;
        const response = await fetch('/api/planning/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                timeline: state.planning.timeline
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('Planning exporté avec succès', 'success');
        } else {
            showToast('Erreur: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Erreur: ' + error.message, 'error');
    }
}

// ===================================================================
// MODAL
// ===================================================================

function showAddTaskModal() {
    document.getElementById('modal-task').classList.add('active');
}

function closeModal() {
    document.getElementById('modal-task').classList.remove('active');
    clearModalForm();
}

function clearModalForm() {
    document.getElementById('task-name').value = '';
    document.getElementById('task-duration').value = '15';
    document.getElementById('task-category').value = '';
    document.getElementById('task-subcategory').value = '';
    document.getElementById('task-description').value = '';
}

async function saveTask() {
    const name = document.getElementById('task-name').value.trim();
    const duration = parseInt(document.getElementById('task-duration').value);
    const category = document.getElementById('task-category').value.trim();
    const subcategory = document.getElementById('task-subcategory').value.trim();
    const description = document.getElementById('task-description').value.trim();

    if (!name || !duration || !category || !subcategory) {
        showToast('Veuillez remplir tous les champs obligatoires', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/planning/tasks/recurrent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                duration_min: duration,
                category,
                sub_category: subcategory,
                description
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('Tâche créée avec succès', 'success');
            closeModal();
            loadRecurrentTasks();
        } else {
            showToast('Erreur: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Erreur: ' + error.message, 'error');
    }
}

// ===================================================================
// NOTIFICATIONS TOAST
// ===================================================================

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}
