# Architecture du projet

## Vue generale

L'architecture est organisee autour d'un pipeline sequentiel. Chaque module transforme une partie de l'information, puis transmet un resultat interpretable au module suivant.

```text
image + titre + description
        |
        v
text_processor
        |
        v
candidate_region_generator
        |
        v
selector
        |
        v
analyzer
        |
        v
score global + recommandations
```

## Modules principaux

| Module | Role | Sortie principale |
| --- | --- | --- |
| `text_processor.py` | Nettoyer le texte et extraire categorie, couleur, marque, embedding | dictionnaire texte structure |
| `candidate_region_generator.py` | Proposer des regions candidates dans l'image | liste de bounding boxes |
| `selector.py` | Choisir le crop produit le plus pertinent | crop selectionne et scores |
| `analyzer.py` | Evaluer la qualite du crop | sous-scores et score global |
| `listing_assistant.py` | Generer une aide vendeur optionnelle | titre, description, checklist |
| `app.py` | Orchestrer l'interface Streamlit | experience utilisateur |

## Flux de donnees

Le texte et l'image avancent ensemble. Le texte donne le contexte attendu, tandis que l'image apporte le contenu visuel. Le selector utilise cette relation pour choisir le produit qui correspond le mieux a l'annonce.

Le module analyzer travaille ensuite sur le crop selectionne. Cela evite d'evaluer toute l'image lorsque le produit n'occupe qu'une partie de la scene.

## Separation entre coeur scientifique et extension produit

Le coeur scientifique correspond a :

- `text_processor`
- `candidate_region_generator`
- `selector`
- `analyzer`

L'extension `Assistant annonce` est utile en demonstration, mais elle est volontairement separee de l'evaluation principale. Cette separation evite de melanger generation de texte vendeur et validation scientifique de la qualite image.

## Pourquoi cette architecture est maintenable

Chaque module a une responsabilite claire. Il est donc possible de remplacer une brique sans reecrire tout le projet :

- changer la logique de selection
- ajuster les poids de scoring
- ajouter une categorie
- ameliorer l'assistant annonce
- remplacer un fallback par un webhook externe
