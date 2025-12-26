/**
 * Shadow IT Report - Main Application JavaScript
 */

// Global state
let reportData = null;
let filteredSites = [];

/**
 * Initialize the application
 */
async function init() {
    try {
        await loadData();
        detectPage();
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Error cargando datos del informe');
    }
}

/**
 * Load report data from JSON file
 */
async function loadData() {
    // Try to load from embedded data first (for static deployment)
    if (typeof REPORT_DATA !== 'undefined') {
        reportData = REPORT_DATA;
        return;
    }

    // Otherwise, load from file
    const response = await fetch('../data/report_data.json');
    if (!response.ok) {
        throw new Error('Could not load report data');
    }
    reportData = await response.json();
}

/**
 * Detect current page and initialize accordingly
 */
function detectPage() {
    const path = window.location.pathname;
    const page = path.split('/').pop() || 'index.html';

    switch (page) {
        case 'index.html':
        case '':
            renderDashboard();
            break;
        case 'sites.html':
            renderSitesList();
            break;
        case 'site-detail.html':
            renderSiteDetail();
            break;
        case 'apps.html':
            renderAppsList();
            break;
        default:
            renderDashboard();
    }
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return dateStr;
    }
}

/**
 * Format date relative to now
 */
function formatRelativeDate(dateStr) {
    if (!dateStr) return 'Nunca';
    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Hoy';
        if (diffDays === 1) return 'Ayer';
        if (diffDays < 7) return `Hace ${diffDays} días`;
        if (diffDays < 30) return `Hace ${Math.floor(diffDays / 7)} semanas`;
        if (diffDays < 365) return `Hace ${Math.floor(diffDays / 30)} meses`;
        return `Hace ${Math.floor(diffDays / 365)} años`;
    } catch {
        return dateStr;
    }
}

/**
 * Parse admin string to extract name and email
 */
function parseAdmin(adminStr) {
    const match = adminStr.match(/^(.+?)\s*(?:\(.*?\))?\s*<(.+?)>$/);
    if (match) {
        return { name: match[1].trim(), email: match[2].trim() };
    }
    return { name: adminStr, email: '' };
}

/**
 * Get initials from name
 */
function getInitials(name) {
    return name.split(' ')
        .filter(w => w.length > 0)
        .map(w => w[0].toUpperCase())
        .slice(0, 2)
        .join('');
}

/**
 * Create status badge HTML
 */
function statusBadge(status) {
    const cls = status.toLowerCase() === 'active' ? 'badge-active' : 'badge-suspended';
    return `<span class="badge ${cls}">${status}</span>`;
}

/**
 * Create product badge HTML
 */
function productBadge(product) {
    let cls = 'badge-jira';
    if (product.includes('confluence')) cls = 'badge-confluence';
    if (product.includes('servicedesk')) cls = 'badge-servicedesk';
    return `<span class="badge ${cls}">${product}</span>`;
}

// ===========================================
// DASHBOARD PAGE
// ===========================================

function renderDashboard() {
    const summary = reportData.summary;

    // Update stats
    document.getElementById('total-sites').textContent = summary.total_sites;
    document.getElementById('total-users').textContent = summary.total_users.toLocaleString();
    document.getElementById('active-sites').textContent = summary.status_distribution.Active || 0;
    document.getElementById('suspended-sites').textContent = summary.status_distribution.Suspended || 0;

    // Update Jira projects
    const jiraProjects = summary.total_jira_projects;
    document.getElementById('jira-software').textContent = jiraProjects.software || 0;
    document.getElementById('jira-servicedesk').textContent = jiraProjects.service_desk || 0;
    document.getElementById('jira-business').textContent = jiraProjects.business || 0;

    // Update Confluence
    document.getElementById('confluence-spaces').textContent = summary.total_confluence_spaces;
    document.getElementById('total-apps').textContent = summary.total_apps;

    // Render recent activity table
    renderRecentActivity();

    // Render charts
    renderCharts();
}

function renderRecentActivity() {
    const tbody = document.getElementById('recent-activity-body');
    if (!tbody) return;

    // Sort by last active date
    const sites = [...reportData.sites]
        .filter(s => s.last_active_csv)
        .sort((a, b) => new Date(b.last_active_csv) - new Date(a.last_active_csv))
        .slice(0, 10);

    tbody.innerHTML = sites.map(site => `
        <tr>
            <td>
                <a href="site-detail.html?url=${encodeURIComponent(site.url)}" class="site-link">
                    ${site.url}
                </a>
            </td>
            <td>${site.user_count}</td>
            <td>
                <div class="products-list">
                    ${site.products.map(p => productBadge(p)).join('')}
                </div>
            </td>
            <td>${formatRelativeDate(site.last_active_csv)}</td>
            <td>${statusBadge(site.status)}</td>
        </tr>
    `).join('');
}

