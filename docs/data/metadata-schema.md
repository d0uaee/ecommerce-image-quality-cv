# Schema des metadonnees

## `metadata.csv`

Colonnes principales :

- `image_id`
- `filename`
- `filepath`
- `category`
- `source_dataset`
- `title`
- `description`
- `width`
- `height`

## `degraded_metadata.csv`

Colonnes supplementaires importantes :

- `source_type`
- `degradation_type`
- `degradation_level`

## Usage

Ces fichiers servent a :

- retrouver les images
- interpreter les evaluations
- relier les degradations aux references propres
