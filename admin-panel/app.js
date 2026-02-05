// Shellia AI Admin Dashboard - JavaScript

let supabaseClient = null;
let currentPage = 1;
const ITEMS_PER_PAGE = 20;
let currentUserPage = 1;

// Charts instances
let messagesChart = null;
let plansChart = null;
let usersChart = null;
let costsChart = null;

// Vérification d'authentification au chargement
document.addEventListener('DOMContentLoaded', async () => {
    // Vérifier si l'utilisateur est authentifié
    const isAuthenticated = await checkAuthentication();
    
    if (!isAuthenticated) {
        // Rediriger vers la page de login sécurisée
        window.location.replace('login.html');
        return;
    }
    
    // Masquer l'overlay de vérification
    const overlay = document.getElementById('auth-check-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
    
    // Marquer le body comme authentifié
    document.body.classList.add('authenticated');
    
    // Initialiser le dashboard
    setupNavigation();
    initSupabaseFromSession();
});

// Vérifier l'authentification
async function checkAuthentication() {
    try {
        // Vérifier la session dans sessionStorage
        const encryptedSession = sessionStorage.getItem('admin_session');
        if (!encryptedSession) {
            return false;
        }
        
        // Décrypter et vérifier la session
        const session = await decryptSession(encryptedSession);
        
        // Vérifier expiration
        if (new Date(session.expiresAt) < new Date()) {
            // Session expirée, supprimer
            sessionStorage.removeItem('admin_session');
            return false;
        }
        
        // Session valide, stocker pour utilisation
        window.currentSession = session;
        return true;
        
    } catch (error) {
        console.error('Erreur vérification auth:', error);
        return false;
    }
}

// Décrypter la session (même fonction que dans login-auth.js)
async function decryptSession(encryptedData) {
    const browserData = navigator.userAgent + navigator.language + screen.width + screen.height;
    
    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        encoder.encode(browserData),
        'PBKDF2',
        false,
        ['deriveKey']
    );
    
    const key = await crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: encoder.encode('shellia-salt'),
            iterations: 100000,
            hash: 'SHA-256'
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['decrypt']
    );
    
    const data = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
    const iv = data.slice(0, 12);
    const ciphertext = data.slice(12);
    
    const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        ciphertext
    );
    
    const decoder = new TextDecoder();
    return JSON.parse(decoder.decode(decrypted));
}

// Initialiser Supabase depuis la session
function initSupabaseFromSession() {
    // En production, les credentials viendraient du serveur
    // Pour l'instant, on utilise les valeurs stockées ou fallback
    const fallback = window.fallbackSupabaseConfig;
    if (fallback) {
        supabaseClient = supabase.createClient(fallback.url, fallback.key);
        loadOverview();
    } else {
        console.error('Configuration Supabase manquante');
        showToast('⚠️ Configuration incomplète', 'warning');
    }
}

// Initialiser Supabase avec URL et clé
function initSupabase(url, key) {
    supabaseClient = supabase.createClient(url, key);
    loadOverview();
}

function initSupabase(url, key) {
    supabaseClient = supabase.createClient(url, key);
    loadOverview();
}

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            
            // Update active state
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            
            // Show page
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(`${page}-page`).classList.add('active');
            
            // Update title
            document.querySelector('.page-title').textContent = 
                page.charAt(0).toUpperCase() + page.slice(1);
            
            // Load page data
            switch(page) {
                case 'overview':
                    loadOverview();
                    break;
                case 'users':
                    loadUsers();
                    break;
                case 'payments':
                    loadPayments();
                    break;
                case 'security':
                    loadSecurity();
                    break;
                case 'analytics':
                    loadAnalytics();
                    break;
            }
        });
    });
}

// Overview Page
async function loadOverview() {
    if (!supabaseClient) return;
    
    try {
        // Stats
        const { count: userCount } = await supabaseClient
            .from('users')
            .select('*', { count: 'exact', head: true });
        
        const today = new Date().toISOString().split('T')[0];
        const { data: todayMessages } = await supabaseClient
            .from('daily_quotas')
            .select('messages_used')
            .eq('date', today);
        
        const totalMessages = todayMessages?.reduce((a, b) => a + (b.messages_used || 0), 0) || 0;
        
        const { data: monthPayments } = await supabaseClient
            .from('payments')
            .select('amount')
            .gte('created_at', new Date(new Date().setDate(1)).toISOString());
        
        const totalRevenue = monthPayments?.reduce((a, b) => a + (b.amount || 0), 0) || 0;
        
        const { data: todayCost } = await supabaseClient
            .from('daily_quotas')
            .select('cost_usd')
            .eq('date', today);
        
        const totalCost = todayCost?.reduce((a, b) => a + (b.cost_usd || 0), 0) || 0;
        
        // Update stats
        document.getElementById('stat-users').textContent = userCount?.toLocaleString() || '-';
        document.getElementById('stat-messages').textContent = totalMessages.toLocaleString();
        document.getElementById('stat-revenue').textContent = `€${totalRevenue.toFixed(2)}`;
        document.getElementById('stat-cost').textContent = `$${totalCost.toFixed(4)}`;
        
        // Charts
        await loadOverviewCharts();
        
        // Recent activity
        await loadRecentActivity();
        
    } catch (error) {
        console.error('Error loading overview:', error);
    }
}

