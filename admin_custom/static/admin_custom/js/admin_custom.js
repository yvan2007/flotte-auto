// Theme Management
(function() {
    'use strict';
    
    // Interface MODERNE : ne jamais écraser le thème (bleu-moderne, emeraude, etc.)
    const modernThemes = ['bleu-moderne', 'emeraude', 'coucher-soleil', 'sombre'];
    const current = document.documentElement.getAttribute('data-theme');
    if (modernThemes.includes(current) || document.querySelector('.admin-layout')) {
        return;
    }
    
    // Interface CLASSIQUE : charger le thème sauvegardé
    const savedTheme = localStorage.getItem('admin-theme') || 'default';
    const validThemes = ['default', 'nostalgie', 'ocean', 'forest', 'dark', 'black'];
    document.documentElement.setAttribute('data-theme', validThemes.includes(savedTheme) ? savedTheme : 'default');
    
    // Marquer le lien de navigation actif (un seul lien actif à la fois)
    function setActiveNavLink() {
        const nav = document.querySelector('.custom-admin-nav');
        if (!nav) return;
        const currentPath = window.location.pathname.replace(/\/$/, '') || '/admin';
        const navLinks = nav.querySelectorAll('.nav-link');
        let activeFound = false;
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href') || '';
            const linkPath = href.split('?')[0].replace(/\/$/, '');
            let isMatch = false;
            
            if (linkPath) {
                // Accueil (index) : correspondance exacte uniquement
                if (linkPath === '/admin' || linkPath.endsWith('/admin')) {
                    isMatch = (currentPath === '/admin');
                } else {
                    // Autres liens : chemin commence par le lien (ex: /admin/charts)
                    isMatch = currentPath === linkPath || currentPath.startsWith(linkPath + '/');
                }
            }
            
            if (isMatch) activeFound = true;
            link.classList.toggle('active', isMatch);
        });
    }
    
    // Appeler au chargement et lors des changements de navigation
    setActiveNavLink();
    window.addEventListener('popstate', setActiveNavLink);
    
    // Initialiser le bouton de thème
    const themeToggle = document.getElementById('theme-toggle');
    const themeMenu = document.getElementById('theme-menu');
    const themeOptions = document.querySelectorAll('.theme-option');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            themeMenu.classList.toggle('active');
        });
    }
    
    // Fermer le menu si on clique ailleurs
    document.addEventListener('click', function() {
        if (themeMenu) {
            themeMenu.classList.remove('active');
        }
    });
    
    // Gérer le changement de thème
    themeOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.stopPropagation();
            const theme = this.getAttribute('data-theme');
            
            // Appliquer le thème avec transition
            document.documentElement.style.transition = 'all 0.3s ease';
            document.documentElement.setAttribute('data-theme', theme);
            
            // Sauvegarder
            localStorage.setItem('admin-theme', theme);
            
            // Mettre à jour l'option active
            themeOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            
            // Fermer le menu
            themeMenu.classList.remove('active');
            
            // Recharger les graphiques si présents
            if (typeof generateChart === 'function') {
                setTimeout(() => {
                    if (currentChart) {
                        generateChart();
                    }
                }, 300);
            }
        });
        
        // Marquer l'option active
        if (option.getAttribute('data-theme') === savedTheme) {
            option.classList.add('active');
        }
    });
})();

// Chart Management
let currentChart = null;

