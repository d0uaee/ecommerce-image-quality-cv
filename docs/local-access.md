# Acces local a la documentation

Cette page explique comment ouvrir la documentation hors ligne.

## Chemin local correct

Apres build, le fichier d'accueil HTML se trouve ici :

```text
docs/_build/html/index.html
```

Depuis le dossier du projet, le lien local complet ressemble a :

```text
file:///C:/Users/ahadj/OneDrive/ecommerce-image-quality/docs/_build/html/index.html
```

## Erreur frequente

Le chemin suivant est incorrect :

```text
docs_build/html/index.html
```

Le bon dossier est :

```text
docs/_build/html/
```

## Reconstruire la documentation

```bash
pip install -r docs/requirements.txt
python -m sphinx -b html docs docs/_build/html
```

## Publication Read the Docs

Le depot contient :

- `.readthedocs.yaml`
- `docs/conf.py`
- `docs/requirements.txt`

Ces fichiers permettent a Read the Docs de construire la documentation automatiquement depuis GitHub.