async function loadOverviewCharts() {
    // Messages chart (7 days)
    const dates = [];
    const messageCounts = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        dates.push(date.toLocaleDateString('fr-FR', { weekday: 'short' }));
        
        const { data } = await supabaseClient
            .from('daily_quotas')
            .select('messages_used')
            .eq('date', dateStr);
        
        messageCounts.push(data?.reduce((a, b) => a + (b.messages_used || 0), 0) || 0);
    }
    
    if (messagesChart) messagesChart.destroy();
    
    const ctx1 = document.getElementById('messages-chart').getContext('2d');
    messagesChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Messages',
                data: messageCounts,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                x: { grid: { display: false } }
            }
        }
    });
    
    // Plans distribution
    const { data: plans } = await supabaseClient
        .from('users')
        .select('plan');
    
    const planCounts = {};
    plans?.forEach(u => {
        planCounts[u.plan] = (planCounts[u.plan] || 0) + 1;
    });
    
    if (plansChart) plansChart.destroy();
    
    const ctx2 = document.getElementById('plans-chart').getContext('2d');
    plansChart = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: Object.keys(planCounts),
            datasets: [{
                data: Object.values(planCounts),
                backgroundColor: ['#6b7280', '#3b82f6', '#7c3aed', '#f59e0b', '#10b981']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right', labels: { color: '#fff' } }
            }
        }
    });
}

async function loadRecentActivity() {
    const { data: logs } = await supabaseClient
        .from('security_logs')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(10);
    
    const container = document.getElementById('activity-list');
    
    if (!logs || logs.length === 0) {
        container.innerHTML = '<p class="text-muted">Aucune activité récente</p>';
        return;
    }
    
    container.innerHTML = logs.map(log => {
        const eventIcons = {
            'message_processed': '💬',
            'stripe_webhook_invalid': '⚠️',
            'rate_limit_exceeded': '⏱️',
            'user_banned': '🚫',
            'plan_changed': '💎'
        };
        
        return `
            <div class="activity-item">
                <div class="activity-icon">${eventIcons[log.event_type] || '📋'}</div>
                <div class="activity-content">
                    <div class="activity-title">${log.event_type}</div>
                    <div class="activity-time">${new Date(log.timestamp).toLocaleString('fr-FR')}</div>
                </div>
            </div>
        `;
    }).join('');
}

