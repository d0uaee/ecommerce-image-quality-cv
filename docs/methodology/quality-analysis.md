# Analyse de la qualite visuelle

## Objectif du module

Le module `analyzer` transforme une image produit ou un crop selectionne en plusieurs sous-scores interpretable. Chaque sous-score represente une dimension concrete de qualite photo e-commerce.

L'objectif n'est pas seulement de donner une note globale, mais d'expliquer **pourquoi** une image est bonne, moyenne ou faible.

## Criteres calcules

| Critere | Question posee | Interpretation |
| --- | --- | --- |
| `sharpness` | L'image est-elle nette ? | Detecte le flou, le manque de contours et la perte de texture. |
| `exposure` | La luminosite est-elle exploitable ? | Penalise les images trop sombres ou trop surexposees. |
| `contrast` | Le produit ressort-il du fond ? | Mesure la separation visuelle entre zones claires et sombres. |
| `color_balance` | Les couleurs semblent-elles equilibrees ? | Detecte les dominantes de couleur trop fortes. |
| `effective_resolution` | L'image contient-elle assez de detail utile ? | Distingue taille brute et resolution réellement exploitable. |
| `framing` | Le produit occupe-t-il correctement l'image ? | Penalise les produits trop petits, coupes ou mal centres. |
| `coherence` | L'image correspond-elle au texte ? | Combine similarite image / texte et indices couleur. |

## Nettete

La nettete est estimee a partir de signaux de contours et de variations locales. Une image nette contient des transitions visibles autour du produit : coutures, bords, textures, boutons, ports, lacets, semelles ou details de surface.

Une mauvaise nettete peut venir de :

- flou de mouvement
- flou de mise au point
- compression excessive
- redimensionnement agressif
- capture d'ecran lissee

## Exposition

L'exposition mesure si la luminosite rend le produit lisible. Le score ne cherche pas une photo artistiquement parfaite ; il cherche une photo e-commerce exploitable.

Cas penalises :

- produit trop sombre
- zones blanches brulees
- eclairage trop dur
- details perdus dans les ombres ou hautes lumieres

Une amelioration a ete faite pour eviter de penaliser trop fortement les photos correctes sur fond clair. Cette nuance est importante car beaucoup de photos e-commerce utilisent un fond blanc ou beige.

## Contraste

Le contraste aide a savoir si le produit ressort. Une photo avec bon contraste permet d'identifier rapidement la silhouette et les details principaux.

Ce critere peut etre eleve meme si l'image n'est pas parfaite. C'est normal : une image peut etre bien contrastee mais mal cadree, de basse resolution ou incoherente avec le texte.

## Balance des couleurs

La balance couleur detecte les dominantes anormales. Par exemple, une image entierement verdatre ou bleuatre peut donner une impression non professionnelle.

Le projet utilise des signaux simples et explicables plutot qu'une estimation complexe de colorimetrie. Cela suffit pour signaler les cas problematiques sans transformer le projet en systeme de retouche photo.

## Resolution effective

La resolution effective est differente de la taille brute du fichier. Une image peut avoir beaucoup de pixels mais peu de detail utile si elle a ete :

- upsampled
- fortement compressee
- lissee
- capturee depuis un ecran

Le score combine donc la taille, le niveau de detail et la proportion de produit visible. L'objectif est de mieux distinguer :

- une photo HD propre sur fond simple
- une image techniquement grande mais pauvre en details
- une image basse resolution ou screenshot

## Cadrage et region utile

Le cadrage mesure si le produit principal est bien visible. Une image e-commerce doit montrer le produit de maniere claire, sans que l'objet soit trop petit ou coupe.

Le projet accorde une attention particuliere au crop selectionne, car le score doit porter sur le produit retenu par le selector, pas sur un fond vide ni sur un element secondaire.

## Coherence image / texte

La coherence verifie si le contenu visuel est compatible avec le titre et la description. Elle utilise une similarite multimodale lorsque le modele est disponible, puis complete avec des indices plus simples comme la couleur attendue.

Exemple :

- titre : `veste bebe rayee violet et blanc`
- image : vetement rayé proche de la description
- score attendu : moyen a bon

Si le modele multimodal n'est pas disponible, le systeme doit le signaler clairement dans le debug au lieu de masquer le fallback.

## Score global

Le score final combine les criteres selon des poids calibres. Il ne s'agit pas d'une moyenne naive. Les criteres les plus importants pour la qualite e-commerce ont plus d'influence, mais aucun score individuel ne doit dominer tous les autres dans les cas normaux.

Le score global est accompagne :

- d'un niveau d'interpretation
- de recommandations en francais
- de recommandations en darija
- d'informations debug si le mode debug est active

## Interpretation prudente

Le score est un outil d'aide a la decision, pas un jugement absolu. Deux photos peuvent avoir le meme score global pour des raisons differentes. C'est pour cela que l'application expose les criteres et les recommandations, pas seulement la note finale.
