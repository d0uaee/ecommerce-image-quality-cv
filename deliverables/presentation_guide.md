# Guide Oral - Soutenance PFE Zero-Shot (environ 1 heure)

## Objectif

Ce guide accompagne le deck :

- `deliverables/presentation_soutenance_pfe_zero_shot_1h.pptx`

Il donne une facon simple de presenter le projet en environ 1 heure, avec une
repartition conseillee du temps et le message cle de chaque slide.

## Repartition globale du temps

- introduction et cadrage : 10 min
- conception technique : 20 min
- dataset et protocole experimental : 10 min
- resultats et discussion : 12 min
- conclusion et perspectives : 8 min

Total cible : 60 min

## Slide par slide

### Slide 1 - Couverture

Temps conseille : 2 min

Message :

- presenter le titre du projet
- dire clairement qu'il s'agit d'un systeme zero-shot
- annoncer les trois piliers :
  - qualite photo
  - explicabilite
  - evaluation experimentale

### Slide 2 - Plan detaille

Temps conseille : 2 min

Message :

- expliquer la structure de la soutenance
- rassurer le jury sur le fait que la presentation va du besoin jusqu'aux resultats

### Slide 3 - Contexte e-commerce

Temps conseille : 2 min

Message :

- montrer le besoin concret des petits vendeurs
- insister sur les consequences metier d'une mauvaise photo

### Slide 4 - Problematique

Temps conseille : 2 min

Message :

- formuler clairement la question de recherche
- expliquer que le vrai enjeu est d'eviter un entrainement lourd

### Slide 5 - Contributions

Temps conseille : 2 min

Message :

- resumer ce que le projet apporte
- montrer qu'il ne s'agit pas seulement d'une app, mais d'une architecture complete

### Slide 6 - Hypotheses

Temps conseille : 3 min

Message :

- texte = source de verite
- pas d'OCR dans le coeur
- pas d'entrainement
- scope reduit a 3 familles

### Slide 7 - Choix zero-shot

Temps conseille : 3 min

Message :

- comparer rapidement supervise vs zero-shot
- justifier le choix par le delai, le cout et l'explicabilite

### Slide 8 - Architecture globale

Temps conseille : 3 min

Message :

- presenter le pipeline complet de maniere fluide
- montrer qu'il y a une logique de traitement claire

### Slide 9 - Pipeline detaille

Temps conseille : 3 min

Message :

- expliquer la circulation de l'information entre texte, image et score
- insister sur le role du crop selectionne

### Slide 10 - Text Processor

Temps conseille : 3 min

Message :

- expliquer comment le texte devient un signal exploitable
- mentionner spaCy, rapidfuzz, dictionnaires et embedding CLIP

### Slide 11 - Candidate Region Generator

Temps conseille : 3 min

Message :

- expliquer pourquoi on parle de regions candidates et non de detection supervisee
- rappeler le fallback DINO

### Slide 12 - Selector

Temps conseille : 4 min

Message :

- montrer la formule de score
- expliquer chaque composante
- insister sur la correction finale du tiny crop

### Slide 13 - Analyzer

Temps conseille : 4 min

Message :

- decrire les criteres
- expliquer pourquoi la couleur est un signal leger
- rappeler que le score global est compose de sous-scores lisibles

### Slide 14 - Application Streamlit

Temps conseille : 2 min

Message :

- montrer que le systeme est demonstrable
- rappeler les modes : unique, batch, debug

### Slide 15 - Strategie dataset

Temps conseille : 3 min

Message :

- expliquer le choix des images propres + degradations controlees
- dire clairement pourquoi c'est defendable scientifiquement

### Slide 16 - Dataset final

Temps conseille : 2 min

Message :

- donner les chiffres :
  - 180 originaux
  - 3240 degrdees
- rappeler le role de `metadata.csv`

### Slide 17 - Exemples d'images propres

Temps conseille : 2 min

Message :

- visualiser les trois categories
- justifier le scope volontairement reduit

### Slide 18 - Degradations controlees

Temps conseille : 3 min

Message :

- montrer quelques exemples
- expliquer quelle degradation teste quel critere

### Slide 19 - Protocole experimental

Temps conseille : 3 min

Message :

- expliquer les deux niveaux de validation :
  - automatique
  - humaine

### Slide 20 - Sensibilite par critere

Temps conseille : 4 min

Message :

- insister sur les bons resultats pour le flou
- commenter honnetement les cas moyens ou faibles

### Slide 21 - Evaluation humaine

Temps conseille : 4 min

Message :

- montrer la Spearman
- expliquer la signification :
  - positive
  - significative
  - mais moderee

### Slide 22 - Cas pratique

Temps conseille : 3 min

Message :

- expliquer comment un utilisateur lit concretement le resultat
- rappeler que le score n'est pas isole du contexte

### Slide 23 - Discussion

Temps conseille : 3 min

Message :

- separer ce qui marche bien, moyennement, et ce qui reste fragile
- montrer la maturite du projet

### Slide 24 - Limites

Temps conseille : 3 min

Message :

- assumer les limites sans se devaloriser
- rappeler que le projet reste coherent avec un PFE de 2 mois

### Slide 25 - Perspectives

Temps conseille : 3 min

Message :

- mentionner les extensions naturelles :
  - HSV
  - categories supplementaires
  - n8n + assistant annonce

### Slide 26 - Conclusion

Temps conseille : 2 min

Message :

- rappeler la question de depart
- rappeler la reponse apportee par le projet
- terminer sur l'idee de systeme zero-shot explicable et utile

## Questions probables du jury

### Pourquoi zero-shot ?

Reponse courte :

- delai court
- besoin d'explicabilite
- eviter le cout d'un dataset annote massif

### Pourquoi pas d'OCR ?

Reponse courte :

- le texte de l'annonce est deja disponible
- l'OCR n'est pas necessaire au coeur du probleme
- il aurait ajoute de la complexite sans benefice central

### Pourquoi RGB et pas HSV ?

Reponse courte :

- la couleur n'est qu'un signal secondaire
- RGB est simple et suffisant dans ce cadre
- HSV est une perspective d'amelioration

### La Spearman est-elle suffisante ?

Reponse courte :

- elle est moderee, mais statistiquement significative
- c'est coherent avec une approche zero-shot explicable
- l'objectif n'etait pas d'obtenir une precision de modele specialise

### Quel est le principal point fort ?

Reponse courte :

- l'architecture multimodale explicable

### Quelle est la principale limite ?

Reponse courte :

- certaines degradations restent moins bien capturees que le flou

## Message final a garder

Si tu dois resumer tout le projet en une phrase :

"J'ai construit un systeme zero-shot explicable qui evalue la qualite d'une photo produit e-commerce en combinant texte, vision, CLIP et heuristiques, sans entrainer de modele localement."
