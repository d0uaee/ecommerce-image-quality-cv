# Script de presentation - Version alignee avec le pipeline zero-shot

## 1) Ouverture

Bonjour,

dans cette presentation, je vais montrer un systeme zero-shot qui evalue automatiquement
la qualite d'une photo produit e-commerce et qui donne un score avec des conseils
d'amelioration en francais et en darija.

Le point central de ce projet est important :

- je n'entraine aucun modele dans ce depot
- j'utilise des modeles pre-entraines et des mesures deterministes
- l'innovation se situe dans l'architecture multimodale et dans l'explicabilite

---

## 2) Probleme vise

De nombreux petits vendeurs publient des photos produits de qualite inegale.

Les problemes les plus frequents sont :

- photo floue
- exposition incorrecte
- contraste faible
- resolution insuffisante
- mauvais cadrage
- manque de coherence entre l'image et le texte de l'annonce

L'objectif est donc de fournir un systeme simple qui repond a trois questions :

1. la photo est-elle bonne ou non pour une fiche e-commerce ?
2. pourquoi ?
3. que faut-il corriger concretement ?

---

## 3) Hypothese scientifique

L'hypothese de travail est la suivante :

le texte de l'annonce (`titre + description`) est la source de verite principale,
et CLIP peut servir a verifier si l'image correspond bien au produit decrit.

Cette logique permet d'eviter de faire reposer le systeme sur l'OCR.

Donc :

- pas d'OCR dans le chemin critique
- pas d'entrainement de reseau specifique
- zero-shot + heuristiques explicables

---

## 4) Scope volontairement reduit

Pour rester realiste dans une contrainte de deux mois, le projet est limite a trois familles :

- chaussures
- vetements
- electronique portable

Ce choix est volontaire.

On evite pour l'instant :

- meubles
- bijoux
- produits transparents
- cosmetiques
- alimentaire

---

## 5) Pipeline actuel

Le pipeline reel du projet est le suivant :

```text
annonce (image + titre + description)
 -> text_processor
 -> candidate_region_generator
 -> selector
 -> analyzer
 -> score global
 -> recommandations FR / Darija
 -> app Streamlit
```

Je peux maintenant expliquer chaque bloc.

---

## 6) Bloc 1 - Text processor

Le premier module traite le texte de l'annonce.

Il fait trois choses :

- nettoyage du texte
- extraction simple de categorie, couleur et marque
- generation d'un embedding texte CLIP

Ce bloc est crucial, parce qu'il fournit la verite metier au reste du pipeline.

Autrement dit :
on ne devine pas le produit depuis l'image seule, on guide l'analyse par le texte fourni.

---

## 7) Bloc 2 - Candidate region generator

Le deuxieme module ne fait pas de detection supervisee classique.

Il propose plusieurs regions candidates possibles dans l'image.

Pourquoi ce choix ?

- c'est plus rigoureux scientifiquement pour un systeme zero-shot
- c'est plus leger qu'un detecteur pleinement supervise
- cela reste interpretable

Par defaut, on utilise :

- la saliency OpenCV
- ou un fallback par contours / seuillage adaptatif

Et un filet de securite existe :

- Grounding DINO
- deja code
- desactive par defaut

---

## 8) Bloc 3 - Selector

Le selector choisit le bon produit parmi les regions candidates.

Pour chaque crop candidat, on calcule :

- un score CLIP image/texte
- un score visuel base sur taille et centralite
- une coherence categorie simple

La formule est :

```text
score = 0.6 * CLIP + 0.25 * visuel + 0.15 * categorie
```

Le choix est explicable :

- CLIP reste le signal principal
- le visuel aide a privilegier une vraie zone produit
- la categorie sert de garde-fou leger

Ce bloc produit aussi des valeurs intermediaires, utiles pour l'explication.

---

## 9) Bloc 4 - Analyzer

Une fois le bon crop selectionne, on evalue sa qualite.

Les criteres actuels sont :

- nettete
- exposition
- contraste
- balance couleurs
- resolution effective
- coherence image / texte

Quelques exemples :

- la nettete est calculee via la variance du Laplacien
- l'exposition repose sur des statistiques d'histogramme
- la coherence combine CLIP et comparaison de couleur dominante

La couleur est volontairement un signal leger, pas un critere dominant.

---

## 10) Explicabilite

Le point fort du projet n'est pas seulement de sortir une note.

Le systeme montre :

- le crop reellement selectionne
- les sous-scores qualite
- le score de coherence image / texte
- des recommandations actionnables

Donc, on n'a pas une boite noire.

On peut expliquer au vendeur :

- quelle zone a ete analysee
- quel critere penalise la photo
- et quelle correction faire

---

## 11) Donnees et validation

La logique dataset est egalement importante.

Les bonnes images viennent de references e-commerce propres.

Les mauvaises images ne sont pas scrappees comme "mauvaises photos reelles".
Elles sont generees par degradations controlees :

- flou
- sous-exposition
- surexposition
- mauvais recadrage
- basse resolution
- compression JPEG

L'avantage est fort :

- la verite-terrain est connue
- on sait quel critere devrait baisser
- cela renforce la validite experimentale du rapport

---

## 12) Ce qui est deja fonctionnel

Aujourd'hui, le projet dispose deja de :

- un `text_processor` executable
- un generateur de regions candidates
- un selector branche sur CLIP
- un analyzer avec score global
- une app Streamlit
- des scripts d'evaluation

Donc le projet n'est pas theorique :
il existe deja comme pipeline executable de bout en bout.

---

## 13) Limites actuelles

Il y a cependant des limites assumees :

- le dataset versionne actuellement contient encore des references historiques a nettoyer
- certaines images historiques sont en basse resolution
- le fallback DINO existe mais n'est pas active par defaut
- le systeme est optimise pour trois familles de produits seulement

Ces limites sont acceptables dans le cadre d'un PFE de deux mois, a condition de bien les expliciter.

---

## 14) Message scientifique final

Le message important pour le jury est le suivant :

ce projet n'essaie pas d'inventer un nouveau modele de deep learning.

Il propose une architecture zero-shot multimodale explicable qui combine :

- NLP
- vision classique
- CLIP
- scoring interpretable
- heuristiques qualite

La contribution principale est donc architecturale et experimentale.

---

## 15) Conclusion

En conclusion :

- le texte de l'annonce guide l'analyse
- la region produit est selectionnee de facon explicable
- la qualite est mesuree par criteres interpretabless
- le systeme fournit des conseils utiles au vendeur

Le projet est donc realiste, defendable scientifiquement, et coherent avec une contrainte PFE.

Merci.

---

## 16) Reponses courtes au jury

### Pourquoi zero-shot ?

Parce que la contrainte temps est courte, et que l'objectif est de produire un systeme
exploitable sans phase d'entrainement lourde.

### Pourquoi le texte est-il central ?

Parce qu'il est deja disponible dans l'annonce et constitue la meilleure verite metier
pour verifier la coherence image / produit.

### Pourquoi pas d'OCR central ?

Parce que l'OCR serait fragile, non necessaire dans la plupart des cas, et contraire
a la logique principale du projet qui prend le texte annonce comme reference.

### Quelle est la vraie innovation ?

L'architecture multimodale zero-shot et l'explicabilite du pipeline.
