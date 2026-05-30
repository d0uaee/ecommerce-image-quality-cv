# E-commerce Image Quality

**E-commerce Image Quality** est un projet PFE en computer vision, NLP et IA multimodale. Il propose un systeme **zero-shot** capable d'evaluer automatiquement la qualite d'une image produit e-commerce a partir d'une image, d'un titre et d'une description.

Le systeme selectionne la region pertinente du produit, calcule plusieurs criteres de qualite visuelle, mesure la coherence image / texte, puis produit un score global explicable avec des recommandations en francais et en darija.

## Ce que le projet demontre

Le projet montre qu'il est possible de construire un pipeline d'evaluation exploitable sans entrainer un modele local specifique. La contribution principale n'est pas un nouveau modele supervise, mais une architecture lisible qui combine :

- traitement du texte vendeur
- proposition de regions candidates
- selection du produit par signaux multimodaux
- analyse de qualite visuelle
- score global calibre
- protocole experimental reproductible

## Perimetre fonctionnel

Le projet couvre trois categories :

- `shoes`
- `clothing`
- `portable_electronics`

Il inclut une application Streamlit avec :

- mode `Analyse unique`
- mode `Batch`
- mode `Debug`
- extension `Assistant annonce`

L'assistant annonce est une extension pratique pour aider un vendeur a generer une fiche produit. Il ne remplace pas le pipeline scientifique principal d'evaluation de qualite.

## Resultats finaux

| Mesure | Valeur |
| --- | ---: |
| Spearman principal, score auto vs evaluation humaine principale | `0.7122` |
| p-value principale | `6.64e-09` |
| Spearman, score auto vs moyenne de 8 annotateurs | `0.675243` |
| Nombre d'images annotees | `50` |
| Nombre d'annotateurs dans la validation multi-annotateurs | `8` |

Ces resultats indiquent que le score automatique suit nettement le jugement humain, tout en restant dans un cadre zero-shot explicable.

## Ce que le projet ne pretend pas faire

Le projet ne pretend pas remplacer un systeme industriel entraine sur des millions d'images. Il ne pretend pas non plus generaliser parfaitement a toutes les categories e-commerce. Son interet est de proposer une methode robuste, interpretable et defendable dans un cadre academique, avec un scope clairement delimite.

## Lecture recommandee

Pour comprendre le projet rapidement :

1. [Vue d'ensemble](getting-started/overview.md)
2. [Quickstart](getting-started/quickstart.md)
3. [Architecture](project/architecture.md)
4. [Methodologie zero-shot](methodology/zero-shot-rationale.md)
5. [Resultats finaux](evaluation/final-results.md)
6. [Limites](academic/limitations.md)

```{toctree}
:maxdepth: 2
:caption: Prise en main

getting-started/overview
getting-started/installation
getting-started/quickstart
getting-started/first-run
local-access
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
