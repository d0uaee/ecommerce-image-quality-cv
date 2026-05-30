# Degradations controlees

## Pourquoi generer des degradations ?

Le projet cherche a evaluer si les criteres de qualite reagissent dans le bon sens. Pour cela, il est plus fiable de partir d'images propres et d'appliquer des degradations controlees que de collecter aleatoirement des images de mauvaise qualite.

## Types de degradations

| Degradation | Critere cible principal | Effet attendu |
| --- | --- | --- |
| `blur` | `sharpness` | baisse forte de la nettete |
| `lowres` | `effective_resolution` | baisse du detail utile |
| `bad_crop` | `framing`, `effective_resolution` | produit moins bien cadre |
| `underexposure` | `exposure` | image trop sombre |
| `overexposure` | `exposure` | image trop claire ou brulee |
| `jpeg` | detail percu | artefacts de compression |

## Niveaux

Chaque degradation existe en trois intensites :

- `low`
- `medium`
- `high`

## Interpretation

Une bonne sensibilite signifie qu'un critere baisse lorsque la degradation qui le concerne est appliquee. Par exemple, `sharpness` doit baisser fortement sur les images floues.

## Resultat important

Les degradations ne sont pas toutes detectees avec la meme facilite. Le flou et la basse resolution sont generalement plus lisibles que certains cas de compression JPEG ou d'exposition complexe.
