# Vue d'ensemble

## Probleme traite

Sur une boutique e-commerce, la qualite d'une photo produit influence directement la confiance du client. Une photo floue, trop sombre, mal cadree ou incoherente avec le texte de l'annonce peut reduire la credibilite d'une fiche produit.

Pour un petit vendeur, il n'est pas toujours realiste de disposer d'un photographe professionnel, d'un studio ou d'un systeme d'evaluation supervise entraine sur un grand dataset. Ce projet propose donc une solution plus legere : evaluer automatiquement la qualite d'une photo produit avec une approche zero-shot.

## Idee centrale

Le systeme prend en entree :

- une image
- un titre
- une description

Il produit en sortie :

- un crop selectionne
- un score global sur 100
- des sous-scores explicables
- une mesure de coherence image / texte
- des recommandations en francais et en darija

Le texte de l'annonce est considere comme la source de verite principale. Cela signifie que le systeme verifie si l'image semble coherente avec ce que le vendeur declare, sans utiliser l'OCR comme chemin critique.

## Pourquoi zero-shot ?

Le choix zero-shot repond a trois contraintes :

- eviter un entrainement lourd dans un cadre PFE
- garder le systeme explicable
- pouvoir fonctionner avec un dataset final limite mais propre

Le projet reutilise des modeles pre-entraines, notamment pour les embeddings texte / image, mais ne fait pas d'entrainement local de modele profond.

## Valeur du projet

La valeur du projet se situe dans l'orchestration des briques :

- NLP pour exploiter le texte vendeur
- computer vision pour proposer et analyser des regions
- CLIP pour relier texte et image
- heuristiques explicables pour la qualite visuelle
- validation experimentale avec annotations humaines

## Resultat attendu pour l'utilisateur

L'utilisateur obtient une lecture simple : la photo est-elle publiable, moyenne ou a corriger ? Les recommandations expliquent ce qu'il faut ameliorer : nettete, exposition, resolution, cadrage ou coherence produit / texte.
