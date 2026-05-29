# Architecture du projet

## Vue generale

Le pipeline principal suit cette logique :

```text
annonce (image + titre + description)
 -> text_processor
 -> candidate_region_generator
 -> selector
 -> analyzer
 -> score global
 -> recommandations
 -> application Streamlit
```

## Composants centraux

- `text_processor` : extraction d'indices textuels et embeddings
- `candidate_region_generator` : proposition de regions candidates
- `selector` : selection de la region produit la plus pertinente
- `analyzer` : evaluation des criteres de qualite
- `app.py` : interface et orchestration

## Extension

Le mode **Assistant annonce** est une extension produit. Il ne remplace pas le pipeline scientifique principal.
