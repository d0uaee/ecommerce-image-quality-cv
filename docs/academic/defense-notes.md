# Notes pour la soutenance

## Message central

Le projet propose un systeme zero-shot, explicable et reproductible pour evaluer automatiquement la qualite d'images produit e-commerce.

La force du projet n'est pas seulement l'application Streamlit. La force principale est l'ensemble complet :

- dataset final propre
- pipeline multimodal
- criteres interpretable
- validation humaine
- validation multi-annotateurs
- rapports et documentation

## Pitch court

> Ce PFE construit un pipeline zero-shot d'evaluation de qualite photo e-commerce. A partir d'une image, d'un titre et d'une description, le systeme selectionne le produit, calcule des criteres visuels, mesure la coherence image / texte et produit un score explicable avec recommandations. Le protocole final montre une correlation Spearman de `0.7122` avec l'evaluation humaine principale et `0.675243` avec la moyenne de `8` annotateurs.

## Points forts a presenter

- Le projet ne depend pas d'un entrainement local opaque.
- Les criteres sont explicables et visibles dans l'application.
- Le dataset final est structure et documente.
- Les mauvaises images sont generees par degradations controlees.
- Les resultats sont compares a des annotations humaines.
- La validation multi-annotateurs mesure la variabilite humaine.
- Les limites sont assumees et documentees.

## Questions probables du jury

### Pourquoi zero-shot ?

Reponse conseillee :

> Parce que le projet vise une methode interpretable et reproductible sans grand dataset annote d'entrainement. L'objectif est de mesurer jusqu'ou un pipeline zero-shot bien structure peut s'aligner avec le jugement humain.

### Pourquoi ne pas utiliser OCR ?

Reponse conseillee :

> Le texte de l'annonce est deja disponible et constitue la source de verite. L'OCR ajouterait un probleme different : lire du texte dans l'image. Ici, on evalue la qualite photo et l'alignement image / annonce.

### Que signifie Spearman `0.7122` ?

Reponse conseillee :

> Cela signifie que le classement des images par le systeme suit fortement le classement humain. Pour une tache subjective, c'est un resultat solide, surtout sans entrainement local.

### Pourquoi les annotateurs ne sont-ils pas parfaitement d'accord ?

Reponse conseillee :

> La qualite photo contient une part subjective. Deux humains peuvent differer d'un ou deux points. C'est pour cela que j'ai ajoute une validation multi-annotateurs et une moyenne humaine.

### Pourquoi l'assistant annonce peut-il se tromper ?

Reponse conseillee :

> L'assistant annonce est une extension produit. S'il fonctionne en fallback local, il reste volontairement prudent. Pour une generation plus riche, il faut brancher un webhook n8n vers un vrai modele vision-langage.

## Ce qu'il faut eviter de dire

- Ne pas dire que le systeme est parfait.
- Ne pas dire qu'il remplace un photographe professionnel.
- Ne pas presenter le fallback local comme un LLM vision complet.
- Ne pas generaliser les resultats a toutes les categories e-commerce.

## Conclusion de soutenance possible

> Le projet montre qu'une approche zero-shot bien structuree peut produire une evaluation utile et explicable de photos produit. Les resultats experimentaux confirment un alignement solide avec le jugement humain, tout en laissant des pistes claires pour une version future plus large et plus industrielle.