// Users Page
async function loadUsers() {
    if (!supabaseClient) return;
    
    const offset = (currentUserPage - 1) * ITEMS_PER_PAGE;
    
    const { data: users, count } = await supabaseClient
        .from('users')
        .select('*', { count: 'exact' })
        .order('created_at', { ascending: false })
        .range(offset, offset + ITEMS_PER_PAGE - 1);
    
    const tbody = document.querySelector('#users-table tbody');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Aucun utilisateur</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.user_id}</td>
            <td>${user.username || 'Unknown'}</td>
            <td><span class="badge badge-${user.plan}">${user.plan}</span></td>
            <td>${user.total_messages?.toLocaleString() || 0}</td>
            <td>${new Date(user.created_at).toLocaleDateString('fr-FR')}</td>
            <td>
                <button onclick="editUser(${user.user_id}, '${user.plan}')" class="btn-primary" style="padding: 6px 12px; font-size: 12px;">Modifier</button>
            </td>
        </tr>
    `).join('');
    
    document.getElementById('page-info').textContent = `Page ${currentUserPage} / ${Math.ceil((count || 0) / ITEMS_PER_PAGE)}`;
}

function searchUsers() {
    const query = document.getElementById('user-search').value;
    // Implement search logic
    alert('Recherche: ' + query);
}

function prevPage() {
    if (currentUserPage > 1) {
        currentUserPage--;
        loadUsers();
    }
}

function nextPage() {
    currentUserPage++;
    loadUsers();
}

function editUser(userId, currentPlan) {
    document.getElementById('edit-user-id').value = userId;
    document.getElementById('edit-user-plan').value = currentPlan;
    document.getElementById('user-modal').classList.add('active');
}

async function saveUser() {
    const userId = document.getElementById('edit-user-id').value;
    const plan = document.getElementById('edit-user-plan').value;
    
    try {
        await supabaseClient
            .from('users')
            .update({ plan })
            .eq('user_id', userId);
        
        closeModal();
        loadUsers();
        alert('Utilisateur mis à jour');
    } catch (error) {
        alert('Erreur: ' + error.message);
    }
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
}

// Payments Page
async function loadPayments() {
    if (!supabaseClient) return;
    
    // Stats
    const { data: monthPayments } = await supabaseClient
        .from('payments')
        .select('amount')
        .gte('created_at', new Date(new Date().setDate(1)).toISOString());
    
    const total = monthPayments?.reduce((a, b) => a + (b.amount || 0), 0) || 0;
    const count = monthPayments?.length || 0;
    
    document.getElementById('payment-total').textContent = `€${total.toFixed(2)}`;
    document.getElementById('payment-count').textContent = count;
    
    // Table
    const { data: payments } = await supabaseClient
        .from('payments')
        .select('*, users(username)')
        .order('created_at', { ascending: false })
        .limit(50);
    
    const tbody = document.querySelector('#payments-table tbody');
    
    if (!payments || payments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">Aucun paiement</td></tr>';
        return;
    }
    
    tbody.innerHTML = payments.map(p => `
        <tr>
            <td>${new Date(p.created_at).toLocaleDateString('fr-FR')}</td>
            <td>${p.users?.username || 'Unknown'}</td>
            <td><span class="badge badge-${p.plan}">${p.plan}</span></td>
            <td>€${p.amount?.toFixed(2)}</td>
            <td>${p.status}</td>
        </tr>
    `).join('');
}

// Security Page
async function loadSecurity() {
    if (!supabaseClient) return;
    
    // Check circuit breaker state
    const { data: circuitState } = await supabaseClient
        .from('circuit_breaker_state')
        .select('*')
        .eq('circuit_name', 'gemini_api')
        .single();
    
    const circuitStatus = document.getElementById('circuit-status');
    if (circuitState) {
        circuitStatus.textContent = circuitState.state.toUpperCase();
        circuitStatus.className = 'status ' + (circuitState.state === 'closed' ? 'ok' : 'warning');
    } else {
        circuitStatus.textContent = 'INACTIF';
        circuitStatus.className = 'status';
    }
    
    // Security alerts
    const { data: alerts } = await supabaseClient
        .from('security_logs')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(5);
    
    const alertsContainer = document.getElementById('security-alerts-list');
    
    if (!alerts || alerts.length === 0) {
        alertsContainer.innerHTML = '<p class="text-muted">Aucune alerte</p>';
    } else {
        alertsContainer.innerHTML = alerts.map(alert => `
            <div class="alert-item ${alert.severity}">
                <strong>${alert.event_type}</strong>
                <span style="float: right; color: #6b7280;">${new Date(alert.timestamp).toLocaleString('fr-FR')}</span>
            </div>
        `).join('');
    }
    
    // Security logs
    const { data: logs } = await supabaseClient
        .from('security_logs')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(20);
    
    const tbody = document.querySelector('#security-logs-table tbody');
    
    if (!logs || logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="loading">Aucun log</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${new Date(log.timestamp).toLocaleString('fr-FR')}</td>
            <td>${log.event_type}</td>
            <td><span class="badge badge-${log.severity}">${log.severity}</span></td>
            <td>${log.user_id || '-'}</td>
        </tr>
    `).join('');
}

// Analytics Page
async function loadAnalytics() {
    if (!supabaseClient) return;
    
    // Users chart (30 days)
    const dates = [];
    const userCounts = [];
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        dates.push(date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }));
        
        const { count } = await supabaseClient
            .from('daily_quotas')
            .select('*', { count: 'exact', head: true })
            .eq('date', dateStr);
        
        userCounts.push(count || 0);
    }
    
    if (usersChart) usersChart.destroy();
    
    const ctx1 = document.getElementById('users-chart').getContext('2d');
    usersChart = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Utilisateurs actifs',
                data: userCounts,
                backgroundColor: '#7c3aed'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                x: { grid: { display: false } }
            }
        }
    });
    
    // Costs chart
    const costDates = [];
    const costs = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        costDates.push(date.toLocaleDateString('fr-FR', { weekday: 'short' }));
        
        const { data } = await supabaseClient
            .from('daily_quotas')
            .select('cost_usd')
            .eq('date', dateStr);
        
        costs.push(data?.reduce((a, b) => a + (b.cost_usd || 0), 0) || 0);
    }
    
    if (costsChart) costsChart.destroy();
    
    const ctx2 = document.getElementById('costs-chart').getContext('2d');
    costsChart = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: costDates,
            datasets: [{
                label: 'Coût ($)',
                data: costs,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                x: { grid: { display: false } }
            }
        }
    });
    
    // Metrics
    const { count: totalUsers } = await supabaseClient
        .from('users')
        .select('*', { count: 'exact', head: true });
    
    const { data: totalMessages } = await supabaseClient
        .from('users')
        .select('total_messages');
    
    const totalMsg = totalMessages?.reduce((a, b) => a + (b.total_messages || 0), 0) || 0;
    
    document.getElementById('metric-msg-per-user').textContent = 
        totalUsers ? (totalMsg / totalUsers).toFixed(1) : '-';
    
    document.getElementById('metric-retention').textContent = '85%'; // Placeholder
    document.getElementById('metric-cost-per-msg').textContent = '$0.002'; // Placeholder
    document.getElementById('metric-response-time').textContent = '1.2s'; // Placeholder
}

// Auto-refresh every 60 seconds
setInterval(() => {
    const activePage = document.querySelector('.page.active');
    if (activePage.id === 'overview-page') {
        loadOverview();
    } else if (activePage.id === 'security-page') {
        loadSecurity();
    } else if (activePage.id === 'tasks-page') {
        loadTasks();
    }
}, 60000);

