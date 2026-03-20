(function () {
    const stageOrder = ['DOC_COLLECTION', 'IT_PROVISIONING', 'POLICY_SIGNOFF', 'MANAGER_INTRO'];
    const stageTitles = {
        DOC_COLLECTION: 'Document Collection',
        IT_PROVISIONING: 'IT Provisioning',
        POLICY_SIGNOFF: 'Policy Sign-off',
        MANAGER_INTRO: 'Manager Intro',
    };

    const isIndex = () => window.location.pathname.endsWith('/') || window.location.pathname.endsWith('index.html');
    const isEmployee = () => window.location.pathname.endsWith('employee-dashboard.html');
    const isHr = () => window.location.pathname.endsWith('hr-dashboard.html');

    const cfg = {
        apiBase: '',
        cognitoDomain: '',
        cognitoClientId: '',
    };

    const parseJwt = (token) => {
        try {
            const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
            return JSON.parse(atob(part));
        } catch (_e) {
            return {};
        }
    };

    const authTokens = () => ({
        idToken: localStorage.getItem('HRMS_ID_TOKEN') || '',
        accessToken: localStorage.getItem('HRMS_ACCESS_TOKEN') || '',
    });

    const authHeader = () => {
        const { accessToken, idToken } = authTokens();
        const token = accessToken || idToken;
        return token ? { Authorization: `Bearer ${token}` } : {};
    };

    const fetchJson = async (url, opts = {}) => {
        const res = await fetch(url, opts);
        if (!res.ok) {
            const txt = await res.text();
            throw new Error(`HTTP ${res.status}: ${txt}`);
        }
        return res.json();
    };

    const loadConfig = async () => {
        try {
            const fileCfg = await fetchJson('./config.json');
            cfg.apiBase = (fileCfg.apiBaseUrl || '').trim().replace(/\/+$/, '');
            cfg.cognitoDomain = fileCfg.cognitoDomain || '';
            cfg.cognitoClientId = fileCfg.cognitoClientId || '';
        } catch (_e) {
            // fallback to localStorage
        }

        if (!cfg.apiBase) cfg.apiBase = (localStorage.getItem('HRMS_API_BASE_URL') || '').trim().replace(/\/+$/, '');
        if (!cfg.cognitoDomain) cfg.cognitoDomain = localStorage.getItem('HRMS_COGNITO_DOMAIN') || '';
        if (!cfg.cognitoClientId) cfg.cognitoClientId = localStorage.getItem('HRMS_COGNITO_CLIENT_ID') || '';
    };

    const setTokensAndRoute = (payload) => {
        localStorage.setItem('HRMS_ID_TOKEN', payload.id_token || '');
        localStorage.setItem('HRMS_ACCESS_TOKEN', payload.access_token || '');
        const claims = parseJwt(payload.id_token || '');
        const groups = claims['cognito:groups'] || [];
        const employeeId = claims['custom:employee_id'] || '';
        if (employeeId) localStorage.setItem('HRMS_EMPLOYEE_ID', employeeId);

        if (groups.includes('HR')) {
            window.location.href = 'hr-dashboard.html';
        } else {
            window.location.href = employeeId ? `employee-dashboard.html?employee_id=${encodeURIComponent(employeeId)}` : 'employee-dashboard.html';
        }
    };

    const enforceAuth = () => {
        if (isIndex()) return true;
        const { idToken, accessToken } = authTokens();
        if (!idToken && !accessToken) {
            window.location.href = 'index.html';
            return false;
        }
        return true;
    };

    const enforceRoleGuards = () => {
        const groups = parseJwt(localStorage.getItem('HRMS_ID_TOKEN') || '')['cognito:groups'] || [];
        if (isHr() && !groups.includes('HR')) {
            window.location.href = 'employee-dashboard.html';
            return false;
        }
        if (isEmployee() && groups.includes('HR')) {
            window.location.href = 'hr-dashboard.html';
            return false;
        }
        return true;
    };

    const logout = () => {
        localStorage.removeItem('HRMS_ID_TOKEN');
        localStorage.removeItem('HRMS_ACCESS_TOKEN');
        localStorage.removeItem('HRMS_EMPLOYEE_ID');
        window.location.href = 'index.html';
    };

    const fetchProgress = async (employeeId) => fetchJson(`${cfg.apiBase}/onboarding/${employeeId}/progress`, { headers: authHeader() });
    const fetchEmployees = async () => fetchJson(`${cfg.apiBase}/employees`, { headers: authHeader() });
    const createEmployee = async (payload) => fetchJson(`${cfg.apiBase}/employees`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeader() }, body: JSON.stringify(payload)
    });
    const completeStage = async (employeeId, stage) => fetchJson(`${cfg.apiBase}/onboarding/${employeeId}/stage-complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify({ stage })
    });

    const getUploadUrl = async (employeeId, docType, file) => {
        const qs = new URLSearchParams({ employee_id: employeeId, doc_type: docType, file_name: file.name, content_type: file.type });
        return fetchJson(`${cfg.apiBase}/upload-url?${qs.toString()}`, { headers: authHeader() });
    };

    const uploadFile = async (url, file) => {
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': file.type, 'x-amz-server-side-encryption': 'AES256' },
            body: file
        });
        if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    };

    const renderEmployeeProgress = (payload) => {
        if (!payload || !Array.isArray(payload.stages)) return;
        const bar = document.querySelector('.progress-fill.gradient-accent');
        const label = document.querySelector('.progress-label');
        const container = document.querySelector('.stages-grid');
        if (!bar || !label || !container) return;

        const statusByStage = {};
        payload.stages.forEach((s) => { statusByStage[s.stage_name] = s.status; });

        const completed = stageOrder.filter((s) => statusByStage[s] === 'COMPLETE').length;
        const pct = Math.round((completed / stageOrder.length) * 100);
        bar.style.width = `${pct}%`;
        label.textContent = `${pct}% Completed`;

        container.innerHTML = '';
        stageOrder.forEach((stage) => {
            const status = statusByStage[stage] || 'PENDING';
            const css = status === 'COMPLETE' ? 'complete' : (status === 'IN_PROGRESS' ? 'in-progress' : 'pending');
            const icon = status === 'COMPLETE' ? 'OK' : (status === 'IN_PROGRESS' ? 'IN' : 'PD');
            const badge = status === 'COMPLETE' ? 'Completed' : (status === 'IN_PROGRESS' ? 'In Progress' : 'Pending');
            container.insertAdjacentHTML('beforeend', `<div class="stage-card ${css}"><div class="stage-icon">${icon}</div><div class="stage-info"><h3>${stageTitles[stage]}</h3><p>${stage}</p></div><span class="badge badge-${css}">${badge}</span></div>`);
        });
    };

    const renderPipeline = (payload) => {
        const list = document.getElementById('pipeline-list');
        const activeEl = document.getElementById('hr-active-count');
        const completeEl = document.getElementById('hr-completed-count');
        if (!list || !payload || !Array.isArray(payload.employees)) return;

        let active = 0;
        let complete = 0;
        list.innerHTML = '';

        payload.employees.forEach((emp) => {
            const done = Math.max(0, Math.min(4, emp.completed_stages || 0));
            const pct = Math.round((done / 4) * 100);
            const isComplete = emp.status === 'DAY1_READY';
            if (isComplete) complete += 1; else active += 1;
            const statusClass = isComplete ? 'badge-complete' : (emp.active_stage === 'PENDING' ? 'badge-pending' : 'badge-in-progress');
            const statusText = isComplete ? 'Ready' : (emp.active_stage || 'PENDING');
            const initials = (emp.full_name || 'NA').slice(0, 2).toUpperCase();
            const canComplete = !isComplete && stageOrder.includes(emp.active_stage || '');
            const actionHtml = canComplete
                ? `<button class="btn-outline small hr-complete-stage-btn" data-employee-id="${emp.employee_id}" data-stage="${emp.active_stage}">Complete ${stageTitles[emp.active_stage] || emp.active_stage}</button>`
                : '';
            list.insertAdjacentHTML('beforeend', `<div class="pipeline-item reveal"><div class="emp-details"><div class="avatar">${initials}</div><div><h4>${emp.full_name || emp.email || emp.employee_id}</h4><span>${emp.department || 'NA'} | ID: ${emp.employee_id}</span></div></div><div class="hr-progress"><div class="hero-progress-bar compact"><div class="progress-fill in-progress-bg" style="width: ${pct}%"></div></div><span class="step-label">${done}/4 Completed</span></div><div class="status-col"><span class="badge ${statusClass}">${statusText}</span>${actionHtml}</div></div>`);
        });

        if (activeEl) activeEl.textContent = String(active);
        if (completeEl) completeEl.textContent = String(complete);
    };

    document.addEventListener('DOMContentLoaded', async () => {
        await loadConfig();

        const loginForm = document.getElementById('login-form');
        const statusEl = document.getElementById('login-status');
        const newPwdGroup = document.getElementById('new-password-group');
        const confirmPwdGroup = document.getElementById('confirm-password-group');

        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                try {
                    if (!cfg.apiBase) throw new Error('HRMS_API_BASE_URL not configured in config.json');

                    const email = document.getElementById('email').value.trim();
                    const password = document.getElementById('password').value;
                    const newPassword = document.getElementById('new_password').value;
                    const confirmNewPassword = (document.getElementById('confirm_new_password') || {}).value || '';
                    const challengeSession = sessionStorage.getItem('HRMS_CHALLENGE_SESSION') || '';

                    if (challengeSession && newPassword) {
                        if (!confirmNewPassword) {
                            if (statusEl) statusEl.textContent = 'Please re-enter new password.';
                            return;
                        }
                        if (newPassword !== confirmNewPassword) {
                            if (statusEl) statusEl.textContent = 'New password and confirm password do not match.';
                            return;
                        }
                        const resp = await fetchJson(`${cfg.apiBase}/auth/complete-new-password`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email, new_password: newPassword, session: challengeSession })
                        });
                        sessionStorage.removeItem('HRMS_CHALLENGE_SESSION');
                        setTokensAndRoute(resp);
                        return;
                    }

                    const resp = await fetchJson(`${cfg.apiBase}/auth/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });

                    if (resp.challenge === 'NEW_PASSWORD_REQUIRED') {
                        sessionStorage.setItem('HRMS_CHALLENGE_SESSION', resp.session || '');
                        if (statusEl) statusEl.textContent = 'First login: set your new password and confirm it.';
                        if (newPwdGroup) newPwdGroup.style.display = 'block';
                        if (confirmPwdGroup) confirmPwdGroup.style.display = 'block';
                        return;
                    }

                    setTokensAndRoute(resp);
                } catch (err) {
                    if (statusEl) statusEl.textContent = `Login failed: ${err.message}`;
                }
            });
        }

        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) logoutBtn.addEventListener('click', logout);

        if (!enforceAuth()) return;
        if (!enforceRoleGuards()) return;

        if (isEmployee()) {
            const params = new URLSearchParams(window.location.search);
            const employeeId = params.get('employee_id') || localStorage.getItem('HRMS_EMPLOYEE_ID') || '';
            if (employeeId) {
                try { renderEmployeeProgress(await fetchProgress(employeeId)); } catch (_e) {}
            }

            const docForm = document.getElementById('employee-doc-form');
            const docStatus = document.getElementById('employee-doc-status');
            if (docForm) {
                docForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const empId = employeeId || localStorage.getItem('HRMS_EMPLOYEE_ID') || '';
                    if (!empId) {
                        if (docStatus) docStatus.textContent = 'Employee ID missing. Please login again.';
                        return;
                    }
                    const files = [
                        { type: 'ID_PROOF', file: document.getElementById('doc_id_proof').files[0] },
                        { type: 'DEGREE_CERT', file: document.getElementById('doc_degree_cert').files[0] },
                        { type: 'OFFER_LETTER', file: document.getElementById('doc_offer_letter').files[0] },
                    ];
                    try {
                        for (const f of files) {
                            if (!f.file) throw new Error(`Missing ${f.type}`);
                            const u = await getUploadUrl(empId, f.type, f.file);
                            await uploadFile(u.upload_url, f.file);
                        }
                        if (docStatus) docStatus.textContent = 'Documents uploaded successfully.';
                        renderEmployeeProgress(await fetchProgress(empId));
                    } catch (err) {
                        if (docStatus) docStatus.textContent = `Upload failed: ${err.message}`;
                    }
                });
            }
        }

        if (isHr()) {
            const toggleBtn = document.getElementById('toggle-create-employee');
            const createForm = document.getElementById('create-employee-form');
            const status = document.getElementById('create-employee-status');

            if (toggleBtn && createForm) {
                toggleBtn.addEventListener('click', () => {
                    createForm.style.display = createForm.style.display === 'none' ? 'block' : 'none';
                });
            }

            if (createForm) {
                createForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const payload = {
                        full_name: document.getElementById('emp_full_name').value.trim(),
                        email: document.getElementById('emp_email').value.trim(),
                        department: document.getElementById('emp_department').value.trim(),
                        role: document.getElementById('emp_role').value.trim(),
                        manager_id: document.getElementById('emp_manager_id').value.trim(),
                        joining_date: document.getElementById('emp_joining_date').value,
                        employment_type: document.getElementById('emp_employment_type').value,
                    };
                    try {
                        const resp = await createEmployee(payload);
                        if (status) status.textContent = `Employee created: ${resp.employee_id}`;
                        createForm.reset();
                        renderPipeline(await fetchEmployees());
                    } catch (err) {
                        if (status) status.textContent = `Failed: ${err.message}`;
                    }
                });
            }

            const pipeline = document.getElementById('pipeline-list');
            if (pipeline) {
                pipeline.addEventListener('click', async (e) => {
                    const btn = e.target.closest('.hr-complete-stage-btn');
                    if (!btn) return;
                    const employeeId = btn.getAttribute('data-employee-id') || '';
                    const stage = btn.getAttribute('data-stage') || '';
                    if (!employeeId || !stage) return;
                    const oldText = btn.textContent;
                    btn.disabled = true;
                    btn.textContent = 'Updating...';
                    try {
                        await completeStage(employeeId, stage);
                        renderPipeline(await fetchEmployees());
                    } catch (err) {
                        btn.disabled = false;
                        btn.textContent = oldText;
                        if (status) status.textContent = `Stage update failed: ${err.message}`;
                    }
                });
            }

            try { renderPipeline(await fetchEmployees()); } catch (_e) {}
        }
    });
})();
