# FAQ

## Comment lancer l'application ?

Depuis la racine du projet :

```powershell
.\.venv\Scripts\streamlit run app.py
```

Puis ouvrir :

```text
http://localhost:8501
```

## Comment ouvrir la documentation locale ?

Apres generation Sphinx, ouvrir :

```text
C:\Users\ahadj\OneDrive\ecommerce-image-quality\docs\_build\html\index.html
```

Dans un navigateur, le lien complet commence par `file:///` :

```text
file:///C:/Users/ahadj/OneDrive/ecommerce-image-quality/docs/_build/html/index.html
```

Si le fichier n'existe pas, regenerer la documentation :

```powershell
.\.venv\Scripts\python -m sphinx -b html docs docs\_build\html
```

## Pourquoi le projet est-il zero-shot ?

Parce qu'il n'entraine aucun modele local dans ce depot. Le systeme combine des modeles pre-entraines, des criteres interpretable et une calibration de scoring.

Ce choix rend le projet plus simple a reproduire et plus facile a defendre academiquement.

## Pourquoi ne pas utiliser OCR ?

L'OCR n'est pas dans le chemin critique car le texte de l'annonce est deja fourni par le vendeur ou le dataset. Le projet evalue l'alignement entre cette annonce et l'image.

Utiliser OCR pourrait ajouter du bruit et melanger deux problemes differents :

- lire du texte dans l'image
- evaluer la qualite visuelle du produit

## Pourquoi ne pas entrainer un modele ?

Un entrainement supervise demanderait un dataset beaucoup plus grand et annote de maniere stable. Le projet privilegie une approche interpretable et reproductible adaptee au PFE.

## Comment interpreter Spearman `0.7122` ?

Cela signifie que le classement produit par le systeme suit fortement le classement humain. Ce n'est pas une precision parfaite, mais c'est une bonne correlation pour une tache subjective.

## Pourquoi la correlation multi-annotateurs est plus basse ?

La moyenne de `8` annotateurs est une reference plus robuste mais aussi plus stricte. Les humains ne sont pas parfaitement d'accord entre eux. Une correlation de `0.675243` avec cette moyenne reste positive et defendable.

## Pourquoi certaines categories sont plus difficiles ?

Les categories ne presentent pas les memes formes visuelles :

- les chaussures sont souvent bien separees du fond
- les vetements peuvent etre portes, plies ou poses a plat
- les produits electroniques peuvent contenir reflets, logos, petits ports ou accessoires

Le comportement par categorie est donc analyse separement.

## Que faire si l'assistant annonce tombe en fallback local ?

Verifier si la variable d'environnement `N8N_ASSISTANT_WEBHOOK` est configuree.

Sans webhook, l'application utilise automatiquement le fallback local. L'interface indique alors une source comme `local_assistant`.

## Pourquoi la description generee peut etre mauvaise ?

Si l'assistant utilise le fallback local, il ne dispose pas d'un vrai modele vision-langage externe. Il applique des regles prudentes basees sur le contexte disponible.

Pour une generation de description plus riche, il faut brancher un webhook n8n vers un modele externe capable de recevoir l'image et le texte.

## Que contient le dataset final ?

Le dataset final contient trois categories :

- `shoes`
- `clothing`
- `portable_electronics`

Les images propres sont dans `dataset/originals/`. Les images degradees sont dans `dataset/degraded/`. Les metadonnees sont dans `dataset/metadata.csv` et `dataset/degraded_metadata.csv`.

## Peut-on ajouter une nouvelle categorie ?

Oui, mais il faut :

- collecter des images propres
- completer les metadonnees
- verifier les criteres de qualite
- tester la coherence image / texte
- refaire une evaluation humaine ou au moins une verification manuelle

## Le score global suffit-il ?

Non. Le score global est utile pour resumer, mais l'interet du projet est surtout l'explication par criteres. Deux images peuvent avoir le meme score pour des raisons differentes.
