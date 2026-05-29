# Guide de Lecture du Livrable

Ce depot contient le livrable final du PFE :

- systeme zero-shot d'evaluation de qualite d'images produit e-commerce
- application Streamlit de demonstration
- dataset final propre et dataset degrade
- scripts d'evaluation
- rapports experimentaux et presentation de soutenance

## Lecture recommandee

Si vous souhaitez aller directement a l'essentiel, lire dans cet ordre :

1. `README.md`
   - vue d'ensemble rapide du projet
   - objectif
   - architecture generale
   - lancement de l'application

2. `DOCUMENTATION.md`
   - description technique detaillee
   - modules
   - pipeline
   - protocole experimental
   - limites et perspectives

3. `output/reports/evaluation_report.md`
   - resultats experimentaux consolides
   - sensibilite aux degradations
   - corrélation avec evaluation humaine
   - analyse par categorie

4. `output/reports/multi_annotator_report.md`
   - accord entre annotateurs humains
   - corrélation avec la moyenne humaine

5. `deliverables/presentation_soutenance_pfe_zero_shot_1h.pptx`
   - support de presentation complet

## Structure utile du depot

- `app.py`
  - application Streamlit principale

- `config.py`
  - configuration globale du projet

- `src/`
  - coeur du pipeline

- `dataset/originals/`
  - images propres finales

- `dataset/degraded/`
  - images degradees pour l'evaluation

- `output/reports/`
  - rapports, tableaux et figures experimentales

- `deliverables/`
  - supports de soutenance

## Lancer l'application

Installer les dependances :

```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

Lancer l'application :

```bash
streamlit run app.py
```

## Resultats finaux a retenir

- pipeline zero-shot complet, sans entrainement local
- aucun OCR dans le chemin critique
- 3 categories cibles :
  - `shoes`
  - `clothing`
  - `portable_electronics`
- score global explicable
- recommandations en francais et en darija

### Resultats de correlation

- Spearman principal (score auto vs evaluation humaine principale) :
  - `0.7122`

- Spearman (score auto vs moyenne de 8 annotateurs) :
  - `0.675243`

### Lecture rapide

Le projet est scientifiquement defendable car :

- il repose sur un pipeline explicable
- il utilise un protocole de degradations controlees
- il dispose d'une evaluation humaine
- il a ete complete par une validation multi-annotateurs

## Remarque

Le module `Assistant annonce` present dans l'application est une extension produit.
Il ne remplace pas le protocole scientifique principal d'evaluation qualite.
