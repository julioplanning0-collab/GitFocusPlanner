/**
 * GitFocus Planner V2 - Frontend JavaScript
 *
 * Features:
 * - Load tasks from API
 * - Generate planning with auto scoring
 * - Display planning timeline
 * - Export planning to CSV
 * - Show statistics
 */

// ============================================================================
// STATE
// ============================================================================

const state = {
    currentDate: null,
    pomodoroTasks: [],
    recurrentTasks: [],
    currentPlanning: [],
    selectedPomodoroIds: []
};

// ============================================================================
// API CALLS
// ============================================================================

const API_BASE = '/api/v2/gitfocus';

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
        // No popup - error logged to console only
        throw error;
    }
}

async function loadPomodoroTasks() {
    try {
        const data = await apiCall('/tasks/pomodoro');
        state.pomodoroTasks = data.tasks || [];
        renderPomodoroTasks();
    } catch (error) {
        console.error('Failed to load Pomodoro tasks:', error);
        state.pomodoroTasks = [];
        renderPomodoroTasks();
    }
}

async function loadRecurrentTasks() {
    try {
        const data = await apiCall('/tasks/recurrent?active_only=true');
        state.recurrentTasks = data.tasks || [];
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
        // No popup - silently return (user sees empty planning)
        return;
    }

    showLoading(true);

    try {
        const data = await apiCall('/planning/generate-auto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: state.currentDate,
                pomodoro_task_ids: selectedIds,
                max_recurrent_tasks: 10
            })
        });

        state.currentPlanning = data.data.planning || [];
        renderPlanning(data.data);
        // No popup - planning is visible in UI

    } catch (error) {
        console.error('Error generating planning:', error);
    } finally {
        showLoading(false);
    }
}

async function exportPlanning() {
    if (state.currentPlanning.length === 0) {
        // No popup - silently return (export button should be hidden anyway)
        return;
    }

    showLoading(true);

    try {
        const data = await apiCall('/planning/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: state.currentDate,
                planning: state.currentPlanning
            })
        });

        // No popup - export is silent

    } catch (error) {
        console.error('Error exporting planning:', error);
    } finally {
        showLoading(false);
    }
}

