# Documentation Technique — Système d'Analyse de Qualité d'Images E-commerce

**Projet :** Analyse automatique de la qualité d'images produits pour Jumia/Avito Maroc  
**Auteur :** Ahadj Idouae  
**Date :** Mai 2026  
**Technologie principale :** Python 3.11 · Streamlit · PyTorch · HuggingFace Transformers · OpenCV

---

## Table des matières

1. [Vue d'ensemble du projet](#1-vue-densemble-du-projet)
2. [Architecture et pipeline de traitement](#2-architecture-et-pipeline-de-traitement)
3. [Description détaillée des modules](#3-description-détaillée-des-modules)
4. [Algorithmes clés](#4-algorithmes-clés)
5. [Flux de données](#5-flux-de-données)
6. [Interface utilisateur (app.py)](#6-interface-utilisateur-apppy)
7. [Dataset et calibration](#7-dataset-et-calibration)
8. [Guide pour le jury](#8-guide-pour-le-jury)

---

## 1. Vue d'ensemble du projet

### 1.1 Contexte et problématique

Les vendeurs sur des places de marché comme **Jumia Maroc** et **Avito Maroc** publient quotidiennement des milliers d'annonces. La qualité de l'image produit est un facteur déterminant du taux de conversion : une photo floue, mal éclairée ou mal cadrée réduit significativement les chances de vente.

Ce système permet à un vendeur de :
- **Évaluer objectivement** la qualité de son image produit selon 6 critères techniques
- **Obtenir un score global** et une note (A à F) comparable aux standards e-commerce
- **Générer automatiquement** une fiche produit en français (titre, description, mots-clés)
- **Comparer** son produit avec les concurrents présents sur Jumia

### 1.2 Périmètre

| Aspect | Valeur |
|--------|--------|
| Plateforme cible | Jumia Maroc, Avito Maroc |
| Langue de l'interface | Français |
| Langue des fiches produit | Français |
| Taille du dataset de calibration | 300 images CDN Jumia (300×300 px) |
| Mode de déploiement | Local (Streamlit), extensible au cloud |

---

## 2. Architecture et pipeline de traitement

### 2.1 Architecture modulaire

```
┌─────────────────────────────────────────────────────────────────────┐
│                          app.py (Streamlit UI)                       │
│  Upload image ──► text_prompt (optionnel) ──► lancer l'analyse      │
└──────────┬──────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       src/scorer.py (façade)                         │
│  score_image(image_path, text_prompt) → {global, grade, criteria}   │
└──────────┬──────────────────────────────────────────────────────────┘
           │
    ┌──────┴──────────────────────────────────────┐
    │                                             │
    ▼                                             ▼
┌─────────────────┐                   ┌──────────────────────────────┐
│  src/detector.py │                   │       src/analyzer.py        │
│  detect_product() │                  │  analyze(image, detection,   │
│  ─────────────  │                   │          text_prompt)        │
│  1. Grounding   │                   │  ─────────────────────────── │
│     DINO        │                   │  6 critères indépendants :   │
│  2. GrabCut     │ ──► mask, bbox ──►│  jpeg_artifacts              │
│  3. Fallback    │                   │  lighting_uniformity         │
│     (Otsu)      │                   │  edge_quality                │
└─────────────────┘                   │  color_consistency           │
                                      │  effective_resolution        │
                                      │  clip_coherence              │
                                      └──────────────────────────────┘

┌─────────────────┐   ┌──────────────┐   ┌─────────────────────────┐
│   src/ocr.py    │──►│  src/nlp.py  │──►│     src/caption.py      │
│  EasyOCR        │   │  Extraction  │   │  BLIP + génération fiche│
│  fr + en        │   │  entités     │   │  (titre/description FR) │
└─────────────────┘   └──────────────┘   └─────────────────────────┘
                                                        │
                                                        ▼
                                          ┌─────────────────────────┐
                                          │   src/n8n_search.py     │
                                          │  Recherche concurrents  │
                                          │  Jumia Maroc (scraping) │
                                          └─────────────────────────┘
```

### 2.2 Pipeline complet pour une image

```
Image produit (JPEG/PNG)
        │
        ├─► [OCR] EasyOCR → texte brut → [NLP] entités (marque, modèle, couleur, prix)
        │
        ├─► [DETECTOR] Grounding DINO (si text_prompt) → bbox → GrabCut → masque binaire
        │          └── Fallback Otsu si DINO indisponible ou prompt vide
        │
        ├─► [ANALYZER] 6 critères sur (image, masque, text_prompt)
        │          └── global_score() → score pondéré [0,1] → grade A-F
        │
        ├─► [CAPTION] BLIP → légende anglaise → titre + description français
        │
        └─► [SEARCH] Jumia scraping → résultats concurrents → affichage comparatif
```

---

## 3. Description détaillée des modules

### 3.1 `src/detector.py` — Détection du produit

**Rôle :** Isoler le produit principal dans l'image et produire un masque binaire.

#### `detect_product(image_path, text_prompt=None) → dict`

| Paramètre | Type | Description |
|-----------|------|-------------|
| `image_path` | `str \| Path` | Chemin vers l'image |
| `text_prompt` | `str \| None` | Description naturelle du produit ("téléphone portable") |

**Retour :**
```python
{
    "mask":       np.ndarray,   # H×W, uint8, 0 ou 255
    "bbox":       [x1, y1, x2, y2],
    "confidence": float,        # 0.0 si fallback
    "label":      str,          # étiquette DINO ou "unknown (fallback)"
    "success":    bool,
    "method":     str,          # "grounding_dino" | "fallback"
}
```

**Logique de décision :**
1. Si `text_prompt` fourni → tente **Grounding DINO** (IDEA-Research/grounding-dino-tiny)
2. DINO trouve une bbox avec confidence > 0.35 → **GrabCut** pour affiner le masque
3. DINO échoue / indisponible → **Otsu + composante connexe** (fallback)
4. Si `text_prompt` est None → fallback direct

#### `visualize_detection(image_path, output_path, text_prompt=None) → bool`

Génère une image annotée avec overlay vert semi-transparent (α=0.35) sur le masque et rectangle vert sur la bbox. Le label DINO + confiance est affiché en blanc sur fond noir. Si la méthode est "fallback", aucun label n'est affiché (pas de watermark technique visible à l'utilisateur).

#### `_fallback_bg_subtraction(gray) → mask`

Algorithme :
1. **Seuillage Otsu inversé** : `cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU` → détecte le foreground sombre sur fond blanc
2. **Fermeture morphologique** (noyau elliptique 7×7, 2 itérations) → comble les trous
3. **Ouverture morphologique** (1 itération) → supprime le bruit
4. **composantesConnexes** → garde uniquement la plus grande région foreground

#### `_refine_mask_from_box(image_bgr, bbox) → mask`

Affine le bbox DINO en masque pixel-par-pixel via **GrabCut** (OpenCV) :
1. Tout hors bbox → `GC_BGD` (fond certain)
2. Intérieur bbox → `GC_PR_FGD` (foreground probable)
3. Rectangle inset 3% pour laisser GrabCut trouver les bords
4. 5 itérations EM
5. Post-traitement : ouverture + fermeture + plus grande composante connexe

---

### 3.2 `src/analyzer.py` — Analyse multi-critères

**Rôle :** Calculer 6 scores de qualité indépendants.

#### Pondérations

| Critère | Poids | Justification |
|---------|-------|---------------|
| `jpeg_artifacts` | 0.20 | Netteté = premier signal visuel client |
| `lighting_uniformity` | 0.20 | Éclairage = deuxième signal |
| `edge_quality` | 0.20 | Détourage produit = confiance acheteur |
| `color_consistency` | 0.15 | Fidélité couleur = réduction retours |
| `effective_resolution` | 0.15 | Zoom client = obligation Jumia ≥500px |
| `clip_coherence` | 0.10 | Cohérence texte-image = anti-fraude |

#### `analyze(image_path, detection, text_prompt=None) → dict`

Prend le masque pré-calculé par `detect_product()`, calcule les 6 critères en parallèle (appels séquentiels), retourne `{"criteria": dict, "success": bool}`.

#### `analyze_image(image_path, text_prompt=None) → dict`

Wrapper de convenance : appelle `detect_product()` en interne, puis `analyze()`.

#### `global_score(criteria) → float`

```python
score = Σ(criteria[name]["score"] × WEIGHTS[name]) / Σ(WEIGHTS[name])
```

#### `_linear(value, low, high) → float`

Normalisation linéaire `[low, high] → [0, 1]` avec saturation :
```
f(x) = clamp((x - low) / (high - low), 0, 1)
```

Utilisée par 4 critères sur 6 comme brique de base.

---

### 3.3 Critères détaillés

#### Critère 1 : `_jpeg_artifacts` — Netteté (Laplacien)

**Méthode :** Variance du filtre Laplacien sur le canal luminance (niveaux de gris).

**Pourquoi le Laplacien ?** Le filtre Laplacien (dérivée seconde) mesure les variations locales d'intensité. Une image nette a des bords francs → grande variance. Une image floue ou compressée a des transitions douces → faible variance.

**Formule :**
```
y = grayscale(image)
lap_var = Var(Laplacian(y))
score = clamp((log10(lap_var) - log10(200)) / (log10(3000) - log10(200)), 0, 1)
```

**Calibration sur 300 images Jumia :**
- Minimum observé : lap_var ≈ 229 → seuil bas = 200
- Maximum observé : lap_var ≈ 3586 → seuil haut = 3000
- Échelle logarithmique car la distribution des lap_var est log-normale

**Pourquoi pas la table de quantification JPEG ?** Les 300 images Jumia CDN ont toutes quality=75 → table identique → score constant 0.673 pour toutes. Discriminant nul.

**Messages utilisateur :**
- score ≥ 0.75 → "La qualité de votre photo est excellente"
- score ≥ 0.40 → "Photo correcte — vérifiez la mise au point"
- score < 0.40 → "Photo floue — reprenez avec un meilleur angle"

---

#### Critère 2 : `_lighting_uniformity` — Uniformité d'éclairage

**Méthode :** Grille 3×3 sur la bbox produit, écart-type des luminosités moyennes par zone.

```
zones_mean = [mean_brightness(zone_ij) for ij in 3×3 grid, masked by product mask]
score = 1 - linear(std(zones_mean), low=15, high=60)
```

**Seuils :** std < 15 = parfait, std > 60 = éclairage très irrégulier (ombre ou surexposition localisée).

**Note :** La grille est calculée sur le bbox produit, pas sur l'image entière, pour ne pas pénaliser les fonds blancs uniformes qui ne sont pas du produit.

---

#### Critère 3 : `_edge_quality` — Netteté des bords produit

**Méthode :** Détection Canny dans la zone de frontière entre masque et background.

```
boundary_mask = dilate(mask, 5px) - erode(mask, 5px)
canny_edges = Canny(gray, 50, 150)
edge_density = countNonZero(canny_edges & boundary_mask) / area(boundary_mask)
score = linear(edge_density, low, high)
```

**Seuils adaptatifs :** Images < 400px utilisent des seuils réduits de 40% pour compenser la perte d'information à basse résolution.

---

#### Critère 4 : `_color_consistency` — Fidélité des couleurs

**Méthode :** Hypothèse du monde gris (grey world assumption) + plage de saturation naturelle.

```python
# Component 1: cast chromatique
channel_std = std([mean_R, mean_G, mean_B])      # appliqué sur pixels produit
color_cast_score = 1 - linear(channel_std, 20, 60)

# Component 2: saturation naturelle (HSV S-channel)
# Plage naturelle : 50 < S < 150 (sur 255)
saturation_score = ...

score = 0.6 × color_cast_score + 0.4 × saturation_score
```

---

#### Critère 5 : `_effective_resolution` — Résolution effective

**Méthode :** Deux composantes égales.

**Composante 1 — Détection d'upscaling :**
```
ratio = Var(Laplacian(upscaled(downscaled(image)))) / Var(Laplacian(image))
upscaling_score = 1 - linear(ratio, 0.3, 0.8)
```
Si l'image originale est genuinement nette, downscaler puis upscaler introduit beaucoup de flou → ratio élevé. Si l'image était déjà floue/upscalée, le ratio est bas (elle ressemble déjà à une version dégradée).

**Composante 2 — Taille absolue :**
```
size_score = linear(min(H, W), 400, 800)
```
Jumia recommande 500×500 px minimum, 800×800 px idéal.

---

#### Critère 6 : `_clip_coherence` — Cohérence image-texte

**Méthode :** Similarité cosinus entre embeddings CLIP (openai/clip-vit-base-patch32).

```python
inputs = clip_processor(text=[text_prompt], images=pil_image)
logits = clip_model(**inputs).logits_per_image[0, 0]
score = sigmoid(logits)   # normalise vers [0,1]
```

**Dégradation gracieuse :** Si text_prompt est absent ou CLIP non disponible → score neutre 0.5 (pas de pénalité).

---

### 3.4 `src/ocr.py` — Extraction de texte (EasyOCR)

**Rôle :** Lire le texte visible sur l'image produit (marque, modèle, prix imprimés).

#### `extract_text(image_path) → dict`

```python
{
    "text_found": list[str],  # blocs bruts EasyOCR
    "prompt":     str,        # 4 mots significatifs filtrés
    "confidence": float,      # moyenne des scores EasyOCR
    "success":    bool,
}
```

**Langues reconnues :** français + anglais (`easyocr.Reader(['fr', 'en'])`, CPU mode).

**Filtrage des tokens :**
- Longueur < 2 caractères → rejeté
- Uniquement chiffres ou ponctuation → rejeté
- Format prix (`299DH`, `99€`) → rejeté
- Commence par un chiffre sans lettres suffisantes → rejeté

Le champ `prompt` retourne les 4 premiers mots significatifs, qui seront passés à `nlp.extract_entities()` et potentiellement à Grounding DINO comme text_prompt.

---

### 3.5 `src/nlp.py` — Extraction d'entités produit

**Rôle :** Structurer le texte OCR brut en entités sémantiques.

#### `extract_entities(text) → dict`

```python
{
    "brand":        str | None,   # "Samsung"
    "model":        str | None,   # "Galaxy A54"
    "color":        str | None,   # "Noir" (normalisé français)
    "storage":      str | None,   # "128GB"
    "price":        float | None, # 2999.0
    "currency":     str | None,   # "DH"
    "keywords":     list[str],    # ["Samsung", "Galaxy A54", "Noir"]
    "search_query": str,          # "Samsung Galaxy A54 Noir"
}
```

**Stratégie d'extraction (pipeline séquentiel) :**

1. **Marque** : correspondance regex `\b` sur un dictionnaire de 50+ marques connues (Samsung, Apple, Nike, Ariston...). Insensible à la casse.

2. **Couleur** : dictionnaire `COLOR_PATTERNS` avec aliases français + anglais (ex : "Noir" → ["noir", "black", "sombre"]). Retourne le nom canonique français.

3. **Stockage** : regex `(\d+)\s*(GB|Go|TB|Mo|Mb)` → normalisé en "128GB".

4. **Prix** : deux patterns regex en cascade :
   - `(\d+(?:[.,]\d+)?)\s*(DH|MAD|EUR|USD)` → ex: "2999DH"
   - `(€|\$)\s*(\d+)` → ex: "€1299"

5. **Modèle** : regex après suppression de la marque → première séquence alphanumérique avant une couleur ou un prix.

6. **search_query** : concaténation `Brand Model Storage Color` (déduplication, ordre fixe).

---

### 3.6 `src/caption.py` — Génération de fiche produit

**Rôle :** Combiner BLIP (légende visuelle) et entités NLP pour générer une fiche produit française.

#### `generate_listing(image_path, entities, lang="fr") → dict`

```python
{
    "caption":     str,       # légende anglaise brute de BLIP
    "title":       str,       # titre français ≤ 80 caractères
    "description": str,       # description française 3-4 phrases
    "keywords":    list[str], # mots-clés des entités NLP
    "success":     bool,      # True si BLIP a fonctionné
}
```

#### Modèle BLIP

**Modèle :** `Salesforce/blip-image-captioning-base`  
**Chargement :** Lazy (une seule fois par processus), CPU uniquement.  
**Inférence :** `model.generate(**inputs, max_new_tokens=50)`.

#### Construction du titre (`_build_title`)

```
Format : "Marque Modèle - TypeProduit Attribut"
Exemple : "Samsung Galaxy A54 - Smartphone Android 128GB Noir"
```

**Règles :**
1. Partie gauche : `[brand] [model]`. Le modèle est exclu s'il contient > 2 mots **et** aucune marque (évite que le text_prompt DINO comme "rotatable aluminum alloy stand" devienne le titre).
2. Partie droite : mots-clés tirés de la légende BLIP, traduits via `_EN_FR`, classés **types** (noms) avant **attributs** (adjectifs) — ordre grammatical français correct.
3. Les couleurs sont exclues de la partie droite (source : entités NLP uniquement, pas BLIP — évite "Blanc" venant du fond blanc derrière le produit).
4. Ajout du stockage et de la couleur NLP en fin de titre si non déjà présents.
5. Troncature à 80 caractères sur un espace (pas en milieu de mot).

#### Construction de la description (`_build_description`)

Quatre phrases structurées :
1. "Samsung Galaxy A54 — 128GB, coloris Noir." (marque + specs)
2. "Ce smartphone android est idéal pour un usage quotidien." (type + attributs BLIP → français)
3. "Prix indicatif : 2999 DH." (si prix trouvé par NLP)
4. "Livraison disponible partout au Maroc." (toujours présente)

**Important :** la légende anglaise brute de BLIP n'est jamais insérée dans la description finale. Elle sert uniquement à extraire des mots-clés via le dictionnaire `_EN_FR`.

---

### 3.7 `src/n8n_search.py` — Recherche concurrentielle

**Rôle :** Rechercher des produits similaires sur Jumia Maroc.

#### `search_competitors(search_query, limit=5) → list[dict]`

**Mode A — Webhook n8n (si disponible localement sur port 5678) :**
```
POST http://localhost:5678/webhook/product-search
{"query": "Samsung Galaxy A54", "limit": 5}
```
Timeout 5s. Si n8n est absent → ConnectionError → fallback automatique.

**Mode B — Scraping direct Jumia :**
```
GET https://www.jumia.ma/catalog/?q=<query>
```
Headers User-Agent Chrome réaliste pour éviter le blocage anti-bot.

**Sélecteurs HTML Jumia (validés mai 2026) :**
```python
articles = soup.find_all("article", class_="prd")
for article in articles[:limit]:
    name  = article.find(class_="name").get_text()
    price = article.find(class_="prc").get_text()   # → parsé "2 999 Dh" → 2999.0
    link  = article.find("a", class_="core")["href"]
    img   = article.find("img").get("data-src")     # lazy-loading, pas "src"
```

**Résultat par produit :**
```python
{
    "name":        str,
    "price":       float | None,  # en DH
    "image_url":   str | None,
    "product_url": str | None,
    "source":      "n8n" | "scraping",
}
```

#### `download_competitor_images(results, output_dir) → list[Path]`

Télécharge et convertit chaque image en JPEG qualité 95 via PIL. Délai 1s entre requêtes (respect robots.txt). Retourne les chemins des fichiers sauvegardés.

---

### 3.8 `src/scorer.py` — Façade de scoring

**Rôle :** Interface publique simplifiée combinant détection + analyse + grade.

#### `score_image(image_path, text_prompt=None) → dict`

```python
{
    "global":   float,          # score global [0, 1]
    "grade":    "A"|"B"|"C"|"D"|"F",
    "criteria": dict,           # 6 sous-scores détaillés
    "success":  bool,
    "error":    str | None,
}
```

**Barème des grades :**
| Grade | Score | Interprétation |
|-------|-------|----------------|
| A | ≥ 0.85 | Image professionnelle |
| B | ≥ 0.70 | Bonne qualité |
| C | ≥ 0.55 | Qualité acceptable |
| D | ≥ 0.40 | Qualité insuffisante |
| F | < 0.40 | Image rejetée |

---

## 4. Algorithmes clés

### 4.1 Détection multi-niveaux (Grounding DINO + GrabCut + Otsu)

```
                      ┌────────────────────────────┐
text_prompt fourni? ──►   Grounding DINO             │
                      │  (zero-shot object detection)│
                      │  BOX_THRESHOLD = 0.35        │
                      │  TEXT_THRESHOLD = 0.25       │
                      └──────────┬─────────────────┘
                                 │ bbox trouvée?
                         YES ────┤──── NO
                         ▼       │         ▼
                    GrabCut      │    Fallback Otsu
                   (5 iter.)     │    + composante
                   → masque fin  │    connexe max
                                 │
                                 ▼
                         Fallback (directement
                         si pas de text_prompt)
```

### 4.2 Calcul du score global

```
score_global = Σ(score_i × poids_i) / Σ(poids_i)

Exemple :
jpeg_artifacts    = 0.72 × 0.20 = 0.144
lighting_uniformity = 0.85 × 0.20 = 0.170
edge_quality      = 0.60 × 0.20 = 0.120
color_consistency = 0.90 × 0.15 = 0.135
effective_resolution = 0.50 × 0.15 = 0.075
clip_coherence    = 0.80 × 0.10 = 0.080
─────────────────────────────────────────
Total             =            0.724 → Grade B
```

### 4.3 Netteté par variance du Laplacien (calibration log-normale)

La distribution des variances Laplaciennes des images Jumia est log-normale (images compressées à qualité constante 75). La normalisation en échelle log est donc plus discriminante qu'une normalisation linéaire :

```
score = clamp((log10(var) - log10(200)) / (log10(3000) - log10(200)), 0, 1)
      = clamp((log10(var) - 2.301) / (3.477 - 2.301), 0, 1)
      = clamp((log10(var) - 2.301) / 1.176, 0, 1)
```

Pour var=500  → score = (2.699 - 2.301) / 1.176 = 0.338
Pour var=1000 → score = (3.000 - 2.301) / 1.176 = 0.594
Pour var=2000 → score = (3.301 - 2.301) / 1.176 = 0.850

---

## 5. Flux de données

### 5.1 Flux complet d'une session utilisateur

```
1. Utilisateur uploade image.jpg
        │
2. Streamlit → tempfile.NamedTemporaryFile → /tmp/image.jpg
        │
3. extract_text(/tmp/image.jpg)
   ──► EasyOCR → ["Samsung", "Galaxy A54", "128Go", "2999DH"]
   ──► prompt = "samsung galaxy a54"
        │
4. extract_entities("samsung galaxy a54 128go 2999dh")
   ──► {brand:"Samsung", model:"Galaxy A54", color:None, storage:"128GB",
        price:2999.0, currency:"DH", search_query:"Samsung Galaxy A54 128GB"}
        │
5. detect_product(/tmp/image.jpg, text_prompt="samsung galaxy a54")
   ──► DINO → bbox=[42,18,258,282], conf=0.87
   ──► GrabCut → mask (H×W, uint8)
        │
6. analyze(/tmp/image.jpg, detection, text_prompt="samsung galaxy a54")
   ──► jpeg_artifacts:      {score:0.72, value:847.3, message:"..."}
   ──► lighting_uniformity: {score:0.85, value:12.4,  message:"..."}
   ──► edge_quality:        {score:0.60, value:0.231,  message:"..."}
   ──► color_consistency:   {score:0.90, value:18.2,   message:"..."}
   ──► effective_resolution:{score:0.50, value:0.421,  message:"..."}
   ──► clip_coherence:      {score:0.80, value:22.4,   message:"..."}
        │
7. global_score(criteria) = 0.724 → Grade B
        │
8. generate_listing(/tmp/image.jpg, entities)
   ──► BLIP → "a black smartphone on a white background"
   ──► title = "Samsung Galaxy A54 - Smartphone 128GB Noir"
   ──► description = "Samsung Galaxy A54 — 128GB, coloris Noir. ..."
        │
9. search_competitors("Samsung Galaxy A54 128GB", limit=5)
   ──► Mode B: scraping Jumia → 4 produits trouvés avec prix et images
        │
10. Affichage Streamlit : score, détection, fiche produit, comparatif
```

### 5.2 Gestion de l'état Streamlit (session_state)

| Clé | Contenu | Utilisée par |
|-----|---------|-------------|
| `_report` | dict complet `analyze()` | Affichage critères |
| `_text_prompt` | texte utilisateur | `visualize_detection`, competitor search |
| `listing_title` | valeur widget titre | Synchronisation formulaire |
| `listing_desc` | valeur widget description | Synchronisation formulaire |

**Problème de cache résolu :** Lors d'un nouvel upload, `listing_title` et `listing_desc` sont supprimés de `session_state` avant le rendu pour forcer les widgets à afficher les nouvelles valeurs (sans `st.session_state.pop()`, Streamlit retourne l'ancienne valeur).

---

## 6. Interface utilisateur (app.py)

### 6.1 Structure de la page

```
┌─────────────────────────────────────────────────┐
│  🛍️ Qualité Image E-commerce — Jumia / Avito    │
├─────────────────────────────────────────────────┤
│  [sidebar]                                       │
│  ├── Upload image                               │
│  ├── Description produit (text_prompt)          │
│  └── [Analyser]                                 │
├─────────────────────────────────────────────────┤
│  col1 : Image originale                         │
│  col2 : Détection produit (visualize_detection) │
│                                                  │
│  Score global : 0.724 [████████░░] Grade B       │
│                                                  │
│  Détail des critères (6 progress bars)          │
│                                                  │
│  ▼ Fiche produit générée                        │
│    Titre (éditable) │ Description (éditable)    │
│    Mots-clés                                    │
│                                                  │
│  ▼ Analyse concurrentielle                      │
│    [5 produits Jumia avec image, nom, prix]     │
└─────────────────────────────────────────────────┘
```

### 6.2 Fonction `_render_competitor_comparison(entities)`

**Stratégie de recherche à 3 niveaux :**
1. `entities["search_query"]` (NLP sur texte OCR) → priorité absolue
2. `st.session_state["_text_prompt"]` (saisie utilisateur) → fallback si OCR vide
3. Champ de saisie manuel → dernier recours affiché à l'utilisateur

Cette chaîne garantit que la section "Analyse concurrentielle" s'affiche pour **toutes les images**, y compris celles sans texte visible (logos, photographies pures).

---

## 7. Dataset et calibration

### 7.1 Dataset Jumia Maroc

- **Taille :** 300 images CDN Jumia (`data/raw_images/`)
- **Résolution :** 300×300 px (format standard Jumia CDN)
- **Format :** JPEG quality=75 (uniforme sur tout le CDN)
- **Catégories :** Électronique, Mode, Electroménager, Accessoires

### 7.2 Calibration du critère `jpeg_artifacts`

**Processus :**
1. Extraction de la variance Laplacienne sur les 300 images
2. Distribution : log-normale, min≈229, max≈3586, médiane≈850
3. Seuil bas = 200 (légèrement sous le minimum observé, garde de sécurité)
4. Seuil haut = 3000 (légèrement sous le maximum, évite 100% pour les meilleures)
5. Validation : 29 valeurs uniques sur 300 images → bonne discrimination

**Résultat :** score moyen = 0.525, distribution uniforme entre 0.05 et 1.0.

### 7.3 Calibration du critère `lighting_uniformity`

- std < 15 (éclairage parfaitement uniforme) → score 1.0
- std > 60 (fort contraste entre zones) → score 0.0
- Validé sur des images avec/sans ombre directionnelle

### 7.4 Calibration du critère `effective_resolution`

- Recommandation Jumia : 500×500 px minimum
- Seuil bas = 400px (trop petit pour le zoom client)
- Seuil haut = 800px (idéal pour toutes les vignettes Jumia)

---

## 8. Guide pour le jury

### 8.1 Comment lancer le système

```bash
# 1. Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# 2. Lancer l'application
streamlit run app.py --server.port 8507

# 3. Ouvrir http://localhost:8507 dans le navigateur
```

### 8.2 Démonstration recommandée

**Scénario 1 — Image électronique avec texte :**
1. Charger `data/raw_images/electronics/001_1.jpg`
2. L'OCR détecte "chargeur" → text_prompt automatique
3. Montrer le masque de détection (DINO ou fallback)
4. Commenter les 6 scores individuels
5. Montrer la fiche produit générée en français
6. Montrer les 4-5 concurrents Jumia trouvés

**Scénario 2 — Image sans texte visible :**
1. Charger une image de vêtement ou accessoire
2. Montrer le champ de saisie manuel pour la recherche concurrentielle
3. Démontrer le fallback text_prompt → recherche Jumia

**Scénario 3 — Comparaison qualité :**
1. Charger une image floue (score bas, grade D/F)
2. Charger une image nette (score élevé, grade A/B)
3. Comparer visuellement les variance Laplaciennes affichées

### 8.3 Questions fréquentes du jury

**Q : Pourquoi 6 critères et pas plus/moins ?**  
R : Six critères couvrent les quatre dimensions de qualité image (netteté, exposition, résolution, fidélité couleur) avec un critère sémantique (CLIP) et un critère de détourage (edges). Au-delà, la redondance nuit à l'interprétabilité. En dessous, on perd en précision diagnostique.

**Q : Comment avez-vous choisi les poids ?**  
R : Les poids reflètent l'importance perçue par les acheteurs sur les places de marché marocaines : la netteté et l'éclairage sont les deux premiers signaux visuels (0.20 chacun), la résolution et la cohérence texte-image sont secondaires (0.15 et 0.10).

**Q : Pourquoi Laplacien et pas FFT ou gradient Sobel ?**  
R : Le Laplacien (dérivée seconde) est plus sensible aux hautes fréquences que le gradient Sobel (dérivée première). Il pénalise davantage le flou de compression JPEG qui atténue précisément ces hautes fréquences. La FFT donnerait des résultats similaires mais est plus coûteuse en calcul.

**Q : Que se passe-t-il si CLIP ou BLIP ne sont pas disponibles ?**  
R : Dégradation gracieuse : CLIP retourne 0.5 (score neutre, pas de pénalité). BLIP retourne une légende vide ; le titre et la description sont construits à partir des entités NLP uniquement. Le système reste fonctionnel sans GPU et en mode hors-ligne.

**Q : Le scraping Jumia est-il légal ?**  
R : Dans le cadre académique, le scraping respecte robots.txt (délai REQUEST_DELAY=2s entre requêtes), ne stocke pas de données personnelles, et cible uniquement les données publiques. Pour une mise en production commerciale, une API officielle ou un accord commercial avec Jumia serait nécessaire.

**Q : Comment étendre le système à Avito ?**  
R : Remplacer les sélecteurs CSS de `n8n_search.py` par ceux d'Avito. L'URL de base passe à `https://www.avito.ma/fr`. Tous les autres modules sont indépendants de la plateforme.

**Q : Quelle est la précision du scoring par rapport à une évaluation humaine ?**  
R : Nous n'avons pas de dataset annoté humainement pour Jumia Maroc. En revanche, les seuils ont été calibrés sur 300 images réelles et validés visuellement : les images notées A/B correspondent effectivement aux meilleures photos du catalogue, et les notes D/F aux photos floues ou sur-exposées visibles à l'œil nu.

### 8.4 Limites et perspectives

| Limite | Perspective |
|--------|-------------|
| Images 300×300px CDN → seuils calibrés sur petites images | Recalibrer sur images haute résolution (800×800+) |
| EasyOCR lent (CPU, ~3s/image) | GPU ou remplacement par PaddleOCR |
| Scraping Jumia peut être bloqué par anti-bot | Intégrer n8n avec API officielle Jumia |
| CLIP non disponible hors ligne | Modèle CLIP local en cache HuggingFace |
| Fiche produit en français uniquement | Ajouter arabe (darija) pour le marché marocain |
| Score non validé par A/B test e-commerce | Corréler avec taux de clics réels Jumia |

---

*Document généré automatiquement le 2026-05-12 à partir du code source du projet.*
