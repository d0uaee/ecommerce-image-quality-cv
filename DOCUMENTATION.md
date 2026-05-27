# Documentation Technique - Systeme Zero-Shot d'Evaluation de Qualite d'Images E-commerce

## 1. Objectif du projet

Ce projet PFE vise a evaluer automatiquement la qualite d'une photo de produit e-commerce
et a fournir un score global accompagne de conseils d'amelioration en francais et en darija.

Le systeme cible des petits vendeurs qui ne disposent pas de photographe professionnel.

## 2. Positionnement scientifique

Le projet suit une logique zero-shot :

- aucun entrainement de modele n'est realise dans ce depot
- les modeles utilises sont pre-entraines
- les donnees servent a calibrer des seuils et a valider le pipeline
- l'innovation se situe dans l'architecture multimodale et l'explicabilite

Les briques principales sont :

- NLP pour exploiter le texte de l'annonce
- vision classique OpenCV pour proposer des regions candidates
- CLIP multilingue pour relier texte et image
- heuristiques explicables pour la qualite visuelle
- scoring global interpretable

## 3. Hypotheses du projet

Le systeme repose sur cinq hypotheses structurantes :

1. le texte de l'annonce (`titre + description`) est la source de verite principale
2. il n'y a pas d'OCR dans le chemin critique du scoring
3. aucun modele n'est entraine localement
4. les bonnes images servent de references et les mauvaises images sont generees par degradation controlee
5. le scope est volontairement reduit a trois familles :
   - `shoes`
   - `clothing`
   - `portable_electronics`

## 4. Pipeline actuel

Le pipeline reel du projet est le suivant :

```text
annonce (image + titre + description)
 -> text_processor
 -> candidate_region_generator
 -> selector
 -> analyzer
 -> score global
 -> conseils FR / Darija
 -> app Streamlit
```

## 5. Description des modules

### 5.1 `src/text_processor.py`

Role :

- nettoyer le texte de l'annonce
- extraire des attributs simples
- produire un embedding texte reutilisable

Sortie principale :

```python
{
    "clean_text": str,
    "color": str | None,
    "category": str | None,
    "brand": str | None,
    "text_embedding": np.ndarray,
}
```

Implementation actuelle :

- normalisation textuelle
- spaCy `fr_core_news_md` si disponible
- extraction heuristique via `rapidfuzz` et dictionnaires
- embedding texte via `sentence-transformers/clip-ViT-B-32-multilingual-v1`
- cache d'embedding pour eviter les recalculs
- fallback robuste vers un vecteur nul si le backend n'est pas disponible

### 5.2 `src/candidate_region_generator.py`

Role :

- proposer des regions candidates sans detection supervisee par defaut

Strategie actuelle :

- saliency OpenCV si disponible
- fallback contours / seuillage adaptatif
- regions triees par aire et centralite
- maximum 5 regions pour limiter le cout du selector

Fonctions principales :

- `propose_regions(image)`
- `refine_crop(image, bbox)` avec GrabCut
- `detect_with_dino(image, prompt)` comme filet de securite activable

Important :

- Grounding DINO existe comme fallback
- il est desactive par defaut via `config.py`

### 5.3 `src/selector.py`

Role :

- choisir le bon produit parmi les regions candidates

Pour chaque region candidate, le systeme calcule :

- `score_clip` : similarite image/texte
- `score_visual` : aire normalisee x centralite
- `score_category` : coherence categorie heuristique

Formule actuelle :

```text
score = 0.6 * clip + 0.25 * visuel + 0.15 * categorie
```

Ces poids sont stockes dans `config.py` et assumes comme une calibration empirique.

Le module retourne :

- la bbox gagnante
- le crop selectionne
- un masque optionnel apres `refine_crop`
- le detail des scores intermediaires pour l'explicabilite

### 5.4 `src/analyzer.py`

Role :

- evaluer la qualite du crop selectionne

Criteres calcules actuellement :

- `sharpness`
- `exposure`
- `contrast`
- `color_balance`
- `effective_resolution`
- `coherence`

Principes de calcul :

- nettete : variance du Laplacien
- exposition : statistiques d'histogramme et ecart a une zone cible
- contraste : ecart-type en niveaux de gris
- balance couleur : deviation inter-canaux
- resolution effective : taille utile + signal de detail
- coherence : CLIP(image, texte) + couleur dominante du crop

La couleur reste un signal leger dans la coherence.

Le module retourne :

- les sous-scores 0-100
- un score global pondéré
- des messages explicatifs
- des recommandations FR / Darija

### 5.5 `app.py`

Role :

- exposer le pipeline dans une interface Streamlit simple

Modes disponibles :

- analyse unique
- batch dossier

Affichage prioritaire :

- crop selectionne
- score global
- criteres en barres
- coherence image / texte
- recommandations
- debug optionnel

## 6. Configuration centrale

Le fichier `config.py` centralise :

- les chemins
- les categories autorisees
- les poids du selector
- les seuils de qualite
- la configuration du fallback DINO
- les poids du score global

Ce choix limite la dispersion de constantes magiques dans le projet.

## 7. Donnees

La structure cible des donnees est :

```text
data/
  raw_images/
  clean_references/
  degraded/
  metadata.csv
```

Le protocole cible est :

- bonnes images propres de reference
- versions degradees generees automatiquement
- verite-terrain connue pour chaque degradation

Note importante :

Le depot contient encore des donnees historiques qui ne sont pas encore totalement alignees
avec la spec finale du PFE. Le code de l'application inclut temporairement une compatibilite
avec cet ancien schema pour continuer les tests.

## 8. Evaluation

Deux scripts principaux existent pour la validation :

### `evaluate_analyzer.py`

- mesure la sensibilite des criteres sur `data/degraded/`
- compare image propre vs image degradee
- produit des tableaux de baisse moyenne par critere

### `evaluate_full.py`

- prepare un echantillon annotable humainement
- exporte un CSV de comparaison
- calcule une correlation de Spearman si les annotations humaines sont remplies
- consolide les sorties d'evaluation dans un rapport

## 9. Forces du projet

- architecture zero-shot defendable en soutenance
- explication visible du choix de crop
- sous-scores interpretabless
- cout de developpement raisonnable pour 2 mois
- forte reutilisabilite de briques standard

## 10. Limites actuelles

- le dataset versionne n'est pas encore completement aligne avec le scope final
- les references historiques en `300x300` penaliseront fortement le critere de resolution
- la qualite du fallback regions candidates depend du type d'image
- les supports de soutenance et certains fichiers de test doivent encore etre alignes avec la version zero-shot finale

## 11. Conclusion

Le coeur du projet n'est pas l'entrainement d'un classifieur de qualite.
La valeur du systeme reside dans la combinaison explicable entre :

- texte de l'annonce
- selection zero-shot du bon produit
- mesures visuelles interpretabless
- recommandations actionnables

Le projet constitue donc un systeme zero-shot multimodal explicable pour l'evaluation
de photos produits e-commerce.
