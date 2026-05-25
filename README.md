# E-commerce Image Quality

Projet PFE centré sur un pipeline zero-shot qui évalue la qualité d'une photo produit
e-commerce et génère un score avec des conseils en français pour de petits vendeurs.

## Principes du projet

- Aucun entraînement de modèle : pipeline multimodal zero-shot uniquement.
- Le texte de l'annonce (`titre + description`) est la source de vérité.
- Pas d'OCR dans le chemin critique du scoring.
- Scope limité à trois familles : `shoes`, `clothing`, `portable_electronics`.
- Les mauvaises images sont générées par dégradation contrôlée des bonnes images.

## Pipeline cible

```text
annonce (image + titre + description)
 -> text_processor
 -> candidate_region_generator
 -> selector
 -> analyzer
 -> global_scorer
 -> conseils FR / Darija
 -> application Streamlit
```

## Arborescence

```text
ecommerce-image-quality/
├── app.py
├── README.md
├── requirements.txt
├── config.py
├── data/
│   ├── raw_images/
│   ├── clean_references/
│   └── degraded/
└── src/
```

## Dépendances clés

- Vision : `opencv-contrib-python`, `scipy`, `scikit-image`, `matplotlib`
- Données et app : `pandas`, `streamlit`
- NLP : `spacy`, `rapidfuzz`
- CLIP / multimodal : `torch`, `torchvision`, `transformers`

## Lancement

```bash
pip install -r requirements.txt
streamlit run app.py
```
