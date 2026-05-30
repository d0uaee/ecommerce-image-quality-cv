# Resultats finaux

## Synthese

Les resultats finaux montrent que le score automatique est fortement aligne avec le jugement humain, tout en restant dans un cadre zero-shot explicable.

| Mesure | Valeur |
| --- | ---: |
| Images avec evaluation humaine principale | `50` |
| Spearman principal, score auto vs score humain principal | `0.7122` |
| p-value principale | `6.64e-09` |
| Annotateurs dans la validation multi-annotateurs | `8` |
| Spearman score auto vs moyenne de 8 annotateurs | `0.675243` |

La correlation principale indique une relation monotone forte : quand les humains jugent une image meilleure, le systeme tend aussi a augmenter son score.

## Pourquoi Spearman ?

La correlation de Spearman est adaptee car le score humain est ordinal et subjectif. On cherche surtout a savoir si le classement relatif des images est coherent, pas si chaque point numerique est parfaitement identique.

Spearman repond a la question :

> Les images bien notees par les humains ont-elles tendance a etre bien notees par le systeme ?

## Resultats par categorie

| Categorie | Nombre d'images | Moyenne score auto | Moyenne score humain | Spearman | p-value |
| --- | ---: | ---: | ---: | ---: | ---: |
| `shoes` | `16` | `0.6838` | `0.6025` | `0.765028` | `0.000555` |
| `clothing` | `16` | `0.6344` | `0.5281` | `0.670612` | `0.004465` |
| `portable_electronics` | `18` | `0.7027` | `0.5661` | `0.715907` | `0.000834` |

Les trois categories montrent une correlation positive. Les chaussures sont les plus stables dans les resultats finaux, probablement parce que le produit est souvent bien separe du fond et visuellement plus reconnaissable.

## Tests de degradations controlees

Les degradations controlees verifient que le systeme reagit dans le bon sens lorsqu'une image propre est volontairement degradee.

| Degradation | Critere cible | Images testees | Baisse moyenne | Taux de succes |
| --- | --- | ---: | ---: | ---: |
| `blur` | `sharpness` | `540` | `65.30` | `99.63%` |
| `lowres` | `effective_resolution` | `540` | `20.95` | `100.00%` |
| `bad_crop` | `effective_resolution` | `540` | `14.20` | `92.96%` |
| `overexposure` | `exposure` | `540` | `14.35` | `55.56%` |
| `jpeg` | `sharpness` | `540` | `5.95` | `47.96%` |
| `underexposure` | `exposure` | `540` | `-6.99` | `47.59%` |

Les degradations de flou et de basse resolution sont tres bien detectees. Les degradations d'exposition sont plus difficiles, notamment parce que certaines images e-commerce sur fond clair restent visuellement acceptables malgre une modification de luminosite.

## Validation multi-annotateurs

La validation multi-annotateurs ajoute une lecture plus scientifique du protocole humain. Elle montre que les humains eux-memes ne sont pas parfaitement alignes, ce qui est normal pour une tache subjective.

| Mesure | Valeur |
| --- | ---: |
| Nombre d'images | `50` |
| Nombre d'annotateurs | `8` |
| Accord exact moyen | `0.1471` |
| Accord avec tolerance | `0.3754` |
| Spearman moyen entre annotateurs | `0.434187` |
| Spearman score auto vs moyenne humaine | `0.675243` |

Le score automatique est donc compare a une moyenne humaine plus robuste que l'avis d'un seul annotateur.

## Test DINO conditionnel

Un test cible a ete mene sur quelques cas difficiles pour evaluer l'interet d'un fallback DINO conditionnel.

| Element | Resultat |
| --- | --- |
| Cas difficiles testes | `8` |
| Regions supplementaires exploitables | `0` |
| Decision finale | garder DINO desactive par defaut |

Ce resultat ne signifie pas que DINO est inutile en general. Il signifie seulement que, dans le scope final et les cas testes, l'ajout n'a pas apporte de gain mesurable suffisant pour justifier une dependance plus lourde dans le chemin principal.

## Conclusion experimentale

Le projet atteint son objectif principal :

- construire un dataset final propre
- evaluer automatiquement la qualite photo
- rester zero-shot et explicable
- obtenir une correlation forte avec le jugement humain
- documenter les limites et la variabilite humaine

Le systeme est donc defendable comme prototype academique solide, avec un potentiel d'amelioration produit pour une version future.
