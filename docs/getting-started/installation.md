# Installation

## Prerequis

En local, il est recommande d'utiliser :

- Python `3.11`
- `pip`
- un environnement virtuel
- une connexion internet pour le premier chargement de certains modeles

Le projet utilise des bibliotheques de vision, NLP et IA multimodale. Certaines dependances, comme `torch`, `transformers` ou `sentence-transformers`, peuvent prendre du temps a installer.

## Installation sous Windows

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

## Installation sous Linux ou macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

## Dependances principales

| Famille | Bibliotheques |
| --- | --- |
| Interface | `streamlit` |
| Vision | `opencv-contrib-python`, `Pillow`, `scikit-image` |
| Donnees | `numpy`, `pandas`, `scipy` |
| NLP | `spacy`, `rapidfuzz` |
| Multimodal | `sentence-transformers`, `transformers`, `torch` |
| Documentation | `sphinx`, `myst-parser`, `furo` |

## Lancer l'application

```bash
streamlit run app.py
```

L'application est disponible par defaut sur :

```text
http://localhost:8501
```

## Construire la documentation localement

```bash
pip install -r docs/requirements.txt
python -m sphinx -b html docs docs/_build/html
```

La documentation locale s'ouvre ensuite avec :

```text
docs/_build/html/index.html
```

## Problemes frequents

Si le modele spaCy n'est pas installe, le projet utilise des fallbacks, mais l'extraction linguistique peut etre moins riche.

Si le chargement CLIP est lent au premier lancement, c'est normal : certains modeles sont telecharges ou initialises a la demande.
