# Reproductibilite

## Objectif

Cette page regroupe les commandes et conditions permettant de reproduire les principales sorties du projet.

Elle ne remplace pas les pages d'installation ou de scripts, mais sert de checklist technique rapide.

## Environnement attendu

Le projet est prevu pour un environnement Python local avec dependances installees dans `.venv`.

Depuis la racine du depot :

```powershell
.\.venv\Scripts\python --version
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Pour la documentation :

```powershell
.\.venv\Scripts\python -m pip install -r docs\requirements.txt
```

## Lancer l'application

```powershell
.\.venv\Scripts\streamlit run app.py
```

URL locale :

```text
http://localhost:8501
```

## Reconstruire la documentation HTML

```powershell
.\.venv\Scripts\python -m sphinx -b html docs docs\_build\html
```

Fichier d'entree local :

```text
docs\_build\html\index.html
```

URL locale navigateur :

```text
file:///C:/Users/ahadj/OneDrive/ecommerce-image-quality/docs/_build/html/index.html
```

## Reconstruire le dataset final

Le script principal est :

```powershell
.\.venv\Scripts\python scripts\build_final_dataset.py --verbose
```

Le projet evite de telecharger inutilement de tres gros datasets lorsque des sources plus legeres ou un cache local sont disponibles.

## Generer les degradations controlees

```powershell
.\.venv\Scripts\python scripts\generate_degraded.py
```

Sorties attendues :

- `dataset/degraded/`
- `dataset/degraded_metadata.csv`

## Relancer les evaluations

Evaluation principale :

```powershell
.\.venv\Scripts\python scripts\evaluate_full.py
```

Evaluation par categorie :

```powershell
.\.venv\Scripts\python scripts\evaluate_by_category.py
```

Validation multi-annotateurs :

```powershell
.\.venv\Scripts\python scripts\evaluate_multi_annotator.py
```

Calibration :

```powershell
.\.venv\Scripts\python scripts\calibrate_weights.py
```

Test DINO conditionnel :

```powershell
.\.venv\Scripts\python scripts\test_dino_fallback.py
```

## Fichiers de sortie importants

Les rapports finaux sont centralises dans :

```text
output/reports/
```

Les livrables propres sont centralises dans :

```text
deliverables/
```

La documentation source est dans :

```text
docs/
```

## Resultats de reference

Les valeurs finales a retrouver dans les rapports sont :

| Mesure | Valeur |
| --- | ---: |
| Spearman principal | `0.7122` |
| p-value principale | `6.64e-09` |
| Spearman vs moyenne de 8 annotateurs | `0.675243` |

## Points de vigilance

Certains composants peuvent dependre :

- de modeles telecharges a la demande
- d'une connexion reseau
- d'un cache local
- d'une variable d'environnement pour le webhook n8n

L'application reste utilisable sans webhook externe grace au fallback local de l'assistant annonce.
