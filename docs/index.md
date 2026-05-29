# E-commerce Image Quality

Bienvenue dans la documentation officielle du projet **E-commerce Image Quality**.

Ce projet implemente un systeme **zero-shot multimodal** d'evaluation automatique de la qualite d'images produit e-commerce. A partir d'une image, d'un titre et d'une description, le systeme :

- selectionne automatiquement la region pertinente du produit
- evalue plusieurs criteres de qualite visuelle
- calcule un score global explicable
- mesure la coherence image / texte
- genere des recommandations en francais et en darija

Le projet inclut egalement un protocole experimental complet :

- dataset final propre organise par categories
- degradations controlees
- evaluation humaine
- validation multi-annotateurs
- analyses par categorie et calibration du score

## Resultats finaux

- **Spearman principal** (score automatique vs evaluation humaine principale) : `0.7122`
- **Spearman** (score automatique vs moyenne de 8 annotateurs) : `0.675243`
- **p-value principale** : `6.64e-09`

## Public cible

Cette documentation s'adresse a :

- des enseignants et membres de jury
- des developpeurs
- des utilisateurs techniques
- des recruteurs
- des lecteurs academiques interesses par une approche zero-shot explicable

## Lecture recommandee

Si vous decouvrez le projet, commencez par :

1. [Vue d'ensemble](getting-started/overview.md)
2. [Installation](getting-started/installation.md)
3. [Quickstart](getting-started/quickstart.md)
4. [Architecture du projet](project/architecture.md)
5. [Resultats finaux](evaluation/final-results.md)

```{toctree}
:maxdepth: 2
:caption: Prise en main

getting-started/overview
getting-started/installation
getting-started/quickstart
getting-started/first-run
```

```{toctree}
:maxdepth: 2
:caption: Projet

project/architecture
project/repository-structure
project/pipeline
project/configuration
```

```{toctree}
:maxdepth: 2
:caption: Donnees

data/dataset-overview
data/metadata-schema
data/degradations
data/generated-outputs
```

```{toctree}
:maxdepth: 2
:caption: Methodologie

methodology/zero-shot-rationale
methodology/text-processing
methodology/candidate-regions
methodology/product-selection
methodology/quality-analysis
methodology/scoring-and-recommendations
```

```{toctree}
:maxdepth: 2
:caption: Utilisation

usage/streamlit-app
usage/batch-mode
usage/debug-mode
usage/listing-assistant
```

```{toctree}
:maxdepth: 2
:caption: Scripts

scripts/scripts-overview
scripts/dataset-building
scripts/degradation-generation
scripts/evaluation-scripts
scripts/calibration-and-analysis
```

```{toctree}
:maxdepth: 2
:caption: Evaluation

evaluation/experimental-protocol
evaluation/controlled-degradations
evaluation/human-evaluation
evaluation/multi-annotator-validation
evaluation/category-analysis
evaluation/final-results
```

```{toctree}
:maxdepth: 2
:caption: Lecture academique

academic/methodological-choices
academic/limitations
academic/future-work
academic/defense-notes
```

```{toctree}
:maxdepth: 2
:caption: Reference

reference/faq
reference/glossary
reference/references
reference/changelog
```

```{toctree}
:maxdepth: 2
:caption: Appendices

appendices/file-map
appendices/report-map
appendices/reproducibility
```
