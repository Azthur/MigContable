
    // ── Global fetch wrapper: NEVER cache API responses ──────────────
    (function() {
        const _originalFetch = window.fetch;
        window.fetch = function(input, init) {
            init = init || {};
            const url = (typeof input === 'string') ? input : (input.url || '');
            if (url.startsWith('/api/') || url.startsWith('/api')) {
                init.cache = 'no-store';
            }
            return _originalFetch.call(this, input, init);
        };
    })();

    const authHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('migconta_token')}`
    };

    let allCompanies = [];
    let scheduleModalObj = null;
    let logDetailsModalObj = null;
    let stagingRowModalObj = null;
    let correlativoModalObj = null;
    let reextractModalObj = null;
    let rawRowDetailModalObj = null;
    let currentVisorItems = [];
    let currentSchedulesList = [];
    let currentReextractParams = { companyId: null, subcatId: null, nasiento: null };

    // Startup
    $(document).ready(function() {
        scheduleModalObj = new bootstrap.Modal(document.getElementById('scheduleModal'));
        logDetailsModalObj = new bootstrap.Modal(document.getElementById('logDetailsModal'));
        stagingRowModalObj = new bootstrap.Modal(document.getElementById('stagingRowModal'));
        correlativoModalObj = new bootstrap.Modal(document.getElementById('correlativoModal'));
        reextractModalObj = new bootstrap.Modal(document.getElementById('reextractModal'));
        rawRowDetailModalObj = new bootstrap.Modal(document.getElementById('rawRowDetailModal'));

        // Load page components
        loadCompanies();
        loadSchedules();
        loadRealtimeLogs();
        
        // Auto refresh logs and summary every 30s
        setInterval(loadRealtimeLogs, 30000);
        
        // Populate current period/month defaults
        const currentYear = new Date().getFullYear();
        const currentMonth = String(new Date().getMonth() + 1).padStart(2, '0');
        
        document.getElementById('visorPeriodo').value = currentYear;
        document.getElementById('visorMes').value = currentMonth;
        document.getElementById('migratedPeriodo').value = currentYear;
    });

    // Load Companies
    async function loadCompanies() {
        try {
            const res = await fetch('/api/v1/companies', { headers: authHeaders });
            if (!res.ok) throw new Error();
            allCompanies = await res.json();
            
            // Populate all company selectors on the page
            const selectors = [
                'schedCompany', 'visorCompany', 'summaryCompany', 'logFilterCompany', 'corrCompany', 'correlativoFilterCompany', 'filterSchedCompany', 'migratedCompany'
            ];
            
            allCompanies.forEach(c => {
                if (c.is_active) {
                    selectors.forEach(selId => {
                        const sel = document.getElementById(selId);
                        if (sel) sel.add(new Option(c.name, c.id));
                    });
                }
            });
            // Populate filter subcategories on load (all companies initially)
            onFilterSchedCompanyChange();
        } catch (err) {
            console.error("Error cargando empresas:", err);
        }
    }

    // ─── Staging Summary per Subcategory ───
    async function loadStagingSummary() {
        const compId = document.getElementById('summaryCompany').value;
        const tbody = document.getElementById('summaryTableBody');
        
        if (!compId) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-secondary py-4">Seleccione una empresa para ver el resumen de staging.</td></tr>';
            return;
        }

        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-secondary py-4"><span class="spinner-sm"></span> Cargando resumen...</td></tr>';

        try {
            const res = await fetch(`/api/v1/etl/staging-summary?company_id=${compId}`, { headers: authHeaders });
            const data = res.ok ? await res.json() : [];
            
            tbody.innerHTML = '';
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-secondary py-4">No hay datos de staging para esta empresa.</td></tr>';
                return;
            }

            data.forEach(s => {
                const pct = s.total > 0 ? Math.round((s.migrado / s.total) * 100) : 0;
                let progressColor = 'bg-warning';
                if (pct >= 100) progressColor = 'bg-success';
                else if (pct >= 50) progressColor = 'bg-info';
                else if (s.error > 0) progressColor = 'bg-danger';

                const toggleId = `subcat-details-${s.subcategoria_id}`;

                tbody.innerHTML += `
                    <tr class="align-middle" style="cursor: pointer;" onclick="toggleSubcatDetails('${toggleId}', this)">
                        <td class="fw-semibold">
                            <i class="bi bi-chevron-right me-2 toggle-icon" style="transition: transform 0.2s; display: inline-block;"></i>
                            ${s.subcategoria_nombre}
                        </td>
                        <td class="text-center font-monospace">${s.total}</td>
                        <td class="text-center">
                            <span class="badge bg-warning-subtle text-warning">${s.pendiente}</span>
                        </td>
                        <td class="text-center">
                            <span class="badge bg-success-subtle text-success">${s.migrado}</span>
                        </td>
                        <td class="text-center">
                            ${s.error > 0 
                                ? `<span class="badge bg-danger-subtle text-danger">${s.error}</span>` 
                                : '<span class="text-secondary">0</span>'}
                        </td>
                        <td class="text-center">
                            <div class="d-flex align-items-center gap-2">
                                <div class="progress flex-grow-1" style="height: 6px; background: rgba(255,255,255,0.1);">
                                    <div class="progress-bar ${progressColor}" style="width: ${pct}%"></div>
                                </div>
                                <span class="text-secondary small font-monospace" style="min-width: 36px;">${pct}%</span>
                            </div>
                        </td>
                        <td class="text-end">
                            <button class="btn btn-outline-primary btn-sm px-2 py-0" style="font-size:0.75rem;" 
                                onclick="event.stopPropagation(); reprocessSubcategory(${compId}, ${s.subcategoria_id}, '${s.subcategoria_nombre}', this)">
                                <i class="bi bi-arrow-clockwise me-1"></i> Reprocesar
                            </button>
                            <button class="btn btn-outline-warning btn-sm px-2 py-0 ms-1" style="font-size:0.75rem;" 
                                onclick="event.stopPropagation(); openReextractModal(${compId}, ${s.subcategoria_id}, '${s.subcategoria_nombre.replace(/'/g, "\\'")}', null)">
                                <i class="bi bi-arrow-repeat me-1"></i> Reextraer
                            </button>
                        </td>
                    </tr>
                    <tr id="${toggleId}" class="d-none" style="background: rgba(255, 255, 255, 0.02); border-left: 3px solid var(--accent);">
                        <td colspan="7" class="p-3">
                            <div class="table-responsive">
                                <table class="table-dark-custom mb-0" style="font-size: 0.8rem; background: rgba(0,0,0,0.2);">
                                    <thead>
                                        <tr>
                                            <th>Periodo</th>
                                            <th class="text-center">Total Registros</th>
                                            <th class="text-center">Pendientes</th>
                                            <th class="text-center">Migrados</th>
                                            <th class="text-center">Errores</th>
                                            <th class="text-center">Progreso</th>
                                            <th class="text-end">Acciones</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${(s.periodos || []).map(p => {
                                            const subPct = p.total > 0 ? Math.round((p.migrado / p.total) * 100) : 0;
                                            let subProgColor = 'bg-warning';
                                            if (subPct >= 100) subProgColor = 'bg-success';
                                            else if (subPct >= 50) subProgColor = 'bg-info';
                                            else if (p.error > 0) subProgColor = 'bg-danger';

                                            return `
                                                <tr>
                                                    <td><i class="bi bi-calendar-event me-2 text-primary"></i>${p.periodo}-${p.mes}</td>
                                                    <td class="text-center font-monospace">${p.total}</td>
                                                    <td class="text-center"><span class="badge bg-warning-subtle text-warning">${p.pendiente}</span></td>
                                                    <td class="text-center"><span class="badge bg-success-subtle text-success">${p.migrado}</span></td>
                                                    <td class="text-center">
                                                        ${p.error > 0 
                                                            ? `<span class="badge bg-danger-subtle text-danger">${p.error}</span>` 
                                                            : '<span class="text-secondary">0</span>'}
                                                    </td>
                                                    <td class="text-center">
                                                        <div class="d-inline-flex align-items-center gap-2" style="width: 120px;">
                                                            <div class="progress flex-grow-1" style="height: 4px; background: rgba(255,255,255,0.1);">
                                                                <div class="progress-bar ${subProgColor}" style="width: ${subPct}%"></div>
                                                            </div>
                                                            <span class="text-secondary font-monospace" style="font-size: 0.75rem;">${subPct}%</span>
                                                        </div>
                                                    </td>
                                                    <td class="text-end">
                                                        <button class="btn btn-outline-danger btn-sm px-2 py-0" style="font-size:0.75rem;" 
                                                            onclick="event.stopPropagation(); clearAndReprocessPeriod(${compId}, ${s.subcategoria_id}, '${s.subcategoria_nombre}', '${p.periodo}', '${p.mes}', this)">
                                                            <i class="bi bi-trash me-1"></i> Reiniciar
                                                        </button>
                                                    </td>
                                                </tr>
                                            `;
                                        }).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </td>
                    </tr>
                `;
            });
        } catch (err) {
            console.error("Error loading staging summary:", err);
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger py-4">Error al cargar resumen.</td></tr>';
        }
    }

    // Toggle subcategory detailed periods
    function toggleSubcatDetails(id, rowEl) {
        const detailRow = document.getElementById(id);
        const icon = rowEl.querySelector('.toggle-icon');
        if (detailRow.classList.contains('d-none')) {
            detailRow.classList.remove('d-none');
            icon.style.transform = 'rotate(90deg)';
        } else {
            detailRow.classList.add('d-none');
            icon.style.transform = 'rotate(0deg)';
        }
    }

    async function reprocessSubcategory(companyId, subcatId, subcatName, btn) {
        const confirmResult = await Swal.fire({
            title: `¿Reprocesar ${subcatName}?`,
            text: 'Se regenerarán y migrarán todos los asientos de esta subcategoría.',
            icon: 'question',
            showCancelButton: true,
            background: '#161b22',
            color: '#fff',
            confirmButtonColor: '#bc8cff',
            cancelButtonColor: '#30363d',
            confirmButtonText: 'Sí, reprocesar',
            cancelButtonText: 'Cancelar'
        });

        if (!confirmResult.isConfirmed) return;

        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            const res = await fetch('/api/v1/etl/reprocess-row', {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify({
                    company_id: companyId,
                    step: 'MIGRATION',
                    table: 'cf_diariol',
                    reference: '',
                    subcategoria_id: subcatId
                })
            });

            const data = await res.json();
            if (res.ok && data.status === 'SUCCESS') {
                showToast('success', data.message || `${subcatName} reprocesada correctamente`);
                loadStagingSummary();
                loadRealtimeLogs();
            } else {
                showToast('error', data.detail || 'Fallo al reprocesar subcategoría');
            }
        } catch (err) {
            showToast('error', 'Error de red');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }

    async function clearAndReprocessPeriod(companyId, subcatId, subcatName, periodo, mes, btn) {
        const confirmResult = await Swal.fire({
            title: '¿Reiniciar Periodo en Staging?',
            html: `
                <div class="text-start">
                    <p class="mb-2">Se eliminarán permanentemente los registros de staging para:</p>
                    <ul class="mb-3">
                        <li><strong>Subcategoría:</strong> ${subcatName}</li>
                        <li><strong>Periodo:</strong> ${periodo}-${mes}</li>
                    </ul>
                    <div class="alert alert-warning py-2 px-3 mb-0" style="font-size: 0.85rem; background: rgba(255,193,7,0.1); border: 1px solid rgba(255,193,7,0.2); color: #ffc107;">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        Esta action <strong>NO</strong> borrará datos del sistema final Contasis (debe eliminarlos manualmente en Contasis si lo desea). Solo limpiará la base intermedia para permitir volver a procesar y migrar.
                    </div>
                </div>
            `,
            icon: 'warning',
            showCancelButton: true,
            background: '#161b22',
            color: '#fff',
            confirmButtonColor: '#ea4c89',
            cancelButtonColor: '#30363d',
            confirmButtonText: 'Sí, eliminar staging y reiniciar',
            cancelButtonText: 'Cancelar'
        });

        if (!confirmResult.isConfirmed) return;

        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            const res = await fetch('/api/v1/etl/clear-period-staging', {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify({
                    company_id: companyId,
                    subcategoria_id: subcatId,
                    periodo: periodo,
                    mes: mes
                })
            });

            const data = await res.json();
            if (res.ok && data.status === 'SUCCESS') {
                showToast('success', data.message || `Periodo ${periodo}-${mes} reiniciado correctamente`);
                loadStagingSummary();
                if (typeof loadRealtimeLogs === 'function') {
                    loadRealtimeLogs();
                }
            } else {
                showToast('error', data.detail || 'Fallo al reiniciar el periodo');
            }
        } catch (err) {
            showToast('error', 'Error de red');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }

    // Load Scheduled Tasks of type ETL_REALTIME
    async function loadSchedules() {
        try {
            const res = await fetch('/api/v1/pipelines', { headers: authHeaders });
            const tasks = await res.json();
            const scheds = tasks.filter(t => t.task_type === 'ETL_REALTIME');
            
            currentSchedulesList = scheds;
            
            renderSchedules();
        } catch (err) {
            console.error("Error loading tasks schedules:", err);
        }
    }

    // Filter and Render Schedules in the Table
    function renderSchedules() {
        const compFilter = document.getElementById('filterSchedCompany').value;
        const subcatFilter = document.getElementById('filterSchedSubcategory').value;
        const tbody = document.getElementById('schedulesTableBody');
        
        tbody.innerHTML = '';
        
        let filtered = currentSchedulesList;
        if (compFilter) {
            filtered = filtered.filter(s => String(s.company_id) === String(compFilter));
        }
        if (subcatFilter) {
            filtered = filtered.filter(s => s.params && s.params.subcategorias && s.params.subcategorias.includes(parseInt(subcatFilter)));
        }
        
        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-secondary py-3">No hay programaciones automáticas registradas.</td></tr>';
            return;
        }

        filtered.forEach((s) => {
            const idx = currentSchedulesList.findIndex(item => item.id === s.id);
            const comp = allCompanies.find(c => c.id === s.company_id);
            const compName = comp ? comp.name : `Empresa ${s.company_id}`;
            
            let freqBadge = '';
            let infoStr = '';
            if (s.schedule_type === 'MINUTES') {
                freqBadge = `<span class="badge bg-info">Cada ${s.time_str} Minutos</span>`;
                infoStr = '-';
            } else if (s.schedule_type === 'DAILY') {
                freqBadge = `<span class="badge bg-primary">Diario</span>`;
                infoStr = `<i class="bi bi-clock me-1"></i>${s.time_str}`;
            } else if (s.schedule_type === 'WEEKLY') {
                freqBadge = `<span class="badge bg-secondary">Semanal</span>`;
                const daysMap = { mon: 'Lunes', tue: 'Martes', wed: 'Miércoles', thu: 'Jueves', fri: 'Viernes', sat: 'Sábado', sun: 'Domingo' };
                infoStr = `${daysMap[s.day_of_week] || s.day_of_week} a las ${s.time_str}`;
            }

            let lastRunStr = '-';
            if (s.last_run) {
                const lrDate = new Date(s.last_run);
                lastRunStr = lrDate.toLocaleDateString('es-CO') + ' ' + lrDate.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            }

            let nextRunStr = '-';
            if (s.next_run && s.is_active) {
                const nrDate = new Date(s.next_run);
                nextRunStr = nrDate.toLocaleDateString('es-CO') + ' ' + nrDate.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            } else if (!s.is_active) {
                nextRunStr = '<span class="text-muted small">Inactivo</span>';
            }

            const statusBadge = s.is_active 
                ? `<span class="badge bg-success-subtle text-success">Activo</span>`
                : `<span class="badge bg-danger-subtle text-danger">Inactivo</span>`;

            tbody.innerHTML += `
                <tr>
                    <td class="fw-semibold">${compName}</td>
                    <td class="text-secondary small font-monospace">${s.subcategoria_nombres || 'Todas las Subcategorías'}</td>
                    <td>${freqBadge}</td>
                    <td>${infoStr}</td>
                    <td class="font-monospace small text-secondary">${lastRunStr}</td>
                    <td class="font-monospace small text-info">${nextRunStr}</td>
                    <td>${statusBadge}</td>
                    <td class="text-end">
                        <button class="btn ${s.is_active ? 'btn-outline-success' : 'btn-outline-secondary'} btn-sm px-2 py-0 me-1" onclick="toggleSchedule(${s.id}, ${s.is_active})" title="${s.is_active ? 'Desactivar Tarea' : 'Activar Tarea'}">
                            <i class="bi ${s.is_active ? 'bi-toggle-on' : 'bi-toggle-off'}"></i>
                        </button>
                        <button class="btn btn-outline-primary btn-sm px-2 py-0 me-1" onclick="editSchedule(${idx})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm px-2 py-0" onclick="deleteSchedule(${s.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    // Populate filter subcategories when company filter changes
    async function onFilterSchedCompanyChange() {
        const compSel = document.getElementById('filterSchedCompany');
        const subcatSel = document.getElementById('filterSchedSubcategory');
        if (!subcatSel) return;
        
        const compId = compSel ? compSel.value : '';
        
        subcatSel.innerHTML = '<option value="">-- Todas las Subcategorías --</option>';
        subcatSel.disabled = true;
        
        let url = '/api/v1/mapeo/categorias';
        if (compId) {
            url += `?company_id=${compId}`;
        }
        
        try {
            console.log("onFilterSchedCompanyChange: fetching categories from:", url);
            const res = await fetch(url, { headers: authHeaders });
            if (res.ok) {
                const cats = await res.json();
                console.log("onFilterSchedCompanyChange: cats loaded:", cats);
                let count = 0;
                
                (cats || []).forEach(cat => {
                    if (cat && cat.subcategorias && cat.subcategorias.length) {
                        cat.subcategorias.forEach(sub => {
                            if (sub && sub.is_active) {
                                const opt = document.createElement('option');
                                opt.value = sub.id;
                                
                                // Include company prefix if viewing all companies
                                const comp = (allCompanies || []).find(c => String(c.id) === String(cat.company_id));
                                const prefix = comp && !compId ? `[${comp.name}] ` : '';
                                
                                opt.textContent = `${prefix}${cat.nombre || ''} → ${sub.nombre || ''}`;
                                subcatSel.appendChild(opt);
                                count++;
                            }
                        });
                    }
                });
                
                console.log("onFilterSchedCompanyChange: subcategories added to dropdown:", count);
                if (count > 0) {
                    subcatSel.disabled = false;
                }
            } else {
                console.error("onFilterSchedCompanyChange: Failed with status:", res.status);
            }
        } catch (e) {
            console.error("Error cargando subcategorías para filtros de programación:", e);
        }
        renderSchedules();
    }


    // Clear schedules filters
    function clearSchedFilters() {
        document.getElementById('filterSchedCompany').value = '';
        onFilterSchedCompanyChange();
    }

    // Toggle Schedule Type inputs in modal
    function toggleSchedInputs() {
        const freq = document.getElementById('schedFrequency').value;
        const divMin = document.getElementById('divMinutes');
        const divTime = document.getElementById('divTime');
        const divDay = document.getElementById('divDayOfWeek');
        
        if (freq === 'MINUTES') {
            divMin.style.display = 'block';
            divTime.style.display = 'none';
        } else {
            divMin.style.display = 'none';
            divTime.style.display = 'flex';
            
            if (freq === 'WEEKLY') {
                divDay.style.display = 'block';
            } else {
                divDay.style.display = 'none';
            }
        }
    }

    async function loadSchedSubcategories(companyId, selectVal = null) {
        const subcatSel = document.getElementById('schedSubcategory');
        subcatSel.innerHTML = '<option value="">-- Todas las Subcategorías (Recomendado) --</option>';
        if (!companyId) {
            subcatSel.disabled = true;
            return;
        }
        subcatSel.disabled = false;
        
        try {
            const res = await fetch(`/api/v1/mapeo/categorias?company_id=${companyId}`, { headers: authHeaders });
            if (res.ok) {
                const cats = await res.json();
                cats.forEach(cat => {
                    if (cat.subcategorias && cat.subcategorias.length) {
                        cat.subcategorias.forEach(sub => {
                            const opt = document.createElement('option');
                            opt.value = sub.id;
                            opt.textContent = `${cat.nombre} → ${sub.nombre}`;
                            subcatSel.appendChild(opt);
                        });
                    }
                });
                if (selectVal) {
                    subcatSel.value = selectVal;
                }
            }
        } catch (e) {
            console.error("Error loading subcategories for scheduler:", e);
        }
    }

    async function onSchedCompanyChange() {
        const compId = document.getElementById('schedCompany').value;
        await loadSchedSubcategories(compId);
    }

    function openScheduleModal() {
        document.getElementById('scheduleForm').reset();
        document.getElementById('editScheduleId').value = '';
        document.getElementById('scheduleModalTitle').innerHTML = '<i class="bi bi-alarm-fill text-primary me-2"></i>Programar Ejecución Automática';
        document.getElementById('schedCompany').disabled = false;
        document.getElementById('schedSubcategory').innerHTML = '<option value="">-- Todas las Subcategorías (Recomendado) --</option>';
        document.getElementById('schedSubcategory').disabled = true;
        toggleSchedInputs();
        scheduleModalObj.show();
    }

    async function editSchedule(index) {
        const s = currentSchedulesList[index];
        if (!s) return;

        document.getElementById('scheduleForm').reset();
        document.getElementById('editScheduleId').value = s.id;
        document.getElementById('scheduleModalTitle').innerHTML = '<i class="bi bi-pencil-fill text-primary me-2"></i>Editar Programación Automática';
        
        document.getElementById('schedCompany').value = s.company_id;
        document.getElementById('schedCompany').disabled = true; // No permitir cambiar de empresa al editar

        let subId = "";
        if (s.params && s.params.subcategorias && s.params.subcategorias.length > 0) {
            subId = s.params.subcategorias[0];
        }

        await loadSchedSubcategories(s.company_id, subId);

        document.getElementById('schedFrequency').value = s.schedule_type;
        toggleSchedInputs();

        if (s.schedule_type === 'MINUTES') {
            document.getElementById('schedMinutesVal').value = s.time_str;
        } else {
            document.getElementById('schedTimeVal').value = s.time_str;
            if (s.schedule_type === 'WEEKLY') {
                document.getElementById('schedDayOfWeek').value = s.day_of_week;
            }
        }

        scheduleModalObj.show();
    }

    async function saveSchedule() {
        const id = document.getElementById('editScheduleId').value;
        const companyId = document.getElementById('schedCompany').value;
        const subcatId = document.getElementById('schedSubcategory').value;
        const freq = document.getElementById('schedFrequency').value;
        
        if (!companyId) {
            showToast('warning', 'Debe seleccionar una empresa');
            return;
        }

        let timeStr = '';
        let dayOfWeek = null;
        
        if (freq === 'MINUTES') {
            timeStr = document.getElementById('schedMinutesVal').value;
        } else {
            timeStr = document.getElementById('schedTimeVal').value;
            if (!timeStr) {
                showToast('warning', 'Debe especificar la hora de ejecución');
                return;
            }
            if (freq === 'WEEKLY') {
                dayOfWeek = document.getElementById('schedDayOfWeek').value;
            }
        }

        const payload = {
            company_id: parseInt(companyId),
            task_type: 'ETL_REALTIME',
            schedule_type: freq,
            time_str: timeStr,
            day_of_week: dayOfWeek,
            params: subcatId ? { subcategorias: [parseInt(subcatId)] } : { subcategorias: [] }
        };

        try {
            let res;
            if (id) {
                res = await fetch(`/api/v1/pipelines/${id}`, {
                    method: 'PUT',
                    headers: authHeaders,
                    body: JSON.stringify(payload)
                });
            } else {
                res = await fetch('/api/v1/pipelines', {
                    method: 'POST',
                    headers: authHeaders,
                    body: JSON.stringify(payload)
                });
            }

            if (res.ok) {
                showToast('success', id ? 'Programación automatizada actualizada' : 'Programación automatizada guardada');
                scheduleModalObj.hide();
                loadSchedules();
            } else {
                const data = await res.json();
                showToast('error', data.detail || 'Fallo al guardar tarea');
            }
        } catch (e) {
            showToast('error', 'Error de red');
        }
    }

    async function deleteSchedule(taskId) {
        Swal.fire({
            title: '¿Eliminar programación?',
            text: 'La tarea dejará de ejecutarse en segundo plano.',
            icon: 'warning',
            showCancelButton: true,
            background: '#161b22',
            color: '#fff',
            confirmButtonColor: '#bc8cff',
            cancelButtonColor: '#30363d',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/api/v1/pipelines/${taskId}`, {
                        method: 'DELETE',
                        headers: authHeaders
                    });
                    if (res.ok) {
                        showToast('success', 'Programación eliminada');
                        loadSchedules();
                    } else {
                        showToast('error', 'Fallo al eliminar');
                    }
                } catch {
                    showToast('error', 'Error de red');
                }
            }
        });
    }

    async function toggleSchedule(taskId, currentlyActive) {
        const newStatus = !currentlyActive;
        const actionText = newStatus ? 'activada' : 'desactivada';
        
        try {
            const res = await fetch(`/api/v1/pipelines/${taskId}`, {
                method: 'PUT',
                headers: {
                    ...authHeaders,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_active: newStatus })
            });
            if (res.ok) {
                showToast('success', `Tarea ${actionText} con éxito`);
                loadSchedules();
            } else {
                const data = await res.json();
                showToast('error', data.detail || 'Fallo al cambiar estado de la tarea');
            }
        } catch (e) {
            showToast('error', 'Error de red');
        }
    }



    // ─── Audit Real-time Logs List & Details ───
    let currentLogsList = [];

    async function loadRealtimeLogs() {
        const statusFilter = document.getElementById('logFilterStatus').value;
        const companyFilter = document.getElementById('logFilterCompany') ? document.getElementById('logFilterCompany').value : '';
        let url = '/api/v1/etl/realtime-logs?limit=50';
        if (statusFilter) {
            url += `&status=${statusFilter}`;
        }
        if (companyFilter) {
            url += `&company_id=${companyFilter}`;
        }
        
        try {
            const res = await fetch(url, { headers: authHeaders });
            currentLogsList = await res.json();
            
            const tbody = document.getElementById('realtimeLogsBody');
            tbody.innerHTML = '';
            
            if (currentLogsList.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="text-center text-secondary py-3">No hay registros de auditoría que coincidan.</td></tr>';
                return;
            }

            // Calculate daily sums for stats panel
            let totalExt = 0;
            let totalGen = 0;
            let totalMig = 0;
            
            const todayStr = new Date().toISOString().split('T')[0];

            currentLogsList.forEach((l, idx) => {
                // Parse date
                const runDateObj = new Date(l.run_date);
                const localDateStr = runDateObj.toLocaleDateString('es-CO') + ' ' + runDateObj.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                
                // Add to stats if ran today
                if (l.run_date && l.run_date.startsWith(todayStr)) {
                    totalExt += l.records_extracted || 0;
                    totalGen += l.records_generated || 0;
                    totalMig += l.records_migrated || 0;
                }

                let statusBadge = '';
                if (l.status === 'SUCCESS') {
                    statusBadge = '<span class="badge bg-success-subtle text-success"><i class="bi bi-check-circle me-1"></i>SUCCESS</span>';
                } else if (l.status === 'WARNING') {
                    statusBadge = '<span class="badge bg-warning-subtle text-warning"><i class="bi bi-exclamation-triangle me-1"></i>WARNING</span>';
                } else {
                    statusBadge = '<span class="badge bg-danger-subtle text-danger"><i class="bi bi-x-circle me-1"></i>ERROR</span>';
                }

                tbody.innerHTML += `
                    <tr>
                        <td class="fw-semibold">${l.company_name}</td>
                        <td class="font-monospace text-secondary" style="font-size: 0.75rem;">${localDateStr}</td>
                        <td class="text-secondary small">${l.subcategorias || 'Todas'}</td>
                        <td>${statusBadge}</td>
                        <td class="text-success font-monospace">+${l.records_extracted}</td>
                        <td class="text-primary font-monospace">+${l.records_generated}</td>
                        <td class="text-warning font-monospace">+${l.records_migrated}</td>
                        <td class="text-truncate text-secondary" style="max-width: 250px;" title="${l.message || ''}">${l.message || ''}</td>
                        <td class="text-end">
                            <button class="btn btn-ghost btn-sm px-2 py-1" onclick="viewLogDetail(${idx})">
                                <i class="bi bi-eye-fill"></i> Detalle
                            </button>
                        </td>
                    </tr>
                `;
            });



        } catch (err) {
            console.error("Error cargando logs de auditoría:", err);
        }
    }

    let modalErrorsData = [];
    let currentLogCompanyId = null;

    function viewLogDetail(index) {
        const log = currentLogsList[index];
        if (!log) return;

        document.getElementById('detailCompany').textContent = log.company_name;
        currentLogCompanyId = log.company_id;
        
        const runDateObj = new Date(log.run_date);
        document.getElementById('detailDate').textContent = runDateObj.toLocaleDateString('es-CO') + ' ' + runDateObj.toLocaleTimeString('es-CO');
        
        const stSpan = document.getElementById('detailStatus');
        if (log.status === 'SUCCESS') {
            stSpan.innerHTML = '<span class="badge bg-success">ÉXITO</span>';
        } else if (log.status === 'WARNING') {
            stSpan.innerHTML = '<span class="badge bg-warning text-dark">ADVERTENCIA / VALIDACIONES</span>';
        } else {
            stSpan.innerHTML = '<span class="badge bg-danger">ERROR CRÍTICO</span>';
        }

        document.getElementById('detailMessage').textContent = log.message || '-';

        // Save data globally in template
        modalErrorsData = log.errors || [];
        
        // Reset modal filters
        document.getElementById('modalSearchInput').value = '';
        document.getElementById('modalStatusFilter').value = '';
        
        renderModalTable();
        logDetailsModalObj.show();
    }

    function renderModalTable() {
        const tbody = document.getElementById('detailErrorsBody');
        tbody.innerHTML = '';
        
        const searchQuery = document.getElementById('modalSearchInput').value.toLowerCase().trim();
        const statusFilter = document.getElementById('modalStatusFilter').value;

        // Filter data on client side
        const filtered = modalErrorsData.filter(e => {
            if (statusFilter && e.status !== statusFilter) return false;
            
            if (searchQuery) {
                const step = String(e.step || '').toLowerCase();
                const table = String(e.table || '').toLowerCase();
                const col = String(e.column || '').toLowerCase();
                const ref = String(e.reference || '').toLowerCase();
                const err = String(e.error || '').toLowerCase();
                const subcat = String(e.subcategoria_nombre || '').toLowerCase();
                
                if (!step.includes(searchQuery) &&
                    !table.includes(searchQuery) &&
                    !col.includes(searchQuery) &&
                    !ref.includes(searchQuery) &&
                    !err.includes(searchQuery) &&
                    !subcat.includes(searchQuery)) {
                    return false;
                }
            }
            return true;
        });

        document.getElementById('detailLogCount').textContent = filtered.length;

        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-secondary py-3">Ningún registro coincide con los filtros.</td></tr>';
            return;
        }

        filtered.forEach(e => {
            let stepLabel = '';
            let stepClass = 'bg-secondary';
            if (e.step === 'ETL') {
                stepLabel = 'Extracción';
                stepClass = 'bg-info-subtle text-info';
            } else if (e.step === 'GENERATION') {
                stepLabel = 'Generación';
                stepClass = 'bg-primary-subtle text-primary';
            } else if (e.step === 'VALIDATION') {
                stepLabel = 'Validación';
                stepClass = 'bg-warning-subtle text-warning';
            } else if (e.step === 'MIGRATION') {
                stepLabel = 'Migración';
                stepClass = 'bg-danger-subtle text-danger';
            } else {
                stepLabel = e.step || 'Sistema';
            }

            const stepBadge = `<span class="badge ${stepClass}">${stepLabel}</span>`;
            
            const statusBadge = e.status === 'SUCCESS' 
                ? '<span class="badge bg-success-subtle text-success"><i class="bi bi-check-circle me-1"></i>Éxito</span>'
                : '<span class="badge bg-danger-subtle text-danger"><i class="bi bi-x-circle me-1"></i>Fallo</span>';

            const refStr = e.reference || '-';
            
            let tableStr = e.table || '-';
            if (e.column) tableStr += ` · Campo: <code>${e.column}</code>`;

            const errorClass = e.status === 'SUCCESS' ? 'text-secondary' : 'text-danger fw-semibold';
            const errorStr = e.error || '-';

            const reprocessBtn = `
                <button class="btn btn-outline-primary btn-sm px-2 py-0" style="font-size:0.75rem;" onclick="reprocessRow(${currentLogCompanyId}, '${e.step || ''}', '${e.table || ''}', '${e.reference || ''}', ${e.subcategoria_id || 'null'}, this)">
                    <i class="bi bi-arrow-clockwise"></i> Reprocesar
                </button>
            `;

            tbody.innerHTML += `
                <tr>
                    <td>${stepBadge}</td>
                    <td class="small text-light">${e.subcategoria_nombre || '-'}</td>
                    <td class="font-monospace small">${refStr}</td>
                    <td class="small">${tableStr}</td>
                    <td>${statusBadge}</td>
                    <td class="${errorClass} small">${errorStr}</td>
                    <td class="text-end">${reprocessBtn}</td>
                </tr>
            `;
        });
    }

    function filterModalTable() {
        renderModalTable();
    }

    async function reprocessRow(companyId, step, table, reference, subcatId, btn) {
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';

        const payload = {
            company_id: companyId,
            step: step,
            table: table,
            reference: reference,
            subcategoria_id: subcatId
        };

        try {
            const res = await fetch('/api/v1/etl/reprocess-row', {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            
            if (res.ok && data.status === 'SUCCESS') {
                showToast('success', data.message || 'Reprocesado correctamente');
                
                // Update local model array so changes are visible instantly
                modalErrorsData.forEach(e => {
                    if (e.reference === reference && e.step === step) {
                        e.status = 'SUCCESS';
                        e.error = data.message || 'Reprocesado exitosamente.';
                    }
                });
                
                renderModalTable();
                loadRealtimeLogs(); // Refresh background counts
            } else {
                showToast('error', data.detail || 'Fallo al reprocesar fila');
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        } catch (err) {
            showToast('error', 'Error de red');
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }

    // ─── Visor de Asientos en Staging JS ───
    let activeVisorTab = 'staging';

    function switchVisorTab(tab) {
        activeVisorTab = tab;
        const tabStaging = document.getElementById('tabStaging');
        const tabRaw = document.getElementById('tabRaw');
        const filtersStaging = document.getElementById('visorStagingFilters');
        const filtersRaw = document.getElementById('visorRawFilters');
        const panelStaging = document.getElementById('panelStagingContainer');
        const panelRaw = document.getElementById('panelRawContainer');

        if (tab === 'staging') {
            tabStaging.classList.add('active');
            tabStaging.classList.remove('text-secondary');
            tabStaging.classList.add('text-light');
            tabRaw.classList.remove('active');
            tabRaw.classList.remove('text-light');
            tabRaw.classList.add('text-secondary');

            filtersStaging.classList.remove('d-none');
            filtersRaw.classList.add('d-none');
            panelStaging.classList.remove('d-none');
            panelRaw.classList.add('d-none');

            loadStagingRows(visorSkip);
        } else {
            tabRaw.classList.add('active');
            tabRaw.classList.remove('text-secondary');
            tabRaw.classList.add('text-light');
            tabStaging.classList.remove('active');
            tabStaging.classList.remove('text-light');
            tabStaging.classList.add('text-secondary');

            filtersRaw.classList.remove('d-none');
            filtersStaging.classList.add('d-none');
            panelRaw.classList.remove('d-none');
            panelStaging.classList.add('d-none');

            loadRawTablesList();
        }
    }

    async function loadRawTablesList() {
        const compId = document.getElementById('visorCompany').value;
        const select = document.getElementById('visorRawTable');
        if (!compId) return;

        select.innerHTML = '<option value="">-- Seleccionar Tabla --</option>';
        select.disabled = true;

        try {
            const res = await fetch(`/api/v1/etl/raw-tables/${compId}`, { headers: authHeaders });
            if (res.ok) {
                const tables = await res.json();
                tables.forEach(t => {
                    const opt = new Option(`${t.table_name} (${t.table_dest})`, t.table_dest);
                    select.add(opt);
                });
                if (tables.length > 0) {
                    select.disabled = false;
                }
            }
        } catch (e) {
            console.error("Error loading raw tables:", e);
        }
    }

    let rawSkip = 0;
    const rawLimit = 50;

    async function loadRawRows(skip = 0) {
        rawSkip = skip;
        const compId = document.getElementById('visorCompany').value;
        const tableDest = document.getElementById('visorRawTable').value;
        if (!compId) return;

        const header = document.getElementById('visorRawTableHeader');
        const tbody = document.getElementById('visorRawTableBody');

        if (!tableDest) {
            header.innerHTML = '<tr><th>Columna 1</th><th>Columna 2</th><th>Columna 3</th></tr>';
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-secondary py-4">Seleccione una tabla para cargar los datos extraídos.</td></tr>';
            document.getElementById('visorRawRangeStart').textContent = '0';
            document.getElementById('visorRawRangeEnd').textContent = '0';
            document.getElementById('visorRawTotalCount').textContent = '0';
            document.getElementById('btnVisorRawPrev').disabled = true;
            document.getElementById('btnVisorRawNext').disabled = true;
            return;
        }

        tbody.innerHTML = `<tr><td colspan="10" class="text-center text-secondary py-4"><span class="spinner-sm"></span> Cargando datos extraídos de la tabla '${tableDest}'...</td></tr>`;

        const search = document.getElementById('visorRawSearch').value;
        let url = `/api/v1/etl/raw-table-data/${compId}/${tableDest}?skip=${rawSkip}&limit=${rawLimit}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        try {
            const res = await fetch(url, { headers: authHeaders });
            if (!res.ok) {
                const errData = await res.json();
                tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger py-4">Error: ${errData.detail || 'Fallo al obtener datos'}</td></tr>`;
                return;
            }

            const data = await res.json();
            const cols = data.columns || [];

            header.innerHTML = '';
            const trHead = document.createElement('tr');
            cols.forEach(c => {
                const th = document.createElement('th');
                th.textContent = c;
                trHead.appendChild(th);
            });
            header.appendChild(trHead);

            tbody.innerHTML = '';
            const rows = data.items || [];

            if (rows.length === 0) {
                tbody.innerHTML = `<tr><td colspan="${cols.length || 1}" class="text-center text-secondary py-4">No se encontraron registros.</td></tr>`;
                document.getElementById('visorRawRangeStart').textContent = '0';
                document.getElementById('visorRawRangeEnd').textContent = '0';
                document.getElementById('visorRawTotalCount').textContent = '0';
                document.getElementById('btnVisorRawPrev').disabled = true;
                document.getElementById('btnVisorRawNext').disabled = true;
                return;
            }

            rows.forEach(row => {
                const tr = document.createElement('tr');
                cols.forEach(c => {
                    const td = document.createElement('td');
                    const val = row[c];
                    if (val === null || val === undefined) {
                        td.innerHTML = '<span class="text-muted small">NULL</span>';
                    } else if (typeof val === 'number') {
                        td.textContent = val.toString();
                        td.className = 'font-monospace text-end';
                    } else if (c.toLowerCase().includes('id') || c.toLowerCase().includes('codigo') || c.toLowerCase().includes('nro') || c.toLowerCase().includes('ruc') || c.toLowerCase().includes('numero')) {
                        td.textContent = val;
                        td.className = 'font-monospace';
                    } else {
                        td.textContent = val;
                    }
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });

            const start = rawSkip + 1;
            const end = rawSkip + rows.length;
            document.getElementById('visorRawRangeStart').textContent = start;
            document.getElementById('visorRawRangeEnd').textContent = end;
            document.getElementById('visorRawTotalCount').textContent = data.total;

            document.getElementById('btnVisorRawPrev').disabled = (rawSkip === 0);
            document.getElementById('btnVisorRawNext').disabled = (end >= data.total);
        } catch (err) {
            console.error("Error loading raw rows:", err);
            tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger py-4">Error de red al conectar con el servidor.</td></tr>`;
        }
    }

    function changeRawPage(direction) {
        const newSkip = rawSkip + (direction * rawLimit);
        if (newSkip >= 0) {
            loadRawRows(newSkip);
        }
    }

    async function onVisorCompanyChange() {
        const compId = document.getElementById('visorCompany').value;
        const subcatSel = document.getElementById('visorSubcategory');
        subcatSel.innerHTML = '<option value="">-- Todas --</option>';
        subcatSel.disabled = true;

        // Limpiar controles de tablas raw
        document.getElementById('visorRawTable').innerHTML = '<option value="">-- Seleccionar Tabla --</option>';
        document.getElementById('visorRawTable').disabled = true;
        document.getElementById('visorRawTableHeader').innerHTML = '<tr><th>Columna 1</th><th>Columna 2</th><th>Columna 3</th></tr>';
        document.getElementById('visorRawTableBody').innerHTML = '<tr><td colspan="3" class="text-center text-secondary py-4">Seleccione una tabla para cargar los datos extraídos.</td></tr>';
        document.getElementById('visorRawRangeStart').textContent = '0';
        document.getElementById('visorRawRangeEnd').textContent = '0';
        document.getElementById('visorRawTotalCount').textContent = '0';
        document.getElementById('btnVisorRawPrev').disabled = true;
        document.getElementById('btnVisorRawNext').disabled = true;
        
        if (!compId) {
            document.getElementById('visorTableBody').innerHTML = '<tr><td colspan="10" class="text-center text-secondary py-4">Seleccione una empresa para cargar los datos de staging.</td></tr>';
            document.getElementById('visorRangeStart').textContent = '0';
            document.getElementById('visorRangeEnd').textContent = '0';
            document.getElementById('visorTotalCount').textContent = '0';
            document.getElementById('btnVisorPrev').disabled = true;
            document.getElementById('btnVisorNext').disabled = true;
            return;
        }
        
        try {
            const res = await fetch(`/api/v1/mapeo/categorias?company_id=${compId}`, { headers: authHeaders });
            const categories = await res.json();
            
            let count = 0;
            categories.forEach(cat => {
                cat.subcategorias.forEach(sub => {
                    if (sub.is_active) {
                        const opt = new Option(sub.nombre, sub.id);
                        subcatSel.add(opt);
                        count++;
                    }
                });
            });
            
            if (count > 0) {
                subcatSel.disabled = false;
            }
        } catch (e) {
            console.error("Error loading subcategories for visor:", e);
        }

        await loadRawTablesList();
        
        if (activeVisorTab === 'staging') {
            loadStagingRows(0);
        } else {
            loadRawRows(0);
        }
    }

    let visorSkip = 0;
    const visorLimit = 50;

    async function loadStagingRows(skip = 0) {
        visorSkip = skip;
        const compId = document.getElementById('visorCompany').value;
        if (!compId) return;

        const tbody = document.getElementById('visorTableBody');
        tbody.innerHTML = '<tr><td colspan="11" class="text-center text-secondary py-4"><span class="spinner-sm"></span> Cargando asientos de staging...</td></tr>';

        const subcatId = document.getElementById('visorSubcategory').value;
        const periodo = document.getElementById('visorPeriodo').value;
        const mes = document.getElementById('visorMes').value;
        const estado = document.getElementById('visorEstado').value;
        const search = document.getElementById('visorSearch').value;

        let url = `/api/v1/mapeo/cf-diariol?company_id=${compId}&skip=${visorSkip}&limit=${visorLimit}`;
        if (subcatId) url += `&subcategoria_id=${subcatId}`;
        if (periodo) url += `&periodo=${periodo}`;
        if (mes) url += `&mes=${mes}`;
        if (estado) url += `&estado=${estado}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        try {
            const res = await fetch(url, { headers: authHeaders });
            const data = res.ok ? await res.json() : { total: 0, items: [] };
            
            tbody.innerHTML = '';
            currentVisorItems = data.items || [];
            
            if (data.items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="11" class="text-center text-secondary py-4">No se encontraron asientos en staging con los filtros seleccionados.</td></tr>';
                document.getElementById('visorRangeStart').textContent = '0';
                document.getElementById('visorRangeEnd').textContent = '0';
                document.getElementById('visorTotalCount').textContent = '0';
                document.getElementById('btnVisorPrev').disabled = true;
                document.getElementById('btnVisorNext').disabled = true;
                return;
            }

            data.items.forEach(r => {
                let stateBadge = '';
                if (r.estado === 'MIGRADO') {
                    stateBadge = '<span class="badge bg-success-subtle text-success"><i class="bi bi-check-circle me-1"></i>MIGRADO</span>';
                } else if (r.estado === 'PENDIENTE' || r.estado === '1') {
                    stateBadge = '<span class="badge bg-warning-subtle text-warning"><i class="bi bi-clock me-1"></i>PENDIENTE</span>';
                } else {
                    stateBadge = `<span class="badge bg-danger-subtle text-danger"><i class="bi bi-exclamation-triangle me-1"></i>${r.estado || 'PENDIENTE'}</span>`;
                }

                const actionsHtml = `
                    <div class="d-flex gap-1 justify-content-end">
                        <button class="btn btn-outline-info btn-sm px-2 py-0" style="font-size:0.7rem;" onclick="viewStagingRowDetail(${r.id})">
                            <i class="bi bi-eye"></i> Ver Fila
                        </button>
                        <button class="btn btn-outline-info btn-sm px-2 py-0" style="font-size:0.7rem;" onclick="viewRawRowDetail(${compId}, ${r.subcategoria_id}, '${r.idcontrol}')" ${r.idcontrol ? '' : 'disabled'} title="Ver fila original en base intermedia">
                            <i class="bi bi-database"></i> Origen
                        </button>
                        <button class="btn btn-outline-primary btn-sm px-2 py-0" style="font-size:0.7rem;" onclick="reprocessVisorRow(${compId}, ${r.subcategoria_id}, '${r.nasiento}', this)">
                            <i class="bi bi-arrow-clockwise"></i> Reprocesar
                        </button>
                        <button class="btn btn-outline-warning btn-sm px-2 py-0" style="font-size:0.7rem;" onclick="openReextractModal(${compId}, ${r.subcategoria_id}, '${r.subcategoria_nombre.replace(/'/g, "\\'")}', '${r.nasiento}')">
                            <i class="bi bi-arrow-repeat"></i> Reextraer
                        </button>
                    </div>
                `;

                tbody.innerHTML += `
                    <tr>
                        <td class="font-monospace text-secondary" style="font-size:0.75rem;">${r.cper}-${r.cmes}</td>
                        <td class="small" title="${r.subcategoria_nombre}">${r.subcategoria_nombre}</td>
                        <td class="fw-semibold text-light font-monospace">${r.nasiento}</td>
                        <td class="text-secondary font-monospace" style="font-size:0.75rem;">${r.nidlin}</td>
                        <td class="font-monospace text-secondary" style="font-size:0.75rem;">${r.idcontrol || '-'}</td>
                        <td class="font-monospace text-info" style="font-size:0.75rem;">${r.ccodcue}</td>
                        <td class="text-end font-monospace text-success">${r.ndebe > 0 ? r.ndebe.toFixed(2) : '-'}</td>
                        <td class="text-end font-monospace text-danger">${r.nhaber > 0 ? r.nhaber.toFixed(2) : '-'}</td>
                        <td class="text-truncate text-secondary small" style="max-width: 250px;" title="${r.cglosa || ''}">${r.cglosa || ''}</td>
                        <td>${stateBadge}</td>
                        <td class="text-end">${actionsHtml}</td>
                    </tr>
                `;
            });

            const start = visorSkip + 1;
            const end = visorSkip + data.items.length;
            document.getElementById('visorRangeStart').textContent = start;
            document.getElementById('visorRangeEnd').textContent = end;
            document.getElementById('visorTotalCount').textContent = data.total;

            document.getElementById('btnVisorPrev').disabled = (visorSkip === 0);
            document.getElementById('btnVisorNext').disabled = (end >= data.total);

        } catch (err) {
            console.error("Error loading visor staging rows:", err);
            tbody.innerHTML = '<tr><td colspan="11" class="text-center text-danger py-4">Error al cargar datos del servidor.</td></tr>';
        }
    }

    function changeVisorPage(direction) {
        const newSkip = visorSkip + (direction * visorLimit);
        if (newSkip >= 0) {
            loadStagingRows(newSkip);
        }
    }

    async function reprocessVisorRow(companyId, subcatId, nasiento, btn) {
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';

        const payload = {
            company_id: companyId,
            step: 'MIGRATION',
            table: 'cf_diariol',
            reference: `Asiento ${nasiento}`,
            subcategoria_id: subcatId
        };

        try {
            const res = await fetch('/api/v1/etl/reprocess-row', {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            
            if (res.ok && data.status === 'SUCCESS') {
                showToast('success', data.message || `Asiento ${nasiento} remigrado correctamente`);
                loadStagingRows(visorSkip); // Reload current page
                loadRealtimeLogs(); // Refresh background counts
            } else {
                showToast('error', data.detail || 'Fallo al reprocesar asiento');
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        } catch (err) {
            showToast('error', 'Error de red');
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }

    function viewStagingRowDetail(rowId) {
        const r = currentVisorItems.find(item => item.id === rowId);
        if (!r) return;
        
        // Buscar errores/advertencias de validación en currentLogsList correspondientes a este registro
        let foundError = null;
        if (typeof currentLogsList !== 'undefined' && currentLogsList) {
            for (const log of currentLogsList) {
                if (log.errors && log.errors.length > 0) {
                    const nasientoStr = String(r.nasiento).toLowerCase();
                    const nidlinStr = String(r.nidlin).toLowerCase();
                    const idcontrolStr = String(r.idcontrol || '').toLowerCase();
                    
                    foundError = log.errors.find(e => {
                        if (String(e.subcategoria_id) !== String(r.subcategoria_id)) {
                            return false;
                        }
                        const refLower = String(e.reference || '').toLowerCase();
                        // Coincidencia por asiento/línea o idcontrol
                        return (
                            refLower.includes("asiento " + nasientoStr) ||
                            refLower === nasientoStr ||
                            (idcontrolStr && refLower.includes(idcontrolStr)) ||
                            (idcontrolStr && idcontrolStr.includes(refLower))
                        );
                    });
                    if (foundError) break;
                }
            }
        }
        
        // Poblar banner de estado
        const statusInfoDiv = document.getElementById('stagingRowStatusInfo');
        if (statusInfoDiv) {
            statusInfoDiv.innerHTML = '';
            
            let statusHtml = '';
            if (r.estado === 'MIGRADO') {
                statusHtml = `
                    <div class="alert alert-success border-0 bg-success-subtle text-success p-3 rounded-3 mb-0 d-flex align-items-start gap-3">
                        <i class="bi bi-check-circle-fill fs-4 mt-0"></i>
                        <div>
                            <strong class="d-block mb-1">Registro Migrado</strong>
                            <span class="small opacity-75">Este asiento ha sido procesado y transferido correctamente al sistema Contasis final. No requiere ninguna acción adicional.</span>
                        </div>
                    </div>
                `;
            } else if (foundError) {
                const fieldInfo = foundError.column ? `<br><strong>Campo / Columna:</strong> <code>${foundError.column}</code>` : '';
                statusHtml = `
                    <div class="alert alert-danger border-0 bg-danger-subtle text-danger p-3 rounded-3 mb-0 d-flex align-items-start gap-3">
                        <i class="bi bi-exclamation-triangle-fill fs-4 mt-0"></i>
                        <div>
                            <strong class="d-block mb-1">Bloqueado por Validación Fallida</strong>
                            <span class="small">
                                <strong>Paso:</strong> ${foundError.step || 'Validación'}<br>
                                <strong>Detalle del error:</strong> ${foundError.error || 'Desconocido'}${fieldInfo}
                                <br><br>
                                <span class="d-block opacity-75 mt-1">Este asiento se mantiene en staging como <strong>PENDIENTE</strong> debido a esta falla. Debe corregir las equivalencias contables o el origen y volver a "Reprocesar".</span>
                            </span>
                        </div>
                    </div>
                `;
            } else if (r.estado === 'PENDIENTE' || r.estado === '1') {
                statusHtml = `
                    <div class="alert alert-warning border-0 bg-warning-subtle text-warning p-3 rounded-3 mb-0 d-flex align-items-start gap-3">
                        <i class="bi bi-clock-fill fs-4 mt-0"></i>
                        <div>
                            <strong class="d-block mb-1">Listo para Migrar (Pendiente)</strong>
                            <span class="small">Este asiento se ha generado en Staging sin errores de validación, pero aún no se ha transferido a Contasis final. Está esperando la ejecución automática programada o la migración manual.</span>
                        </div>
                    </div>
                `;
            } else {
                statusHtml = `
                    <div class="alert alert-info border-0 bg-info-subtle text-info p-3 rounded-3 mb-0 d-flex align-items-start gap-3">
                        <i class="bi bi-info-circle-fill fs-4 mt-0"></i>
                        <div>
                            <strong class="d-block mb-1">Estado: ${r.estado || 'Desconocido'}</strong>
                            <span class="small opacity-75">El registro se encuentra en estado '${r.estado}'. Puede hacer clic en reprocesar para intentar migrarlo nuevamente.</span>
                        </div>
                    </div>
                `;
            }
            statusInfoDiv.innerHTML = statusHtml;
        }

        const tbody = document.getElementById('stagingRowModalBody');
        tbody.innerHTML = '';
        
        const keys = Object.keys(r).sort();
        keys.forEach(k => {
            if (k === 'subcategoria_nombre') return;
            const val = r[k];
            const valDisplay = (val === null || val === undefined) ? '<span class="text-secondary">NULL</span>' : val;
            tbody.innerHTML += `
                <tr>
                    <td class="font-monospace text-info small" style="width: 35%;">${k}</td>
                    <td class="font-monospace small text-light">${valDisplay}</td>
                </tr>
            `;
        });
        
        stagingRowModalObj.show();
    }

    async function viewRawRowDetail(companyId, subcatId, idcontrol) {
        if (!idcontrol) {
            showToast('warning', 'Este registro no posee ID de control.');
            return;
        }

        try {
            const url = `/api/v1/etl/raw-row-detail?company_id=${companyId}&subcategoria_id=${subcatId}&idcontrol=${encodeURIComponent(idcontrol)}`;
            const res = await fetch(url, { headers: authHeaders });
            if (!res.ok) {
                const errData = await res.json();
                showToast('error', errData.detail || 'No se pudo obtener el registro de la base intermedia.');
                return;
            }

            const data = await res.json();
            document.getElementById('rawRowDetailTable').textContent = data.source_table || 'Tabla Origen';
            document.getElementById('rawRowDetailIdControl').textContent = idcontrol;

            const headerRow = document.getElementById('rawRowDetailHeader');
            const bodyRow = document.getElementById('rawRowDetailBody');
            
            headerRow.innerHTML = '';
            bodyRow.innerHTML = '';

            const headers = data.headers || [];
            const rowVal = data.row || {};

            if (headers.length === 0) {
                bodyRow.innerHTML = '<tr><td class="text-center text-secondary py-3">No hay columnas para mostrar.</td></tr>';
                rawRowDetailModalObj.show();
                return;
            }

            let headHtml = '<tr>';
            let bodyHtml = '<tr>';

            headers.forEach(h => {
                headHtml += `<th class="font-monospace small text-info px-3 py-2 border-bottom border-secondary text-nowrap" style="background: rgba(255,255,255,0.01);">${h}</th>`;
                const val = rowVal[h];
                const valDisplay = (val === null || val === undefined) ? '<span class="text-secondary small">NULL</span>' : val;
                bodyHtml += `<td class="font-monospace small text-light px-3 py-2 border-bottom border-secondary text-nowrap">${valDisplay}</td>`;
            });

            headHtml += '</tr>';
            bodyHtml += '</tr>';

            headerRow.innerHTML = headHtml;
            bodyRow.innerHTML = bodyHtml;

            rawRowDetailModalObj.show();
        } catch (err) {
            console.error("Error al cargar detalle horizontal:", err);
            showToast('error', 'Fallo al consultar el registro original.');
        }
    }

    // ─── Control de Migrados JS Functions ───
    let migratedSkip = 0;
    const migratedLimit = 50;
    let currentMigratedItems = [];

    async function onMigratedCompanyChange() {
        const compId = document.getElementById('migratedCompany').value;
        const subcatSel = document.getElementById('migratedSubcategory');
        subcatSel.innerHTML = '<option value="">-- Todas --</option>';
        subcatSel.disabled = true;

        if (!compId) {
            loadMigratedRows(0);
            return;
        }

        try {
            const res = await fetch(`/api/v1/mapeo/categorias?company_id=${compId}`, { headers: authHeaders });
            if (res.ok) {
                const cats = await res.json();
                cats.forEach(cat => {
                    if (cat.subcategorias) {
                        cat.subcategorias.forEach(sub => {
                            const opt = document.createElement('option');
                            opt.value = sub.id;
                            opt.textContent = `${cat.nombre} → ${sub.nombre}${sub.is_active ? '' : ' (Inactivo)'}`;
                            subcatSel.appendChild(opt);
                        });
                    }
                });
                subcatSel.disabled = false;
            }
        } catch (err) {
            console.error("Error cargando subcategorías para migrados:", err);
        }
        
        loadMigratedRows(0);
    }

    async function loadMigratedRows(skip = 0) {
        migratedSkip = skip;
        
        let compId = document.getElementById('migratedCompany').value;
        if (!compId) {
            const syncCompId = document.getElementById('visorCompany').value || document.getElementById('summaryCompany').value;
            if (syncCompId) {
                document.getElementById('migratedCompany').value = syncCompId;
                compId = syncCompId;
                onMigratedCompanyChange();
                return;
            }
        }
        
        const tbody = document.getElementById('migratedTableBody');
        
        if (!compId) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-secondary py-4">Seleccione una empresa para cargar los datos migrados.</td></tr>';
            document.getElementById('migratedRangeStart').textContent = '0';
            document.getElementById('migratedRangeEnd').textContent = '0';
            document.getElementById('migratedTotalCount').textContent = '0';
            document.getElementById('btnMigratedPrev').disabled = true;
            document.getElementById('btnMigratedNext').disabled = true;
            return;
        }

        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-secondary py-4"><span class="spinner-sm"></span> Cargando datos migrados...</td></tr>';

        const subcatId = document.getElementById('migratedSubcategory').value;
        const periodo = document.getElementById('migratedPeriodo').value;
        const search = document.getElementById('migratedSearch').value;

        let url = `/api/v1/mapeo/cf-diariol?company_id=${compId}&estado=MIGRADO&skip=${migratedSkip}&limit=${migratedLimit}`;
        if (subcatId) url += `&subcategoria_id=${subcatId}`;
        if (periodo) url += `&periodo=${periodo}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        try {
            const res = await fetch(url, { headers: authHeaders });
            const data = res.ok ? await res.json() : { total: 0, items: [] };

            tbody.innerHTML = '';
            currentMigratedItems = data.items || [];

            if (data.items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" class="text-center text-secondary py-4">No se encontraron registros migrados con los filtros seleccionados.</td></tr>';
                document.getElementById('migratedRangeStart').textContent = '0';
                document.getElementById('migratedRangeEnd').textContent = '0';
                document.getElementById('migratedTotalCount').textContent = '0';
                document.getElementById('btnMigratedPrev').disabled = true;
                document.getElementById('btnMigratedNext').disabled = true;
                return;
            }

            data.items.forEach(r => {
                const actionsHtml = `
                    <div class="d-flex gap-1 justify-content-end">
                        <button class="btn btn-outline-info btn-sm px-2 py-0" style="font-size:0.7rem;" onclick="viewStagingRowDetail(${r.id})">
                            <i class="bi bi-eye"></i> Ver
                        </button>
                        <button class="btn btn-outline-danger btn-sm px-2 py-0" style="font-size:0.7rem;" onclick="resetMigratedRow(${compId}, ${r.subcategoria_id}, '${r.idcontrol}', '${r.nasiento}')">
                            <i class="bi bi-arrow-counterclockwise"></i> Reiniciar
                        </button>
                    </div>
                `;

                tbody.innerHTML += `
                    <tr>
                        <td class="font-monospace text-secondary" style="font-size:0.75rem;">${r.cper}-${r.cmes}</td>
                        <td class="small" title="${r.subcategoria_nombre}">${r.subcategoria_nombre}</td>
                        <td class="fw-semibold text-light font-monospace">${r.nasiento}</td>
                        <td class="text-secondary font-monospace" style="font-size:0.75rem;">${r.nidlin}</td>
                        <td class="font-monospace text-secondary" style="font-size:0.75rem;">${r.idcontrol || '-'}</td>
                        <td class="font-monospace text-info" style="font-size:0.75rem;">${r.ccodcue}</td>
                        <td class="text-end font-monospace text-success">${r.ndebe > 0 ? r.ndebe.toFixed(2) : '-'}</td>
                        <td class="text-end font-monospace text-danger">${r.nhaber > 0 ? r.nhaber.toFixed(2) : '-'}</td>
                        <td class="text-truncate text-secondary small" style="max-width: 250px;" title="${r.cglosa || ''}">${r.cglosa || ''}</td>
                        <td class="text-end">${actionsHtml}</td>
                    </tr>
                `;
            });

            const start = migratedSkip + 1;
            const end = migratedSkip + data.items.length;
            document.getElementById('migratedRangeStart').textContent = start;
            document.getElementById('migratedRangeEnd').textContent = end;
            document.getElementById('migratedTotalCount').textContent = data.total;

            document.getElementById('btnMigratedPrev').disabled = (migratedSkip === 0);
            document.getElementById('btnMigratedNext').disabled = (end >= data.total);

        } catch (err) {
            console.error("Error al cargar registros migrados:", err);
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-danger py-4">Error al cargar la información.</td></tr>';
        }
    }

    function changeMigratedPage(direction) {
        const newSkip = migratedSkip + (direction * migratedLimit);
        if (newSkip >= 0) {
            loadMigratedRows(newSkip);
        }
    }

    async function resetMigratedRow(companyId, subcatId, idcontrol, nasiento) {
        if (!idcontrol) {
            showToast('error', 'El registro no posee ID de control para ser reiniciado.');
            return;
        }

        const confirmRes = await Swal.fire({
            title: '¿Confirmar Reinicio?',
            html: `
                <div class="text-start small">
                    <p class="mb-2 text-warning"><i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Atención:</strong> Esto devolverá el registro en staging local a estado <strong>PENDIENTE</strong>.</p>
                    <ul>
                        <li><strong>Asiento:</strong> ${nasiento}</li>
                        <li><strong>ID Control:</strong> ${idcontrol}</li>
                    </ul>
                    <p class="mb-0 text-danger-subtle"><i class="bi bi-shield-lock-fill me-2"></i>Por seguridad, <strong>no se borrará nada en Contasis Final</strong>. Deberá limpiarlo manualmente en su base final si es necesario.</p>
                </div>
            `,
            icon: 'warning',
            background: '#161b22',
            color: '#fff',
            showCancelButton: true,
            confirmButtonColor: '#ff7b72',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, reiniciar en staging',
            cancelButtonText: 'Cancelar'
        });

        if (!confirmRes.isConfirmed) return;

        try {
            const res = await fetch('/api/v1/etl/reset-migrated-row', {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify({
                    company_id: companyId,
                    subcategoria_id: subcatId,
                    idcontrol: idcontrol
                })
            });

            const data = await res.json();
            if (res.ok && data.status === 'SUCCESS') {
                showToast('success', 'Registro reiniciado correctamente.');
                loadMigratedRows(migratedSkip);
                if (typeof loadStagingSummary === 'function') loadStagingSummary();
                if (typeof loadRealtimeLogs === 'function') loadRealtimeLogs();
                if (activeVisorTab === 'staging') {
                    if (typeof loadStagingRows === 'function') loadStagingRows(visorSkip);
                }
            } else {
                showToast('error', data.detail || 'Fallo al reiniciar el registro.');
            }
        } catch (err) {
            console.error("Error al reiniciar registro:", err);
            showToast('error', 'Error de red.');
        }
    }

    // ─── Control de Correlativos JS ───
    let currentCorrelativosList = [];

    async function onCorrelativoFilterCompanyChange() {
        const compId = document.getElementById('correlativoFilterCompany').value;
        const subcatSel = document.getElementById('correlativoFilterSubcategory');
        subcatSel.innerHTML = '<option value="">-- Todas las Subcategorías --</option>';
        subcatSel.disabled = true;

        if (!compId) {
            loadCorrelativos();
            return;
        }

        try {
            const res = await fetch(`/api/v1/mapeo/categorias?company_id=${compId}`, { headers: authHeaders });
            if (res.ok) {
                const cats = await res.json();
                let count = 0;
                cats.forEach(cat => {
                    if (cat.subcategorias) {
                        cat.subcategorias.forEach(sub => {
                            const opt = document.createElement('option');
                            opt.value = sub.id;
                            opt.textContent = `${cat.nombre} → ${sub.nombre}${sub.is_active ? '' : ' (Inactivo)'}`;
                            opt.setAttribute('data-period-col', sub.col_origen_periodo || '');
                            opt.setAttribute('data-mes-col', sub.col_origen_mes || '');
                            opt.setAttribute('data-generate-headers', sub.generate_headers !== false ? 'true' : 'false');
                            subcatSel.appendChild(opt);
                            count++;
                        });
                    }
                });
                if (count > 0) subcatSel.disabled = false;
            }
        } catch (e) {
            console.error("Error cargando subcategorías para filtro:", e);
        }
        
        loadCorrelativos();
    }

    async function loadCorrelativos() {
        const compId = document.getElementById('correlativoFilterCompany').value;
        const tbody = document.getElementById('correlativosTableBody');
        
        if (!compId) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-secondary py-4">Seleccione una empresa para cargar los correlativos.</td></tr>';
            return;
        }

        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-secondary py-4"><span class="spinner-sm"></span> Cargando correlativos...</td></tr>';
        
        try {
            let url = `/api/v1/etl/correlativos?company_id=${compId}`;
            const res = await fetch(url, { headers: authHeaders });
            currentCorrelativosList = res.ok ? await res.json() : [];
            
            renderCorrelativos();
        } catch (err) {
            console.error("Error cargando correlativos:", err);
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger py-4">Error al cargar correlativos.</td></tr>';
        }
    }

    function renderCorrelativos() {
        const tbody = document.getElementById('correlativosTableBody');
        if (!tbody) return;

        const subcatFilterId = document.getElementById('correlativoFilterSubcategory').value;
        const searchVal = document.getElementById('correlativoSearch').value.toLowerCase().trim();
        const sortVal = document.getElementById('correlativoSort').value;

        // 1. Filter elements
        let filtered = currentCorrelativosList.filter(c => {
            // Dropdown subcategory filter
            if (subcatFilterId && String(c.subcategoria_id) !== String(subcatFilterId)) {
                return false;
            }
            // Search text filter (by subcategory name)
            if (searchVal && !c.subcategoria_name.toLowerCase().includes(searchVal)) {
                return false;
            }
            return true;
        });

        tbody.innerHTML = '';
        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-secondary py-4">No hay correlativos registrados que coincidan con los filtros.</td></tr>';
            return;
        }

        // 2. Group by subcategoria_id
        const subcatGroups = {};
        filtered.forEach(c => {
            const subId = c.subcategoria_id;
            if (!subcatGroups[subId]) {
                subcatGroups[subId] = {
                    subcategoria_id: subId,
                    subcategoria_name: c.subcategoria_name,
                    col_origen_periodo: c.col_origen_periodo,
                    col_origen_mes: c.col_origen_mes,
                    periods: {}
                };
            }
            
            const per = c.periodo;
            if (!subcatGroups[subId].periods[per]) {
                subcatGroups[subId].periods[per] = [];
            }
            subcatGroups[subId].periods[per].push(c);
        });

        // 3. Sort subcategories
        const subcatList = Object.values(subcatGroups);
        if (sortVal === 'subcat_asc') {
            subcatList.sort((a, b) => a.subcategoria_name.localeCompare(b.subcategoria_name));
        } else if (sortVal === 'subcat_desc') {
            subcatList.sort((a, b) => b.subcategoria_name.localeCompare(a.subcategoria_name));
        } else {
            // Sort by subcategory name by default
            subcatList.sort((a, b) => a.subcategoria_name.localeCompare(b.subcategoria_name));
        }

        // 4. Render
        subcatList.forEach(sub => {
            const totalMonths = Object.values(sub.periods).reduce((sum, list) => sum + list.length, 0);
            
            // Subcategory main header row
            tbody.innerHTML += `
                <tr style="background: rgba(188, 140, 255, 0.08); font-weight: 600; border-left: 4px solid var(--accent);">
                    <td colspan="6" class="py-2 align-middle">
                        <div class="d-flex justify-content-between align-items-center">
                            <span>
                                <strong class="text-accent" style="font-size: 0.88rem;">
                                    <i class="bi bi-folder-fill me-2 text-warning"></i>${sub.subcategoria_name}
                                </strong>
                                <span class="text-secondary ms-3 small" style="font-size: 0.75rem; font-weight: normal;">
                                    Col. Periodo: <code class="text-info">${sub.col_origen_periodo || '-'}</code> | 
                                    Col. Mes: <code class="text-info">${sub.col_origen_mes || '-'}</code>
                                </span>
                            </span>
                            <span class="badge bg-accent-subtle text-accent" style="font-size: 0.7rem;">${totalMonths} registros</span>
                        </div>
                    </td>
                </tr>
            `;

            // Sort periods keys
            const periodsKeys = Object.keys(sub.periods);
            if (sortVal === 'period_desc') {
                periodsKeys.sort((a, b) => b.localeCompare(a));
            } else if (sortVal === 'period_asc') {
                periodsKeys.sort((a, b) => a.localeCompare(b));
            } else {
                periodsKeys.sort((a, b) => b.localeCompare(a)); // Default: recent first
            }

            periodsKeys.forEach(per => {
                const monthsList = sub.periods[per];
                monthsList.sort((a, b) => a.mes.localeCompare(b.mes));

                // Year Sub-header row
                const yearText = per === 'GLOBAL' ? 'Global (Sin Periodo)' : `Año ${per}`;
                tbody.innerHTML += `
                    <tr style="background: rgba(255, 255, 255, 0.02); font-weight: 500;">
                        <td colspan="6" class="py-1 ps-4 text-secondary small" style="font-size: 0.8rem;">
                            <i class="bi bi-calendar-check me-2 text-primary"></i>${yearText}
                        </td>
                    </tr>
                `;

                // Render months
                monthsList.forEach(c => {
                    const idx = currentCorrelativosList.findIndex(item => item.id === c.id);
                    const mesText = c.mes === '00' ? 'Global / Sin Mes' : `Mes ${c.mes}`;
                    tbody.innerHTML += `
                        <tr style="border-left: 2px dashed rgba(188, 140, 255, 0.3);">
                            <td class="ps-5 text-secondary small" style="font-size: 0.78rem;">
                                <i class="bi bi-calendar-event me-2 text-secondary"></i>${mesText}
                            </td>
                            <td class="text-center font-monospace small">${c.periodo}</td>
                            <td class="text-center font-monospace small">${c.mes}</td>
                            <td class="text-center font-monospace small">${c.asiento_inicial}</td>
                            <td class="text-center font-monospace small text-warning">${c.asiento_actual}</td>
                            <td class="text-end py-1">
                                <div class="d-flex gap-1 justify-content-end">
                                    <button class="btn btn-outline-primary btn-sm px-2 py-0" style="font-size:0.7rem;" onclick="editCorrelativo(${idx})">
                                        <i class="bi bi-pencil-fill"></i>
                                    </button>
                                    <button class="btn btn-outline-danger btn-sm px-2 py-0" style="font-size:0.7rem;" onclick="deleteCorrelativo(${c.id})">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                });
            });
        });
    }

    function filterCorrelativosUI() {
        renderCorrelativos();
    }

    async function onCorrCompanyChange() {
        const compId = document.getElementById('corrCompany').value;
        const subcatSel = document.getElementById('corrSubcategory');
        subcatSel.innerHTML = '<option value="">-- Seleccionar Subcategoría --</option>';
        if (!compId) {
            subcatSel.disabled = true;
            return;
        }
        subcatSel.disabled = false;
        
        try {
            const res = await fetch(`/api/v1/mapeo/categorias?company_id=${compId}`, { headers: authHeaders });
            if (res.ok) {
                const cats = await res.json();
                cats.forEach(cat => {
                    if (cat.subcategorias && cat.subcategorias.length) {
                        cat.subcategorias.forEach(sub => {
                            if (sub.is_active) {
                                const opt = document.createElement('option');
                                opt.value = sub.id;
                                opt.textContent = `${cat.nombre} → ${sub.nombre}`;
                                opt.setAttribute('data-period-col', sub.col_origen_periodo || '');
                                opt.setAttribute('data-mes-col', sub.col_origen_mes || '');
                                opt.setAttribute('data-generate-headers', sub.generate_headers !== false ? 'true' : 'false');
                                subcatSel.appendChild(opt);
                            }
                        });
                    }
                });
            }
        } catch (e) {
            console.error("Error cargando subcategorías para correlativo:", e);
        }
    }

    async function onCorrSubcatChange(keepValues = false) {
        const subcatSel = document.getElementById('corrSubcategory');
        const subcatId = subcatSel.value;
        const dlPeriod = document.getElementById('corrPeriodColsList');
        const dlMes = document.getElementById('corrMesColsList');
        if (dlPeriod) dlPeriod.innerHTML = '';
        if (dlMes) dlMes.innerHTML = '';

        if (!subcatId) return;

        const selectedOpt = subcatSel.options[subcatSel.selectedIndex];
        const periodCol = selectedOpt ? selectedOpt.getAttribute('data-period-col') : '';
        const mesCol = selectedOpt ? selectedOpt.getAttribute('data-mes-col') : '';

        const generateHeaders = selectedOpt ? selectedOpt.getAttribute('data-generate-headers') === 'true' : true;

        // Auto-detect global correlative: Global if subcategory generate_headers is false (Mode B / row-by-row)
        const isGlobal = !generateHeaders;
        const inputPeriodo = document.getElementById('corrPeriodo');
        const selectMes = document.getElementById('corrMes');
        const chkBulk = document.getElementById('corrBulkYear');

        if (isGlobal) {
            inputPeriodo.type = 'text';
            if (!keepValues || !inputPeriodo.value) {
                inputPeriodo.value = 'GLOBAL';
            }
            inputPeriodo.readOnly = true;

            let globalOpt = selectMes.querySelector('option[value="00"]');
            if (!globalOpt) {
                globalOpt = document.createElement('option');
                globalOpt.value = '00';
                globalOpt.textContent = 'GLOBAL / Sin Mes';
                selectMes.appendChild(globalOpt);
            }
            if (!keepValues || !selectMes.value) {
                selectMes.value = '00';
            }
            selectMes.disabled = true;

            if (chkBulk) {
                chkBulk.checked = false;
                const parent = chkBulk.closest('.form-check');
                if (parent) parent.style.display = 'none';
            }
            toggleCorrBulk({ checked: false });
        } else {
            inputPeriodo.type = 'number';
            inputPeriodo.readOnly = false;
            if (!keepValues) {
                inputPeriodo.value = new Date().getFullYear();
            }

            selectMes.disabled = false;
            let globalOpt = selectMes.querySelector('option[value="00"]');
            if (globalOpt) globalOpt.remove();
            if (!keepValues) {
                selectMes.value = String(new Date().getMonth() + 1).padStart(2, '0');
            }

            if (chkBulk) {
                const parent = chkBulk.closest('.form-check');
                if (parent) parent.style.display = 'block';
            }
        }

        try {
            const hRes = await fetch(`/api/v1/mapeo/subcategorias/${subcatId}/helper-data`, { headers: authHeaders });
            if (hRes.ok) {
                const hData = await hRes.json();
                const cols = hData.columns || [];
                const listOpts = cols.map(c => {
                    const val = (typeof c === 'string') ? c : (c.column_name || '');
                    return `<option value="${val}"></option>`;
                }).join('');
                if (dlPeriod) dlPeriod.innerHTML = listOpts;
                if (dlMes) dlMes.innerHTML = listOpts;
            }
        } catch (e) {
            console.error("Error cargando helper-data de columnas:", e);
        }
    }

    function toggleCorrBulk(chk) {
        const divMes = document.getElementById('divCorrMes');
        const selectMes = document.getElementById('corrMes');
        const inputAsientoActual = document.getElementById('corrAsientoActual');
        
        if (chk.checked) {
            if (divMes) divMes.style.display = 'none';
            if (selectMes) selectMes.required = false;
            if (selectMes) selectMes.value = '';
            if (inputAsientoActual) {
                inputAsientoActual.value = '0';
                const col = inputAsientoActual.closest('.col-6');
                if (col) col.style.display = 'none';
            }
        } else {
            if (divMes) divMes.style.display = 'block';
            if (selectMes) selectMes.required = true;
            if (inputAsientoActual) {
                const col = inputAsientoActual.closest('.col-6');
                if (col) col.style.display = 'block';
            }
        }
    }

    function openCorrelativoModal() {
        document.getElementById('correlativoForm').reset();
        document.getElementById('editCorrelativoId').value = '';
        document.getElementById('correlativoModalTitle').innerHTML = '<i class="bi bi-hash text-primary me-2"></i>Registrar Correlativo por Periodo/Mes';
        
        // Enable fields
        document.getElementById('corrCompany').disabled = false;
        document.getElementById('corrSubcategory').disabled = true;
        document.getElementById('corrPeriodo').disabled = false;
        document.getElementById('corrMes').disabled = false;
        
        // Show bulk container and make sure it is unchecked
        const chkBulk = document.getElementById('corrBulkYear');
        if (chkBulk) {
            chkBulk.checked = false;
            const parent = chkBulk.closest('.form-check');
            if (parent) parent.style.display = 'block';
        }
        toggleCorrBulk({ checked: false });

        document.getElementById('corrSubcategory').innerHTML = '<option value="">-- Seleccionar Subcategoría --</option>';
        document.getElementById('corrPeriodColsList').innerHTML = '';
        document.getElementById('corrMesColsList').innerHTML = '';

        // Prepopulate current period and month
        document.getElementById('corrPeriodo').value = new Date().getFullYear();
        document.getElementById('corrMes').value = String(new Date().getMonth() + 1).padStart(2, '0');

        correlativoModalObj.show();
    }

    async function editCorrelativo(index) {
        const c = currentCorrelativosList[index];
        if (!c) return;

        document.getElementById('editCorrelativoId').value = c.id;
        document.getElementById('correlativoModalTitle').innerHTML = '<i class="bi bi-pencil-fill text-primary me-2"></i>Editar Correlativo por Periodo/Mes';

        // Pre-fill fields
        document.getElementById('corrCompany').value = c.company_id;
        
        // Load subcategories for this company
        const subcatSel = document.getElementById('corrSubcategory');
        subcatSel.innerHTML = '<option value="">-- Seleccionar Subcategoría --</option>';
        try {
            const res = await fetch(`/api/v1/mapeo/categorias?company_id=${c.company_id}`, { headers: authHeaders });
            if (res.ok) {
                const cats = await res.json();
                cats.forEach(cat => {
                    if (cat.subcategorias) {
                        cat.subcategorias.forEach(sub => {
                            if (sub.is_active) {
                                const opt = document.createElement('option');
                                opt.value = sub.id;
                                opt.textContent = `${cat.nombre} → ${sub.nombre}`;
                                opt.setAttribute('data-period-col', sub.col_origen_periodo || '');
                                opt.setAttribute('data-mes-col', sub.col_origen_mes || '');
                                opt.setAttribute('data-generate-headers', sub.generate_headers !== false ? 'true' : 'false');
                                subcatSel.appendChild(opt);
                            }
                        });
                    }
                });
            }
        } catch (e) {
            console.error(e);
        }
        
        subcatSel.value = c.subcategoria_id;
        document.getElementById('corrPeriodo').value = c.periodo;
        document.getElementById('corrMes').value = c.mes;
        document.getElementById('corrColPeriodo').value = c.col_origen_periodo || '';
        document.getElementById('corrColMes').value = c.col_origen_mes || '';
        document.getElementById('corrAsientoInicial').value = c.asiento_inicial;
        document.getElementById('corrAsientoActual').value = c.asiento_actual;

        // Load columns autocomplete list
        await onCorrSubcatChange(true);

        // Hide bulk container for editing
        const chkBulk = document.getElementById('corrBulkYear');
        if (chkBulk) {
            chkBulk.checked = false;
            const parent = chkBulk.closest('.form-check');
            if (parent) parent.style.display = 'none';
        }
        toggleCorrBulk({ checked: false });

        // Disable keys
        document.getElementById('corrCompany').disabled = true;
        document.getElementById('corrSubcategory').disabled = true;
        document.getElementById('corrPeriodo').disabled = true;
        document.getElementById('corrMes').disabled = true;

        correlativoModalObj.show();
    }

    async function saveCorrelativo() {
        const id = document.getElementById('editCorrelativoId').value;
        const companyId = document.getElementById('corrCompany').value;
        const subcatId = document.getElementById('corrSubcategory').value;
        const periodo = document.getElementById('corrPeriodo').value;
        const mes = document.getElementById('corrMes').value;
        const colPeriodo = document.getElementById('corrColPeriodo').value || null;
        const colMes = document.getElementById('corrColMes').value || null;
        const asientoInicial = parseInt(document.getElementById('corrAsientoInicial').value) || 1;
        const asientoActual = parseInt(document.getElementById('corrAsientoActual').value) || 0;
        const isBulk = document.getElementById('corrBulkYear')?.checked || false;

        if (!id) {
            if (!companyId || !subcatId || !periodo) {
                showToast('warning', 'Debe completar Empresa, Subcategoría y Periodo.');
                return;
            }
            if (!isBulk && !mes) {
                showToast('warning', 'Debe seleccionar un mes.');
                return;
            }
        }

        // If bulk register year
        if (!id && isBulk) {
            showToast('info', 'Registrando los 12 meses de manera masiva...');
            const payload = {
                company_id: parseInt(companyId),
                subcategoria_id: parseInt(subcatId),
                periodo: periodo,
                col_origen_periodo: colPeriodo,
                col_origen_mes: colMes,
                asiento_inicial: asientoInicial,
                bulk_year: true
            };

            try {
                const res = await fetch('/api/v1/etl/correlativos', {
                    method: 'POST',
                    headers: authHeaders,
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    showToast('success', data.message || 'Registro masivo de periodo completado.');
                    correlativoModalObj.hide();
                    
                    // Reload grid
                    const filterComp = document.getElementById('correlativoFilterCompany').value;
                    if (filterComp && String(filterComp) === String(companyId)) {
                        loadCorrelativos();
                    } else {
                        document.getElementById('correlativoFilterCompany').value = companyId;
                        loadCorrelativos();
                    }
                } else {
                    showToast('error', data.detail || 'Fallo al realizar el registro masivo.');
                }
            } catch (e) {
                showToast('error', 'Error de red.');
            }
            return;
        }

        const payload = {
            company_id: parseInt(companyId),
            subcategoria_id: parseInt(subcatId),
            periodo: periodo,
            mes: mes,
            col_origen_periodo: colPeriodo,
            col_origen_mes: colMes,
            asiento_inicial: asientoInicial,
            asiento_actual: asientoActual
        };

        try {
            let res;
            if (id) {
                // Update
                res = await fetch(`/api/v1/etl/correlativos/${id}`, {
                    method: 'PUT',
                    headers: authHeaders,
                    body: JSON.stringify({
                        asiento_inicial: asientoInicial,
                        asiento_actual: asientoActual,
                        col_origen_periodo: colPeriodo,
                        col_origen_mes: colMes
                    })
                });
            } else {
                // Create
                res = await fetch('/api/v1/etl/correlativos', {
                    method: 'POST',
                    headers: authHeaders,
                    body: JSON.stringify(payload)
                });
            }

            const data = await res.json();
            if (res.ok) {
                showToast('success', data.message || 'Correlativo guardado correctamente.');
                correlativoModalObj.hide();
                
                // If company matches currently selected filter, reload
                const filterComp = document.getElementById('correlativoFilterCompany').value;
                if (filterComp && String(filterComp) === String(companyId)) {
                    loadCorrelativos();
                } else {
                    document.getElementById('correlativoFilterCompany').value = companyId;
                    loadCorrelativos();
                }
            } else {
                showToast('error', data.detail || 'Error al guardar correlativo.');
            }
        } catch (e) {
            showToast('error', 'Error de red.');
        }
    }

    async function deleteCorrelativo(id) {
        const confirmResult = await Swal.fire({
            title: '¿Eliminar correlativo?',
            text: 'Se eliminará la configuración y el contador de correlativo para este periodo/mes.',
            icon: 'warning',
            showCancelButton: true,
            background: '#161b22',
            color: '#fff',
            confirmButtonColor: '#bc8cff',
            cancelButtonColor: '#30363d',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        });

        if (!confirmResult.isConfirmed) return;

        try {
            const res = await fetch(`/api/v1/etl/correlativos/${id}`, {
                method: 'DELETE',
                headers: authHeaders
            });
            if (res.ok) {
                showToast('success', 'Correlativo eliminado correctamente.');
                loadCorrelativos();
            } else {
                showToast('error', 'Fallo al eliminar correlativo.');
            }
        } catch {
            showToast('error', 'Error de red.');
        }
    }

    // ─── Reextraer y Reprocesar JS Functions ───
    async function openReextractModal(companyId, subcatId, subcatName, nasiento) {
        currentReextractParams = { companyId, subcatId, nasiento };
        
        // Show modal and loading state
        document.getElementById('reextractLoading').classList.remove('d-none');
        document.getElementById('reextractContent').classList.add('d-none');
        document.getElementById('btnConfirmReextract').disabled = true;
        reextractModalObj.show();

        let url = `/api/v1/etl/reextract-preview?company_id=${companyId}&subcategoria_id=${subcatId}`;
        if (nasiento) {
            url += `&nasiento=${encodeURIComponent(nasiento)}`;
        }

        try {
            const res = await fetch(url, { headers: authHeaders });
            if (!res.ok) throw new Error();
            
            const data = await res.json();
            document.getElementById('reextractSubcatName').textContent = data.subcategory_name || subcatName;
            document.getElementById('reextractSourceTable').textContent = data.source_table || '';

            const tbody = document.getElementById('reextractTableBody');
            tbody.innerHTML = '';

            const items = data.items || [];
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="text-center text-secondary py-4">No hay asientos pendientes o con error en staging.</td></tr>';
                document.getElementById('reextractLoading').classList.add('d-none');
                document.getElementById('reextractContent').classList.remove('d-none');
                return;
            }

            items.forEach(item => {
                let stagingInfoHtml = '';
                item.staging_rows.forEach(r => {
                    stagingInfoHtml += `<div class="font-monospace text-secondary small" style="font-size:0.72rem;">Cuenta: ${r.ccodcue} | Debe: ${r.ndebe} | Haber: ${r.nhaber} | Glosa: ${r.cglosa}</div>`;
                });

                let stateBadge = '';
                if (item.staging_status === 'ERROR' || item.staging_status === '0') {
                    stateBadge = '<span class="badge bg-danger-subtle text-danger small px-1 py-0"><i class="bi bi-x-circle me-1"></i>ERROR</span>';
                } else {
                    stateBadge = '<span class="badge bg-warning-subtle text-warning small px-1 py-0"><i class="bi bi-clock me-1"></i>PENDIENTE</span>';
                }

                let linkBadge = `<div class="text-center py-2"><i class="bi bi-arrow-left-right text-info fs-5" title="Mapeado por idcontrol"></i></div>`;

                let rawInfoHtml = '';
                if (item.raw_exists) {
                    rawInfoHtml = `
                        <div>
                            <span class="badge bg-success-subtle text-success small px-1 py-0 mb-1"><i class="bi bi-check-circle me-1"></i>Encontrado</span>
                            <div class="small text-light font-monospace" style="font-size:0.75rem;">${item.raw_info}</div>
                        </div>
                    `;
                } else {
                    rawInfoHtml = `
                        <div>
                            <span class="badge bg-danger-subtle text-danger small px-1 py-0 mb-1"><i class="bi bi-x-circle me-1"></i>No Encontrado</span>
                            <div class="small text-secondary" style="font-size:0.75rem;">Se consultará y extraerá de la base origen (SQL Server).</div>
                        </div>
                    `;
                }

                tbody.innerHTML += `
                    <tr class="align-middle">
                        <td class="pe-3">
                            <div class="fw-semibold text-light mb-1">Asiento: ${item.nasiento} <span class="text-secondary font-monospace ms-2">(${item.cper}-${item.cmes})</span> ${stateBadge}</div>
                            ${stagingInfoHtml}
                        </td>
                        <td class="text-center font-monospace text-secondary" style="font-size: 0.72rem;">
                            ${linkBadge}
                            <span class="d-block text-truncate" style="max-width: 90px;" title="${item.idcontrol}">${item.idcontrol}</span>
                        </td>
                        <td class="ps-3 border-start border-secondary" style="border-left-color: rgba(255,255,255,0.05) !important;">
                            ${rawInfoHtml}
                        </td>
                    </tr>
                `;
            });

            document.getElementById('btnConfirmReextract').disabled = false;
        } catch (e) {
            console.error("Error cargando vista previa de reextracción:", e);
            showToast('error', 'Error al cargar la relación de registros.');
            reextractModalObj.hide();
        } finally {
            document.getElementById('reextractLoading').classList.add('d-none');
            document.getElementById('reextractContent').classList.remove('d-none');
        }
    }

    async function executeReextractReprocess() {
        const btnConfirm = document.getElementById('btnConfirmReextract');
        const btnCancel = document.getElementById('btnCancelReextract');
        
        const originalHtml = btnConfirm.innerHTML;
        btnConfirm.disabled = true;
        btnCancel.disabled = true;
        btnConfirm.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando 3 pasos...';

        try {
            const res = await fetch('/api/v1/etl/reextract-reprocess', {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify({
                    company_id: currentReextractParams.companyId,
                    subcategoria_id: currentReextractParams.subcatId,
                    nasiento: currentReextractParams.nasiento
                })
            });

            const data = await res.json();
            if (res.ok && data.status === 'SUCCESS') {
                const det = data.details || {};
                await Swal.fire({
                    title: '¡Proceso Completado!',
                    html: `
                        <div class="text-start small">
                            <p class="mb-2 text-success"><i class="bi bi-check-circle-fill me-2"></i>Se ejecutó el flujo correctamente:</p>
                            <ul>
                                <li><strong>Extraídos (SQL Server):</strong> ${det.reextracted || 0} filas</li>
                                <li><strong>Generados (Staging):</strong> ${det.generated || 0} filas</li>
                                <li><strong>Migrados (Contasis):</strong> ${det.migrated || 0} filas</li>
                            </ul>
                            <div class="text-muted text-end mt-2 font-monospace" style="font-size:0.7rem;">Lote: ${det.lote_id || '-'}</div>
                        </div>
                    `,
                    icon: 'success',
                    background: '#161b22',
                    color: '#fff',
                    confirmButtonColor: '#bc8cff'
                });

                reextractModalObj.hide();
                
                // Refresh UI
                if (typeof loadStagingSummary === 'function') loadStagingSummary();
                if (typeof loadRealtimeLogs === 'function') loadRealtimeLogs();
                if (activeVisorTab === 'staging') {
                    if (typeof loadStagingRows === 'function') loadStagingRows(visorSkip);
                }
            } else {
                let errorMsg = 'Fallo en la reextracción y reprocesamiento.';
                let detailsHtml = '';
                let reextracted = 0;
                let generated = 0;
                if (data && data.detail) {
                    if (typeof data.detail === 'object') {
                        errorMsg = data.detail.message || errorMsg;
                        reextracted = data.detail.reextracted || 0;
                        generated = data.detail.generated || 0;
                        if (data.detail.failed_rows && data.detail.failed_rows.length > 0) {
                            detailsHtml = '<div class="text-start mt-3 p-2 rounded" style="max-height: 200px; overflow-y: auto; background: rgba(255, 0, 0, 0.05); border: 1px solid rgba(255, 0, 0, 0.15);"><small class="text-danger fw-semibold d-block mb-1"><i class="bi bi-exclamation-triangle-fill me-1"></i>Detalles de error por asiento:</small><ul class="ps-3 mb-0 text-secondary" style="font-size:0.75rem; line-height: 1.4;">';
                            data.detail.failed_rows.forEach(item => {
                                const seat = item.seat || 'Desconocido';
                                const err = item.error || 'Error desconocido';
                                detailsHtml += `<li class="mb-1"><strong class="text-light">Asiento ${seat}:</strong> <span class="text-danger">${err}</span></li>`;
                            });
                            detailsHtml += '</ul></div>';
                        }
                    } else {
                        errorMsg = data.detail;
                    }
                }
                
                await Swal.fire({
                    title: 'Error en Reprocesamiento',
                    html: `
                        <div class="text-start small">
                            <p class="mb-2 text-danger fw-semibold">${errorMsg}</p>
                            <ul class="mb-3 text-secondary ps-3" style="font-size:0.8rem; line-height: 1.4;">
                                <li><strong>Extraídos (SQL Server):</strong> ${reextracted} filas</li>
                                <li><strong>Generados (Staging):</strong> ${generated} filas</li>
                                <li><strong>Migrados (Contasis):</strong> 0 (Fallo)</li>
                            </ul>
                            ${detailsHtml}
                        </div>
                    `,
                    icon: 'error',
                    background: '#161b22',
                    color: '#fff',
                    confirmButtonColor: '#ff7b72'
                });
            }
        } catch (err) {
            showToast('error', 'Error de red al procesar.');
        } finally {
            btnConfirm.disabled = false;
            btnCancel.disabled = false;
            btnConfirm.innerHTML = originalHtml;
        }
    }
