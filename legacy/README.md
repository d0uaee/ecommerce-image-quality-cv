# legacy/ — Première itération abandonnée

## Contexte

Ces fichiers constituent la **première itération** du système d'évaluation de photos
e-commerce, basée sur une architecture OCR + Grounding DINO + BLIP.

Cette approche a été **abandonnée** au profit de l'architecture multimodale zero-shot
pilotée par le texte de l'annonce (titre + description), décrite ci-dessous.

## Pourquoi abandonnée

| Problème | Détail |
|---|---|
| OCR sur le chemin critique | `ocr.py` extrayait le texte depuis l'image — or le texte de l'annonce est disponible directement. L'OCR ajoutait bruit et latence. |
| DINO activé par défaut | `detector.py` chargeait Grounding DINO au démarrage, même quand inutile (~900 MB). |
| BLIP non demandé | `caption.py` générait des légendes BLIP — non prévu dans la spec, modèle lourd. |
| n8n / scraping concurrents | `n8n_search.py` ajoutait une dépendance externe (n8n webhook) hors-spec. |
| Architecture fragmentée | `scorer.py` et `visualizer.py` utilisaient des clés de critères (`jpeg_artifacts`, `lighting_uniformity`…) incompatibles avec `analyzer.py`. |
| `demo_pipeline.py` trompeur | Affichait des scores **hardcodés** (75 %, 100 %…) sans appeler le vrai pipeline. |

## Architecture actuelle (pipeline zero-shot)

```
annonce (image + titre + description)
  → src/text_processor.py     — nettoyage spaCy + embedding CLIP texte
  → src/candidate_region_generator.py — régions candidates (saliency / contours)
  → src/selector.py           — sélection crop par score CLIP + taille + catégorie
  → src/analyzer.py           — 6 critères qualité + conseils FR/Darija
  → app.py                    — interface Streamlit
```

## Fichiers conservés ici

| Fichier | Rôle original |
|---|---|
| `ocr.py` | Extraction texte via EasyOCR |
| `nlp.py` | Extraction entités (marque, prix…) depuis texte OCR |
| `caption.py` | Génération légende BLIP + fiche produit française |
| `detector.py` | Détection produit via Grounding DINO (activé par défaut) |
| `n8n_search.py` | Recherche concurrents Jumia via n8n ou scraping direct |
| `visualizer.py` | Annotation image avec scores (clés incompatibles) |
| `scorer.py` | Façade de score — bugs de seuils et de kwargs |
| `demo_pipeline.py` | Démo avec scores hardcodés, n'appelait pas le vrai pipeline |
