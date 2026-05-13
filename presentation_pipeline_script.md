# Script de presentation - Version mise a jour (avancement + logique)

## 1) Ouverture (30 sec)

Bonjour, aujourd'hui je vais presenter surtout deux choses:
- l'etat d'avancement reel du projet,
- et la logique technique utilisee pour construire le pipeline.

Le projet vise un systeme d'analyse de qualite d'images produit e-commerce, interpretable et evolutif.

Message cle de cette version:
on a deja une base executable, et on sait exactement comment passer au niveau PFE complet.

---

## 2) Etat d'avancement global (45 sec)

Nous avons defini un pipeline de 8 etapes.

Etat actuel:
- 2 etapes finalisees,
- 3 etapes partiellement implementees,
- 3 etapes planifiees (bonus inclus).

En pourcentage, nous sommes environ a 40% d'avancement fonctionnel.

Point important:
la faisabilite est deja validee par un prototype operationnel (interface + analyse + batch CSV).

Lecture simple de l'avancement:
- Bloc "fonctionnel minimum" : valide
- Bloc "intelligence avancee" : en construction
- Bloc "valeur business" : planifie

---

## 3) Logique de conception (message cle) (1 min)

La logique utilisee est incrementale et hybride:

1. D'abord une base CV classique interpretable:
- pour obtenir des scores explicables rapidement,
- et eviter une boite noire des le debut.

2. Ensuite un enrichissement IA/NLP:
- OCR + prompt intelligent pour mieux detecter le produit principal,
- CNN pour capter la perception visuelle globale.

3. Enfin une couche de valeur metier:
- fusion des signaux,
- recommandations actionnables,
- et bonus business (similaires, prix, popularite).

Donc, on avance de "robuste et explicable" vers "intelligent et complet".

Cette logique nous permet de reduire le risque:
- on valide d'abord ce qui marche,
- puis on ajoute la complexite seulement quand la base est stable.

---

## 4) Avancement par etape du pipeline (2 min)

### [1] Pretraitement - EN COURS

Ce qui existe:
- redimensionnement et normalisation de base.

Pourquoi cette etape:
- stabiliser les mesures,
- reduire l'impact des differences de source.

Ce qui reste:
- harmoniser contraste/couleurs sur dataset multi-sources.

Indicateur avancement estime: 35%

### [2] Detection produit - PARTIELLEMENT FAIT

Ce qui existe:
- detection objet principal dans le flux actuel.

Logique technique:
- detection de base d'abord,
- puis ajout OCR -> mots-cles -> prompt intelligent pour Grounding DINO.

Ce qui reste:
- brancher OCR et strategie fallback "main product" robuste.

Indicateur avancement estime: 55%

### [3] Raffinement masque (GrabCut) - FAIT

Ce qui existe:
- bbox + GrabCut + nettoyage.

Pourquoi:
- isoler correctement le produit,
- fiabiliser les calculs qualite en aval.

Indicateur avancement estime: 70%

### [4] Analyse qualite CV - FAIT

Ce qui existe:
- blur, luminosite, fond blanc, centrage, ratio produit, watermark.

Pourquoi:
- obtenir des indicateurs explicables pour l'utilisateur et le jury.

Resultat:
- score par critere + score global intermediaire + recommandations de base.

Indicateur avancement estime: 75%

### [5] CNN qualite globale - A FAIRE

Logique:
- le CV classique mesure des regles techniques,
- le CNN capte la qualite percue globalement.

Ce qui reste:
- preparer dataset labelise,
- entrainer une classification good/medium/bad.

Indicateur avancement estime: 10%

### [6] Fusion + explication - EN CONCEPTION

Logique:
- combiner score CV + score CNN,
- produire une decision unique mais justifiee.

Sortie cible:
- score final,
- causes principales,
- recommandations priorisees.

Indicateur avancement estime: 20%

### [7] Produits similaires (bonus) - PLANIFIE

Logique:
- embeddings CLIP + nearest neighbors pour proposer des visuels proches.

Indicateur avancement estime: 15%

### [8] Infos externes (bonus) - PLANIFIE

Logique:
- enrichir l'analyse image par un contexte business (prix, tendance, popularite).

Indicateur avancement estime: 5%

---

## 5) Ce qui a ete mis a jour recemment (30-40 sec)

Depuis la version precedente, nous avons clarifie:
- la separation entre ce qui est termine, en cours, et planifie,
- les priorites techniques par sprint,
- et la logique de fusion CV + CNN pour l'explicabilite finale.

Donc la presentation n'est pas seulement une liste d'idees:
elle montre une trajectoire de realisation concrete.

---

## 6) Ce qui prouve l'avancement aujourd'hui (45 sec)

Elements deja demonstrables:
- application Streamlit fonctionnelle,
- analyse d'une image en temps reel,
- analyse par lot d'un dossier,
- export des resultats en CSV,
- affichage de scores et recommandations.

Donc, on ne presente pas une idee theorique: on presente un systeme deja executable.

---

## 7) Risques techniques et logique de maitrise (45 sec)

Risque 1: variabilite des images
- reponse: pretraitement + collecte multi-sources.

Risque 2: mauvaise detection sur cas limites
- reponse: OCR + prompt intelligent + fallback.

Risque 3: manque d'interpretabilite si on fait seulement du deep learning
- reponse: architecture hybride CV explicable + CNN.

Risque 4: faible valeur business
- reponse: couche recommandations + bonus similaires + infos externes.

---

## 8) Plan de finalisation (roadmap courte) (1 min)

Sprint 1:
- finaliser collecte/annotation multi-sources,
- consolider pretraitement.

Sprint 2:
- integration OCR + generation prompt intelligent,
- benchmark detection.

Sprint 3:
- entrainement CNN qualite,
- module de fusion explicable.

Sprint 4:
- bonus recommandation,
- bonus infos externes,
- evaluation finale et redaction resultats.

Resultat attendu en fin de roadmap:
- pipeline complet executable,
- evaluation quantitative par module,
- demo finale orientee usage e-commerce.

---

## 9) Conclusion orientee avancement (30 sec)

En resume:
- l'avancement actuel valide deja la base technique,
- la logique de developpement est claire: robuste -> intelligent -> business,
- et la suite est planifiee avec des livrables precis.

Le projet est donc sur une trajectoire realiste vers une version PFE complete.

Merci.

---

## 10) Q/R du jury (version courte)

Q1. Pourquoi ne pas faire seulement du deep learning?
Reponse: nous voulons un systeme interpretable et fiable rapidement; le CV classique donne cette base, puis le CNN complete.

Q2. Comment justifier l'etat d'avancement?
Reponse: prototype deja executable, analyse single + batch + export; il reste surtout la couche intelligence avancee.

Q3. Quelle est la logique scientifique?
Reponse: pipeline modulaire, evaluation par etape, fusion de signaux heterogenes, puis validation experimentale.