// ============================================================================
// TASKS SCHEDULER FUNCTIONS
// ============================================================================

let currentTaskFilter = 'all';
let currentExecutionFilter = 'all';

async function loadTasks() {
    if (!supabaseClient) return;
    
    try {
        // Charger les tâches actives
        const { data: tasks, error: tasksError } = await supabaseClient
            .from('scheduled_tasks')
            .select('*')
            .order('created_at', { ascending: false });
        
        if (tasksError) throw tasksError;
        
        // Mettre à jour les stats
        const activeCount = tasks?.filter(t => t.is_active).length || 0;
        const runningCount = tasks?.filter(t => t.is_running).length || 0;
        
        document.getElementById('task-total').textContent = activeCount;
        document.getElementById('task-running').textContent = runningCount;
        document.getElementById('task-badge').textContent = runningCount > 0 ? runningCount : '';
        
        // Afficher les tâches
        const tbody = document.querySelector('#tasks-table tbody');
        if (!tasks || tasks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Aucune tâche planifiée</td></tr>';
        } else {
            tbody.innerHTML = tasks.map(task => `
                <tr>
                    <td>
                        <strong>${escapeHtml(task.name)}</strong>
                        ${task.description ? `<br><small style="color: var(--text-muted);">${escapeHtml(task.description)}</small>` : ''}
                    </td>
                    <td><span class="badge badge-${task.task_type}">${task.task_type}</span></td>
                    <td><code>${task.cron_expression}</code></td>
                    <td>${formatNextRun(task.next_run_at)}</td>
                    <td>${formatTaskStatus(task)}</td>
                    <td>
                        <button onclick="runTaskNow('${task.id}')" class="btn-icon" title="Exécuter maintenant" ${task.is_running ? 'disabled' : ''}>▶️</button>
                        <button onclick="editTask('${task.id}')" class="btn-icon" title="Modifier">✏️</button>
                        <button onclick="toggleTask('${task.id}', ${!task.is_active})" class="btn-icon" title="${task.is_active ? 'Désactiver' : 'Activer'}">${task.is_active ? '⏸️' : '▶️'}</button>
                        <button onclick="deleteTask('${task.id}')" class="btn-icon" title="Supprimer">🗑️</button>
                    </td>
                </tr>
            `).join('');
        }
        
        // Charger les statistiques
        await loadTaskStats();
        
        // Charger les exécutions
        await loadExecutions();
        
        // Charger les templates
        await loadTaskTemplates();
        
    } catch (error) {
        console.error('Erreur chargement tâches:', error);
        showToast('❌ Erreur chargement des tâches', 'error');
    }
}

async function loadTaskStats() {
    try {
        const { data: stats, error } = await supabaseClient.rpc('get_task_statistics', {
            p_days: 1
        });
        
        if (error) throw error;
        
        if (stats) {
            document.getElementById('task-success').textContent = stats.successful_executions || 0;
            document.getElementById('task-failed').textContent = stats.failed_executions || 0;
        }
    } catch (error) {
        console.error('Erreur stats:', error);
    }
}