async function loadHistoryStats() {
    try {
        const data = await apiCall('/stats/history');
        renderHistoryStats(data.stats);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ============================================================================
// RENDERING
// ============================================================================

function renderPomodoroTasks() {
    const container = document.getElementById('pomodoro-task-list');

    if (state.pomodoroTasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Aucune tâche Pomodoro</p></div>';
        return;
    }

    container.innerHTML = state.pomodoroTasks.map(task => {
        const metaInfo = `${task.category} › ${task.sub_category}${task.deadline ? ` • ⏰ ${task.deadline}` : ''}`;
        const description = task.description || '';

        return `
            <div class="task-item" onclick="toggleTaskSelection('${task.id}')">
                <input type="checkbox"
                       id="task-${task.id}"
                       ${state.selectedPomodoroIds.includes(task.id) ? 'checked' : ''}
                       onclick="event.stopPropagation(); toggleTaskSelection('${task.id}')">
                <div class="task-item-content">
                    <div class="task-item-header">
                        <span class="task-item-name">${task.name}</span>
                        <span class="task-item-duration">${task.remaining_min} min</span>
                        <span class="task-item-priority">P${task.priority}</span>
                    </div>
                    <div class="task-item-details">${metaInfo}${description ? ` • ${description}` : ''}</div>
                </div>
            </div>
        `;
    }).join('');

    document.getElementById('pomodoro-count').textContent = `${state.pomodoroTasks.length} tâches`;
}

function renderRecurrentTasks() {
    const container = document.getElementById('recurrent-tasks-list');

    if (state.recurrentTasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Aucune tâche récurrente active</p></div>';
        return;
    }

    container.innerHTML = state.recurrentTasks.map(task => {
        const metaInfo = `${task.category} › ${task.sub_category}${task.next_due_date ? ` • 📅 ${task.next_due_date}` : ''}`;
        const description = task.description || '';

        return `
            <div class="task-item clickable" onclick="addRecurrentTaskToPlanning('${task.id}')" title="Cliquez pour ajouter au planning">
                <div class="task-item-header">
                    <span class="task-item-icon">🟣</span>
                    <span class="task-item-name">${task.name}</span>
                    <span class="task-item-duration">${task.duration_min} min</span>
                </div>
                <div class="task-item-details">${metaInfo}${description ? ` • ${description}` : ''}</div>
            </div>
        `;
    }).join('');

    document.getElementById('recurrent-count').textContent = `${state.recurrentTasks.length} tâches`;
}

function addRecurrentTaskToPlanning(taskId) {
    // Check if planning exists
    if (state.currentPlanning.length === 0) {
        // No popup - silently return
        return;
    }

    // Find the task
    const task = state.recurrentTasks.find(t => t.id === taskId);
    if (!task) {
        // No popup - silently return
        return;
    }

    // Find first default pause (5-min pause created by Pomodoro)
    const firstPauseIndex = state.currentPlanning.findIndex(
        slot => slot.type === 'pause' && slot.task_id === 'default_pause'
    );

    if (firstPauseIndex !== -1) {
        // Replace the default pause with the recurrent task
        const pauseStartTime = state.currentPlanning[firstPauseIndex].heure_debut;
        const pauseStartDate = state.currentPlanning[firstPauseIndex].date;
        const oldPauseDuration = state.currentPlanning[firstPauseIndex].duration_min;
        const newTaskDuration = task.duration_min;

        // Calculate end time (may cross midnight)
        const endResult = addMinutes(pauseStartTime, newTaskDuration, pauseStartDate);
        const endTime = typeof endResult === 'string' ? endResult : endResult.time;
        const endDate = typeof endResult === 'string' ? pauseStartDate : endResult.date;

        // Create new recurrent slot
        const newSlot = {
            id: `slot_${Date.now()}`,
            heure_debut: pauseStartTime,
            heure_fin: endTime,
            type: 'recurrent',
            task_id: task.id,
            task_name: task.name,
            category: task.category || '',
            sub_category: task.sub_category || '',
            duration_min: newTaskDuration,
            date: pauseStartDate
        };

        // Replace the pause
        state.currentPlanning[firstPauseIndex] = newSlot;

        // If duration changed, recalculate all following slots' times
        const timeDifference = newTaskDuration - oldPauseDuration;
        if (timeDifference !== 0) {
            let currentDate = endDate; // Start from the end date of the replaced slot
            for (let i = firstPauseIndex + 1; i < state.currentPlanning.length; i++) {
                const slot = state.currentPlanning[i];

                // Recalculate start time
                const startResult = addMinutes(slot.heure_debut, timeDifference, currentDate);
                if (typeof startResult === 'string') {
                    slot.heure_debut = startResult;
                } else {
                    slot.heure_debut = startResult.time;
                    slot.date = startResult.date;
                    currentDate = startResult.date;
                }

                // Recalculate end time
                const endResult = addMinutes(slot.heure_fin, timeDifference, currentDate);
                if (typeof endResult === 'string') {
                    slot.heure_fin = endResult;
                } else {
                    slot.heure_fin = endResult.time;
                    slot.date = endResult.date;
                    currentDate = endResult.date;
                }
            }
        }
    } else {
        // No default pause found, add to end (fallback behavior)
        const lastSlot = state.currentPlanning[state.currentPlanning.length - 1];
        const lastEndTime = lastSlot.heure_fin;
        const lastEndDate = lastSlot.date;

        // Calculate end time (may cross midnight)
        const endResult = addMinutes(lastEndTime, task.duration_min, lastEndDate);
        const endTime = typeof endResult === 'string' ? endResult : endResult.time;
        const endDate = typeof endResult === 'string' ? lastEndDate : endResult.date;

        const newSlot = {
            id: `slot_${Date.now()}`,
            heure_debut: lastEndTime,
            heure_fin: endTime,
            type: 'recurrent',
            task_id: task.id,
            task_name: task.name,
            category: task.category || '',
            sub_category: task.sub_category || '',
            duration_min: task.duration_min,
            date: lastEndDate
        };

        state.currentPlanning.push(newSlot);
    }

    // Re-render planning
    renderPlanning({
        planning: state.currentPlanning,
        stats: calculateStats(state.currentPlanning),
        recurrent_task_scores: []
    });

    // No popup - task added silently
}

// Helper functions for time manipulation
function addMinutes(timeStr, minutes, currentDate = null) {
    /**
     * Add minutes to a time string, handling day transitions correctly.
     *
     * If time exceeds 23:59, returns next day's time (00:00+).
     * If currentDate provided, also returns the new date.
     *
     * @param {string} timeStr - Time in HH:MM format
     * @param {number} minutes - Minutes to add (can be negative)
     * @param {string|null} currentDate - Optional date in YYYY-MM-DD format
     * @returns {string|object} - Time string, or {time, date} if currentDate provided
     */
    const [h, m] = timeStr.split(':').map(Number);
    const totalMinutes = h * 60 + m + minutes;

    // Calculate days offset and time within day
    const daysOffset = Math.floor(totalMinutes / 1440); // 1440 = 24 * 60
    const minutesInDay = totalMinutes % 1440;

    // Handle negative times (wrap to previous day)
    const finalMinutes = minutesInDay < 0 ? minutesInDay + 1440 : minutesInDay;
    const finalDaysOffset = minutesInDay < 0 ? daysOffset - 1 : daysOffset;

    const newH = Math.floor(finalMinutes / 60);
    const newM = finalMinutes % 60;
    const timeResult = `${String(newH).padStart(2, '0')}:${String(newM).padStart(2, '0')}`;

    // If date provided, calculate new date
    if (currentDate && finalDaysOffset !== 0) {
        const date = new Date(currentDate + 'T00:00:00');
        date.setDate(date.getDate() + finalDaysOffset);
        const newDate = date.toISOString().split('T')[0];
        return { time: timeResult, date: newDate };
    }

    // If no date provided but days changed, log warning
    if (!currentDate && finalDaysOffset !== 0) {
        console.warn(`⚠️ addMinutes: Time crossed midnight (${finalDaysOffset} days), but no date provided. Returning time only.`);
    }

    return currentDate ? { time: timeResult, date: currentDate } : timeResult;
}

function compareTime(time1, time2) {
    const [h1, m1] = time1.split(':').map(Number);
    const [h2, m2] = time2.split(':').map(Number);
    return (h1 * 60 + m1) - (h2 * 60 + m2);
}

function formatDate(dateStr) {
    // Convert YYYY-MM-DD to French formatted date
    const date = new Date(dateStr + 'T00:00:00');
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('fr-FR', options);
}

function calculateStats(planning) {
    const workTypes = new Set(['pomodoro', 'planned']);
    const pauseTypes = new Set(['recurrent', 'respiration', 'pause']);

    return {
        total_slots: planning.length,
        pomodoro_slots: planning.filter(s => s.type === 'pomodoro').length,
        recurrent_slots: planning.filter(s => s.type === 'recurrent').length,
        planned_slots: planning.filter(s => s.type === 'planned').length,
        respiration_slots: planning.filter(s => s.type === 'respiration').length,
        pause_slots: planning.filter(s => s.type === 'pause').length,
        work_minutes: planning.filter(s => workTypes.has(s.type)).reduce((sum, s) => sum + s.duration_min, 0),
        pause_minutes: planning.filter(s => pauseTypes.has(s.type)).reduce((sum, s) => sum + s.duration_min, 0)
    };
}

// ============================================================================
// DRAG & DROP HANDLERS
// ============================================================================

let draggedSlotIndex = null;

function attachDragDropHandlers() {
    const slots = document.querySelectorAll('.planning-slot');

    slots.forEach(slot => {
        slot.addEventListener('dragstart', handleDragStart);
        slot.addEventListener('dragover', handleDragOver);
        slot.addEventListener('drop', handleDrop);
        slot.addEventListener('dragend', handleDragEnd);
    });
}

function handleDragStart(e) {
    draggedSlotIndex = parseInt(e.currentTarget.getAttribute('data-slot-index'));
    e.currentTarget.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    const dropTarget = e.currentTarget;
    if (dropTarget.classList.contains('planning-slot')) {
        dropTarget.classList.add('drag-over');
    }
}

function handleDrop(e) {
    e.preventDefault();

    const dropTargetIndex = parseInt(e.currentTarget.getAttribute('data-slot-index'));

    if (draggedSlotIndex === null || draggedSlotIndex === dropTargetIndex) {
        return;
    }

    // Reorder slots
    const draggedSlot = state.currentPlanning[draggedSlotIndex];
    state.currentPlanning.splice(draggedSlotIndex, 1);

    // Adjust target index if dragging downward
    const newIndex = draggedSlotIndex < dropTargetIndex ? dropTargetIndex - 1 : dropTargetIndex;
    state.currentPlanning.splice(newIndex, 0, draggedSlot);

    // Repair alternation violations
    repairAlternationViolations();

    // Recalculate times sequentially (respecting durations)
    recalculateTimesAfterReorder();

    // Re-render
    renderPlanning({
        planning: state.currentPlanning,
        stats: calculateStats(state.currentPlanning),
        recurrent_task_scores: []
    });
}

function repairAlternationViolations() {
    /**
     * Scan planning and fix alternation violations.
     * If two work tasks consecutive → insert pause between them
     * If two pause tasks consecutive → remove one
     */
    const workTypes = new Set(['pomodoro', 'planned', 'recurrent']);
    const pauseTypes = new Set(['respiration', 'pause']);

    let modified = true;
    let iterations = 0;
    const maxIterations = 50; // Safety limit

    while (modified && iterations < maxIterations) {
        modified = false;
        iterations++;

        for (let i = 0; i < state.currentPlanning.length - 1; i++) {
            const current = state.currentPlanning[i];
            const next = state.currentPlanning[i + 1];

            const currentIsWork = workTypes.has(current.type);
            const nextIsWork = workTypes.has(next.type);
            const currentIsPause = pauseTypes.has(current.type);
            const nextIsPause = pauseTypes.has(next.type);

            // Violation: Two work tasks consecutive
            if (currentIsWork && nextIsWork) {
                // Find a pause to insert (prefer later in planning to minimize disruption)
                let pauseToMove = null;
                let pauseIndex = -1;

                for (let j = i + 2; j < state.currentPlanning.length; j++) {
                    if (pauseTypes.has(state.currentPlanning[j].type)) {
                        pauseToMove = state.currentPlanning[j];
                        pauseIndex = j;
                        break;
                    }
                }

                if (pauseToMove) {
                    // Move pause between the two work tasks
                    state.currentPlanning.splice(pauseIndex, 1);
                    state.currentPlanning.splice(i + 1, 0, pauseToMove);
                    modified = true;
                    break; // Restart scan
                } else {
                    // No pause available, create default pause
                    const defaultPause = {
                        id: `pause_${Date.now()}`,
                        type: 'pause',
                        task_id: 'default_pause',
                        task_name: 'Pause',
                        duration_min: 5,
                        heure_debut: '',
                        heure_fin: '',
                        date: current.date
                    };
                    state.currentPlanning.splice(i + 1, 0, defaultPause);
                    modified = true;
                    break;
                }
            }

            // Violation: Two pause tasks consecutive (remove second)
            if (currentIsPause && nextIsPause) {
                state.currentPlanning.splice(i + 1, 1);
                modified = true;
                break;
            }
        }
    }

    if (iterations >= maxIterations) {
        console.warn(`Repair hit max iterations (${maxIterations}), may still have violations`);
    }
}

function recalculateTimesAfterReorder() {
    /**
     * Recalculate all slot times after reordering.
     * Uses first slot's start time as reference.
     * Does NOT respect temps_morts (would need API call for that).
     */
    if (state.currentPlanning.length === 0) return;

    let currentTime = state.currentPlanning[0].heure_debut;
    let currentDate = state.currentPlanning[0].date;

    for (let i = 0; i < state.currentPlanning.length; i++) {
        const slot = state.currentPlanning[i];
        const duration = slot.duration_min;

        // Calculate end time
        const endResult = addMinutes(currentTime, duration, currentDate);
        const endTime = typeof endResult === 'string' ? endResult : endResult.time;
        const endDate = typeof endResult === 'string' ? currentDate : endResult.date;

        // Update slot
        slot.heure_debut = currentTime;
        slot.heure_fin = endTime;
        slot.date = currentDate;

        // Move to next slot
        currentTime = endTime;
        currentDate = endDate;
    }
}

function handleDragEnd(e) {
    e.currentTarget.classList.remove('dragging');

    // Remove drag-over class from all slots
    document.querySelectorAll('.planning-slot').forEach(slot => {
        slot.classList.remove('drag-over');
    });

    draggedSlotIndex = null;
}

// ============================================================================
// DELETE HANDLERS
// ============================================================================

function attachDeleteHandlers() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', handleDeleteSlot);
    });
}

