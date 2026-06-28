const API_BASE = '/api';

// State
let services = [];
let suites = [];
let reports = [];
let currentEndpoints = [];

// Tab navigation
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
    });
});

// API helpers
async function api(method, path, body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${path}`, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// Service Management
async function loadServices() {
    services = await api('GET', '/services');
    renderServices();
}

function renderServices() {
    const list = document.getElementById('serviceList');
    if (services.length === 0) {
        list.innerHTML = '<div class="empty-state">No services configured yet. Add one above.</div>';
        return;
    }
    list.innerHTML = services.map(s => `
        <div class="service-card" onclick="selectService('${s.id}')">
            <div>
                <strong>${s.name}</strong>
                <div style="font-size:0.85rem;color:var(--text-muted)">${s.base_url} &bull; ${s.endpoints.length} endpoint(s)</div>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
                <span class="badge ${s.service_type === 'dotnet_core' ? 'badge-dotnet' : 'badge-spring'}">
                    ${s.service_type === 'dotnet_core' ? '.NET Core' : 'Spring Boot'}
                </span>
                <button class="btn btn-sm btn-primary" onclick="event.stopPropagation();generateTests('${s.id}')">Generate Tests</button>
                <button class="btn btn-sm btn-danger" onclick="event.stopPropagation();deleteService('${s.id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function addEndpoint() {
    const name = document.getElementById('epName').value;
    const path = document.getElementById('epPath').value;
    const method = document.getElementById('epMethod').value;
    const dataSource = document.getElementById('epDataSource').value;
    const expectedStatus = parseInt(document.getElementById('epExpectedStatus').value) || 200;

    if (!name || !path) {
        showAlert('Please fill in endpoint name and path', 'error');
        return;
    }

    currentEndpoints.push({
        name, path, method, data_source: dataSource,
        expected_status_code: expectedStatus,
        headers: [], query_params: {}, request_body: null,
        expected_response_schema: null, description: ''
    });

    renderEndpoints();
    document.getElementById('epName').value = '';
    document.getElementById('epPath').value = '';
    document.getElementById('epExpectedStatus').value = '200';
}

function renderEndpoints() {
    const list = document.getElementById('endpointList');
    list.innerHTML = currentEndpoints.map((ep, i) => `
        <div class="endpoint-item">
            <div>
                <span class="method">${ep.method}</span>
                <strong style="margin-left:8px">${ep.name}</strong>
                <span style="color:var(--text-muted);margin-left:8px">${ep.path}</span>
                <span style="color:var(--text-muted);margin-left:8px">[${ep.data_source}]</span>
            </div>
            <button class="btn btn-sm btn-danger" onclick="removeEndpoint(${i})">Remove</button>
        </div>
    `).join('');
}

function removeEndpoint(idx) {
    currentEndpoints.splice(idx, 1);
    renderEndpoints();
}

async function saveService() {
    const name = document.getElementById('serviceName').value;
    const serviceType = document.getElementById('serviceType').value;
    const baseUrl = document.getElementById('baseUrl').value;
    const authHeader = document.getElementById('authHeader').value;
    const authToken = document.getElementById('authToken').value;

    if (!name || !baseUrl) {
        showAlert('Please fill in service name and base URL', 'error');
        return;
    }

    if (currentEndpoints.length === 0) {
        showAlert('Please add at least one endpoint', 'error');
        return;
    }

    const config = {
        name,
        service_type: serviceType,
        base_url: baseUrl,
        endpoints: currentEndpoints,
        auth_header: authHeader || null,
        auth_token: authToken || null,
        description: ''
    };

    try {
        await api('POST', '/services', config);
        showAlert(`Service "${name}" saved successfully!`, 'success');
        currentEndpoints = [];
        renderEndpoints();
        document.getElementById('serviceName').value = '';
        document.getElementById('baseUrl').value = '';
        document.getElementById('authHeader').value = '';
        document.getElementById('authToken').value = '';
        await loadServices();
    } catch (e) {
        showAlert(`Error: ${e.message}`, 'error');
    }
}

async function deleteService(id) {
    if (!confirm('Delete this service?')) return;
    try {
        await api('DELETE', `/services/${id}`);
        await loadServices();
        showAlert('Service deleted', 'success');
    } catch (e) {
        showAlert(`Error: ${e.message}`, 'error');
    }
}

// Test Generation
async function generateTests(serviceId) {
    try {
        showAlert('Generating test cases...', 'info');
        const suite = await api('POST', `/generate/${serviceId}`);
        showAlert(`Generated ${suite.test_cases.length} test cases!`, 'success');
        await loadSuites();
        // Switch to suites tab
        document.querySelector('[data-tab="tab-suites"]').click();
    } catch (e) {
        showAlert(`Error: ${e.message}`, 'error');
    }
}