async function loadExecutions() {
    try {
        let query = supabaseClient
            .from('recent_task_executions')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(50);
        
        if (currentExecutionFilter !== 'all') {
            query = query.eq('status', currentExecutionFilter);
        }
        
        const { data: executions, error } = await query;
        
        if (error) throw error;
        
        const tbody = document.querySelector('#executions-table tbody');
        if (!executions || executions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Aucune exécution</td></tr>';
        } else {
            tbody.innerHTML = executions.map(exec => `
                <tr>
                    <td>${new Date(exec.created_at).toLocaleString('fr-FR')}</td>
                    <td>${escapeHtml(exec.task_name)}</td>
                    <td><span class="badge badge-${exec.task_type}">${exec.task_type}</span></td>
                    <td>${exec.duration_seconds ? exec.duration_seconds + 's' : '-'}</td>
                    <td>${formatExecutionStatus(exec.status)}</td>
                    <td>
                        <button onclick="viewExecutionDetails('${exec.id}')" class="btn-icon" title="Voir détails">👁️</button>
                        ${exec.status === 'failed' ? `<button onclick="retryTask('${exec.task_id}', '${exec.id}')" class="btn-icon" title="Réessayer">🔄</button>` : ''}
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Erreur chargement exécutions:', error);
    }
}

async function loadTaskTemplates() {
    try {
        const { data: templates, error } = await supabaseClient
            .from('task_templates')
            .select('*')
            .order('name');
        
        if (error) throw error;
        
        const container = document.getElementById('templates-grid');
        if (!templates || templates.length === 0) {
            container.innerHTML = '<p class="text-muted">Aucun template disponible</p>';
        } else {
            container.innerHTML = templates.map(template => `
                <div class="template-card" onclick="createFromTemplate('${template.id}')">
                    <h4>${getTaskTypeIcon(template.task_type)} ${escapeHtml(template.name)}</h4>
                    <p>${escapeHtml(template.description)}</p>
                    <div class="template-meta">
                        <span>⏰ ${template.default_cron || 'Manuel'}</span>
                        <span>⏱️ ${template.default_timeout}s</span>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Erreur chargement templates:', error);
    }
}

function formatTaskStatus(task) {
    if (task.is_running) {
        return '<span class="task-status running">⏳ En cours...</span>';
    }
    
    if (!task.is_active) {
        return '<span class="task-status" style="background: rgba(107,114,128,0.2); color: #9ca3af;">⏸️ Désactivée</span>';
    }
    
    if (!task.next_run_at) {
        return '<span class="task-status scheduled">📅 Planifiée</span>';
    }
    
    const nextRun = new Date(task.next_run_at);
    const now = new Date();
    
    if (nextRun < now) {
        return '<span class="task-status overdue">⚠️ En retard</span>';
    }
    
    if (nextRun - now < 3600000) { // Moins d'1 heure
        return '<span class="task-status soon">🔜 Bientôt</span>';
    }
    
    return '<span class="task-status scheduled">📅 Planifiée</span>';
}

function formatExecutionStatus(status) {
    const icons = {
        'pending': '⏳',
        'running': '⏯️',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '🚫'
    };
    return `<span class="task-status ${status}">${icons[status] || '❓'} ${status}</span>`;
}

function formatNextRun(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date - now;
    
    if (diff < 0) return '<span style="color: var(--danger);">En retard !</span>';
    if (diff < 60000) return 'Dans moins d\'une minute';
    if (diff < 3600000) return `Dans ${Math.floor(diff / 60000)} min`;
    if (diff < 86400000) return `Dans ${Math.floor(diff / 3600000)}h`;
    
    return date.toLocaleString('fr-FR');
}

function getTaskTypeIcon(type) {
    const icons = {
        'backup': '💾',
        'cleanup': '🧹',
        'report': '📊',
        'notification': '🔔',
        'custom': '⚙️'
    };
    return icons[type] || '📋';
}

async function runTaskNow(taskId) {
    try {
        showToast('🚀 Exécution de la tâche...', 'info');
        
        const { data, error } = await supabaseClient.rpc('execute_task_now', {
            p_task_id: taskId,
            p_executed_by: authState.admin?.id || null
        });
        
        if (error) throw error;
        
        showToast('✅ Tâche lancée !', 'success');
        
        // Rafraîchir après 2 secondes
        setTimeout(loadTasks, 2000);
        
    } catch (error) {
        console.error('Erreur exécution:', error);
        showToast('❌ Erreur: ' + error.message, 'error');
    }
}

async function toggleTask(taskId, activate) {
    try {
        const { error } = await supabaseClient.rpc('update_scheduled_task', {
            p_task_id: taskId,
            p_is_active: activate
        });
        
        if (error) throw error;
        
        showToast(activate ? '✅ Tâche activée' : '⏸️ Tâche désactivée', 'success');
        loadTasks();
        
    } catch (error) {
        console.error('Erreur:', error);
        showToast('❌ Erreur', 'error');
    }
}

async function deleteTask(taskId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette tâche ?')) return;
    
    try {
        const { error } = await supabaseClient.rpc('delete_scheduled_task', {
            p_task_id: taskId
        });
        
        if (error) throw error;
        
        showToast('🗑️ Tâche supprimée', 'success');
        loadTasks();
        
    } catch (error) {
        console.error('Erreur:', error);
        showToast('❌ Impossible de supprimer', 'error');
    }
}

function filterExecutions(status) {
    currentExecutionFilter = status;
    
    // Mettre à jour les boutons
    document.querySelectorAll('.filter-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    loadExecutions();
}

function showCreateTaskModal() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'create-task-modal';
    modal.innerHTML = `
        <div class="modal-content wide">
            <h3>➕ Nouvelle Tâche Planifiée</h3>
            
            <div class="form-group">
                <label>Nom de la tâche</label>
                <input type="text" id="task-name" placeholder="Ex: Sauvegarde quotidienne">
            </div>
            
            <div class="form-group">
                <label>Description</label>
                <input type="text" id="task-description" placeholder="Description optionnelle">
            </div>
            
            <div class="form-group">
                <label>Type de tâche</label>
                <select id="task-type">
                    <option value="backup">💾 Sauvegarde</option>
                    <option value="cleanup">🧹 Nettoyage</option>
                    <option value="report">📊 Rapport</option>
                    <option value="notification">🔔 Notification</option>
                    <option value="custom">⚙️ Personnalisé</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Expression Cron (fréquence)</label>
                <input type="text" id="task-cron" placeholder="0 2 * * *" value="0 2 * * *">
                <div class="cron-helper">
                    <span class="cron-preset" onclick="setCron('0 2 * * *')">Tous les jours à 2h</span>
                    <span class="cron-preset" onclick="setCron('0 */6 * * *')">Toutes les 6h</span>
                    <span class="cron-preset" onclick="setCron('0 0 * * 0')">Tous les dimanches</span>
                    <span class="cron-preset" onclick="setCron('0 0 1 * *')">Tous les 1er du mois</span>
                </div>
                <span class="help-text">Format: minute heure jour_du_mois mois jour_de_la_semaine</span>
            </div>
            
            <div class="form-group">
                <label>Fuseau horaire</label>
                <select id="task-timezone">
                    <option value="UTC">UTC</option>
                    <option value="Europe/Paris">Europe/Paris</option>
                    <option value="America/New_York">America/New_York</option>
                    <option value="Asia/Tokyo">Asia/Tokyo</option>
                </select>
            </div>
            
            <div class="form-actions">
                <button onclick="createTask()" class="btn-primary">💾 Créer la tâche</button>
                <button onclick="closeTaskModal()" class="btn-secondary">Annuler</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function setCron(expression) {
    document.getElementById('task-cron').value = expression;
}

function closeTaskModal() {
    const modal = document.getElementById('create-task-modal');
    if (modal) modal.remove();
}

async function createTask() {
    const name = document.getElementById('task-name').value.trim();
    const description = document.getElementById('task-description').value.trim();
    const type = document.getElementById('task-type').value;
    const cron = document.getElementById('task-cron').value.trim();
    const timezone = document.getElementById('task-timezone').value;
    
    if (!name || !cron) {
        showToast('❌ Nom et expression cron requis', 'error');
        return;
    }
    
    try {
        const { data, error } = await supabaseClient.rpc('create_scheduled_task', {
            p_name: name,
            p_description: description,
            p_task_type: type,
            p_cron_expression: cron,
            p_parameters: {},
            p_timezone: timezone,
            p_created_by: authState.admin?.id || null
        });
        
        if (error) throw error;
        
        showToast('✅ Tâche créée avec succès !', 'success');
        closeTaskModal();
        loadTasks();
        
    } catch (error) {
        console.error('Erreur création:', error);
        showToast('❌ Erreur: ' + error.message, 'error');
    }
}

async function createFromTemplate(templateId) {
    try {
        const { data: template, error } = await supabaseClient
            .from('task_templates')
            .select('*')
            .eq('id', templateId)
            .single();
        
        if (error) throw error;
        
        // Pré-remplir le modal avec le template
        showCreateTaskModal();
        document.getElementById('task-name').value = template.name;
        document.getElementById('task-description').value = template.description || '';
        document.getElementById('task-type').value = template.task_type;
        document.getElementById('task-cron').value = template.default_cron || '0 2 * * *';
        
    } catch (error) {
        console.error('Erreur:', error);
        showToast('❌ Erreur chargement template', 'error');
    }
}

async function viewExecutionDetails(executionId) {
    try {
        const { data: execution, error } = await supabaseClient
            .from('task_executions')
            .select('*')
            .eq('id', executionId)
            .single();
        
        if (error) throw error;
        
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content wide">
                <h3>📋 Détails de l'exécution</h3>
                
                <div class="form-group">
                    <label>Statut</label>
                    <p>${formatExecutionStatus(execution.status)}</p>
                </div>
                
                <div class="form-group">
                    <label>Date</label>
                    <p>${new Date(execution.created_at).toLocaleString('fr-FR')}</p>
                </div>
                
                ${execution.duration_seconds ? `
                <div class="form-group">
                    <label>Durée</label>
                    <p>${execution.duration_seconds} secondes</p>
                </div>
                ` : ''}
                
                ${execution.output ? `
                <div class="form-group">
                    <label>Sortie</label>
                    <div class="execution-output">${escapeHtml(execution.output)}</div>
                </div>
                ` : ''}
                
                ${execution.error_message ? `
                <div class="form-group">
                    <label>Erreur</label>
                    <div class="execution-output error">${escapeHtml(execution.error_message)}</div>
                </div>
                ` : ''}
                
                <div class="form-actions">
                    <button onclick="this.closest('.modal').remove()" class="btn-secondary">Fermer</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
    } catch (error) {
        console.error('Erreur:', error);
        showToast('❌ Impossible de charger les détails', 'error');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// CONFIGURATION API FUNCTIONS
// ============================================================================

// CryptoJS pour le chiffrement (simplifié - en production utiliser Web Crypto API)
// Note: Cette implémentation utilise une librairie externe, ajoutez dans index.html:
// <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>

let configData = {
    masterKey: localStorage.getItem('config_master_key') || '',
    apis: {}
};

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === 'password' ? 'text' : 'password';
}

function generateMasterKey() {
    // Générer une clé Fernet-like (simplifié pour le dashboard)
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    const key = btoa(String.fromCharCode(...array));
    document.getElementById('master-key').value = key;
    showToast('Clé maître générée ! Sauvegardez-la immédiatement.', 'success');
}

function saveMasterKey() {
    const key = document.getElementById('master-key').value.trim();
    
    if (!key) {
        showToast('Veuillez entrer une clé maître', 'error');
        return;
    }
    
    if (key.length < 32) {
        showToast('Clé trop courte (min 32 caractères)', 'error');
        return;
    }
    
    configData.masterKey = key;
    localStorage.setItem('config_master_key', key);
    
    // Logger l'action
    logConfigChange('MASTER_KEY_UPDATED', 'Clé maître mise à jour');
    
    showToast('Clé maître sauvegardée avec succès !', 'success');
}

function testMasterKey() {
    const key = document.getElementById('master-key').value.trim();
    
    if (!key) {
        showToast('Aucune clé à tester', 'error');
        return;
    }
    
    // Test simple: vérifier le format
    try {
        atob(key);
        showToast('✅ Format de clé valide', 'success');
    } catch (e) {
        showToast('❌ Format de clé invalide (doit être en base64)', 'error');
    }
}

async function testGeminiKey() {
    const key = document.getElementById('gemini-key').value.trim();
    
    if (!key) {
        showToast('Veuillez entrer une clé Gemini', 'error');
        return;
    }
    
    showToast('🧪 Test de la clé Gemini...', 'info');
    
    try {
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${key}`);
        
        if (response.ok) {
            document.getElementById('gemini-status').textContent = '✅ Valide';
            document.getElementById('gemini-status').className = 'api-status ok';
            showToast('✅ Clé Gemini valide !', 'success');
        } else {
            document.getElementById('gemini-status').textContent = '❌ Invalide';
            document.getElementById('gemini-status').className = 'api-status error';
            showToast('❌ Clé Gemini invalide', 'error');
        }
    } catch (error) {
        showToast('❌ Erreur de connexion', 'error');
    }
}

