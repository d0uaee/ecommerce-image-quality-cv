# Pipeline principal

## Entrees

Le pipeline principal prend trois entrees :

- image produit
- titre
- description

Le titre et la description ne sont pas accessoires. Ils permettent au systeme de comprendre quel produit est attendu et servent de reference pour la coherence image / texte.

## Etape 1 : `text_processor`

Le module traite le texte de l'annonce. Il extrait :

- categorie probable
- couleur attendue
- marque potentielle
- texte nettoye
- embedding texte

Le systeme peut fonctionner avec des fallbacks si certains modeles ne sont pas disponibles, mais la coherence multimodale est meilleure lorsque le backend CLIP est charge correctement.

## Etape 2 : `candidate_region_generator`

L'image est analysee pour proposer plusieurs regions candidates. Le projet ne pretend pas faire une detection supervisee par classe. Il propose des zones plausibles que le selector va ensuite comparer.

Par defaut, la strategie repose sur OpenCV et des signaux visuels. DINO existe comme fallback testable, mais il n'est pas active par defaut car les tests cibles n'ont pas montre de gain exploitable sur l'echantillon difficile.

## Etape 3 : `selector`

Le selector choisit le crop le plus pertinent. Il combine :

- similarite texte / image
- centralite
- taille relative
- coherence categorie
- penalites contre les crops trop petits

Cette etape est critique : si le crop est mauvais, les sous-scores de qualite risquent de devenir moins fiables.

## Etape 4 : `analyzer`

Le crop selectionne est evalue selon plusieurs criteres :

| Critere | Question posee |
| --- | --- |
| `sharpness` | L'image est-elle nette ? |
| `exposure` | La luminosite est-elle correcte ? |
| `contrast` | Le produit ressort-il visuellement ? |
| `color_balance` | Les couleurs sont-elles equilibrees ? |
| `effective_resolution` | Le niveau de detail utile est-il suffisant ? |
| `framing` | Le produit est-il bien cadre ? |
| `coherence` | L'image correspond-elle au texte ? |

## Etape 5 : sortie utilisateur

Le pipeline produit :

- un score global
- un message de synthese
- des sous-scores
- des details de coherence image / texte
- des recommandations en francais et en darija

Le mode debug permet d'inspecter les signaux intermediaires.
