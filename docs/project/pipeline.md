# Pipeline principal

## 1. Traitement du texte

Le texte vendeur (`titre + description`) est la source de verite principale.

## 2. Generation de regions candidates

Le systeme propose plusieurs zones plausibles dans l'image sans detecteur supervise principal.

## 3. Selection du produit

Le `selector` choisit le crop le plus coherent en combinant :

- similarite texte / image
- centralite
- taille utile
- coherence categorie

## 4. Analyse qualite

Le `analyzer` calcule :

- sharpness
- exposure
- contrast
- color balance
- effective resolution
- framing
- coherence image / texte

## 5. Sortie

Le systeme produit :

- un score global
- des sous-scores
- un crop selectionne
- des recommandations FR / Darija
