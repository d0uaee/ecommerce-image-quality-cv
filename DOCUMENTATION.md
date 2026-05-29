# Documentation Technique Detaillee - Systeme Zero-Shot d'Evaluation de Qualite d'Images E-commerce

## 1. Resume du projet

Ce projet PFE implemente un systeme zero-shot capable d'evaluer automatiquement la qualite
d'une photo de produit e-commerce a partir d'une annonce composee de :

- une image produit
- un titre
- une description

Le systeme produit :

- un score global de qualite sur 100
- des sous-scores explicables
- un crop selectionne correspondant au produit retenu
- des recommandations d'amelioration en francais et en darija

La cible principale est le petit vendeur e-commerce qui souhaite verifier rapidement
si sa photo est publiable sans avoir recours a un photographe professionnel.

## 2. Problematique

Dans les petites boutiques e-commerce, la qualite des photos est souvent heterogene :

- produit mal cadre
- image floue
- faible resolution
- mauvaise exposition
- texte de l'annonce non coherent avec l'image

Les approches supervisees classiques exigent generalement :

- un dataset annote important
- un entrainement specifique
- un cout de developpement et de maintenance eleve

Dans ce projet, le choix est inverse :

- pas d'entrainement de modele local
- reutilisation de modeles pre-entraines
- regles et mesures explicables
- evaluation reproductible sur des degradations controlees

## 3. Hypotheses et choix scientifiques

Le projet repose sur cinq hypotheses non negociables :

1. le texte de l'annonce (`titre + description`) est la source de verite principale
2. il n'y a pas d'OCR dans le chemin critique du scoring
3. aucun modele n'est entraine dans ce depot
4. les bonnes images servent de references et les mauvaises sont generees par degradation controlee
5. le scope est volontairement reduit a trois familles :
   - `shoes`
   - `clothing`
   - `portable_electronics`

Ces hypotheses permettent de garder un projet realiste sur environ deux mois, tout en
conservant une base scientifique defendable.

## 4. Positionnement de l'innovation

L'innovation de ce projet ne repose pas sur l'entrainement d'un nouveau modele.
Elle repose sur la combinaison explicable de plusieurs briques :

- NLP pour exploiter le texte de l'annonce
- vision classique OpenCV pour proposer des regions candidates
- CLIP multilingue pour relier texte et image
- heuristiques interpretable pour la qualite visuelle
- fusion de scores pour choisir le bon produit

Le second point fort est l'explicabilite :

- le crop retenu est visible
- les sous-scores sont detailles
- les valeurs intermediaires du selector peuvent etre affichees
- la coherence image/texte est decomposable

## 5. Architecture generale

Le pipeline principal est le suivant :

```text
annonce (image + titre + description)
 -> text_processor
 -> candidate_region_generator
 -> selector
 -> analyzer
 -> score global
 -> recommandations
 -> app Streamlit
```

### Lecture du pipeline

1. le texte est nettoye et converti en representation exploitable
2. plusieurs regions candidates sont proposees dans l'image
3. le systeme choisit la region la plus probable pour representer le bon produit
4. la qualite du crop selectionne est analysee
5. le systeme calcule un score global et formule des conseils

## 6. Arborescence du projet

Structure principale :

```text
ecommerce-image-quality/
|- app.py
|- config.py
|- requirements.txt
|- README.md
|- DOCUMENTATION.md
|- generate_degraded.py
|- evaluate_analyzer.py
|- evaluate_full.py
|- scripts/
|  `- build_final_dataset.py
|- dataset/
|  |- originals/
|  |- degraded/
|  |- annotations/
|  |- metadata.csv
|  `- degraded_metadata.csv
|- output/
|  `- reports/
`- src/
   |- __init__.py
   |- analyzer.py
   |- candidate_region_generator.py
   |- dictionaries.py
   |- selector.py
   |- listing_assistant.py
   `- text_processor.py
