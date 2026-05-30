# Schema des metadonnees

## `metadata.csv`

Le fichier `dataset/metadata.csv` decrit les images propres.

| Colonne | Description |
| --- | --- |
| `image_id` | identifiant unique de l'image |
| `filename` | nom du fichier image |
| `filepath` | chemin relatif vers l'image |
| `category` | categorie cible |
| `source_dataset` | source ou origine de l'image |
| `title` | titre associe a l'image |
| `description` | description textuelle associee |
| `width` | largeur en pixels |
| `height` | hauteur en pixels |
| `source_type` | type de source |
| `degradation_type` | vide pour les images propres |
| `degradation_level` | vide pour les images propres |
| `human_score` | champ reserve pour annotation |
| `notes` | remarques eventuelles |

## `degraded_metadata.csv`

Le fichier `dataset/degraded_metadata.csv` decrit les images degradees.

| Colonne | Role |
| --- | --- |
| `filepath` | chemin de l'image degradee |
| `category` | categorie du produit |
| `degradation_type` | type de degradation appliquee |
| `degradation_level` | intensite de la degradation |

## Utilisation

Ces metadonnees sont utilisees pour :

- charger les images dans l'application
- relier les images degradees aux images propres
- produire les rapports d'evaluation
- analyser les performances par categorie et type de degradation

## Bonne pratique

Les chemins doivent rester relatifs au depot afin que le projet reste transportable vers une autre machine.
