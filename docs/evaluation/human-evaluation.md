# Validation humaine principale

## Objectif

La validation humaine sert a verifier si le score automatique correspond au jugement d'un utilisateur humain sur la qualite d'une image produit.

Le score humain ne sert pas a entrainer un modele local. Il sert a evaluer et a calibrer le pipeline.

## Protocole

Un ensemble de `50` images a ete note manuellement. Chaque image est associee a :

- un fichier image
- une categorie
- un titre et une description
- un score automatique
- un score humain

Les notes humaines permettent de comparer le comportement du systeme a une reference subjective mais concrete.

## Grille d'annotation

L'annotation humaine se base sur une logique simple :

| Zone de score | Interpretation |
| --- | --- |
| `0-2` | Image tres faible, difficilement exploitable |
| `3-4` | Image faible, plusieurs problemes visibles |
| `5-6` | Image moyenne, exploitable mais perfectible |
| `7-8` | Bonne image produit |
| `9-10` | Image tres bonne, proche d'une photo e-commerce professionnelle |

L'annotateur ne doit pas etre photographe professionnel. Il doit seulement repondre a une question pratique :

> Est-ce que cette image inspire confiance pour une annonce e-commerce ?

## Resultat principal

| Mesure | Valeur |
| --- | ---: |
| Nombre d'images | `50` |
| Spearman score automatique vs score humain | `0.7122` |
| p-value | `6.64e-09` |

La p-value tres faible indique que la correlation observee est statistiquement significative dans ce protocole.

## Interpretation

Une correlation de `0.7122` est forte pour une tache subjective. Elle signifie que le systeme reproduit bien la tendance generale du jugement humain.

Il ne faut pas l'interpreter comme une precision parfaite image par image. Une photo peut recevoir un score automatique different du score humain si :

- le texte est incomplet ou ambigu
- le crop selectionne n'est pas ideal
- la photo est bonne visuellement mais incoherente avec l'annonce
- l'humain privilegie un critere different du systeme

## Analyse des desaccords

Les cas de desaccord ont ete utilises pour ameliorer le projet sans transformer le systeme en modele supervise. Les corrections ont surtout cible :

- `framing`
- `effective_resolution`
- `sharpness`
- coherence image / texte
- interpretation des photos sur fond clair

Cette etape est importante car elle montre une demarche d'ingenierie experimentale : observer, expliquer, ajuster, puis reevaluer.

## Limites du protocole humain principal

Le protocole principal repose sur un nombre limite d'images. Il donne une indication solide pour un PFE, mais il ne remplace pas une etude utilisateur industrielle.

Pour renforcer cette limite, le projet ajoute une validation multi-annotateurs separee.
