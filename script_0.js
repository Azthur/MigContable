
        const companyId = window.location.pathname.split('/').pop();

        // Load initial data
        window.addEventListener('DOMContentLoaded', async () => {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('etlStart').value = today;
            document.getElementById('etlEnd').value = today;

            await loadCompanyInfo();
            await loadSourceConnection();
            await loadDestConnection();
            await loadFinalDestConnection();
        });

        async function loadCompanyInfo() {
            try {
                const res = await fetch(`/api/v1/companies/${companyId}`);
                if (!res.ok) throw new Error("Error cargando empresa");
                const data = await res.json();
                document.getElementById('companyHeaderName').textContent = data.name;
                document.getElementById('crumbCompanyName').textContent = data.name;
                document.getElementById('companyStatusBadge').textContent = data.is_active ? 'Activo' : 'Inactivo';
                document.getElementById('companyStatusBadge').className = data.is_active ? 'badge-success' : 'badge-error';
            } catch (e) {
                showToast('error', "No se pudo cargar la información de la empresa");
            }
        }

        // ─── SOURCE CONNECTION ───
        async function loadSourceConnection() {
            try {
                const res = await fetch(`/ api / v1 / companies / ${companyId}/source-connection`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('srcHost').value = data.host;
                    document.getElementById('srcPort').value = data.port;
                    document.getElementById('srcDb').value = data.database_name;
                    document.getElementById('srcUser').value = data.username;
                    if (data.driver) {
                        document.getElementById('srcDriver').value = data.driver;
                    }
                }
            } catch (e) { console.log("No source config found yet"); }
        }

        async function saveSourceConnection() {
            const body = {
                host: document.getElementById('srcHost').value,
                port: document.getElementById('srcPort').value,
                database_name: document.getElementById('srcDb').value,
                username: document.getElementById('srcUser').value,
                password: document.getElementById('srcPass').value,
                driver: document.getElementById('srcDriver').value,
                db_type: 'MSSQL'
            };

            if (!body.host || !body.database_name || !body.username || !body.password) {
                showToast('warning', "Todos los campos son obligatorios (incluyendo contraseña para guardar)");
                return;
            }

            try {
                const res = await fetch(`/api/v1/companies/${companyId}/source-connection`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
                });
                if (res.ok) {
                    showToast('success', "Conexión guardada correctamente");
                    document.getElementById('srcPass').value = '';
                } else {
                    showToast('error', "Error al guardar conexión");
                }
            } catch (e) { showToast('error', "Error de red"); }
        }

        async function testSourceConnection() {
            const resDiv = document.getElementById('srcTestResult');
            resDiv.innerHTML = '<div class="spinner-sm"></div> Probando...';
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/test-source`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'OK') {
                    resDiv.innerHTML = `<span class="text-success"><i class="bi bi-check-circle me-1"></i> Conexión Exitosa (${data.server_version})</span>`;
                } else {
                    resDiv.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle me-1"></i> Error: ${data.message}</span>`;
                }
            } catch (e) {
                resDiv.innerHTML = `<span class="text-danger">Error de red</span>`;
            }
        }

        // ─── TABLES ───
        async function loadTables() {
            const container = document.getElementById('tablesContainer');
            container.innerHTML = '<div class="text-center py-4"><div class="spinner-sm"></div> Cargando tablas...</div>';
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/tables`);
                if (!res.ok) {
                    const errData = await res.json();
                    throw new Error(errData.detail || "Error cargando tablas. Verifique la conexión origen.");
                }
                const tables = await res.json();
                if (tables.length === 0) {
                    container.innerHTML = '<div class="alert alert-warning-dark">No se encontraron tablas o la base de datos está vacía.</div>';
                    return;
                }
                container.innerHTML = `
                <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                    <table class="table-dark-custom">
                        <thead style="position: sticky; top: 0; background: var(--bg-card); z-index: 10;">
                            <tr>
                                <th width="40" title="Arrastrar para ordenar"><i class="bi bi-arrows-expand"></i></th>
                                <th width="40"><input type="checkbox" id="selectAllTables" onclick="toggleAllTables()"></th>
                                <th>Esquema</th>
                                <th>Tabla</th>
                                <th>Tipo</th>
                                <th>Columnas</th>
                                <th width="100">Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tables.map((t, index) => `
                                <tr class="table-row-sortable">
                                    <td class="drag-handle text-muted" style="cursor: grab;"><i class="bi bi-grip-vertical"></i></td>
                                    <td><input type="checkbox" class="table-checkbox" data-schema="${t.table_schema}" data-name="${t.table_name}" ${t.is_selected ? 'checked' : ''} data-order="${t.extraction_order !== undefined ? t.extraction_order : index}"></td>
                                    <td>${t.table_schema}</td>
                                    <td><strong>${t.table_name}</strong></td>
                                    <td>${t.table_type}</td>
                                    <td>${t.column_count}</td>
                                    <td>
                                        <button class="btn-ghost btn-sm" 
                                            onclick="openTableConfig(${t.selection_id}, '${t.table_schema}', '${t.table_name}', '${t.control_column || ''}', '${t.control_column_type || ''}')"
                                            title="Configurar Filtros e Incremental"
                                            ${t.is_selected && t.selection_id ? '' : 'disabled'}>
                                            <i class="bi bi-gear"></i>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="mt-2 text-muted small">Total tablas encontradas: ${tables.length} <span class="ms-3"><i class="bi bi-info-circle"></i> Arrastre las filas para cambiar el orden de extracción.</span></div>
            `;

                // Inicializar Sortable.js
                const tbody = container.querySelector('tbody');
                if (tbody) {
                    new Sortable(tbody, {
                        handle: '.drag-handle',
                        animation: 150,
                        ghostClass: 'sortable-ghost',
                        onEnd: function (evt) {
                            // Actualizar el dataset order en los checkboxes despues de reordenar
                            const rows = tbody.querySelectorAll('tr');
                            rows.forEach((row, index) => {
                                const cb = row.querySelector('.table-checkbox');
                                if (cb) cb.dataset.order = index;
                            });
                        }
                    });
                }
            } catch (e) {
                container.innerHTML = `<div class="alert alert-error-dark">
                <i class="bi bi-exclamation-triangle me-2"></i>
                No se pudieron cargar las tablas. Asegúrese de guardar y probar la Conexión Origen primero.
                <br><small class="mt-2 d-block text-muted">${e.message}</small>
            </div>`;
            }
        }

        function toggleAllTables() {
            const checked = document.getElementById('selectAllTables').checked;
            document.querySelectorAll('.table-checkbox').forEach(cb => cb.checked = checked);
        }

        async function saveTableSelection() {
            const checkboxes = document.querySelectorAll('.table-checkbox');
            const selections = Array.from(checkboxes).map(cb => ({
                table_schema: cb.dataset.schema,
                table_name: cb.dataset.name,
                is_selected: cb.checked,
                extraction_order: parseInt(cb.dataset.order) || 0
            }));
            const msgDiv = document.getElementById('tablesMsg');
            msgDiv.innerHTML = '<span class="spinner-sm"></span> Guardando...';
            try {
                const connRes = await fetch(`/api/v1/companies/${companyId}/source-connection`);
                const connData = await connRes.json();
                const res = await fetch(`/api/v1/companies/${companyId}/table-selections`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_connection_id: connData.id, selections: selections })
                });
                if (res.ok) {
                    msgDiv.innerHTML = '<span class="text-success"><i class="bi bi-check-lg"></i> Guardado exitosamente</span>';
                    setTimeout(() => msgDiv.innerHTML = '', 3000);
                } else { throw new Error("Error al guardar"); }
            } catch (e) {
                msgDiv.innerHTML = '<span class="text-danger">Error al guardar selección</span>';
            }
        }

        // ─── DEST CONNECTION (BD Intermedia) ───
        async function loadDestConnection() {
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/dest-connection`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('destHost').value = data.host;
                    document.getElementById('destPort').value = data.port;
                    document.getElementById('destDb').value = data.database_name;
                    document.getElementById('destUser').value = data.username;
                }
            } catch (e) { }
        }

        async function saveDestConnection() {
            const body = {
                host: document.getElementById('destHost').value,
                port: document.getElementById('destPort').value,
                database_name: document.getElementById('destDb').value,
                username: document.getElementById('destUser').value,
                password: document.getElementById('destPass').value
            };
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/dest-connection`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
                });
                if (res.ok) {
                    showToast('success', "Conexión BD Intermedia guardada");
                    document.getElementById('destPass').value = '';
                } else { showToast('error', "Error al guardar conexión"); }
            } catch (e) { showToast('error', "Error de red"); }
        }

        async function testDestConnection() {
            const resDiv = document.getElementById('destTestResult');
            resDiv.innerHTML = '<div class="spinner-sm"></div> Probando...';
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/test-dest`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'OK') {
                    resDiv.innerHTML = `<span class="text-success"><i class="bi bi-check-circle me-1"></i> Conexión Exitosa (${data.server_version})</span>`;
                } else {
                    resDiv.innerHTML = `<span class="text-danger">Error: ${data.message}</span>`;
                }
            } catch (e) {
                resDiv.innerHTML = `<span class="text-danger">Error de red</span>`;
            }
        }

        // ─── FINAL DESTINATION (Contabilidad) ───
        async function loadFinalDestConnection() {
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/final-dest-connection`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('finalDestHost').value = data.host;
                    document.getElementById('finalDestPort').value = data.port;
                    document.getElementById('finalDestDb').value = data.database_name;
                    document.getElementById('finalDestUser').value = data.username;
                }
            } catch (e) { console.log("No final dest config found yet"); }
        }

        function parseApiError(errData) {
            // Handles both string detail and Pydantic array detail
            if (!errData) return "Error desconocido";
            if (typeof errData.detail === 'string') return errData.detail;
            if (Array.isArray(errData.detail)) {
                return errData.detail.map(e => `${e.loc ? e.loc.join('.') + ': ' : ''}${e.msg}`).join('; ');
            }
            return JSON.stringify(errData);
        }

        async function saveFinalDestConnection() {
            const host = document.getElementById('finalDestHost').value.trim();
            const port = parseInt(document.getElementById('finalDestPort').value);
            const db = document.getElementById('finalDestDb').value.trim();
            const user = document.getElementById('finalDestUser').value.trim();
            const pass = document.getElementById('finalDestPass').value;

            if (!host || !db || !user || !pass) {
                showToast('warning', "Todos los campos son obligatorios, incluyendo la contraseña.");
                return;
            }

            const body = {
                host: host,
                port: port,
                database_name: db,
                username: user,
                password: pass,
                db_type: 'POSTGRESQL'
            };

            try {
                const res = await fetch(`/api/v1/companies/${companyId}/final-dest-connection`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
                });
                const data = await res.json();
                if (res.ok) {
                    showToast('success', "Conexión destino contabilidad guardada correctamente");
                    document.getElementById('finalDestPass').value = '';
                } else {
                    showToast('error', "❌ Error al guardar: " + parseApiError(data));
                }
            } catch (e) { showToast('error', "Error de red: " + e.message); }
        }

        async function testFinalDestConnection() {
            const resDiv = document.getElementById('finalDestTestResult');
            resDiv.innerHTML = '<div class="spinner-sm"></div> Probando conexión a contabilidad...';
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/test-final-dest`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'OK') {
                    resDiv.innerHTML = `<span class="text-success"><i class="bi bi-check-circle me-1"></i> Conexión Exitosa — ${data.server_version}</span>`;
                } else {
                    resDiv.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle me-1"></i> Error: ${data.message || parseApiError(data)}</span>`;
                }
            } catch (e) {
                resDiv.innerHTML = `<span class="text-danger">Error de red: ${e.message}</span>`;
            }
        }

        async function loadFinalDestTables() {
            const container = document.getElementById('finalTablesContainer');
            container.innerHTML = '<div class="text-center py-4"><div class="spinner-sm"></div> Cargando tablas de contabilidad...</div>';
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/final-dest-tables`);
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Error cargando tablas");
                }
                const tables = await res.json();
                if (tables.length === 0) {
                    container.innerHTML = '<div class="alert alert-warning-dark">No se encontraron tablas en la base de datos destino.</div>';
                    return;
                }
                container.innerHTML = `
                <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                    <table class="table-dark-custom">
                        <thead style="position: sticky; top: 0; background: var(--bg-card); z-index: 10;">
                            <tr>
                                <th width="40"><input type="checkbox" id="selectAllFinalTables" onclick="toggleAllFinalTables()"></th>
                                <th>Esquema</th>
                                <th>Tabla</th>
                                <th>Tipo</th>
                                <th>Columnas</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tables.map(t => `
                                <tr class="table-row-clickable">
                                    <td>
                                        <input type="checkbox" class="final-table-checkbox"
                                            data-schema="${t.table_schema}"
                                            data-name="${t.table_name}"
                                            ${t.is_selected ? 'checked' : ''}>
                                    </td>
                                    <td>${t.table_schema}</td>
                                    <td><strong>${t.table_name}</strong></td>
                                    <td>${t.table_type}</td>
                                    <td>${t.column_count}</td>
                                    <td>
                                        <button class="btn-ghost btn-sm" onclick="viewFinalTableColumns('${t.table_schema}', '${t.table_name}')" title="Ver columnas">
                                            <i class="bi bi-eye"></i>
                                        </button>
                                        <button class="btn-ghost btn-sm text-primary" onclick="cloneFinalTable('${t.table_schema}', '${t.table_name}')" title="Clonar Estructura (DROP + CREATE)"> 
                                            <i class="bi bi-copy"></i>
                                        </button>
                                        <button class="btn-ghost btn-sm text-warning" onclick="syncFinalTableColumns('${t.table_schema}', '${t.table_name}')" title="Sincronizar Columnas Nuevas (sin perder datos)">
                                            <i class="bi bi-arrow-repeat"></i>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="mt-2 text-muted small">Total tablas encontradas: ${tables.length}</div>
            `;
            } catch (e) {
                container.innerHTML = `<div class="alert alert-error-dark">
                <i class="bi bi-exclamation-triangle me-2"></i>
                No se pudieron cargar las tablas. Guarde y pruebe primero la conexión destino.
                <br><small class="mt-2 d-block text-muted">${e.message}</small>
            </div>`;
            }
        }

        function toggleAllFinalTables() {
            const checked = document.getElementById('selectAllFinalTables').checked;
            document.querySelectorAll('.final-table-checkbox').forEach(cb => cb.checked = checked);
        }

        async function saveFinalTableSelection() {
            const checkboxes = document.querySelectorAll('.final-table-checkbox');
            if (checkboxes.length === 0) {
                showToast('warning', "Cargue primero las tablas antes de guardar.");
                return;
            }
            const selections = Array.from(checkboxes).map(cb => ({
                table_schema: cb.dataset.schema,
                table_name: cb.dataset.name,
                is_selected: cb.checked
            }));
            const msgDiv = document.getElementById('finalTablesMsg');
            msgDiv.innerHTML = '<span class="spinner-sm"></span> Guardando...';
            try {
                const connRes = await fetch(`/api/v1/companies/${companyId}/final-dest-connection`);
                const connData = await connRes.json();
                const res = await fetch(`/api/v1/companies/${companyId}/final-table-selections`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ final_dest_connection_id: connData.id, selections: selections })
                });
                if (res.ok) {
                    msgDiv.innerHTML = '<span class="text-success"><i class="bi bi-check-lg"></i> Tablas destino guardadas</span>';
                    setTimeout(() => msgDiv.innerHTML = '', 3000);
                } else { throw new Error("Error al guardar"); }
            } catch (e) {
                msgDiv.innerHTML = '<span class="text-danger">Error al guardar selección de tablas</span>';
            }
        }

        async function cloneFinalTable(schema, tableName) {
            const { isConfirmed } = await Swal.fire({
                title: 'Clonar Estructura',
                html: `<p style="color:#8b949e;">Se clonará la estructura de la tabla <strong style="color:#58a6ff;">${tableName}</strong> a la Base de Datos Intermedia.</p>
                       <p style="color:#f85149; font-size:13px;"><i class="bi bi-exclamation-triangle me-1"></i>Esto reemplazará la tabla si ya existe (se perderán datos previos).</p>`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: '<i class="bi bi-copy me-1"></i> Sí, Clonar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#1f6feb',
                cancelButtonColor: '#30363d',
                background: '#161b22',
                color: '#e6edf3',
            });
            if (!isConfirmed) return;

            showToast('info', `Clonando tabla ${tableName}...`);
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/clone-final-table`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ table_schema: schema, table_name: tableName })
                });
                const data = await res.json();
                if (res.ok) {
                    showToast('success', `${data.message}`);
                } else {
                    showToast('error', `Error al clonar: ${data.detail || 'Error desconocido'}`);
                }
            } catch (e) {
                showToast('error', `Error de red: ${e.message}`);
            }
        }

        async function syncFinalTableColumns(schema, tableName) {
            const { isConfirmed } = await Swal.fire({
                title: 'Sincronizar Columnas',
                html: `<p style="color:#8b949e;">Se verificarán columnas nuevas en <strong style="color:#58a6ff;">${tableName}</strong> desde el destino final.</p>
                       <p style="color:#3fb950; font-size:13px;"><i class="bi bi-shield-check me-1"></i>Solo se agregarán columnas faltantes. Los datos existentes NO se perderán.</p>`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: '<i class="bi bi-arrow-repeat me-1"></i> Sincronizar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#d29922',
                cancelButtonColor: '#30363d',
                background: '#161b22',
                color: '#e6edf3',
            });
            if (!isConfirmed) return;

            showToast('info', `Sincronizando columnas de ${tableName}...`);
            try {
                const res = await fetch(`/api/v1/companies/${companyId}/sync-final-table-columns`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ table_schema: schema, table_name: tableName })
                });
                const data = await res.json();
                if (res.ok) {
                    if (data.total_new > 0) {
                        showToast('success', `${data.message} Columnas: ${data.added_columns.join(', ')}`);
                    } else {
                        showToast('info', `${data.message}`);
                    }
                } else {
                    showToast('error', `Error al sincronizar: ${data.detail || 'Error desconocido'}`);
                }
            } catch (e) {
                showToast('error', `Error de red: ${e.message}`);
            }
        }

        async function viewFinalTableColumns(schema, tableName) {
            const panel = document.getElementById('finalColumnsPanel');
            const container = document.getElementById('finalColumnsContainer');
            const nameSpan = document.getElementById('finalColumnsTableName');

            panel.style.display = 'block';
            nameSpan.textContent = `${schema}.${tableName}`;
            container.innerHTML = '<div class="text-center py-3"><div class="spinner-sm"></div> Cargando columnas...</div>';

            try {
                const res = await fetch(`/api/v1/companies/${companyId}/final-dest-table-columns?table_schema=${schema}&table_name=${tableName}`);
                if (!res.ok) throw new Error("Error cargando columnas");
                const columns = await res.json();

                container.innerHTML = `
                <div class="table-responsive">
                    <table class="table-dark-custom">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Columna</th>
                                <th>Tipo de Dato</th>
                                <th>Nullable</th>
                                <th>Longitud Máx.</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${columns.map((c, idx) => `
                                <tr>
                                    <td>${idx + 1}</td>
                                    <td><strong>${c.column_name}</strong></td>
                                    <td><code>${c.data_type}</code></td>
                                    <td>${c.is_nullable === 'YES' ? '<span class="text-warning">Sí</span>' : '<span class="text-muted">No</span>'}</td>
                                    <td>${c.max_length || '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

                // Scroll into view
                panel.scrollIntoView({ behavior: 'smooth' });
            } catch (e) {
                container.innerHTML = `<div class="alert alert-error-dark">Error: ${e.message}</div>`;
            }
        }

        // ─── ETL ───────────────────────────────────────────────────────────────────

        // Inicializar período/mes con fecha actual (Eliminado)

        // Cargar subcategorías del mapeo en el dropdown del Paso 2
        async function loadEtlSubcategories() {
            const subcatSel = document.getElementById('genSubcatSelect');
            if (!subcatSel) return;
            try {
                const res = await fetch(`/api/v1/mapeo/categorias?company_id=${companyId}`);
                if (!res.ok) return;
                const cats = await res.json();
                subcatSel.innerHTML = '<option value="">-- Todas las subcategorías --</option>';
                step2SubcatTableMap = {};
                cats.forEach(cat => {
                    (cat.subcategorias || []).forEach(sub => {
                        if (!sub.is_active) return;
                        const opt = document.createElement('option');
                        opt.value = sub.id;
                        opt.textContent = `[${cat.nombre}] ${sub.nombre}${sub.tabla_origen ? ' (' + sub.tabla_origen + ')' : ''}`;
                        subcatSel.appendChild(opt);
                        if (sub.tabla_origen) step2SubcatTableMap[String(sub.id)] = sub.tabla_origen;
                    });
                });
            } catch (e) {
                console.error('Error cargando subcategorías ETL:', e);
            }
        }
        loadEtlSubcategories();

        // Funciones de ETL Periodo eliminadas

        function setStepLoading(btnId, resultId, msg) {
            const btn = document.getElementById(btnId);
            if (btn) { btn.disabled = true; btn.innerHTML = `<span class="spinner-sm"></span> ${msg}`; }
            const res = document.getElementById(resultId);
            if (res) res.innerHTML = `<div class="alert alert-info-dark mt-2"><div class="spinner-sm"></div> ${msg}</div>`;
        }

        function setStepResult(btnId, originalHtml, resultId, success, msg) {
            const btn = document.getElementById(btnId);
            if (btn) { btn.disabled = false; btn.innerHTML = originalHtml; }
            const res = document.getElementById(resultId);
            if (res) res.innerHTML = success
                ? `<div class="alert alert-success-dark mt-2"><i class="bi bi-check-circle me-1"></i>${msg}</div>`
                : `<div class="alert alert-error-dark mt-2"><i class="bi bi-x-circle me-1"></i>${msg}</div>`;
        }

        async function runEtlStep1() {
            const fullRefresh = document.getElementById('fullRefreshSwitch')?.checked;
            const origHtml = '<i class="bi bi-cloud-download me-2"></i> Extraer Datos';
            setStepLoading('btnStep1', 'step1Result', 'Extrayendo datos...');
            try {
                let url = `/api/v1/etl/run-etl/?company_id=${companyId}`;
                if (fullRefresh) url += `&full_refresh=true`;

                const res = await fetch(url, { method: 'POST' });
                const data = await res.json();
                if (res.ok) {
                    setStepResult('btnStep1', origHtml, 'step1Result', true,
                        data.message || `ETL completado: ${data.records || 0} registros`);
                } else {
                    setStepResult('btnStep1', origHtml, 'step1Result', false, data.detail || 'Error en ETL');
                }
            } catch (e) {
                setStepResult('btnStep1', origHtml, 'step1Result', false, 'Error de red: ' + e.message);
            }
        }

        // ─── Step 2 Filter Management ─────────────────────────────────────────────
        let step2Columns = [];
        let step2SubcatTableMap = {}; // subcategoria_id -> tabla_origen

        async function onSubcatChange() {
            const subcatId = document.getElementById('genSubcatSelect')?.value || '';
            const panel = document.getElementById('step2FiltersPanel');
            const container = document.getElementById('step2FiltersContainer');
            const info = document.getElementById('step2FilterInfo');

            if (!subcatId) {
                panel.style.display = 'none';
                step2Columns = [];
                container.innerHTML = '';
                return;
            }

            panel.style.display = 'block';
            container.innerHTML = '';
            info.textContent = 'Cargando columnas...';

            // Get the table name for this subcategory
            const tableName = step2SubcatTableMap[subcatId];
            if (!tableName) {
                info.textContent = 'No se encontró tabla origen para esta subcategoría.';
                return;
            }

            try {
                const res = await fetch(`/api/v1/companies/${companyId}/dest-table-columns?table_name=${encodeURIComponent(tableName)}`);
                if (res.ok) {
                    const data = await res.json();
                    step2Columns = data.columns || [];
                    info.textContent = `Tabla: ${tableName} — ${step2Columns.length} columnas disponibles. Agregue filtros o deje vacío para procesar todos.`;
                    // Add one empty filter row by default
                    addStep2FilterRow();
                } else {
                    info.textContent = 'Error al cargar columnas de la tabla.';
                }
            } catch (e) {
                info.textContent = 'Error de conexión: ' + e.message;
            }
        }

        function addStep2FilterRow(data = {}) {
            const container = document.getElementById('step2FiltersContainer');
            const row = document.createElement('div');
            row.className = 'd-flex gap-1 mb-1 align-items-center step2-filter-row';

            let colOptions = '<option value="">-- Columna --</option>';
            step2Columns.forEach(c => {
                colOptions += `<option value="${c}" ${data.column === c ? 'selected' : ''}>${c}</option>`;
            });

            row.innerHTML = `
            <select class="form-select-dark s2f-col" style="font-size:0.78rem; padding:4px 6px; flex:2;">
                ${colOptions}
            </select>
            <select class="form-select-dark s2f-op" style="font-size:0.78rem; padding:4px 6px; flex:1;" onchange="toggleStep2Val2(this)">
                <option value="=" ${data.operator === '=' ? 'selected' : ''}>=</option>
                <option value=">" ${data.operator === '>' ? 'selected' : ''}>&gt;</option>
                <option value="<" ${data.operator === '<' ? 'selected' : ''}>&lt;</option>
                <option value=">=" ${data.operator === '>=' ? 'selected' : ''}>&gt;=</option>
                <option value="<=" ${data.operator === '<=' ? 'selected' : ''}>&lt;=</option>
                <option value="BETWEEN" ${data.operator === 'BETWEEN' ? 'selected' : ''}>BETWEEN</option>
                <option value="LIKE" ${data.operator === 'LIKE' ? 'selected' : ''}>LIKE</option>
                <option value="IN" ${data.operator === 'IN' ? 'selected' : ''}>IN</option>
                <option value="IS NULL" ${data.operator === 'IS NULL' ? 'selected' : ''}>IS NULL</option>
                <option value="IS NOT NULL" ${data.operator === 'IS NOT NULL' ? 'selected' : ''}>IS NOT NULL</option>
            </select>
            <input type="text" class="form-control-dark s2f-val" style="font-size:0.78rem; padding:4px 6px; flex:2;" placeholder="Valor" value="${data.value || ''}">
            <input type="text" class="form-control-dark s2f-val2" style="font-size:0.78rem; padding:4px 6px; flex:1; display:${data.operator === 'BETWEEN' ? 'block' : 'none'};" placeholder="Hasta" value="${data.value2 || ''}">
            <button class="btn-ghost btn-sm text-danger" onclick="this.parentElement.remove()" style="padding:2px 6px; font-size:0.78rem;">
                <i class="bi bi-x-lg"></i>
            </button>
        `;
            container.appendChild(row);
        }

        function toggleStep2Val2(opSelect) {
            const row = opSelect.closest('.step2-filter-row');
            const val2 = row.querySelector('.s2f-val2');
            val2.style.display = opSelect.value === 'BETWEEN' ? 'block' : 'none';
        }

        function collectStep2Filters() {
            const rows = document.querySelectorAll('.step2-filter-row');
            const filters = [];
            rows.forEach(row => {
                const col = row.querySelector('.s2f-col')?.value || '';
                const op = row.querySelector('.s2f-op')?.value || '=';
                const val = row.querySelector('.s2f-val')?.value || '';
                const val2 = row.querySelector('.s2f-val2')?.value || '';
                if (col && (val || op === 'IS NULL' || op === 'IS NOT NULL')) {
                    filters.push({ column: col, operator: op, value: val, value2: val2 });
                }
            });
            return filters;
        }

        async function runEtlStep2() {
            const subcatId = document.getElementById('genSubcatSelect')?.value || '';
            const regen = document.getElementById('regenSwitch')?.checked || false;
            const origHtml = '<i class="bi bi-gear me-2"></i> Generar Asientos';
            setStepLoading('btnStep2', 'step2Result', 'Generando asientos en staging...');
            try {
                const body = { company_id: parseInt(companyId) };
                if (regen) body.clear_previous = true;
                if (subcatId) body.subcategoria_id = parseInt(subcatId);

                // Collect filters from the UI
                const filters = collectStep2Filters();
                if (filters.length > 0) body.filters = filters;

                const res = await fetch('/api/v1/mapeo/generate-to-cf-diariol', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
                });
                const data = await res.json();
                if (res.ok) {
                    const filterMsg = filters.length > 0 ? ` (${filters.length} filtro(s) aplicados)` : '';
                    setStepResult('btnStep2', origHtml, 'step2Result', true,
                        `${data.message}${filterMsg} — Lote: <strong>${data.lote_id || '-'}</strong>`);
                    document.getElementById('cfDiariolPanel').style.display = 'block';
                    loadCfDiariol();
                } else {
                    setStepResult('btnStep2', origHtml, 'step2Result', false, data.detail || 'Error al generar');
                }
            } catch (e) {
                setStepResult('btnStep2', origHtml, 'step2Result', false, 'Error de red: ' + e.message);
            }
        }

        async function runEtlStep3() {
            const origHtml = '<i class="bi bi-send me-2"></i> Migrar a Contasis';
            setStepLoading('btnStep3', 'step3Result', 'Migrando al destino final...');
            try {
                const res = await fetch(`/api/v1/mapeo/migrate-to-final/${companyId}`, { method: 'POST' });
                const data = await res.json();
                if (res.ok) {
                    setStepResult('btnStep3', origHtml, 'step3Result', true,
                        data.message || `Migradas ${data.migrated_lineas || 0} líneas`);
                } else {
                    setStepResult('btnStep3', origHtml, 'step3Result', false, data.detail || 'Error en migración');
                }
            } catch (e) {
                setStepResult('btnStep3', origHtml, 'step3Result', false, 'Error de red: ' + e.message);
            }
        }

        async function runFullEtl() {
            const fullRefresh = document.getElementById('fullRefreshSwitch')?.checked;
            const origHtml = '<i class="bi bi-lightning-charge me-2"></i> Proceso Completo';
            setStepLoading('btnFull', 'fullResult', 'Ejecutando proceso completo...');
            try {
                const res = await fetch(`/api/v1/etl/run-full/${companyId}`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ full_refresh: fullRefresh })
                });
                const data = await res.json();
                if (res.ok) {
                    const r = data.resultados || {};
                    const html = `
                    <div class="mt-2">
                        <div class="d-flex gap-2 flex-wrap">
                            <span class="badge ${r.paso1_etl?.status === 'OK' ? 'bg-success' : r.paso1_etl?.status === 'ERROR' ? 'bg-danger' : 'bg-secondary'}">
                                ETL: ${r.paso1_etl?.status || '-'} (${r.paso1_etl?.records || 0} reg.)
                            </span>
                            <span class="badge ${r.paso2_generar?.status === 'OK' ? 'bg-success' : r.paso2_generar?.status === 'ERROR' ? 'bg-danger' : 'bg-secondary'}">
                                Generar: ${r.paso2_generar?.status || '-'} (${r.paso2_generar?.generated || 0} líneas)
                            </span>
                            <span class="badge ${r.paso3_migrar?.status === 'OK' ? 'bg-success' : r.paso3_migrar?.status === 'ERROR' ? 'bg-danger' : 'bg-secondary'}">
                                Migrar: ${r.paso3_migrar?.status || '-'} (${r.paso3_migrar?.migrated || 0} reg.)
                            </span>
                        </div>
                        ${r.paso1_etl?.status === 'ERROR' ? `<div class="text-danger small mt-1">ETL: ${r.paso1_etl.message}</div>` : ''}
                        ${r.paso2_generar?.status === 'ERROR' ? `<div class="text-danger small mt-1">Generar: ${r.paso2_generar.message}</div>` : ''}
                        ${r.paso3_migrar?.status === 'ERROR' ? `<div class="text-danger small mt-1">Migrar: ${r.paso3_migrar.message}</div>` : ''}
                    </div>`;
                    const btn = document.getElementById('btnFull');
                    if (btn) { btn.disabled = false; btn.innerHTML = origHtml; }
                    document.getElementById('fullResult').innerHTML = html;
                    document.getElementById('cfDiariolPanel').style.display = 'block';
                    loadCfDiariol();
                } else {
                    setStepResult('btnFull', origHtml, 'fullResult', false, data.detail || 'Error en proceso completo');
                }
            } catch (e) {
                setStepResult('btnFull', origHtml, 'fullResult', false, 'Error de red: ' + e.message);
            }
        }

        async function loadCfDiariol(subcatId = null) {
            const container = document.getElementById('cfDiariolContainer');
            if (!container) return;
            container.innerHTML = '<div class="text-center py-3"><div class="spinner-sm"></div> Cargando registros...</div>';
            try {
                let url = `/api/v1/mapeo/staging-preview?company_id=${companyId}&limit=50`;
                const filterSubcat = subcatId || document.getElementById('genSubcatSelect')?.value;
                if (filterSubcat) {
                    url += `&subcategoria_id=${filterSubcat}`;
                }
                const res = await fetch(url);
                if (!res.ok) throw new Error('Error cargando la vista previa de staging');
                const data = await res.json();

                // Update title
                const titleSpan = document.getElementById('previewTableName');
                if (titleSpan) titleSpan.textContent = data.table_name || 'cf_diariol';

                if (data.error) {
                    container.innerHTML = `<div class="alert alert-error-dark">Error al consultar tabla ${data.table_name}: ${data.error}</div>`;
                    return;
                }

                if (!data.items || data.items.length === 0) {
                    container.innerHTML = `<div class="text-muted small py-2">No hay registros en ${data.table_name} aún.</div>`;
                    return;
                }

                // Generar columnas dinámicamente
                const headers = Object.keys(data.items[0]);

                container.innerHTML = `
                <div class="table-responsive" style="max-height:300px; overflow-y:auto;">
                    <table class="table-dark-custom" style="white-space: nowrap;">
                        <thead style="position:sticky;top:0;background:var(--bg-card);z-index:10;">
                            <tr>
                                ${headers.map(h => `<th>${h}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${data.items.map(row => `
                                <tr>
                                    ${headers.map(h => {
                    let val = row[h];
                    if (val === null || val === undefined) val = '-';

                    // Estilos para ciertas columnas clave
                    if (h === 'estado' && val === 'MIGRADO') return `<td><span class="badge bg-success">${val}</span></td>`;
                    if (h === 'estado' && val === 'ERROR') return `<td><span class="badge bg-danger">${val}</span></td>`;

                    return `<td>${val}</td>`;
                }).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="text-muted small mt-2">Mostrando ${data.items.length} de ${data.total} registros en ${data.table_name}</div>
            `;
            } catch (e) {
                container.innerHTML = `<div class="alert alert-error-dark">Error: ${e.message}</div>`;
            }
        }

        // ─── MAPEO CONTABLE ────────────────────────────────────────────────────────

        async function loadMapeo() {
            const container = document.getElementById('mapeoContainer');
            if (!container) return;
            container.innerHTML = '<div class="text-center py-5"><div class="spinner-sm"></div> Cargando mapeo...</div>';
            try {
                const res = await fetch(`/api/v1/mapeo/categorias?company_id=${companyId}`);
                if (!res.ok) throw new Error('Error cargando categorías');
                const cats = await res.json();

                // Populate subcategory dropdown in ETL tab and build table map
                const subcatSel = document.getElementById('genSubcatSelect');
                if (subcatSel) {
                    subcatSel.innerHTML = '<option value="">-- Todas las subcategorías --</option>';
                    step2SubcatTableMap = {};
                    cats.forEach(cat => {
                        (cat.subcategorias || []).forEach(sub => {
                            subcatSel.innerHTML += `<option value="${sub.id}">[${cat.nombre}] ${sub.nombre}${sub.tabla_origen ? ' (' + sub.tabla_origen + ')' : ''}</option>`;
                            if (sub.tabla_origen) {
                                step2SubcatTableMap[String(sub.id)] = sub.tabla_origen;
                            }
                        });
                    });
                }

                if (cats.length === 0) {
                    container.innerHTML = `
                    <div class="text-center py-5 text-muted">
                        <i class="bi bi-diagram-3 display-4 opacity-50"></i>
                        <p class="mt-3">No hay categorías de mapeo configuradas.</p>
                        <button class="btn-accent" onclick="showNewCatModal()">
                            <i class="bi bi-plus-lg me-1"></i> Crear primera categoría
                        </button>
                    </div>`;
                    return;
                }

                container.innerHTML = cats.map(cat => `
                <div class="card-dark p-3 mb-3" style="border-left: 3px solid #a78bfa;">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>
                            <strong>${cat.nombre}</strong>
                            <span class="badge bg-secondary ms-2">${cat.tipo_asiento || 'GENERAL'}</span>
                            ${cat.is_active ? '<span class="badge bg-success ms-1">Activo</span>' : '<span class="badge bg-secondary ms-1">Inactivo</span>'}
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn-ghost btn-sm" onclick="showNewSubcatModal(${cat.id})" title="Nueva subcategoría">
                                <i class="bi bi-plus-lg"></i> Subcategoría
                            </button>
                            <a href="/mapeo/${cat.id}" class="btn-ghost btn-sm" title="Editar mapeo">
                                <i class="bi bi-pencil"></i>
                            </a>
                        </div>
                    </div>
                    ${cat.descripcion ? `<p class="text-muted small mb-2">${cat.descripcion}</p>` : ''}
                    <div class="ms-3">
                        ${(cat.subcategorias || []).length === 0
                        ? '<div class="text-muted small">Sin subcategorías</div>'
                        : (cat.subcategorias || []).map(sub => `
                                <div class="d-flex justify-content-between align-items-center py-1 border-bottom" style="border-color: var(--border-color) !important;">
                                    <div>
                                        <i class="bi bi-arrow-right-short text-muted"></i>
                                        <strong>${sub.nombre}</strong>
                                        ${sub.tabla_origen ? `<code class="ms-2 small">${sub.tabla_origen}</code>` : '<span class="text-warning ms-2 small">Sin tabla origen</span>'}
                                        ${sub.is_active ? '' : '<span class="badge bg-secondary ms-1 small">Inactivo</span>'}
                                    </div>
                                    <div class="d-flex gap-2">
                                        <button class="btn-ghost btn-sm" onclick="generateSubcat(${sub.id})" title="Generar asientos">
                                            <i class="bi bi-gear"></i>
                                        </button>
                                        <a href="/mapeo/${sub.id}" class="btn-ghost btn-sm" title="Editar líneas">
                                            <i class="bi bi-list-ul"></i>
                                        </a>
                                    </div>
                                </div>
                            `).join('')
                    }
                    </div>
                </div>
            `).join('');
            } catch (e) {
                container.innerHTML = `<div class="alert alert-error-dark"><i class="bi bi-exclamation-triangle me-2"></i>Error: ${e.message}</div>`;
            }
        }

        async function generateSubcat(subcatId) {
            const { periodo, mes } = getEtlPeriod();
            const { isConfirmed } = await Swal.fire({
                title: 'Generar Asientos',
                html: `<p style="color:#8b949e;">Se generarán asientos contables para la subcategoría <strong style="color:#58a6ff;">#${subcatId}</strong></p>
                       <p style="color:#e6edf3; font-size:14px;"><i class="bi bi-calendar3 me-1"></i>Período: <strong>${periodo}-${mes}</strong></p>`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: '<i class="bi bi-play-fill me-1"></i> Generar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#3fb950',
                cancelButtonColor: '#30363d',
                background: '#161b22',
                color: '#e6edf3',
            });
            if (!isConfirmed) return;
            try {
                const res = await fetch('/api/v1/mapeo/generate-to-cf-diariol', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ subcategoria_id: subcatId, periodo, mes })
                });
                const data = await res.json();
                if (res.ok) {
                    showToast('success', `${data.message} — Lote: ${data.lote_id}`);
                } else {
                    showToast('error', `Error: ${data.detail}`);
                }
            } catch (e) { showToast('error', 'Error de red: ' + e.message); }
        }

        // Modals references
        const modalMapeoCategoria = new bootstrap.Modal(document.getElementById('modalMapeoCategoria'));
        const modalMapeoSubcategoria = new bootstrap.Modal(document.getElementById('modalMapeoSubcategoria'));

        function showNewCatModal() {
            document.getElementById('newCatName').value = '';
            document.getElementById('newCatType').value = 'GENERAL';
            modalMapeoCategoria.show();
        }

        async function saveCategoria() {
            const nombre = document.getElementById('newCatName').value;
            const tipo = document.getElementById('newCatType').value;
            if (!nombre) return showToast('warning', "Nombre requerido");

            try {
                const res = await fetch('/api/v1/mapeo/categorias', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ company_id: companyId, nombre: nombre.trim(), tipo_asiento: tipo, is_active: true })
                });
                const data = await res.json();
                if (res.ok) {
                    modalMapeoCategoria.hide();
                    loadMapeo();
                } else {
                    showToast('error', "Error al crear categoría: " + (data.detail || JSON.stringify(data)));
                }
            } catch (e) { showToast('error', "Error de red: " + e.message); }
        }

        async function showNewSubcatModal(catId) {
            document.getElementById('currentCatId').value = catId;
            document.getElementById('newSubName').value = '';
            document.getElementById('newSubCode').value = '';

            // Load tables for dropdown
            const select = document.getElementById('newSubTable');
            select.innerHTML = '<option>Cargando...</option>';

            try {
                // First check if tables endpoint works
                const res = await fetch(`/api/v1/companies/${companyId}/intermediate-tables`);
                if (res.ok) {
                    const tables = await res.json();
                    select.innerHTML = '<option value="">-- Seleccionar tabla --</option>';
                    tables.forEach(t => {
                        const opt = document.createElement('option');
                        opt.value = t;
                        opt.textContent = t;
                        select.appendChild(opt);
                    });
                } else {
                    select.innerHTML = '<option value="">Error cargando tablas</option>';
                }
            } catch (e) {
                console.error(e);
                select.innerHTML = '<option value="">Error de conexión</option>';
            }

            modalMapeoSubcategoria.show();
        }

        async function saveSubcategoria() {
            const catId = document.getElementById('currentCatId').value;
            const nombre = document.getElementById('newSubName').value;
            const tabla = document.getElementById('newSubTable').value;
            const codigo = document.getElementById('newSubCode').value;

            if (!nombre || !tabla) return showToast('warning', "Nombre y Tabla Origen son obligatorios");

            try {
                const res = await fetch('/api/v1/mapeo/subcategorias', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        categoria_id: catId,
                        nombre: nombre.trim(),
                        tabla_origen: tabla,
                        codigo_origen: codigo || null,
                        generate_headers: document.getElementById('newSubGenHeaders').checked,
                        generate_details: document.getElementById('newSubGenDetails').checked,
                        is_active: true
                    })
                });
                const data = await res.json();
                if (res.ok) {
                    modalMapeoSubcategoria.hide();
                    loadMapeo();
                } else {
                    showToast('error', "Error al crear subcategoría: " + (data.detail || JSON.stringify(data)));
                }
            } catch (e) { showToast('error', "Error de red: " + e.message); }
        }

        // ─── TABLE CONFIGURATION (FILTERS & INCREMENTAL) ───
        const modalTableConfig = new bootstrap.Modal(document.getElementById('modalTableConfig'));
        let currentTableColumns = []; // Store fetched columns

        async function openTableConfig(selectionId, tableSchema, tableName, controlCol, controlType) {
            document.getElementById('configSelectionId').value = selectionId;
            document.getElementById('configTableSchema').value = tableSchema;
            document.getElementById('configTableName').textContent = tableName;

            // Incremental Tab
            document.getElementById('configControlCol').value = controlCol && controlCol !== 'null' ? controlCol : '';
            document.getElementById('configControlType').value = controlType && controlType !== 'null' ? controlType : 'DATE';

            // Load Columns for UI
            currentTableColumns = [];
            const incrSel = document.getElementById('incrSourceCols');
            incrSel.innerHTML = '<option>Cargando...</option>';

            try {
                const res = await fetch(`/api/v1/companies/${companyId}/source-table-columns?table_name=${tableName}&table_schema=${tableSchema}`);
                if (res.ok) {
                    const cols = await res.json();
                    currentTableColumns = cols.map(c => c.column_name); // Just names for now
                    incrSel.innerHTML = currentTableColumns.map(c => `<option value="${c}">${c}</option>`).join('');
                } else {
                    incrSel.innerHTML = '<option>Error cargando columnas</option>';
                }
            } catch (e) {
                incrSel.innerHTML = '<option>Error de red</option>';
            }

            // Load Filters
            loadTableFilters(selectionId);

            // Load Computed Columns
            loadComputedColumns(selectionId);

            modalTableConfig.show();
        }

        function addToIncrementalKey() {
            const sel = document.getElementById('incrSourceCols');
            const val = sel.value;
            const input = document.getElementById('configControlCol');
            let current = input.value ? input.value.split(',').map(s => s.trim()) : [];
            if (val && !current.includes(val)) {
                current.push(val);
                input.value = current.join(', ');
                // Auto-set type to STRING if multiple columns
                if (current.length > 1) document.getElementById('configControlType').value = 'STRING';
            }
        }

        function clearIncrementalKey() {
            document.getElementById('configControlCol').value = '';
        }

        async function loadTableFilters(selectionId) {
            const tbody = document.getElementById('filtersBody');
            tbody.innerHTML = '<tr><td colspan="4" class="text-center"><div class="spinner-sm"></div> Cargando...</td></tr>';

            try {
                const res = await fetch(`/api/v1/mapeo/table-selections/${selectionId}/filters`);
                if (res.ok) {
                    const filters = await res.json();
                    tbody.innerHTML = '';
                    if (filters.length === 0) {
                        addFilterRow(); // Add empty row if none
                    } else {
                        filters.forEach(f => addFilterRow(f));
                    }
                } else {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-danger">Error cargando filtros</td></tr>';
                }
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="4" class="text-danger">Error: ${e.message}</td></tr>`;
            }
        }

        function addFilterRow(data = {}) {
            const tbody = document.getElementById('filtersBody');
            const tr = document.createElement('tr');

            // Build options for select
            let colOptions = '<option value="">-- Columna --</option>';
            if (currentTableColumns.length > 0) {
                colOptions += currentTableColumns.map(c =>
                    `<option value="${c}" ${data.column_name === c ? 'selected' : ''}>${c}</option>`
                ).join('');
            } else {
                // Fallback if columns failed to load or pre-loading existing filter with raw value
                if (data.column_name) colOptions = `<option value="${data.column_name}" selected>${data.column_name}</option>`;
            }

            tr.innerHTML = `
            <td>
                <select class="form-select form-select-sm form-select-dark f-col">
                    ${colOptions}
                </select>
            </td>
            <td>
                <select class="form-select form-select-sm form-select-dark f-op">
                    <option value="=" ${data.operator === '=' ? 'selected' : ''}>=</option>
                    <option value=">" ${data.operator === '>' ? 'selected' : ''}>&gt;</option>
                    <option value="<" ${data.operator === '<' ? 'selected' : ''}>&lt;</option>
                    <option value=">=" ${data.operator === '>=' ? 'selected' : ''}>&gt;=</option>
                    <option value="<=" ${data.operator === '<=' ? 'selected' : ''}>&lt;=</option>
                    <option value="LIKE" ${data.operator === 'LIKE' ? 'selected' : ''}>LIKE</option>
                    <option value="IN" ${data.operator === 'IN' ? 'selected' : ''}>IN</option>
                    <option value="IS NULL" ${data.operator === 'IS NULL' ? 'selected' : ''}>IS NULL</option>
                    <option value="IS NOT NULL" ${data.operator === 'IS NOT NULL' ? 'selected' : ''}>IS NOT NULL</option>
                </select>
            </td>
            <td><input type="text" class="form-control form-control-sm form-control-dark f-val" placeholder="Valor" value="${data.filter_value || ''}"></td>
            <td><button class="btn-ghost btn-sm text-danger" onclick="this.closest('tr').remove()"><i class="bi bi-trash"></i></button></td>
        `;
            tbody.appendChild(tr);
        }

        async function saveTableFilters() {
            const selectionId = document.getElementById('configSelectionId').value;
            const rows = document.querySelectorAll('#filtersBody tr');
            const filters = [];

            for (let tr of rows) {
                const col = tr.querySelector('.f-col').value; // Now a Select
                const op = tr.querySelector('.f-op').value;
                const val = tr.querySelector('.f-val').value;

                if (col) { // Only save if column name is present
                    filters.push({
                        column_name: col,
                        operator: op,
                        filter_value: val,
                        is_active: true
                    });
                }
            }

            try {
                const res = await fetch(`/api/v1/mapeo/table-selections/${selectionId}/filters`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ table_selection_id: parseInt(selectionId), filters: filters })
                });
                if (res.ok) {
                    showToast('success', "Filtros guardados correctamente");
                } else {
                    const data = await res.json();
                    showToast('error', "❌ Error: " + (data.detail || "Error desconocido"));
                }
            } catch (e) { showToast('error', "Error de red: " + e.message); }
        }

        async function saveIncrementalConfig() {
            const selectionId = document.getElementById('configSelectionId').value;
            const col = document.getElementById('configControlCol').value.trim(); // Reads from the read-only input updated by JS
            const type = document.getElementById('configControlType').value;

            try {
                const res = await fetch(`/api/v1/mapeo/table-selections/${selectionId}/control-column`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ control_column: col || null, control_column_type: type })
                });
                if (res.ok) {
                    showToast('success', "Configuración incremental guardada");
                    loadTables();
                } else {
                    showToast('error', "❌ Error al guardar configuracion");
                }
            } catch (e) { showToast('error', "Error de red"); }
        }

        // ─── TIPO DE CAMBIO SUNAT ───

        async function syncTcMonth() {
            const ym = document.getElementById('tcYearMonth').value; // YYYY-MM
            if (!ym) return showToast('warning', "Seleccione un mes");

            document.getElementById('tcSyncStatus').textContent = "Sincronizando...";
            try {
                const res = await fetch('/api/v1/tipo-cambio/sync-month', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ year_month: ym })
                });
                const data = await res.json();
                if (res.ok) {
                    showToast('success', `${data.message}`);
                    loadTipoCambio(ym); // Reload table
                } else {
                    showToast('error', `Error: ${data.detail}`);
                }
            } catch (e) { showToast('error', "Error de red"); }
            document.getElementById('tcSyncStatus').textContent = "";
        }

        async function syncTcToday() {
            document.getElementById('tcSyncStatus').textContent = "Sincronizando hoy...";
            try {
                const res = await fetch('/api/v1/tipo-cambio/sync-today', { method: 'POST' });
                const data = await res.json();
                if (res.ok) {
                    showToast('success', `${data.message}`);
                    // Use current month of today to reload list
                    const today = new Date().toISOString().slice(0, 7);
                    document.getElementById('tcYearMonth').value = today;
                    loadTipoCambio(today);
                } else {
                    showToast('error', `Error: ${data.detail}`);
                }
            } catch (e) { showToast('error', "Error de red"); }
            document.getElementById('tcSyncStatus').textContent = "";
        }

        async function loadTipoCambio(yearMonth) {
            if (!yearMonth) return;
            const [year, month] = yearMonth.split('-');
            const tbody = document.getElementById('tcTableBody');
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">Cargando...</td></tr>';

            try {
                const res = await fetch(`/api/v1/tipo-cambio?year=${year}&month=${month}`);
                if (res.ok) {
                    const rows = await res.json();
                    tbody.innerHTML = rows.map(r => `
                    <tr>
                        <td>${r.fecha}</td>
                        <td>${r.compra}</td>
                        <td>${r.venta}</td>
                    </tr>
                `).join('');
                    if (rows.length === 0) tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';
                }
            } catch (e) { tbody.innerHTML = '<tr><td colspan="3" class="text-danger">Error carga</td></tr>'; }
        }

        // Auto-load TC when changing date picker or entering tab
        document.getElementById('tcYearMonth').addEventListener('change', (e) => loadTipoCambio(e.target.value));

        // ─── COMPUTED COLUMNS (Columnas Calculadas) ───

        async function loadComputedColumns(selectionId) {
            const tbody = document.getElementById('computedBody');
            tbody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner-sm"></div> Cargando...</td></tr>';
            try {
                const res = await fetch(`/api/v1/mapeo/table-selections/${selectionId}/computed-columns`);
                if (res.ok) {
                    const rules = await res.json();
                    tbody.innerHTML = '';
                    if (rules.length === 0) {
                        addComputedRule();
                    } else {
                        rules.forEach(r => addComputedRule(r));
                    }
                } else {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-danger">Error cargando reglas</td></tr>';
                }
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-danger">Error: ${e.message}</td></tr>`;
            }
        }

        function addComputedRule(data = {}) {
            const escapeHtml = (s) => (s || '').toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");

            const tbody = document.getElementById('computedBody');
            const tr = document.createElement('tr');

            // Build column options from currentTableColumns
            let srcColOptions = '<option value="">-- Columna --</option>';
            if (currentTableColumns.length > 0) {
                srcColOptions += currentTableColumns.map(c =>
                    `<option value="${escapeHtml(c)}" ${data.source_column === c ? 'selected' : ''}>${escapeHtml(c)}</option>`
                ).join('');
            } else if (data.source_column) {
                srcColOptions = `<option value="${escapeHtml(data.source_column)}" selected>${escapeHtml(data.source_column)}</option>`;
            }

            tr.innerHTML = `
            <td><input type="text" class="form-control form-control-sm form-control-dark cc-newcol" 
                placeholder="ej: tipo_doc" value="${escapeHtml(data.new_column_name)}" style="min-width:100px;"></td>
            <td>
                <select class="form-select form-select-sm form-select-dark cc-srccol">
                    ${srcColOptions}
                </select>
            </td>
            <td>
                <div>
                    <input type="text" class="form-control form-control-sm form-control-dark cc-condval" list="condOptions"
                        placeholder="ej: BOLE o BUSCARX..." value="${escapeHtml(data.condition_value)}" 
                        oninput="validateFormula(this)"
                        style="min-width:300px; max-width:400px;">
                    <div class="invalid-feedback formula-error-msg" style="display:none; font-size:0.75rem; margin-top:0.25rem;"></div>
                </div>
            </td>
            <td><input type="text" class="form-control form-control-sm form-control-dark cc-result" 
                placeholder="ej: 03" value="${escapeHtml(data.result_value)}" style="min-width:60px;"></td>
            <td><input type="text" class="form-control form-control-sm form-control-dark cc-default" 
                placeholder="default" value="${escapeHtml(data.default_value)}" style="min-width:60px;"></td>
            <td class="d-flex gap-1 align-items-center">
                <button class="btn-ghost btn-sm text-muted" onclick="moveRuleUp(this)" title="Subir prioridad"><i class="bi bi-arrow-up"></i></button>
                <button class="btn-ghost btn-sm text-muted" onclick="moveRuleDown(this)" title="Bajar prioridad"><i class="bi bi-arrow-down"></i></button>
                <button class="btn-ghost btn-sm text-danger" onclick="this.closest('tr').remove()" title="Eliminar regla">
                <i class="bi bi-trash"></i></button>
            </td>
        `;
            tbody.appendChild(tr);
        }

        function moveRuleUp(btn) {
            const row = btn.closest('tr');
            if (row.previousElementSibling) {
                row.parentNode.insertBefore(row, row.previousElementSibling);
            }
        }

        function moveRuleDown(btn) {
            const row = btn.closest('tr');
            if (row.nextElementSibling) {
                row.parentNode.insertBefore(row.nextElementSibling, row);
            }
        }

        function validateFormula(input) {
            const val = input.value.trim();
            const errorDiv = input.parentElement.querySelector('.formula-error-msg');

            // Si está vacío, no hay error de sintaxis per se (puede no usarse)
            if (!val) {
                setFormulaValidity(input, errorDiv, true, "");
                return true;
            }

            // Validar comillas equilibradas
            let sQuotes = (val.match(/'/g) || []).length;
            let dQuotes = (val.match(/"/g) || []).length;
            if (sQuotes % 2 !== 0 || dQuotes % 2 !== 0) {
                setFormulaValidity(input, errorDiv, false, "Comillas sin cerrar (desbalanceadas)");
                return false;
            }

            // Validar paréntesis equilibrados
            let openP = (val.match(/\(/g) || []).length;
            let closeP = (val.match(/\)/g) || []).length;
            if (openP !== closeP) {
                setFormulaValidity(input, errorDiv, false, "Paréntesis sin cerrar (desbalanceados)");
                return false;
            }

            // Validar funciones que exigen comas (múltiples parámetros)
            const multiParamFuncs = ["SI.CONJUNTO", "SUMAR.SI.CONJUNTO", "CONCAT", "CONCAT_EXACTO", "RESTA", "MULTIPLICA", "DIVIDE", "BUSCARX", "BUSCARX_EXT"];
            for (let f of multiParamFuncs) {
                if (val.toUpperCase().includes(f + "(")) {
                    // Extracting content inside parenthesis roughly without full AST parsing
                    // Just check if there is at least a comma overall if the formula is complex
                    if (!val.includes(",")) {
                        setFormulaValidity(input, errorDiv, false, `La función ${f} suele requerir parámetros separados por coma (,)`);
                        return false;
                    }
                }
            }

            // TODO OK
            setFormulaValidity(input, errorDiv, true, "Sintaxis válida");
            return true;
        }

        function setFormulaValidity(input, errorDiv, isValid, msg) {
            if (isValid) {
                if (msg) {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                    errorDiv.style.display = 'block';
                    errorDiv.className = 'valid-feedback formula-error-msg';
                    errorDiv.textContent = msg;
                } else {
                    input.classList.remove('is-invalid', 'is-valid');
                    errorDiv.style.display = 'none';
                }
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
                errorDiv.style.display = 'block';
                errorDiv.className = 'invalid-feedback formula-error-msg';
                errorDiv.textContent = msg;
            }
        }

        async function saveComputedColumns() {
            const selectionId = document.getElementById('configSelectionId').value;
            const rows = document.querySelectorAll('#computedBody tr');
            const rules = [];

            // Validar todas las formulas activas antes de guardar
            let hasErrors = false;
            document.querySelectorAll('.cc-condval').forEach(input => {
                if (!validateFormula(input)) {
                    hasErrors = true;
                }
            });

            if (hasErrors) {
                showToast('error', 'Corrige los errores en las fórmulas sintácticas antes de guardar.');
                return;
            }

            for (let tr of rows) {
                const newCol = tr.querySelector('.cc-newcol');
                const srcCol = tr.querySelector('.cc-srccol');
                const condVal = tr.querySelector('.cc-condval');
                const result = tr.querySelector('.cc-result');
                const defVal = tr.querySelector('.cc-default');

                if (!newCol) continue; // Skip malformed rows

                const n = newCol.value.trim();
                const s = srcCol ? srcCol.value : '';
                const c = condVal.value.trim();
                const r = result ? result.value.trim() : '';

                if (n && (s || c || r)) {
                    rules.push({
                        new_column_name: n,
                        source_column: s,
                        condition_value: c,
                        result_value: r,
                        default_value: defVal ? defVal.value.trim() : ''
                    });
                }
            }

            try {
                const res = await fetch(`/api/v1/mapeo/table-selections/${selectionId}/computed-columns`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rules: rules })
                });
                if (res.ok) {
                    const data = await res.json();
                    showToast('success', `${data.message}`);
                } else {
                    const data = await res.json();
                    showToast('error', '❌ Error: ' + (data.detail || 'Error desconocido'));
                }
            } catch (e) { showToast('error', 'Error de red: ' + e.message); }
        }


    