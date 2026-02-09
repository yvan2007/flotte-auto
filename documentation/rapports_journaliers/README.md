# Rapports journaliers — Projet FLOTTE

Rapports journaliers au format DOCX pour la semaine d'amélioration (lundi 2 au lundi 9 février 2025).

**Dernier rapport journalier :** `Rapport_journalier_FLOTTE_synthese_finale.docx` — rapport combiné (8–9 février + toutes les modifs), 2 pages.

## Équipe

- **KOUAKOU EBOUHO** — Scrum Master  
- **KONAN OCEANE** — Product Owner  
- **YOBOUKOI DIVINE** — Développeuse  
- **DJEDJE ESTHER** — Développeuse  

## Contenu des rapports

Chaque rapport (2 pages maximum) contient :

- **Réalisations du jour** : ce qui a été fait
- **Répartition des tâches** : qui a fait quoi
- **Améliorations et remarques** : erreurs corrigées, points d’attention
- **Prévision lendemain** : objectifs du jour suivant  

Les 4 axes d’amélioration couverts dans la semaine :

1. **Interface** : sidebar sticky, revue des couleurs, couleur véhicule en select  
2. **Charges d’importation** : fret, dédouanement, transitaire, coût total  
3. **Pièces importées** : gestion des pièces, coûts, quantités, lien véhicules  
4. **Location** : coût, frais annexes, contraventions, pénalités, impact coût total  

## Régénérer les rapports

Depuis la racine du projet :

```bash
pip install python-docx
python documentation/generer_rapports_journaliers.py
```

Les fichiers `.docx` sont créés dans ce dossier.