```

## 7. Description detaillee des modules

### 7.1 `src/text_processor.py`

#### Role

Transformer le texte de l'annonce en informations structurantes pour le pipeline.

#### Entrees

- `title: str`
- `description: str`

#### Sortie principale

```python
{
    "clean_text": str,
    "color": str | None,
    "category": str | None,
    "brand": str | None,
    "text_embedding": np.ndarray,
}
```

#### Fonctions principales

- normalisation du texte
- tokenisation avec spaCy si disponible
- extraction heuristique de couleur
- extraction heuristique de categorie
- extraction heuristique de marque
- embedding texte via CLIP multilingue

#### Backend d'embedding

Le backend utilise repose sur `sentence-transformers` avec un modele CLIP multilingue.

Un cache est applique pour eviter de recalculer les embeddings texte identiques.

#### Robustesse

Si le backend d'embedding n'est pas disponible :

- aucun `False` n'est stocke comme modele
- le modele vaut `None`
- la fonction retourne un vecteur nul de taille fixe

Cela evite les crashs du type `bool object is not callable`.

#### Limites

- extraction couleur heuristique
- extraction marque susceptible de faux positifs
- dependance partielle a la qualite du texte fourni

### 7.2 `src/dictionaries.py`

#### Role

Centraliser les dictionnaires de connaissance legers utilises par `text_processor`.

#### Contenu

- categories autorisees
- mots-cles par categorie
- couleurs francaises et alias
- mapping couleur vers RGB
- marques frequentes
- taille fixe du vecteur d'embedding

#### Raison d'exister

Permet de garder :

- un code plus lisible
- une extraction plus facilement ajustable
- une base explicable pour les correspondances texte -> attributs

### 7.3 `src/candidate_region_generator.py`

#### Role

Proposer des regions candidates dans l'image sans detection supervisee par defaut.

Le terme "candidate region generator" est volontaire :

- on ne pretend pas faire une detection entrainee sur classes
- on propose un ensemble restreint de crops possibles

#### Strategie par defaut

- saliency OpenCV si disponible
- sinon seuillage adaptatif + contours

#### Strategie fallback

- Grounding DINO disponible en filet de securite
- activable par configuration
- desactive par defaut pour conserver une approche plus legere

#### Contraintes

- maximum 5 regions candidates
- tri par aire et centralite
- compatibilite avec le selector

#### Sortie type

```python
[
    {
        "bbox": (x1, y1, x2, y2),
        "area": float,
        "centrality": float,
    },
    ...
]
```

#### Fonction `refine_crop`

Le refine final repose sur GrabCut applique uniquement au gagnant.

Objectif :

- eviter un cout eleve sur toutes les regions
- affiner le cadrage du produit final

### 7.4 `src/selector.py`

#### Role

Choisir la meilleure region candidate pour representer le produit cible de l'annonce.

#### Entrees

- image
- liste de regions candidates
- `text_data` venant de `text_processor`

#### Principe

Pour chaque region candidate :

1. extraire le crop
2. encoder le crop en embedding image
3. comparer le crop au texte avec CLIP
4. ajouter un score visuel
5. ajouter une coherence categorie

#### Formule de score

```text
score = 0.6 * score_clip + 0.25 * score_visual + 0.15 * score_category
```

Ces poids sont stockes dans `config.py` et assumes comme une calibration empirique.

#### Score CLIP

- similarite cosinus entre embedding image et embedding texte
- backend partage avec le reste du pipeline

#### Score visuel

Le score visuel combine :

- aire normalisee
- centralite

Il favorise les zones :

- suffisamment grandes
- visuellement centrales

#### Score categorie

Coherence heuristique faible mais utile pour eviter certains faux crops.

Exemple :

- une chaussure minuscule hyper contrastee ne doit pas toujours battre un produit plus grand et mieux cadre

#### Sortie

Le module retourne notamment :

- la bbox selectionnee
- le crop selectionne
- les details de scoring
- le masque GrabCut si disponible

#### Explicabilite

En mode debug, l'application peut afficher :

- les regions candidates
- les scores du selector
- le backend utilise
- les sous-composantes du score

### 7.5 `src/analyzer.py`

#### Role

Analyser la qualite du crop selectionne.

#### Criteres calcules

- `sharpness`
- `exposure`
- `contrast`
- `color_balance`
- `effective_resolution`
- `coherence`

#### Definition des criteres

##### Nettete

- basee sur la variance du Laplacien
- penalise les images floues

##### Exposition

- basee sur des statistiques de luminance
- corrigee pour eviter de trop punir des produits naturellement fonces

##### Contraste

- base sur l'ecart-type des niveaux de gris
- verifie si le produit ressort suffisamment

##### Balance couleurs

- mesure une dominante anormale entre canaux
- critere volontairement peu punitif

##### Resolution effective

- combine la resolution brute et le niveau de detail utile
- permet de penaliser une image grande mais tres lisse ou reechantillonnee

##### Coherence image/texte

Combine :

- la similarite CLIP image/texte
- la coherence entre couleur attendue et couleur dominante

Important :

- la couleur n'est qu'un signal leger
- CLIP reste la composante principale de la coherence

#### Sorties

Le module retourne :

- les sous-scores 0-100
- des messages explicatifs
- un score global pondere
- des recommandations FR / Darija

### 7.6 `app.py`

#### Role

Exposer le pipeline dans une interface Streamlit simple pour :

- l'analyse unique
- le batch
- l'inspection debug

#### Modes principaux

##### Analyse unique

Entrees :

- image
- titre
- description

Affichage :

- crop selectionne en priorite
- score global
- criteres en barres
- bloc coherence image/texte
- recommandations

##### Batch

Permet de traiter un dossier d'images et d'exporter un tableau recapitulatif.

##### Debug

Affiche :

- regions candidates
- scores du selector
- donnees texte
- resultat du fallback DINO si active

## 8. Configuration centrale

Le fichier `config.py` contient les constantes globales du projet.

### Ce qui y est centralise

- chemins du dataset
- categories autorisees
- poids du selector
- poids du score global
- seuils de criteres
- configuration DINO
- configuration batch / application

### Interet

Ce choix permet :

- d'eviter les constantes magiques dispersees
- de documenter les decisions empiriques
- de faciliter la calibration

## 9. Dataset final

## 9.1 Structure

```text
dataset/
|- originals/
|  |- shoes/
|  |- clothing/
|  `- portable_electronics/
|- degraded/
|- annotations/
|- metadata.csv
`- degraded_metadata.csv
```

## 9.2 Categories retenues

- `shoes`
- `clothing`
- `portable_electronics`

## 9.3 Contenu du dataset

Le dataset final contient :

- `180` images propres dans `dataset/originals/`
- `3240` images degradees dans `dataset/degraded/`

Repartition :

- `60` images par categorie pour les originaux
- degradations controlees appliquees a toutes les images propres

## 9.4 Format de `metadata.csv`

Colonnes principales :

- `image_id`
- `filename`
- `filepath`
- `category`
- `source_dataset`
- `title`
- `description`
- `width`
- `height`
- `source_type`
- `degradation_type`
- `degradation_level`
- `human_score`
- `notes`

## 9.5 Format de `degraded_metadata.csv`

Colonnes principales :

- image degradee
- image source
- type de degradation
- niveau de degradation

## 10. Generation des degradations

Le script principal est :

- `generate_degraded.py`

### Types de degradation

- flou gaussien
- sous-exposition
- sur-exposition
- mauvais recadrage
- basse resolution
- compression JPEG

### Objectif scientifique

Utiliser des degradations controlees pour obtenir :

- une verite-terrain exacte
- une comparaison propre entre image reference et image degradee
- un protocole de validation defendable

## 11. Evaluation experimentale

## 11.1 `evaluate_analyzer.py`

Role :

- mesurer la sensibilite des criteres sur les images degradees

Principe :

1. analyser une image propre
2. analyser sa version degradee
3. comparer la baisse du critere cible

Sorties :

- `analyzer_sensitivity.csv`
- `analyzer_sensitivity_full_matrix.csv`

## 11.2 `evaluate_full.py`

Role :

- consolider l'evaluation complete du projet

Fonctions :

- generation d'un echantillon de 50 images pour jugement humain
- export du CSV d'annotation
- calcul de la correlation de Spearman
- generation d'un rapport consolide

Sorties importantes :

- `human_evaluation_template.csv`
- `evaluation_report.md`
- `spearman_correlation.png`

## 11.3 Resultat final de validation humaine

Le projet inclut une evaluation humaine finale sur 50 images.

Resultat principal :

- `Spearman rho = 0.7122`
- `p-value = 6.64e-09`

Interpretation :

- le score automatique suit nettement mieux le jugement humain apres l'ajout du critere `framing`
- la recalibration des poids a partir des annotations humaines augmente fortement la coherence globale du score
- le systeme reste zero-shot : il n'y a toujours aucun entrainement de modele profond, seulement une calibration des poids du score final

Lecture par categorie :

- `clothing` : categorie la plus robuste
- `portable_electronics` : comportement globalement bon
- `shoes` : categorie la plus difficile, mais en progression apres les derniers ajustements

Causes principales du gain :

- ajout d'un critere de cadrage produit (`framing`)
- mesure de `sharpness` sur la zone informative du produit plutot que sur tout le fond
- mesure de `effective_resolution` moins punitive sur les produits studio nets poses sur fond simple
- recalibration empirique des poids pour mieux coller au jugement humain

## 11.4 Evolution de la correlation

Cette section sert uniquement a montrer la progression du projet. Elle ne remplace pas les
resultats finaux presentes ci-dessus.

- version initiale evaluee : `rho ~= 0.3799`
- apres ajout de `framing` et premiere calibration : `rho ~= 0.6322`
- apres raffinement cible de `sharpness`, `effective_resolution` et `framing` : `rho ~= 0.7122`

## 11.5 Verification manuelle complementaire

Une verification manuelle supplementaire a ete faite sur 12 cas representatifs couvrant :

- `clothing`
- `portable_electronics`
- `shoes`

Objectif :

- verifier que le score reste plausible sur des cas propres
- verifier que les criteres `framing`, `effective_resolution` et `sharpness` ne degradent pas les bons cas visuellement acceptables

Constat :

- les cas `clothing` restent globalement stables
- les cas `portable_electronics` conservent une bonne coherence de score
- les cas les plus faibles restent concentres sur `shoes`, ce qui confirme que cette categorie est la priorite d'amelioration residuelle

## 12. Flux d'execution typiques

### 12.1 Lancer l'application

```bash
streamlit run app.py
```

### 12.2 Construire le dataset final

```bash
python scripts/build_final_dataset.py --verbose
```

### 12.3 Generer les degradations

```bash
python generate_degraded.py
```

### 12.4 Lancer l'evaluation des criteres

```bash
python evaluate_analyzer.py
```

### 12.5 Lancer l'evaluation complete

```bash
python evaluate_full.py
```

## 13. Dependances

Dependances Python importantes :

- `opencv-contrib-python`
- `numpy`
- `pandas`
- `pillow`
- `scipy`
- `matplotlib`
- `streamlit`
- `spacy`
- `rapidfuzz`
- `sentence-transformers`
- `torch`
- `torchvision`
- `transformers`

### Note spaCy

Le modele francais doit etre installe separement :

```bash
python -m spacy download fr_core_news_md
```

## 14. Decisions d'implementation importantes

### Pourquoi le texte est-il la verite ?

Parce que dans une annonce e-commerce :

- le titre et la description sont deja disponibles
- ils sont plus fiables que de l'OCR sur une image variable
- ils permettent de cibler le bon produit parmi plusieurs regions

### Pourquoi pas d'OCR ?

Parce que l'OCR :

- n'est pas necessaire pour le coeur du probleme
- introduit une complexite supplementaire
- serait plus fragile sur des images tres heterogenes

### Pourquoi RGB plutot que HSV pour la couleur ?

Parce que la couleur n'est qu'un signal secondaire.

Le choix de RGB est pragmatique :

- simple
- compatible avec le reste du pipeline image
- suffisant pour une coherence couleur legere

HSV peut etre cite comme perspective pour une comparaison couleur plus robuste a l'eclairage.

### Pourquoi CLIP ?

CLIP permet :

- de relier directement image et texte
- de selectionner le bon crop
- de mesurer une forme simple de coherence semantique

## 15. Forces du projet

- zero-shot defendable
- architecture multimodale claire
- explicabilite forte
- dataset degrade a verite-terrain connue
- application demonstrable
- evaluation automatique et humaine

## 16. Limites du projet

- performance variable selon les categories et les scenes
- sensibilite tres bonne sur le flou, plus moderee sur `lowres` et `bad_crop`
- extraction de marque encore heuristique
- extraction couleur simplifiee
- scope limite a trois familles
- pas de generalisation garantie hors distribution

## 17. Perspectives

Plusieurs extensions sont possibles :

- ameliorer la robustesse couleur avec HSV
- enrichir les dictionnaires et la taxonomie de categories
- renforcer la qualite du region proposal avec un fallback plus intelligent
- etendre a d'autres familles de produits
- ajouter un assistant d'annonce optionnel base sur LLM vision
- proposer un module separable de generation de titre / description / conseils vendeur

## 18. Conclusion

Le coeur de ce projet n'est pas l'entrainement d'un nouveau modele de qualite d'image.
Sa valeur vient de la combinaison entre :

- texte de l'annonce
- region proposal zero-shot
- selection du bon produit via CLIP et heuristiques
- analyse de qualite interpretable
- recommandations actionnables

Le resultat final est un systeme zero-shot multimodal explicable, adapte a un cadre PFE,
coherent avec un delai court, et suffisamment robuste pour etre demontre, evalue et defendu.