function generateChart() {
    const model = document.getElementById('chart-model').value;
    const field = document.getElementById('chart-field').value;
    const chartType = document.getElementById('chart-type').value;
    const frequency = document.getElementById('chart-frequency').value;
    const operation = document.getElementById('chart-operation').value;
    
    if (!model || !field) {
        alert('Veuillez sélectionner un modèle et un champ');
        return;
    }
    
    const url = `/admin_custom/api/chart-data/?model=${model}&field=${field}&type=${chartType}&frequency=${frequency}&operation=${operation}`;
    
    // Afficher un loader
    const loadingAlert = document.getElementById('chart-loading');
    if (loadingAlert) {
        loadingAlert.style.display = 'block';
    }
    
    const generateBtn = document.getElementById('generate-chart');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Génération...';
    }
    
    const canvas = document.getElementById('chart-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#666';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Chargement...', canvas.width / 2, canvas.height / 2);
    }
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            const ctx = document.getElementById('chart-canvas').getContext('2d');
            
            // Masquer le loader
            if (loadingAlert) {
                loadingAlert.style.display = 'none';
            }
            
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-magic"></i> Générer le graphique';
            }
            
            // Masquer le placeholder et afficher le canvas
            const placeholder = document.getElementById('chart-placeholder');
            const canvas = document.getElementById('chart-canvas');
            if (placeholder) placeholder.style.display = 'none';
            if (canvas) canvas.style.display = 'block';
            
            // Détruire le graphique précédent
            if (currentChart) {
                currentChart.destroy();
            }
            
            // Configuration selon le type avec couleurs du thème
            const theme = document.documentElement.getAttribute('data-theme') || 'default';
            const themeColors = getThemeColors(chartType);
            const borderColor = getThemeColors(chartType, true);
            
            let config = {
                type: chartType,
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: `${model} - ${field}`,
                        data: data.data,
                        backgroundColor: themeColors,
                        borderColor: borderColor,
                        borderWidth: 2,
                        pointRadius: chartType === 'line' ? 4 : undefined,
                        pointHoverRadius: chartType === 'line' ? 6 : undefined
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 15,
                                font: {
                                    size: 12,
                                    weight: '500'
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: `${model} - ${field} (${frequency})`,
                            font: {
                                size: 16,
                                weight: '600'
                            },
                            padding: 20
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                size: 14,
                                weight: '600'
                            },
                            bodyFont: {
                                size: 13
                            },
                            cornerRadius: 8
                        }
                    },
                    scales: chartType !== 'pie' && chartType !== 'doughnut' ? {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            },
                            ticks: {
                                font: {
                                    size: 11
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                font: {
                                    size: 11
                                }
                            }
                        }
                    } : {}
                }
            };
            
            // Ajustements selon le type
            if (chartType === 'line' || chartType === 'area') {
                config.data.datasets[0].fill = chartType === 'area';
            }
            
            currentChart = new Chart(ctx, config);
            
            // Afficher le bouton de téléchargement
            const downloadBtn = document.getElementById('download-chart');
            if (downloadBtn) {
                downloadBtn.style.display = 'block';
                downloadBtn.onclick = function() {
                    const url = canvas.toDataURL('image/png');
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `graphique-${model}-${field}-${Date.now()}.png`;
                    a.click();
                };
            }
        })
        .catch(error => {
            console.error('Erreur lors de la génération du graphique:', error);
            
            // Masquer le loader
            const loadingAlert = document.getElementById('chart-loading');
            if (loadingAlert) {
                loadingAlert.style.display = 'none';
            }
            
            const generateBtn = document.getElementById('generate-chart');
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-magic"></i> Générer le graphique';
            }
            
            const errorMsg = error.error || error.message || 'Erreur lors de la génération du graphique';
            let alertMsg = errorMsg;
            
            if (error.available_fields && error.available_fields.length > 0) {
                alertMsg += `\n\nChamps disponibles: ${error.available_fields.join(', ')}`;
                if (error.suggestion) {
                    alertMsg += `\n\nSuggestion: utilisez "${error.suggestion}"`;
                }
            }
            
            // Afficher une alerte Bootstrap
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
            alertDiv.innerHTML = `
                <i class="fas fa-exclamation-circle"></i> ${alertMsg}
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
            `;
            const cardBody = document.querySelector('.card-body');
            if (cardBody) {
                cardBody.appendChild(alertDiv);
                setTimeout(() => alertDiv.remove(), 5000);
            }
            
            // Afficher un message d'erreur sur le canvas
            const canvas = document.getElementById('chart-canvas');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#fee';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#c33';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                const lines = errorMsg.split('\n');
                lines.forEach((line, i) => {
                    ctx.fillText(line, canvas.width / 2, canvas.height / 2 + (i * 20));
                });
            }
        });
}

function getThemeColors(type, border = false) {
    const theme = document.documentElement.getAttribute('data-theme') || 'default';
    /* Palettes alignées sur daisyUI / specs projet */
    const colors = {
        default: border ? '#3B82F6' : 'rgba(59, 130, 246, 0.6)',
        dark: border ? '#60A5FA' : 'rgba(96, 165, 250, 0.6)',
        black: border ? '#60A5FA' : 'rgba(96, 165, 250, 0.6)',
        'liquid-glass': border ? '#89D2DC' : 'rgba(137, 210, 220, 0.6)',
        nostalgie: border ? '#D97706' : 'rgba(217, 119, 6, 0.6)',
        ocean: border ? '#0EA5E9' : 'rgba(14, 165, 233, 0.6)',
        sunset: border ? '#F97316' : 'rgba(249, 115, 22, 0.6)',
        forest: border ? '#16A34A' : 'rgba(22, 163, 74, 0.6)'
    };
    
    if (type === 'pie' || type === 'doughnut') {
        const baseColor = colors[theme] || colors.default;
        return [
            baseColor.replace('0.6', '0.9'),
            baseColor.replace('0.6', '0.7'),
            baseColor.replace('0.6', '0.5'),
            baseColor.replace('0.6', '0.4'),
            baseColor.replace('0.6', '0.3')
        ];
    }
    
    return colors[theme] || colors.default;
}

