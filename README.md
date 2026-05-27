# E-commerce Image Quality

Projet PFE centre sur un pipeline zero-shot qui evalue la qualite d'une photo produit
e-commerce et genere un score accompagne de conseils en francais et en darija.

## Objectif

Le systeme aide de petits vendeurs a verifier rapidement si une photo produit est exploitable
pour une fiche e-commerce, sans entrainer de modele specifique.

## Principes du projet

- aucun entrainement de modele dans ce depot
- texte de l'annonce (`titre + description`) = source de verite principale
- aucun OCR dans le chemin critique du scoring
- scope volontairement limite a :
  - `shoes`
  - `clothing`
  - `portable_electronics`
- mauvaises images obtenues par degradation controlee d'images propres

## Pipeline actuel

```text
annonce (image + titre + description)
 -> text_processor
 -> candidate_region_generator
 -> selector
 -> analyzer
 -> score global
 -> conseils FR / Darija
 -> application Streamlit
```

## Modules principaux

- `src/text_processor.py`
  - nettoyage texte
  - extraction couleur / categorie / marque
  - embedding texte CLIP

- `src/candidate_region_generator.py`
  - proposition de regions candidates sans labels
  - saliency OpenCV par defaut
  - fallback DINO activable

- `src/selector.py`
  - selection du bon produit parmi les regions candidates
  - fusion CLIP + heuristiques visuelles + coherence categorie

- `src/analyzer.py`
  - calcul des criteres qualite
  - score global explicable
  - recommandations FR / Darija

- `app.py`
  - interface Streamlit

## Structure minimale

```text
ecommerce-image-quality/
|- app.py
|- config.py
|- requirements.txt
|- README.md
|- DOCUMENTATION.md
|- dataset/
|  |- originals/
|  |- clean_references/
|  |- degraded/
|  `- metadata.csv
`- src/
   |- text_processor.py
   |- candidate_region_generator.py
   |- selector.py
   |- analyzer.py
   `- dictionaries.py
```

## Dependances principales

- vision :
  - `opencv-contrib-python`
  - `scipy`
  - `matplotlib`
  - `pillow`

- donnees et app :
  - `numpy`
  - `pandas`
  - `streamlit`

- NLP :
  - `spacy`
  - `rapidfuzz`

- multimodal :
  - `sentence-transformers`
  - `torch`
  - `torchvision`
  - `transformers`

## Installation

### 1. Installer les dependances Python

```bash
pip install -r requirements.txt
```

### 2. Installer le modele spaCy francais

```bash
python -m spacy download fr_core_news_md
```

## Lancement de l'application

```bash
streamlit run app.py
```

## Evaluation

Scripts utiles :

- `evaluate_analyzer.py`
  - sensibilite des criteres sur les images degradees

- `evaluate_full.py`
  - export CSV pour annotation humaine
  - correlation Spearman
  - rapport consolide

## Etat actuel

Le coeur du pipeline zero-shot est en place et le projet travaille maintenant par defaut
sur `dataset/` comme source principale.

Etat du livrable :

- dataset final propre disponible dans `dataset/originals/`
- dataset degrade disponible dans `dataset/degraded/`
- rapports d'evaluation disponibles dans `output/reports/`

## Idee centrale du PFE

La valeur du projet ne vient pas de l'entrainement d'un nouveau modele.
Elle vient de l'architecture zero-shot multimodale et de l'explicabilite :

- selection explicable du bon crop
- sous-scores qualite lisibles
- coherence image / texte
- recommandations actionnables