async function testStripeKey() {
    const key = document.getElementById('stripe-key').value.trim();
    
    if (!key) {
        showToast('Veuillez entrer une clé Stripe', 'error');
        return;
    }
    
    showToast('🧪 Test de la clé Stripe...', 'info');
    
    try {
        const response = await fetch('https://api.stripe.com/v1/account', {
            headers: {
                'Authorization': `Bearer ${key}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('stripe-status').textContent = `✅ ${data.settings?.dashboard?.display_name || 'Valide'}`;
            document.getElementById('stripe-status').className = 'api-status ok';
            showToast('✅ Clé Stripe valide !', 'success');
        } else {
            document.getElementById('stripe-status').textContent = '❌ Invalide';
            document.getElementById('stripe-status').className = 'api-status error';
            showToast('❌ Clé Stripe invalide', 'error');
        }
    } catch (error) {
        showToast('❌ Erreur de connexion', 'error');
    }
}

async function testDiscordToken() {
    const token = document.getElementById('discord-token').value.trim();
    
    if (!token) {
        showToast('Veuillez entrer un token Discord', 'error');
        return;
    }
    
    showToast('🧪 Test du token Discord...', 'info');
    
    try {
        const response = await fetch('https://discord.com/api/v10/users/@me', {
            headers: {
                'Authorization': `Bot ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('discord-status').textContent = `✅ ${data.username}`;
            document.getElementById('discord-status').className = 'api-status ok';
            showToast('✅ Token Discord valide !', 'success');
        } else {
            document.getElementById('discord-status').textContent = '❌ Invalide';
            document.getElementById('discord-status').className = 'api-status error';
            showToast('❌ Token Discord invalide', 'error');
        }
    } catch (error) {
        showToast('❌ Erreur de connexion', 'error');
    }
}

async function testSupabaseKey() {
    const url = document.getElementById('supabase-url-config').value.trim();
    const key = document.getElementById('supabase-key-config').value.trim();
    
    if (!url || !key) {
        showToast('Veuillez entrer l\'URL et la clé Supabase', 'error');
        return;
    }
    
    showToast('🧪 Test de la connexion Supabase...', 'info');
    
    try {
        const response = await fetch(`${url}/rest/v1/`, {
            headers: {
                'apikey': key,
                'Authorization': `Bearer ${key}`
            }
        });
        
        if (response.ok) {
            document.getElementById('supabase-status').textContent = '✅ Connecté';
            document.getElementById('supabase-status').className = 'api-status ok';
            showToast('✅ Connexion Supabase réussie !', 'success');
        } else {
            document.getElementById('supabase-status').textContent = '❌ Erreur';
            document.getElementById('supabase-status').className = 'api-status error';
            showToast('❌ Impossible de se connecter à Supabase', 'error');
        }
    } catch (error) {
        document.getElementById('supabase-status').textContent = '❌ Erreur';
        document.getElementById('supabase-status').className = 'api-status error';
        showToast('❌ Erreur de connexion', 'error');
    }
}

async function saveAllKeys() {
    const masterKey = document.getElementById('master-key').value.trim();
    
    if (!masterKey) {
        showToast('⚠️ Vous devez d\'abord configurer une clé maître', 'warning');
        return;
    }
    
    // Collecter toutes les clés
    const config = {
        SECURE_CONFIG_KEY: masterKey,
        GEMINI_API_KEY: document.getElementById('gemini-key').value.trim(),
        STRIPE_SECRET_KEY: document.getElementById('stripe-key').value.trim(),
        STRIPE_WEBHOOK_SECRET: document.getElementById('stripe-webhook-key').value.trim(),
        DISCORD_TOKEN: document.getElementById('discord-token').value.trim(),
        SUPABASE_URL: document.getElementById('supabase-url-config').value.trim(),
        SUPABASE_SERVICE_KEY: document.getElementById('supabase-key-config').value.trim(),
        REDIS_URL: document.getElementById('redis-url').value.trim()
    };
    
    // Filtrer les valeurs vides
    const envContent = Object.entries(config)
        .filter(([key, value]) => value)
        .map(([key, value]) => `${key}=${value}`)
        .join('\n');
    
    // Sauvegarder dans Supabase (table secure_config)
    try {
        // D'abord, chiffrer les valeurs sensibles
        const encryptedConfig = await encryptConfig(config, masterKey);
        
        // Sauvegarder dans Supabase
        const { error } = await supabaseClient
            .from('secure_config')
            .upsert({
                config_key: 'api_keys',
                encrypted_value: JSON.stringify(encryptedConfig),
                encrypted_by: 'admin_dashboard',
                updated_at: new Date().toISOString()
            });
        
        if (error) throw error;
        
        // Logger
        logConfigChange('API_KEYS_UPDATED', 'Configuration API mise à jour');
        
        showToast('✅ Configuration sauvegardée avec succès !', 'success');
        
        // Proposer le téléchargement du .env
        downloadEnvFile(envContent);
        
    } catch (error) {
        console.error('Erreur sauvegarde:', error);
        showToast('❌ Erreur lors de la sauvegarde: ' + error.message, 'error');
    }
}

async function encryptConfig(config, masterKey) {
    // Simplifié - en production, utiliser une vraie librairie de chiffrement
    // Cette fonction simule le chiffrement
    const encrypted = {};
    
    for (const [key, value] of Object.entries(config)) {
        if (value && key !== 'SECURE_CONFIG_KEY') {
            // Marquer comme chiffré (préfixe ENC:)
            encrypted[key] = `ENC:${btoa(value)}`;
        } else {
            encrypted[key] = value;
        }
    }
    
    return encrypted;
}

function downloadEnvFile(content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '.env.backup';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function exportConfig() {
    const inputs = [
        'master-key', 'gemini-key', 'stripe-key', 'stripe-webhook-key',
        'discord-token', 'supabase-url-config', 'supabase-key-config', 'redis-url'
    ];
    
    const config = {};
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const key = id.replace(/-([a-z])/g, g => g[1].toUpperCase()).toUpperCase();
            config[key] = el.value;
        }
    });
    
    const envContent = Object.entries(config)
        .filter(([key, value]) => value)
        .map(([key, value]) => `${key}=${value}`)
        .join('\n');
    
    downloadEnvFile(envContent);
    showToast('📥 Configuration exportée !', 'success');
}