// Test Suites
async function loadSuites() {
    suites = await api('GET', '/suites');
    renderSuites();
}

function renderSuites() {
    const list = document.getElementById('suiteList');
    if (suites.length === 0) {
        list.innerHTML = '<div class="empty-state">No test suites generated yet. Configure a service and generate tests.</div>';
        return;
    }
    list.innerHTML = suites.map(s => `
        <div class="service-card">
            <div>
                <strong>${s.name}</strong>
                <div style="font-size:0.85rem;color:var(--text-muted)">${s.test_cases.length} test cases &bull; ${s.service_config.service_type === 'dotnet_core' ? '.NET Core' : 'Spring Boot'}</div>
            </div>
            <div style="display:flex;gap:10px">
                <button class="btn btn-sm btn-success" onclick="executeSuite('${s.id}')">Execute</button>
                <button class="btn btn-sm btn-danger" onclick="deleteSuite('${s.id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

async function deleteSuite(id) {
    if (!confirm('Delete this test suite?')) return;
    try {
        await api('DELETE', `/suites/${id}`);
        await loadSuites();
        showAlert('Suite deleted', 'success');
    } catch (e) {
        showAlert(`Error: ${e.message}`, 'error');
    }
}

// Test Execution
async function executeSuite(suiteId) {
    try {
        showAlert('Executing tests... this may take a moment.', 'info');
        document.getElementById('executionLoading').classList.add('active');
        const report = await api('POST', `/execute/${suiteId}`);
        document.getElementById('executionLoading').classList.remove('active');
        showAlert(`Execution complete: ${report.passed} passed, ${report.failed} failed, ${report.errors} errors`, 
            report.failed === 0 && report.errors === 0 ? 'success' : 'error');
        await loadReports();
        document.querySelector('[data-tab="tab-results"]').click();
    } catch (e) {
        document.getElementById('executionLoading').classList.remove('active');
        showAlert(`Execution error: ${e.message}`, 'error');
    }
}

// Reports
async function loadReports() {
    reports = await api('GET', '/reports');
    renderReports();
}

function renderReports() {
    const container = document.getElementById('reportResults');
    if (reports.length === 0) {
        container.innerHTML = '<div class="empty-state">No test results yet. Execute a test suite first.</div>';
        return;
    }

    const latest = reports[0];
    container.innerHTML = `
        <h3 style="margin-bottom:16px">${latest.suite_name}</h3>
        <div class="result-summary">
            <div class="stat-card stat-passed">
                <div class="value">${latest.passed}</div>
                <div class="label">Passed</div>
            </div>
            <div class="stat-card stat-failed">
                <div class="value">${latest.failed}</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card stat-error">
                <div class="value">${latest.errors}</div>
                <div class="label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="value">${latest.total_duration_ms.toFixed(0)}ms</div>
                <div class="label">Total Time</div>
            </div>
        </div>
        <div>
            ${latest.results.map(r => `
                <div class="result-row">
                    <div class="status-icon status-${r.status}">${r.status === 'passed' ? '✓' : r.status === 'failed' ? '✗' : '!'}</div>
                    <div class="test-info">
                        <div class="test-name">${r.test_name}</div>
                        <div class="test-detail">${r.error_message || `Status: ${r.response_status_code}`}</div>
                    </div>
                    <div class="response-time">${r.response_time_ms.toFixed(0)}ms</div>
                </div>
            `).join('')}
        </div>
        ${reports.length > 1 ? `<h3 style="margin-top:30px;margin-bottom:16px">Previous Reports</h3>` +
            reports.slice(1).map(r => `
                <div class="service-card" style="cursor:default">
                    <div>
                        <strong>${r.suite_name}</strong>
                        <div style="font-size:0.85rem;color:var(--text-muted)">
                            ${r.passed} passed, ${r.failed} failed, ${r.errors} errors &bull; ${r.total_duration_ms.toFixed(0)}ms
                        </div>
                    </div>
                    <div style="font-size:0.8rem;color:var(--text-muted)">${new Date(r.executed_at).toLocaleString()}</div>
                </div>
            `).join('') : ''}
    `;
}

// Utility
function showAlert(msg, type) {
    const el = document.getElementById('alertArea');
    el.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
    setTimeout(() => { el.innerHTML = ''; }, 5000);
}

// Init
document.addEventListener('DOMContentLoaded', async () => {
    await loadServices();
    await loadSuites();
    await loadReports();
});