function renderCharts() {
    // Status Distribution Chart
    const statusCtx = document.getElementById('status-chart');
    if (statusCtx) {
        const statusData = reportData.summary.status_distribution;
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(statusData),
                datasets: [{
                    data: Object.values(statusData),
                    backgroundColor: ['#00875A', '#FF991F', '#DE350B'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Products Distribution Chart
    const productsCtx = document.getElementById('products-chart');
    if (productsCtx) {
        // Count products across all sites
        const productCounts = {};
        reportData.sites.forEach(site => {
            site.products.forEach(product => {
                productCounts[product] = (productCounts[product] || 0) + 1;
            });
        });

        new Chart(productsCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(productCounts),
                datasets: [{
                    label: 'Sitios',
                    data: Object.values(productCounts),
                    backgroundColor: ['#0052CC', '#00875A', '#6554C0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Users by Site Chart
    const usersCtx = document.getElementById('users-chart');
    if (usersCtx) {
        const topSites = [...reportData.sites]
            .sort((a, b) => b.user_count - a.user_count)
            .slice(0, 10);

        new Chart(usersCtx, {
            type: 'bar',
            data: {
                labels: topSites.map(s => s.url.replace('.atlassian.net', '')),
                datasets: [{
                    label: 'Usuarios',
                    data: topSites.map(s => s.user_count),
                    backgroundColor: '#0052CC',
                    borderWidth: 0
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// ===========================================
// SITES LIST PAGE
// ===========================================

function renderSitesList() {
    filteredSites = [...reportData.sites];
    updateSitesTable();
    setupFilters();
}

function setupFilters() {
    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const productFilter = document.getElementById('product-filter');

    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }
    if (productFilter) {
        productFilter.addEventListener('change', applyFilters);
    }
}

function applyFilters() {
    const searchTerm = document.getElementById('search-input')?.value.toLowerCase() || '';
    const statusValue = document.getElementById('status-filter')?.value || '';
    const productValue = document.getElementById('product-filter')?.value || '';

    filteredSites = reportData.sites.filter(site => {
        // Search filter
        if (searchTerm && !site.url.toLowerCase().includes(searchTerm)) {
            return false;
        }

        // Status filter
        if (statusValue && site.status.toLowerCase() !== statusValue.toLowerCase()) {
            return false;
        }

        // Product filter
        if (productValue && !site.products.includes(productValue)) {
            return false;
        }

        return true;
    });

    updateSitesTable();
}

function updateSitesTable() {
    const tbody = document.getElementById('sites-table-body');
    const countEl = document.getElementById('sites-count');

    if (countEl) {
        countEl.textContent = `${filteredSites.length} sitios`;
    }

    if (!tbody) return;

    if (filteredSites.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    No se encontraron sitios con los filtros aplicados
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filteredSites.map(site => `
        <tr>
            <td>
                <a href="site-detail.html?url=${encodeURIComponent(site.url)}" class="site-link">
                    ${site.url}
                </a>
            </td>
            <td>${site.user_count}</td>
            <td>
                <div class="products-list">
                    ${site.products.map(p => productBadge(p)).join('')}
                </div>
            </td>
            <td>${formatDate(site.created_on)}</td>
            <td>${formatRelativeDate(site.last_active_csv)}</td>
            <td>${statusBadge(site.status)}</td>
        </tr>
    `).join('');
}

// ===========================================
// SITE DETAIL PAGE
// ===========================================

function renderSiteDetail() {
    const urlParam = new URLSearchParams(window.location.search).get('url');
    if (!urlParam) {
        showError('No se especificó un sitio');
        return;
    }

    const site = reportData.sites.find(s => s.url === urlParam);
    if (!site) {
        showError('Sitio no encontrado');
        return;
    }

    // Header info
    document.getElementById('site-url').textContent = site.url;
    document.getElementById('site-url-link').href = `https://${site.url}`;
    document.getElementById('site-status').innerHTML = statusBadge(site.status);
    if (site.status_details) {
        document.getElementById('site-status-details').textContent = site.status_details;
    }

    // Meta info
    document.getElementById('site-users').textContent = site.user_count;
    document.getElementById('site-created').textContent = formatDate(site.created_on);
    document.getElementById('site-last-active').textContent = formatRelativeDate(site.last_active_csv);

    // Products
    const productsEl = document.getElementById('site-products');
    if (productsEl) {
        productsEl.innerHTML = site.products.map(p => productBadge(p)).join('');
    }

    // Admins
    renderAdmins(site.admins);

    // Projects
    renderProjects(site);

    // Spaces
    renderSpaces(site);

    // Apps
    renderSiteApps(site);
}

function renderAdmins(admins) {
    const container = document.getElementById('admins-list');
    if (!container) return;

    if (!admins || admins.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay administradores registrados</p>';
        return;
    }

    container.innerHTML = admins.map(adminStr => {
        const admin = parseAdmin(adminStr);
        return `
            <div class="admin-item">
                <div class="admin-avatar">${getInitials(admin.name)}</div>
                <div class="admin-info">
                    <div class="admin-name">${admin.name}</div>
                    <div class="admin-email">${admin.email}</div>
                </div>
            </div>
        `;
    }).join('');
}

function renderProjects(site) {
    const container = document.getElementById('projects-section');
    if (!container) return;

    if (!site.has_jira) {
        container.innerHTML = '<p class="text-muted">Este sitio no tiene Jira</p>';
        return;
    }

    const projects = site.jira_projects;
    const totalProjects = Object.values(projects).reduce((a, b) => a + b, 0);

    let html = `
        <div class="stats-grid" style="margin-bottom: 1rem;">
            <div class="stat-card">
                <div class="stat-value">${projects.software || 0}</div>
                <div class="stat-label">Software</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${projects.service_desk || 0}</div>
                <div class="stat-label">Service Desk</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${projects.business || 0}</div>
                <div class="stat-label">Business</div>
            </div>
        </div>
    `;

    if (site.jira_project_details && site.jira_project_details.length > 0) {
        html += `
            <div class="items-grid">
                ${site.jira_project_details.map(proj => `
                    <div class="item-card">
                        <div class="item-info">
                            <h4>${proj.name}</h4>
                            <span class="key">${proj.key}</span>
                        </div>
                        <span class="badge badge-jira">${proj.project_type}</span>
                    </div>
                `).join('')}
            </div>
        `;
    } else if (totalProjects === 0) {
        html += '<p class="text-muted mt-1">No se encontraron proyectos (datos no disponibles via API)</p>';
    }

    if (site.last_jira_activity) {
        html += `<p class="text-muted mt-2">Última actividad: ${formatRelativeDate(site.last_jira_activity)}</p>`;
    }

    container.innerHTML = html;
}

function renderSpaces(site) {
    const container = document.getElementById('spaces-section');
    if (!container) return;

    if (!site.has_confluence) {
        container.innerHTML = '<p class="text-muted">Este sitio no tiene Confluence</p>';
        return;
    }

    let html = `
        <div class="stat-card" style="display: inline-block; min-width: 150px; margin-bottom: 1rem;">
            <div class="stat-value">${site.confluence_spaces}</div>
            <div class="stat-label">Espacios</div>
        </div>
    `;

    if (site.confluence_space_details && site.confluence_space_details.length > 0) {
        html += `
            <div class="items-grid">
                ${site.confluence_space_details.map(space => `
                    <div class="item-card">
                        <div class="item-info">
                            <h4>${space.name}</h4>
                            <span class="key">${space.key}</span>
                        </div>
                        <span class="badge badge-confluence">${space.type}</span>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        html += '<p class="text-muted mt-1">Detalles de espacios no disponibles (requiere acceso API)</p>';
    }

    if (site.last_confluence_activity) {
        html += `<p class="text-muted mt-2">Última actividad: ${formatRelativeDate(site.last_confluence_activity)}</p>`;
    }

    container.innerHTML = html;
}

function renderSiteApps(site) {
    const container = document.getElementById('apps-section');
    if (!container) return;

    if (!site.installed_apps || site.installed_apps.length === 0) {
        container.innerHTML = '<p class="text-muted">No se encontraron apps instaladas (requiere acceso API de administrador)</p>';
        return;
    }

    container.innerHTML = `
        <div class="apps-grid">
            ${site.installed_apps.map(app => `
                <div class="app-card">
                    <h3>${app.name}</h3>
                    <div class="app-vendor">Por ${app.vendor}</div>
                    <div class="text-muted">v${app.version}</div>
                </div>
            `).join('')}
        </div>
    `;
}

// ===========================================
// APPS LIST PAGE
// ===========================================

function renderAppsList() {
    const container = document.getElementById('apps-container');
    if (!container) return;

    const apps = reportData.apps;
    const appKeys = Object.keys(apps);

    if (appKeys.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No se encontraron apps instaladas</p>
                <p class="text-muted">Los datos de apps requieren ejecutar el script con credenciales de administrador</p>
            </div>
        `;
        return;
    }

    // Sort by number of sites
    appKeys.sort((a, b) => apps[b].sites.length - apps[a].sites.length);

    container.innerHTML = `
        <div class="apps-grid">
            ${appKeys.map(key => {
                const app = apps[key];
                return `
                    <div class="app-card">
                        <h3>${app.name}</h3>
                        <div class="app-vendor">Por ${app.vendor}</div>
                        <div class="app-sites">
                            Instalada en ${app.sites.length} sitio(s)
                        </div>
                        <div class="mt-1 text-muted" style="font-size: 0.8rem;">
                            ${app.sites.join(', ')}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;

    // Update count
    const countEl = document.getElementById('apps-count');
    if (countEl) {
        countEl.textContent = `${appKeys.length} apps`;
    }
}

// ===========================================
// UTILITIES
// ===========================================

function showError(message) {
    const container = document.querySelector('.container');
    if (container) {
        container.innerHTML = `
            <div class="card">
                <div class="empty-state">
                    <h2>Error</h2>
                    <p>${message}</p>
                    <a href="index.html" class="back-link mt-2">Volver al inicio</a>
                </div>
            </div>
        `;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);
