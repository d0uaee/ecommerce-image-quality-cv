# Installation

## Prerequis

- Python `3.11` recommande
- `pip`
- environnement virtuel recommande

## Installation locale

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

## Dependances importantes

- `opencv-contrib-python`
- `sentence-transformers`
- `transformers`
- `torch`
- `spacy`
- `streamlit`

## Lancer l'application

```bash
streamlit run app.py
```

L'application demarre ensuite sur `http://localhost:8501` par defaut.