function handleDeleteSlot(e) {
    e.stopPropagation();
    const slotIndex = parseInt(e.currentTarget.getAttribute('data-slot-index'));

    if (slotIndex < 0 || slotIndex >= state.currentPlanning.length) {
        return;
    }

    const deletedSlot = state.currentPlanning[slotIndex];

    // Identify type: work (pomodoro, planned, recurrent) or pause (respiration, pause)
    const workTypes = new Set(['pomodoro', 'planned', 'recurrent']);
    const pauseTypes = new Set(['respiration', 'pause']);
    const deletedIsWork = workTypes.has(deletedSlot.type);

    // Remove the slot
    state.currentPlanning.splice(slotIndex, 1);

    // Find next slot of same type and move it up to fill the gap
    let gapIndex = slotIndex;

    while (gapIndex < state.currentPlanning.length) {
        // Find next slot of same type
        let nextSameTypeIndex = -1;

        for (let i = gapIndex + 1; i < state.currentPlanning.length; i++) {
            const candidateIsWork = workTypes.has(state.currentPlanning[i].type);

            if (deletedIsWork && candidateIsWork) {
                nextSameTypeIndex = i;
                break;
            } else if (!deletedIsWork && !candidateIsWork) {
                nextSameTypeIndex = i;
                break;
            }
        }

        if (nextSameTypeIndex === -1) {
            // No more slots of same type, done
            break;
        }

        // Move the found slot to fill the gap
        const slotToMove = state.currentPlanning[nextSameTypeIndex];
        state.currentPlanning.splice(nextSameTypeIndex, 1);
        state.currentPlanning.splice(gapIndex, 0, slotToMove);

        // Next gap is at gapIndex + 2 (skip the slot we just moved + the pause/work after it)
        gapIndex += 2;
    }

    // Recalculate all times to ensure continuity
    recalculateTimesAfterReorder();

    // Re-render
    renderPlanning({
        planning: state.currentPlanning,
        stats: calculateStats(state.currentPlanning),
        recurrent_task_scores: []
    });
}

