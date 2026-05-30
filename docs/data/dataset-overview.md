# Vue d'ensemble du dataset

## Objectif du dataset

Le dataset final sert a tester un systeme d'evaluation de qualite photo, pas a entrainer un modele. Les images propres servent de references et les images degradees permettent de verifier si les criteres reagissent correctement.

## Categories

Le scope final est volontairement limite a trois familles :

- `shoes`
- `clothing`
- `portable_electronics`

Ce choix reduit le bruit experimental et rend la soutenance plus claire. Il permet aussi d'analyser les erreurs par categorie.

## Organisation

```text
dataset/
|- originals/
|  |- shoes/
|  |- clothing/
|  `- portable_electronics/
|- degraded/
|  |- shoes/
|  |- clothing/
|  `- portable_electronics/
|- metadata.csv
`- degraded_metadata.csv
```

## Volumes

| Partie | Volume |
| --- | ---: |
| Images propres | `180` |
| Images propres par categorie | `60` |
| Images degradees | `3240` |

## Logique experimentale

Les mauvaises images sont generees a partir des images propres. Cette strategie permet de connaitre la degradation appliquee et d'associer chaque image degradee a une reference propre.

Cette approche rend le protocole plus controlable qu'une collecte aleatoire de mauvaises images.

## Limites

Le dataset reste de taille modeste et limite a trois categories. Il est suffisant pour un PFE et pour une validation experimentale ciblee, mais il ne doit pas etre interprete comme un benchmark universel de qualite e-commerce.
