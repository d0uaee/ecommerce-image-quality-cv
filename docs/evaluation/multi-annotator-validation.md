# Validation multi-annotateurs

## Pourquoi plusieurs annotateurs ?

La qualite d'une photo produit n'est pas une verite totalement objective. Deux personnes peuvent juger differemment une image selon leur sensibilite :

- importance donnee a la nettete
- tolerance aux fonds simples
- perception de l'eclairage
- niveau d'exigence e-commerce
- interpretation de la categorie produit

Ajouter plusieurs annotateurs permet de mesurer cette variabilite humaine.

## Protocole

La validation multi-annotateurs utilise :

- `50` images
- `8` colonnes de scores humains
- une moyenne humaine par image
- une comparaison entre score automatique et moyenne humaine
- une estimation de l'accord entre annotateurs

Le script principal associe est :

```powershell
.\.venv\Scripts\python scripts\evaluate_multi_annotator.py
```

## Resultats

| Mesure | Valeur |
| --- | ---: |
| Images evaluees | `50` |
| Annotateurs | `8` |
| Accord exact moyen | `0.1471` |
| Accord avec tolerance | `0.3754` |
| Spearman moyen entre annotateurs | `0.434187` |
| Spearman score auto vs moyenne humaine | `0.675243` |

## Lecture des resultats

L'accord exact est faible, ce qui est attendu : demander exactement la meme note sur une echelle de `0` a `10` est strict.

L'accord avec tolerance est plus informatif. Il accepte qu'un annotateur donne par exemple `7` et un autre `8`, car ces notes traduisent souvent le meme jugement qualitatif.

Le Spearman moyen entre annotateurs montre que les humains partagent une tendance generale, mais avec une variabilite notable.

## Ce que cela apporte au projet

La validation multi-annotateurs rend la soutenance plus solide car elle montre que :

- le score humain n'est pas traite comme une verite absolue
- la subjectivite est mesuree
- le score automatique reste competitif face a une moyenne humaine
- l'evaluation est plus serieuse qu'une simple demonstration visuelle

## Interpretation du score `0.675243`

Le score automatique obtient une correlation de `0.675243` avec la moyenne de `8` annotateurs. Cette valeur est legerement plus basse que la correlation principale, ce qui est normal : la moyenne multi-annotateurs lisse les preferences individuelles et rend la reference plus stricte.

Le resultat reste positif et defendable pour une approche zero-shot sans entrainement local.
