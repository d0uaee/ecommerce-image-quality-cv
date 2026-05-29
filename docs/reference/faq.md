# FAQ

## Comment lancer l'application ?

```bash
streamlit run app.py
```

## Pourquoi le systeme est-il zero-shot ?

Parce qu'il ne repose sur aucun entrainement de modele local dans ce depot.

## Pourquoi pas d'OCR ?

Parce que le texte vendeur est la source de verite principale et que l'OCR n'est pas necessaire au chemin critique.

## Que faire si l'assistant annonce tombe en fallback local ?

Verifier la configuration du webhook n8n. Sans `N8N_ASSISTANT_WEBHOOK`, l'application utilise automatiquement `local_assistant`.