function importConfig() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.env,.txt';
    
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target.result;
            parseEnvFile(content);
        };
        reader.readAsText(file);
    };
    
    input.click();
}

function parseEnvFile(content) {
    const lines = content.split('\n');
    const mapping = {
        'SECURE_CONFIG_KEY': 'master-key',
        'GEMINI_API_KEY': 'gemini-key',
        'STRIPE_SECRET_KEY': 'stripe-key',
        'STRIPE_WEBHOOK_SECRET': 'stripe-webhook-key',
        'DISCORD_TOKEN': 'discord-token',
        'SUPABASE_URL': 'supabase-url-config',
        'SUPABASE_SERVICE_KEY': 'supabase-key-config',
        'REDIS_URL': 'redis-url'
    };
    
    let imported = 0;
    
    lines.forEach(line => {
        const match = line.match(/^([A-Z_]+)=(.+)$/);
        if (match) {
            const [, key, value] = match;
            const inputId = mapping[key];
            if (inputId) {
                const input = document.getElementById(inputId);
                if (input) {
                    input.value = value.trim();
                    imported++;
                }
            }
        }
    });
    
    showToast(`📤 ${imported} valeurs importées !`, 'success');
}

async function logConfigChange(action, details) {
    if (!supabaseClient) return;
    
    try {
        await supabaseClient
            .from('audit_logs')
            .insert({
                admin_user_id: 0, // Système/dashboard
                action: action,
                target_type: 'config',
                new_value: { details },
                reason: 'Modification via dashboard admin',
                created_at: new Date().toISOString()
            });
    } catch (error) {
        console.error('Erreur log audit:', error);
    }
}

async function loadConfigLogs() {
    if (!supabaseClient) return;
    
    try {
        const { data: logs } = await supabaseClient
            .from('audit_logs')
            .select('*')
            .eq('target_type', 'config')
            .order('created_at', { ascending: false })
            .limit(20);
        
        const tbody = document.querySelector('#config-logs-table tbody');
        
        if (!logs || logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="loading">Aucun historique</td></tr>';
            return;
        }
        
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${new Date(log.created_at).toLocaleString('fr-FR')}</td>
                <td>${log.admin_user_id || 'Système'}</td>
                <td><span class="badge badge-${log.action.includes('ERROR') ? 'danger' : 'info'}">${log.action}</span></td>
                <td>${log.new_value?.details || '-'}</td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Erreur chargement logs:', error);
    }
}

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Charger les logs de config au chargement de la page
loadConfigLogs();
