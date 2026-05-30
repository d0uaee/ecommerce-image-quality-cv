# References

## Modeles et concepts

### CLIP

CLIP est une reference importante pour les approches image / texte zero-shot. Le projet s'inscrit dans cette logique : utiliser des representations multimodales pre-entrainees pour comparer une image et un texte sans entrainer un modele specifique au dataset local.

Reference :

- Radford et al., *Learning Transferable Visual Models From Natural Language Supervision*, OpenAI, 2021.

### SentenceTransformers

SentenceTransformers fournit des representations de texte utiles pour comparer titres, descriptions et termes candidats.

Reference :

- Reimers and Gurevych, *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*, 2019.

### spaCy

spaCy est utilise pour le traitement de texte et l'extraction d'informations linguistiques lorsque disponible.

Reference :

- Documentation officielle spaCy.

## Vision par ordinateur

### OpenCV

OpenCV est utilise pour les traitements image classiques :

- lecture d'image
- dimensions
- flou
- contraste
- luminosite
- transformations de degradation

Reference :

- Documentation officielle OpenCV.

### Pillow

Pillow est utilise pour certaines operations image simples et pour la compatibilite avec Streamlit.

## Application et documentation

### Streamlit

Streamlit fournit l'interface utilisateur du projet :

- upload manuel
- mode dataset
- batch
- debug
- assistant annonce
- historique et export

Reference :

- Documentation officielle Streamlit.

### Sphinx et Read the Docs

Sphinx est utilise pour construire cette documentation. Read the Docs peut ensuite publier automatiquement les pages depuis le depot GitHub.

References :

- Documentation officielle Sphinx
- Documentation officielle Read the Docs
- Theme Furo pour Sphinx

## Datasets

Le projet s'appuie sur des sources publiques pour construire un dataset final propre :

- Kaggle Fashion Product Images Dataset pour `shoes` et `clothing`
- Hugging Face Shopify Product Catalogue Dataset pour `portable_electronics`

Le dataset final du projet n'est pas une copie brute complete de ces sources. Il s'agit d'un sous-ensemble filtre, structure et documente.

## Evaluation humaine

La validation humaine et la validation multi-annotateurs s'appuient sur des principes classiques d'evaluation experimentale :

- comparaison entre score automatique et jugement humain
- correlation de Spearman pour donnees ordinales
- analyse des desaccords
- mesure de l'accord entre annotateurs

## Note de lecture

Les references ne sont pas listees pour donner une impression artificielle de complexite. Elles indiquent les briques conceptuelles et techniques qui permettent de situer le projet dans un cadre computer vision / NLP / IA multimodale.
