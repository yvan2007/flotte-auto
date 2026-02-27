/**
 * Gestion des graphiques sur le tableau de bord moderne
 */
(function() {
    'use strict';

    let previewChart = null;
    const chartsRow = document.getElementById('dashboard-charts-row');
    const chartForm = document.getElementById('chartForm');
    const chartModel = document.getElementById('chartModel');
    const chartField = document.getElementById('chartField');
    const chartName = document.getElementById('chartName');
    const chartId = document.getElementById('chartId');
    const chartType = document.getElementById('chartType');
    const chartFrequency = document.getElementById('chartFrequency');
    const chartOperation = document.getElementById('chartOperation');
    const previewContainer = document.getElementById('chartPreview');
    const previewCanvas = document.getElementById('previewChartCanvas');
    const createModal = new bootstrap.Modal(document.getElementById('createChartModal'));

    function getCookie(name) {
        const cookies = document.cookie.split('; ');
        for (let i = 0; i < cookies.length; i++) {
            const parts = cookies[i].split('=');
            if (parts[0] === name) return parts.slice(1).join('=');
        }
        return null;
    }

    function getCSRFToken() {
        return getCookie('csrftoken');
    }

    // Charger les modèles disponibles (API dashboard_models)
    function loadModels() {
        return fetch('/admin_custom/api/dashboard-models/')
            .then(r => r.json())
            .then(data => {
                if (!chartModel) return;
                chartModel.innerHTML = '<option value="">-- Sélectionner un modèle --</option>';
                if (Array.isArray(data.models)) {
                    data.models.forEach(m => {
                        const option = document.createElement('option');
                        // Utiliser app_label.ModelName (géré par get_model_class)
                        option.value = m.app + '.' + m.model;
                        option.textContent = (m.verbose_name || m.model) + ' (' + m.app + ')';
                        chartModel.appendChild(option);
                    });
                }
            })
            .catch(err => {
                console.error('Erreur lors du chargement des modèles pour le dashboard:', err);
            });
    }

    // Charger les champs numériques d'un modèle (API model_fields)
    function loadModelFields(modelName) {
        if (!chartField) return Promise.resolve();
        if (!modelName) {
            chartField.innerHTML = '<option value="">-- Sélectionner un modèle d\'abord --</option>';
            return Promise.resolve();
        }
        return fetch(`/admin_custom/api/model-fields/?model=${encodeURIComponent(modelName)}`)
            .then(r => r.json())
            .then(data => {
                chartField.innerHTML = '<option value="">-- Sélectionner un champ --</option>';
                // L'API renvoie une liste de noms de champs (strings)
                if (Array.isArray(data.fields)) {
                    data.fields.forEach(fieldName => {
                        const option = document.createElement('option');
                        option.value = fieldName;
                        option.textContent = fieldName;
                        chartField.appendChild(option);
                    });
                }
            })
            .catch(err => {
                console.error('Erreur lors du chargement des champs pour le dashboard:', err);
            });
    }

    // Charger les graphiques sauvegardés
    function loadCharts() {
        return fetch('/admin_custom/api/dashboard-charts/')
            .then(r => r.json())
            .then(data => {
                if (!chartsRow) return;
                if (!data.charts || data.charts.length === 0) {
                    chartsRow.innerHTML = '<div class="col-12"><div class="alert alert-info"><i class="fa-solid fa-info-circle"></i> Aucun graphique configuré. Cliquez sur "Créer un graphique" pour en ajouter.</div></div>';
                    return;
                }
                renderCharts(data.charts);
            });
    }

    // Afficher les graphiques
    function renderCharts(charts) {
        if (!chartsRow) return;
        chartsRow.innerHTML = '';
        charts.forEach((chart, index) => {
            const col = document.createElement('div');
            col.className = 'col-12 col-md-6 col-lg-4';
            col.innerHTML = `
                <div class="card" style="position:relative;">
                    <button type="button" class="btn btn-sm btn-danger" style="position:absolute;top:8px;right:8px;z-index:10;" onclick="deleteChart(${chart.id})" title="Supprimer">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${chart.name}</h6>
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="editChart(${chart.id})" title="Modifier">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                    </div>
                    <div class="card-body" style="height:300px;">
                        <canvas id="chart-${chart.id}"></canvas>
                    </div>
                </div>
            `;
            chartsRow.appendChild(col);
            // Charger et afficher le graphique
            setTimeout(() => renderChart(chart, `chart-${chart.id}`), 100);
        });
    }

    // Afficher un graphique
    function renderChart(chart, canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const url = `/admin_custom/api/chart-data/?model=${encodeURIComponent(chart.model_name)}&field=${encodeURIComponent(chart.field_name)}&type=${chart.chart_type}&frequency=${chart.frequency}&operation=${chart.operation}`;
        fetch(url)
            .then(r => r.json())
            .then(data => {
                if (data.labels && data.data) {
                    const chartConfig = {
                        type: chart.chart_type,
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: chart.name,
                                data: data.data,
                                borderColor: getChartColor(chart.chart_type),
                                backgroundColor: getChartColor(chart.chart_type, true),
                                tension: chart.chart_type === 'line' || chart.chart_type === 'area' ? 0.4 : 0,
                                fill: chart.chart_type === 'area'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: chart.chart_type !== 'pie' && chart.chart_type !== 'doughnut' ? {
                                y: { beginAtZero: true }
                            } : {}
                        }
                    };
                    new Chart(ctx, chartConfig);
                }
            })
            .catch(err => console.error('Erreur chargement graphique:', err));
    }

    // Couleurs pour les graphiques
    function getChartColor(type, isBackground = false) {
        const colors = {
            line: isBackground ? 'rgba(59, 130, 246, 0.1)' : 'rgb(59, 130, 246)',
            bar: isBackground ? 'rgba(16, 185, 129, 0.1)' : 'rgb(16, 185, 129)',
            pie: ['rgb(59, 130, 246)', 'rgb(16, 185, 129)', 'rgb(245, 158, 11)', 'rgb(239, 68, 68)', 'rgb(139, 92, 246)'],
            doughnut: ['rgb(59, 130, 246)', 'rgb(16, 185, 129)', 'rgb(245, 158, 11)', 'rgb(239, 68, 68)', 'rgb(139, 92, 246)'],
            area: isBackground ? 'rgba(59, 130, 246, 0.3)' : 'rgb(59, 130, 246)'
        };
        return colors[type] || colors.line;
    }

    // Prévisualiser le graphique
    function previewChartData() {
        const model = chartModel.value;
        const field = chartField.value;
        const type = chartType.value;
        const frequency = chartFrequency.value;
        const operation = chartOperation.value;
        if (!model || !field) {
            alert('Veuillez sélectionner un modèle et un champ');
            return;
        }
        const url = `/admin_custom/api/chart-data/?model=${encodeURIComponent(model)}&field=${encodeURIComponent(field)}&type=${type}&frequency=${frequency}&operation=${operation}`;
        fetch(url)
            .then(r => r.json())
            .then(data => {
                if (data.labels && data.data) {
                    previewContainer.style.display = 'block';
                    const ctx = previewCanvas.getContext('2d');
                    if (previewChart) previewChart.destroy();
                    previewChart = new Chart(ctx, {
                        type: type,
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: chartName.value || 'Aperçu',
                                data: data.data,
                                borderColor: getChartColor(type),
                                backgroundColor: getChartColor(type, true),
                                tension: type === 'line' || type === 'area' ? 0.4 : 0,
                                fill: type === 'area'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: type !== 'pie' && type !== 'doughnut' ? {
                                y: { beginAtZero: true }
                            } : {}
                        }
                    });
                } else {
                    alert('Erreur lors du chargement des données');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Erreur lors du chargement des données');
            });
    }

    // Sauvegarder le graphique
    function saveChart() {
        const data = {
            id: chartId.value || null,
            name: chartName.value.trim(),
            model_name: chartModel.value,
            field_name: chartField.value,
            chart_type: chartType.value,
            frequency: chartFrequency.value,
            operation: chartOperation.value
        };
        if (!data.name || !data.model_name || !data.field_name) {
            alert('Veuillez remplir tous les champs obligatoires');
            return;
        }
        fetch('/admin_custom/api/dashboard-chart/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(data)
        })
            .then(r => r.json())
            .then(result => {
                if (result.ok) {
                    createModal.hide();
                    resetForm();
                    loadCharts();
                } else {
                    alert(result.error || 'Erreur lors de la sauvegarde');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Erreur lors de la sauvegarde');
            });
    }

    // Supprimer un graphique
    window.deleteChart = function(chartId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer ce graphique ?')) return;
        fetch('/admin_custom/api/dashboard-chart/delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ id: chartId })
        })
            .then(r => r.json())
            .then(result => {
                if (result.ok) {
                    loadCharts();
                } else {
                    alert(result.error || 'Erreur lors de la suppression');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Erreur lors de la suppression');
            });
    };

    // Éditer un graphique
    window.editChart = function(chartId) {
        fetch('/admin_custom/api/dashboard-charts/')
            .then(r => r.json())
            .then(data => {
                const chart = data.charts.find(c => c.id === chartId);
                if (chart) {
                    chartId.value = chart.id;
                    chartName.value = chart.name;
                    chartModel.value = chart.model_name;
                    loadModelFields(chart.model_name).then(() => {
                        chartField.value = chart.field_name;
                        chartType.value = chart.chart_type;
                        chartFrequency.value = chart.frequency;
                        chartOperation.value = chart.operation;
                        createModal.show();
                    });
                }
            });
    };

    // Réinitialiser le formulaire
    function resetForm() {
        chartForm.reset();
        chartId.value = '';
        previewContainer.style.display = 'none';
        if (previewChart) {
            previewChart.destroy();
            previewChart = null;
        }
    }

    // Événements
    if (chartModel) {
        chartModel.addEventListener('change', function() {
            loadModelFields(this.value);
        });
    }

    if (document.getElementById('btn-preview-chart')) {
        document.getElementById('btn-preview-chart').addEventListener('click', previewChartData);
    }

    if (document.getElementById('btn-save-chart')) {
        document.getElementById('btn-save-chart').addEventListener('click', saveChart);
    }

    // Réinitialiser le formulaire quand le modal est fermé
    document.getElementById('createChartModal').addEventListener('hidden.bs.modal', resetForm);

    // Initialisation
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            loadModels();
            loadCharts();
        });
    } else {
        loadModels();
        loadCharts();
    }
})();
