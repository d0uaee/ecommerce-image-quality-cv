# Selection du produit

Le `selector` choisit la region la plus probable pour representer le bon produit.

## Signaux combines

- similarite CLIP texte / image
- centralite
- taille du crop
- coherence categorie

## Importance

Le choix du bon crop est critique, car il conditionne ensuite :

- la coherence image / texte
- le framing
- plusieurs criteres de qualite
