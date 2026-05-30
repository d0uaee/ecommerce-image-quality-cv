# Justification de l'approche zero-shot

## Idee principale

Le projet adopte une approche **zero-shot** : aucun modele n'est entraine localement dans ce depot pour apprendre a noter les images. Le systeme combine des composants pre-entraines, des heuristiques interpretable et une calibration experimentale des poids de scoring.

Ce choix est volontaire. Dans un contexte PFE, l'objectif n'est pas de battre un modele industriel entraine sur un tres grand volume de donnees privees, mais de proposer un pipeline reproductible, explicable et defendable avec un dataset final propre.

## Pourquoi ne pas entrainer un modele supervise ?

Un entrainement supervise fiable demanderait :

- un grand volume d'images produit annotees par des humains
- plusieurs annotateurs par image pour limiter le bruit subjectif
- une couverture large de categories, styles, eclairages et plateformes
- une separation stricte entrainement / validation / test
- une evaluation des biais et de la generalisation

Le projet travaille plutot sur un probleme plus realiste pour un PFE : construire un systeme complet capable de fonctionner sans phase d'apprentissage specifique, puis mesurer objectivement son alignement avec des evaluations humaines.

## Avantages scientifiques

L'approche zero-shot apporte plusieurs avantages :

- **Explicabilite** : chaque sous-score peut etre inspecte.
- **Reproductibilite** : les regles et scripts sont visibles dans le depot.
- **Faible dependance aux annotations** : les annotations servent a evaluer et calibrer, pas a entrainer un modele noir.
- **Portabilite** : le systeme peut etre teste sur de nouvelles images sans reentrainement.
- **Defense academique plus claire** : les choix methodologiques sont faciles a expliquer devant un jury.

## Hypothese centrale

L'hypothese du projet est la suivante :

> Une combinaison de criteres visuels interpretable, de selection de region produit et de coherence image / texte peut produire un score global suffisamment correle avec le jugement humain pour etre utile dans un contexte e-commerce.

Cette hypothese est testee experimentalement avec :

- des images originales propres
- des degradations controlees
- une evaluation humaine principale
- une validation multi-annotateurs
- une analyse par categorie

## Role du texte dans la methode

Le texte vendeur est utilise comme **source de verite principale**. Le titre et la description indiquent ce que l'image est censee representer. Le systeme ne cherche pas a lire du texte dans l'image pour comprendre le produit.

Ce choix evite de confondre deux problemes :

- evaluer la qualite d'une photo produit
- extraire du texte visible dans une image

L'OCR peut etre utile dans d'autres projets, mais il n'est pas necessaire dans le chemin critique ici.

## Ce qui est calibre

Le projet ne calibre pas un modele profond. Il calibre plutot :

- les poids des criteres dans le score final
- les seuils d'interpretation
- certaines penalites liees au cadrage, a la resolution effective et a la coherence

La calibration est guidee par les resultats humains et par l'analyse des cas de desaccord.

## Limite importante

Zero-shot ne signifie pas magique. Le systeme reste dependant :

- de la qualite du titre et de la description
- de la bonne selection de la region produit
- de la pertinence des criteres visuels choisis
- du scope des categories supportees

La documentation presente donc les resultats avec prudence : une correlation forte ne signifie pas une prediction parfaite image par image.