// Grid Management
let gridCounter = 0;

function generateGrid() {
    const modelSelect = document.getElementById('grid-model');
    const model = modelSelect ? modelSelect.value : '';
    const description = document.getElementById('grid-description').value || `Grille ${model}`;
    
    // Toujours utiliser les champs du modèle sélectionné (data-fields) pour afficher nom, slug, description, prix, stock, etc.
    // Envoyer TOUJOURS toutes les colonnes disponibles pour garantir l'affichage complet
    const dataFields = modelSelect && modelSelect.selectedIndex >= 0
        ? (modelSelect.options[modelSelect.selectedIndex].getAttribute('data-fields') || '')
        : '';
    const columns = dataFields ? dataFields.split(',').map(function(c) { return c.trim(); }).filter(Boolean) : [];
    // Toujours envoyer les colonnes si disponibles, sinon laisser l'API utiliser tous les champs du modèle
    const url = columns.length > 0
        ? `/admin_custom/api/grid-data/?model=${encodeURIComponent(model)}&${columns.map(function(c) { return 'columns=' + encodeURIComponent(c); }).join('&')}`
        : `/admin_custom/api/grid-data/?model=${encodeURIComponent(model)}`;
    
    // Afficher le loader
    const loadingAlert = document.getElementById('grid-loading');
    if (loadingAlert) {
        loadingAlert.style.display = 'block';
    }
    
    const generateBtn = document.getElementById('generate-grid');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Création...';
    }
    
    fetch(url)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.error) {
                throw new Error(data.error);
            }
            if (!data.columns || !Array.isArray(data.columns)) {
                data.columns = [];
            }
            if (!data.data || !Array.isArray(data.data)) {
                data.data = [];
            }
            gridCounter++;
            const gridId = 'grid-' + gridCounter;
            const gridsContainer = document.getElementById('grids-container');
            
            // Créer l'élément de grille avec style AdminLTE
            const gridItem = document.createElement('div');
            gridItem.className = 'card card-primary card-outline';
            gridItem.id = gridId;
            gridItem.style.marginBottom = '20px';
            
            let html = `
                <div class="card-header">
                    <h3 class="card-title">
                        <i class="fas fa-table"></i> ${description}
                    </h3>
                    <div class="card-tools">
                        <button type="button" class="btn btn-tool" onclick="this.closest('.card').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="icon fas fa-info"></i>
                        Modèle: <strong>${model}</strong> | Colonnes: <strong>${(data.columns && data.columns.length) ? data.columns.join(', ') : 'Tous les champs'}</strong>
                    </div>
                    <div class="table-responsive">
                        <table id="${gridId}-table" class="table table-bordered table-striped table-hover" style="width:100%">
                            <thead>
                                <tr>`;
            data.columns.forEach(col => {
                html += `<th>${col}</th>`;
            });
            html += `</tr>
                            </thead>
                            <tbody>`;
            
            data.data.forEach(row => {
                html += '<tr>';
                data.columns.forEach(col => {
                    html += `<td>${row[col] || '-'}</td>`;
                });
                html += '</tr>';
            });
            
            html += `</tbody>
                        </table>
                    </div>
                </div>
            `;
            gridItem.innerHTML = html;
            
            gridsContainer.appendChild(gridItem);
            
            // Masquer le loader
            if (loadingAlert) {
                loadingAlert.style.display = 'none';
            }
            
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-plus"></i> Créer la grille';
            }
            
            // Initialiser DataTables avec style AdminLTE
            setTimeout(() => {
                $(`#${gridId}-table`).DataTable({
                    language: {
                        url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/fr-FR.json'
                    },
                    pageLength: 10,
                    order: [[0, 'desc']],
                    responsive: true,
                    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                         '<"row"<"col-sm-12"tr>>' +
                         '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
                    drawCallback: function() {
                        // Appliquer les styles AdminLTE
                        $(this.api().table().container()).addClass('table-bordered table-striped table-hover');
                    }
                });
            }, 100);
            
            // Ne pas vider les colonnes pour garder la liste visible ; vider seulement la description
            var descEl = document.getElementById('grid-description');
            if (descEl) descEl.value = '';
        })
        .catch(error => {
            console.error('Erreur lors de la génération de la grille:', error);
            
            // Masquer le loader
            const loadingAlert = document.getElementById('grid-loading');
            if (loadingAlert) {
                loadingAlert.style.display = 'none';
            }
            
            const generateBtn = document.getElementById('generate-grid');
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-plus"></i> Créer la grille';
            }
            
            // Afficher une alerte Bootstrap
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
            alertDiv.innerHTML = `
                <i class="fas fa-exclamation-circle"></i> Erreur lors de la génération de la grille. Vérifiez que les colonnes existent.
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
            `;
            const cardBody = document.querySelector('.card-body');
            if (cardBody) {
                cardBody.appendChild(alertDiv);
                setTimeout(() => alertDiv.remove(), 5000);
            }
        });
}

