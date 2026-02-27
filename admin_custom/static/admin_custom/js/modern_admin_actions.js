/**
 * JavaScript pour gérer les actions admin dans l'interface moderne
 * Gère la sélection multiple, les actions personnalisées et la soumission du formulaire
 */
(function() {
    'use strict';

    // Configuration par défaut pour les actions Django
    const defaults = {
        actionContainer: "div.actions",
        actionCounter: ".action-counter",
        allContainer: ".all",
        acrossInput: "input.select-across",
        acrossClears: ".clear",
        acrossQuestions: ".question",
        allToggleId: "action-toggle",
        selectedClass: "selected"
    };

    function initializeAdminActions() {
        const actionCheckboxes = document.querySelectorAll('input[name="_selected_action"]');
        const actionToggle = document.getElementById(defaults.allToggleId);
        const actionForm = document.querySelector(defaults.actionContainer);
        
        if (!actionForm || actionCheckboxes.length === 0) {
            return;
        }

        const options = {
            ...defaults,
            actionContainer: defaults.actionContainer,
            counterContainer: defaults.actionCounter
        };

        // Fonction pour afficher/masquer les éléments
        function show(selector) {
            document.querySelectorAll(selector).forEach(function(el) {
                el.classList.remove('hidden');
                el.style.display = '';
            });
        }

        function hide(selector) {
            document.querySelectorAll(selector).forEach(function(el) {
                el.classList.add('hidden');
                el.style.display = 'none';
            });
        }

        // Fonction pour mettre à jour le compteur
        function updateCounter() {
            const selected = Array.from(actionCheckboxes).filter(cb => cb.checked).length;
            const total = actionCheckboxes.length;
            const counter = document.querySelector(options.actionCounter);
            
            if (counter) {
                if (selected > 0) {
                    counter.textContent = `${selected} sur ${total} sélectionné${selected > 1 ? 's' : ''}`;
                    counter.style.display = '';
                } else {
                    counter.textContent = '0 sélectionné';
                }
            }
        }

        // Fonction pour cocher/décocher toutes les checkboxes
        function checker(checked) {
            actionCheckboxes.forEach(function(cb) {
                cb.checked = checked;
                const row = cb.closest('tr');
                if (row) {
                    row.classList.toggle(options.selectedClass, checked);
                }
            });
            updateCounter();
        }

        // Gestionnaire pour la checkbox "sélectionner tout"
        if (actionToggle) {
            actionToggle.addEventListener('change', function() {
                checker(this.checked);
                
                // Afficher le message "sélectionner toutes les pages" si nécessaire
                const resultCount = parseInt(actionToggle.dataset.totalCount || actionCheckboxes.length);
                if (this.checked && resultCount > actionCheckboxes.length) {
                    show(options.acrossQuestions);
                    hide(options.counterContainer);
                } else {
                    hide(options.acrossQuestions);
                    show(options.counterContainer);
                }
            });
        }

        // Gestionnaire pour chaque checkbox individuelle
        actionCheckboxes.forEach(function(cb) {
            cb.addEventListener('change', function() {
                const row = this.closest('tr');
                if (row) {
                    row.classList.toggle(options.selectedClass, this.checked);
                }
                updateCounter();
                
                // Mettre à jour la checkbox "sélectionner tout"
                if (actionToggle) {
                    const allChecked = Array.from(actionCheckboxes).every(c => c.checked);
                    actionToggle.checked = allChecked;
                }
            });
        });

        // Gestionnaire pour "Sélectionner toutes les pages"
        document.querySelectorAll(options.acrossQuestions + " a").forEach(function(el) {
            el.addEventListener('click', function(e) {
                e.preventDefault();
                const acrossInputs = document.querySelectorAll(options.acrossInput);
                acrossInputs.forEach(function(acrossInput) {
                    acrossInput.value = '1';
                });
                hide(options.acrossQuestions);
                show(options.acrossClears);
                show(options.allContainer);
                hide(options.counterContainer);
                if (actionToggle) {
                    actionToggle.checked = true;
                }
            });
        });

        // Gestionnaire pour "Effacer la sélection"
        document.querySelectorAll(options.acrossClears + " a").forEach(function(el) {
            el.addEventListener('click', function(e) {
                e.preventDefault();
                const acrossInputs = document.querySelectorAll(options.acrossInput);
                acrossInputs.forEach(function(acrossInput) {
                    acrossInput.value = '0';
                });
                if (actionToggle) {
                    actionToggle.checked = false;
                }
                checker(false);
                hide(options.acrossClears);
                hide(options.allContainer);
                show(options.counterContainer);
            });
        });

        // Gestionnaire pour la soumission du formulaire d'actions
        const changelistForm = document.getElementById('changelist-form');
        if (changelistForm) {
            const actionSelect = changelistForm.querySelector('select[name="action"]');
            const goButton = changelistForm.querySelector('button[name="index"]');
            
            if (actionSelect && goButton) {
                goButton.addEventListener('click', function(e) {
                    const selectedAction = actionSelect.value;
                    const selectedItems = Array.from(actionCheckboxes).filter(cb => cb.checked);
                    
                    if (!selectedAction || selectedAction === '') {
                        e.preventDefault();
                        alert('Veuillez sélectionner une action.');
                        return false;
                    }
                    
                    if (selectedItems.length === 0) {
                        e.preventDefault();
                        alert('Veuillez sélectionner au moins un élément.');
                        return false;
                    }
                    
                    // Confirmation pour les actions de suppression
                    if (selectedAction.includes('delete') || selectedAction === 'delete_selected') {
                        if (!confirm(`Êtes-vous sûr de vouloir supprimer ${selectedItems.length} élément(s) sélectionné(s) ?`)) {
                            e.preventDefault();
                            return false;
                        }
                    }
                });
            }
        }

        // Initialiser le compteur
        updateCounter();
    }

    // Actions personnalisées pour l'interface moderne
    function initializeCustomActions() {
        // Améliorer l'affichage des messages de confirmation pour les actions
        const changelistForm = document.getElementById('changelist-form');
        if (changelistForm) {
            const actionSelect = changelistForm.querySelector('select[name="action"]');
            const goButton = changelistForm.querySelector('button[name="index"]');
            
            if (actionSelect && goButton) {
                // Ajouter des icônes et améliorer l'UX
                actionSelect.addEventListener('change', function() {
                    const selectedAction = this.value;
                    const actionText = this.options[this.selectedIndex].text;
                    
                    // Changer le style du bouton selon l'action
                    if (selectedAction.includes('delete') || selectedAction === 'delete_selected') {
                        goButton.classList.add('btn-danger');
                        goButton.classList.remove('btn-primary');
                    } else {
                        goButton.classList.remove('btn-danger');
                        goButton.classList.add('btn-primary');
                    }
                });
            }
        }
    }

    // Initialiser quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeAdminActions();
            initializeCustomActions();
        });
    } else {
        initializeAdminActions();
        initializeCustomActions();
    }
})();