// ============================================================================
// RENDERING FUNCTIONS
// ============================================================================

function renderPlanning(data) {
    const planning = data.planning || [];
    const stats = data.stats || {};
    const scores = data.recurrent_task_scores || [];

    // Stats
    if (planning.length > 0) {
        document.getElementById('planning-stats').style.display = 'flex';
        document.getElementById('stat-total').textContent = stats.total_slots || 0;
        document.getElementById('stat-work').textContent = `${stats.work_minutes || 0} min`;
        document.getElementById('stat-pause').textContent = `${stats.pause_minutes || 0} min`;
    }

    // Recurrent scores (transparency)
    if (scores.length > 0) {
        document.getElementById('recurrent-scores').style.display = 'block';
        document.getElementById('scores-list').innerHTML = scores.map(s => `
            <div class="score-item">
                <span class="score-item-name">${s.task_name}</span>:
                <span class="score-item-score">${s.score.toFixed(1)}/100</span>
            </div>
        `).join('');
    }

    // Planning timeline
    const container = document.getElementById('planning-display');

    if (planning.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Aucun planning généré</p></div>';
        document.getElementById('btn-export').style.display = 'none';
        return;
    }

    // Build planning HTML with delete buttons on each slot
    let html = '';
    let previousDate = null;

    planning.forEach((slot, index) => {
        // Check if date changed from previous slot
        if (previousDate && slot.date !== previousDate) {
            html += `
                <div class="date-separator">
                    <div class="date-separator-line"></div>
                    <div class="date-separator-text">📅 ${formatDate(slot.date)}</div>
                    <div class="date-separator-line"></div>
                </div>
            `;
        }
        previousDate = slot.date;

        const typeIcon = {
            'pomodoro': '🔴',
            'recurrent': '🟣',
            'planned': '🔵',
            'respiration': '🟢',
            'pause': '⚪'
        }[slot.type] || '';

        let metaInfo = `${slot.duration_min} min`;

        if (slot.pomodoro_num && slot.total_pomodoros) {
            metaInfo += ` • Pomodoro ${slot.pomodoro_num}/${slot.total_pomodoros}`;
        }

        if (slot.category) {
            metaInfo += ` • ${slot.category}`;
        }

        if (slot.is_rescheduled) {
            metaInfo += ` • ⚠️ Replanifiée (prévu ${slot.original_time})`;
        }

        html += `
            <div class="planning-slot ${slot.type}"
                 data-slot-index="${index}"
                 draggable="true">
                <div class="slot-header">
                    <span class="slot-time">${typeIcon} ${slot.heure_debut}</span>
                    <span class="slot-name">${slot.task_name}</span>
                    <span class="slot-duration">${slot.duration_min} min</span>
                    <button class="delete-btn" data-slot-index="${index}" title="Supprimer">✕</button>
                </div>
                <div class="slot-details">${metaInfo}</div>
            </div>
        `;
    });

    container.innerHTML = html;

    // Attach delete button handlers
    attachDeleteHandlers();

    // Attach drag & drop handlers
    attachDragDropHandlers();

    document.getElementById('btn-export').style.display = 'block';
}

