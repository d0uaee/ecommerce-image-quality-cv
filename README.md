# Outil de Qualité d'Images Produit E-commerce

Système automatisé d'évaluation de la qualité d'images produit pour les vendeurs
Jumia Maroc et Avito Maroc. Analyse chaque image sur 6 critères objectifs, génère
une annonce en français, et recherche des produits similaires sur Jumia.

## Pipeline

```
Image produit
     │
     ▼
┌─────────────┐     ┌──────────┐     ┌──────────┐
│  Detector   │────▶│   OCR    │────▶│   NLP    │
│ (DINO+mask) │     │(EasyOCR) │     │(entités) │
└─────────────┘     └──────────┘     └──────────┘
                                           │
     ┌─────────────────────────────────────┘
     ▼
┌─────────────┐     ┌──────────┐     ┌──────────────┐
│  Analyzer   │────▶│ Caption  │────▶│   n8n/Jumia  │
│ (6 critères)│     │  (BLIP)  │     │  (concurrence│
└─────────────┘     └──────────┘     └──────────────┘
                                           │
                                           ▼
                                   ┌──────────────┐
                                   │  Streamlit   │
                                   │  Dashboard   │
                                   └──────────────┘
```

## Installation

```bash
git clone <repo>
cd ecommerce-image-quality

python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

Ouvre automatiquement sur `http://localhost:8501`.

## Modules

| Module | Fichier | Rôle |
|--------|---------|------|
| Détection | `src/detector.py` | Localise le produit (Grounding DINO + GrabCut, fallback Otsu) |
| OCR | `src/ocr.py` | Extrait le texte visible (EasyOCR FR+EN) |
| NLP | `src/nlp.py` | Identifie marque, modèle, couleur, stockage, prix |
| Analyse qualité | `src/analyzer.py` | Calcule 6 critères + score global pondéré |
| Annonce | `src/caption.py` | Génère titre et description en français (BLIP + templates) |
| Concurrence | `src/n8n_search.py` | Recherche produits similaires sur Jumia Maroc |
| Score rapide | `src/scorer.py` | Façade : score global + grade A–F |
| Visualisation | `src/visualizer.py` | Superpose détection + scores sur l'image |

### Critères d'analyse (src/analyzer.py)

| Critère | Poids | Description |
|---------|-------|-------------|
| `jpeg_artifacts` | 20 % | Netteté globale (variance du Laplacien) — détecte les photos floues ou sous-détaillées |
| `lighting_uniformity` | 20 % | Uniformité de l'éclairage (grille 3×3) |
| `edge_quality` | 20 % | Netteté des contours produit (Canny) |
| `color_consistency` | 15 % | Balance des blancs et naturalité des couleurs |
| `effective_resolution` | 15 % | Détection de sur-échantillonnage + taille absolue |
| `clip_coherence` | 10 % | Cohérence image-texte (CLIP ViT-B/32) |

## Dataset

300 images produit issues de Jumia Maroc, réparties en 3 catégories :
- **electronics** — smartphones, tablettes, accessoires
- **clothing** — vêtements, chaussures, accessoires mode
- **home_appliances** — électroménager, cuisine, maison

Images téléchargées via `src/scraper.py` (respect robots.txt, délai 2–5 s).

## Technologies

- **OpenCV** — traitement d'image, JPEG DCT, Canny, GrabCut
- **Grounding DINO** — détection d'objet zero-shot par texte
- **CLIP** (openai/clip-vit-base-patch32) — cohérence image-texte
- **BLIP** (Salesforce/blip-image-captioning-base) — génération de légendes
- **EasyOCR** — reconnaissance de texte FR+EN sur images produit
- **Streamlit** — dashboard interactif avec export CSV
- **n8n** — workflow de recherche Jumia (webhook + fallback scraping)

## Structure

```
ecommerce-image-quality/
├── app.py                  # Dashboard Streamlit
├── src/
│   ├── analyzer.py         # 6 critères qualité + score global
│   ├── caption.py          # Génération d'annonces en français
│   ├── detector.py         # Détection et segmentation produit
│   ├── nlp.py              # Extraction d'entités produit
│   ├── n8n_search.py       # Recherche concurrents Jumia
│   ├── ocr.py              # Extraction de texte (EasyOCR)
│   ├── scorer.py           # Score rapide + grade A–F
│   ├── visualizer.py       # Annotations visuelles
│   └── scraper.py          # Scraper dataset Jumia
├── data/
│   ├── raw_images/         # Images par catégorie
│   └── batch_results.csv   # Résultats analyse batch
└── requirements.txt
```
