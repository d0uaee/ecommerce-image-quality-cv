# Assistant annonce

## Role de l'extension

L'assistant annonce est une extension pratique ajoutee a l'application Streamlit. Son objectif est d'aider un vendeur a ameliorer une fiche produit a partir de l'image et des informations disponibles.

Il peut proposer :

- un titre
- une description
- des attributs detectes ou probables
- des informations manquantes
- une checklist vendeur
- un prix indicatif prudent

## Position dans le projet

L'assistant annonce n'est pas le coeur scientifique du PFE. Le coeur scientifique reste le pipeline d'evaluation qualite :

```text
texte -> regions candidates -> selector -> analyzer -> score explicable
```

L'assistant annonce est une extension produit qui montre comment le pipeline peut etre transforme en outil plus complet pour un usage e-commerce.

## Modes de fonctionnement

| Mode | Condition | Comportement |
| --- | --- | --- |
| `n8n_webhook` | `N8N_ASSISTANT_WEBHOOK` configure | Envoie les donnees a un workflow externe. |
| `local_assistant` | Aucun webhook disponible | Utilise un fallback local prudent. |

L'interface affiche explicitement la source utilisee afin d'eviter toute ambiguite.

## Pourquoi le fallback local est limite

Le fallback local ne voit pas l'image comme un vrai modele vision-langage externe. Il utilise surtout :

- le titre
- la description
- la categorie estimee
- des indices simples
- des templates prudents

Il peut donc produire une description generique ou incorrecte si le texte d'entree est incoherent.

## Exemple d'ambiguite

Si l'utilisateur charge une image de chaussure mais saisit :

```text
Bateau gonflable 2 places avec rames
```

Le systeme doit rester prudent. Le probleme vient du fait que le texte fourni ne correspond pas a l'image. L'assistant peut signaler des informations a verifier au lieu d'inventer une fiche parfaite.

## Recommandation pour une vraie version produit

Pour une version plus forte, connecter un workflow n8n a un modele vision-langage capable de recevoir :

- l'image
- le titre
- la description
- la categorie estimee
- les scores de qualite

Le workflow peut ensuite retourner un JSON structure avec :

```json
{
  "title": "Titre propose",
  "description": "Description proposee",
  "attributes": ["attribut 1", "attribut 2"],
  "missing_info": ["info manquante"],
  "seller_checklist": ["action a verifier"],
  "price_hint": "prix indicatif prudent"
}
```

## Precaution sur le prix

Le prix indicatif doit rester prudent. Le systeme ne connait pas toujours :

- la marque exacte
- l'etat du produit
- l'age
- les accessoires inclus
- le marche local exact

La documentation et l'interface doivent donc presenter cette sortie comme une indication, jamais comme une estimation definitive.