function renderHistoryStats(stats) {
    const container = document.getElementById('stats-content');

    container.innerHTML = `
        <div class="info-box">
            <h3>📊 Statistiques Historique Apprentissage</h3>
            <p><strong>Total placements enregistrés:</strong> ${stats.total_entries || 0}</p>
            <p><strong>Tâches récurrentes uniques:</strong> ${stats.unique_tasks || 0}</p>
            ${stats.date_range ? `
                <p><strong>Période:</strong> ${stats.date_range.start} → ${stats.date_range.end}</p>
            ` : '<p><em>Aucune donnée historique encore</em></p>'}
        </div>

        <div class="info-box" style="margin-top: 20px;">
            <h4>🧠 Comment fonctionne l'apprentissage ?</h4>
            <p>Le système enregistre chaque planification de tâche récurrente dans un historique append-only.</p>
            <p><strong>Scoring 4 critères:</strong></p>
            <ul style="margin-left: 20px; margin-top: 10px;">
                <li><strong>50%</strong> Récurrence DUE (urgence - tâches en retard)</li>
                <li><strong>20%</strong> Fréquence jour semaine (habitudes - lundi → arrosage)</li>
                <li><strong>15%</strong> Fréquence globale (popularité)</li>
                <li><strong>15%</strong> Récence (tâches récentes)</li>
            </ul>
            <p style="margin-top: 10px;"><em>Plus vous exportez, plus le système apprend vos habitudes!</em></p>
        </div>
    `;
}

