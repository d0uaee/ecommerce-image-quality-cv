# Quickstart

Cette page permet de tester le projet rapidement, sans lire toute la documentation.

## 1. Installer les dependances

```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

## 2. Lancer l'application

```bash
streamlit run app.py
```

Ouvrir ensuite :

```text
http://localhost:8501
```

## 3. Tester une image propre

Choisir une image dans :

- `dataset/originals/shoes/`
- `dataset/originals/clothing/`
- `dataset/originals/portable_electronics/`

Dans l'interface, renseigner :

- un titre coherent avec le produit
- une description simple

Verifier ensuite :

- le crop selectionne
- le score global
- la coherence image / texte
- les recommandations

## 4. Tester une image degradee

Choisir une image dans :

- `dataset/degraded/`

Comparer le score avec une image propre equivalente. Le score doit generalement baisser lorsque la degradation est visible.

## 5. Lire les resultats experimentaux

Les rapports principaux sont :

- `output/reports/evaluation_report.md`
- `output/reports/multi_annotator_report.md`
- `output/reports/category_evaluation_summary.csv`

## 6. Commandes utiles

```bash
python generate_degraded.py
python evaluate_analyzer.py
python evaluate_full.py
python scripts/evaluate_multi_annotator.py
```

Ces scripts permettent de regenerer les degradations, les evaluations et les rapports.