// Mise à jour dynamique des champs selon le modèle - utilise l'auto-découverte
function updateChartFields() {
    const modelSelect = document.getElementById('chart-model');
    const fieldSelect = document.getElementById('chart-field');
    const fieldHelp = document.getElementById('field-help');
    
    if (!modelSelect || !fieldSelect) return;
    
    const selectedModel = modelSelect.value;
    
    if (!selectedModel) {
        fieldSelect.innerHTML = '<option value="">-- Sélectionner d\'abord un modèle --</option>';
        if (fieldHelp) fieldHelp.textContent = 'Sélectionnez d\'abord un modèle';
        return;
    }
    
    // Afficher un loader
    fieldSelect.innerHTML = '<option value="">Chargement...</option>';
    fieldSelect.disabled = true;
    
    // Récupérer les champs via l'API d'auto-découverte
    fetch(`/admin_custom/api/model-fields/?model=${selectedModel}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors de la récupération des champs');
            }
            return response.json();
        })
        .then(data => {
            fieldSelect.innerHTML = '';
            fieldSelect.disabled = false;
            
            if (data.fields && data.fields.length > 0) {
                // Ajouter l'option par défaut
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '-- Sélectionner un champ --';
                fieldSelect.appendChild(defaultOption);
                
                // Ajouter les champs disponibles
                data.fields.forEach(field => {
                    const option = document.createElement('option');
                    option.value = field;
                    option.textContent = field;
                    fieldSelect.appendChild(option);
                });
                
                if (fieldHelp) {
                    fieldHelp.textContent = `${data.fields.length} champ(s) numérique(s) disponible(s)`;
                }
            } else {
                fieldSelect.innerHTML = '<option value="">Aucun champ numérique disponible</option>';
                if (fieldHelp) {
                    fieldHelp.textContent = 'Ce modèle n\'a pas de champs numériques pour les graphiques';
                }
            }
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des champs:', error);
            fieldSelect.innerHTML = '<option value="">Erreur de chargement</option>';
            fieldSelect.disabled = false;
            if (fieldHelp) {
                fieldHelp.textContent = 'Erreur lors du chargement des champs';
            }
        });
}

// Remplir les colonnes avec tous les champs quand on change de modèle (grilles)
function updateGridColumnsFromModel() {
    const modelSelect = document.getElementById('grid-model');
    const columnsInput = document.getElementById('grid-columns');
    if (!modelSelect || !columnsInput) return;
    const opt = modelSelect.options[modelSelect.selectedIndex];
    const fieldsStr = opt && opt.getAttribute('data-fields');
    if (fieldsStr) {
        const fields = fieldsStr.split(',').filter(Boolean);
        columnsInput.placeholder = fields.length + ' champs disponibles';
        // Pré-remplir avec tous les champs pour afficher nom, état, montants, dates, etc.
        columnsInput.value = fields.join(', ');
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    const generateChartBtn = document.getElementById('generate-chart');
    const generateGridBtn = document.getElementById('generate-grid');
    const chartModelSelect = document.getElementById('chart-model');
    const gridModelSelect = document.getElementById('grid-model');
    
    if (generateChartBtn) {
        generateChartBtn.addEventListener('click', generateChart);
    }
    
    if (generateGridBtn) {
        generateGridBtn.addEventListener('click', generateGrid);
    }
    
    if (chartModelSelect) {
        chartModelSelect.addEventListener('change', updateChartFields);
        updateChartFields();
    }
    
    if (gridModelSelect) {
        gridModelSelect.addEventListener('change', updateGridColumnsFromModel);
        updateGridColumnsFromModel();
    }
});