// ============================================================================
// UI INTERACTIONS
// ============================================================================

async function toggleTaskSelection(taskId) {
    const checkbox = document.getElementById(`task-${taskId}`);
    const index = state.selectedPomodoroIds.indexOf(taskId);

    if (index === -1) {
        // ADD task to selection
        state.selectedPomodoroIds.push(taskId);
        if (checkbox) checkbox.checked = true;
    } else {
        // REMOVE task from selection
        state.selectedPomodoroIds.splice(index, 1);
        if (checkbox) checkbox.checked = false;
    }

    // Regenerate planning via API (respects temps_morts for all days)
    await generatePlanning();
}

function setTodayDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('planning-date').value = today;
    state.currentDate = today;
}

function showLoading(show) {
    document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
}

function openStatsModal() {
    document.getElementById('stats-modal').style.display = 'flex';
    loadHistoryStats();
}

function closeStatsModal() {
    document.getElementById('stats-modal').style.display = 'none';
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Set today's date
    setTodayDate();

    // Date change
    document.getElementById('planning-date').addEventListener('change', (e) => {
        state.currentDate = e.target.value;
    });

    // Buttons
    document.getElementById('btn-today').addEventListener('click', setTodayDate);
    document.getElementById('btn-refresh').addEventListener('click', () => {
        loadPomodoroTasks();
        loadRecurrentTasks();
    });
    document.getElementById('btn-generate').addEventListener('click', generatePlanning);
    document.getElementById('btn-export').addEventListener('click', exportPlanning);
    document.getElementById('btn-stats').addEventListener('click', openStatsModal);

    // Modal close
    document.querySelector('.close').addEventListener('click', closeStatsModal);
    window.addEventListener('click', (e) => {
        if (e.target.id === 'stats-modal') {
            closeStatsModal();
        }
    });

    // Mobile tabs switching
    const mobileTabs = document.querySelectorAll('.mobile-tab');
    mobileTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');

            // Update active tab
            mobileTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Toggle body class for CSS
            if (targetTab === 'planning') {
                document.body.classList.add('mobile-view-planning');
            } else {
                document.body.classList.remove('mobile-view-planning');
            }
        });
    });

    // Initial load
    loadPomodoroTasks();
    loadRecurrentTasks();

    console.log('GitFocus Planner V2 initialized ✅');
});
