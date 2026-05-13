const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, BorderStyle, WidthType, ShadingType,
  HeadingLevel, LevelFormat, PageNumber, TabStopType, TabStopPosition,
} = require("docx");
const fs = require("fs");

// ─── Palette ────────────────────────────────────────────────────────────────
const NAVY   = "0D2137";
const TEAL   = "0E8C9B";
const MINT   = "00B98A";
const LIGHT  = "EBF4F7";
const WHITE  = "FFFFFF";
const GRAY   = "64748B";
const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "D1E4EB" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

// ─── Content Width (A4 with 2cm margins) ────────────────────────────────────
// A4 = 11906 DXA wide; 2cm = 1134 DXA; content = 11906 - 2*1134 = 9638
const PAGE_W = 11906;
const MARGIN  = 1134;   // ~2 cm
const CONT_W  = PAGE_W - 2 * MARGIN;   // 9638

// ─── Helpers ────────────────────────────────────────────────────────────────
function sp(size, color = "1A252F", bold = false, italic = false, font = "Calibri") {
  return new TextRun({ text: " ", size, color, bold, italic, font });
}
function run(text, size = 22, color = "1A252F", bold = false, italic = false, font = "Calibri") {
  return new TextRun({ text, size, color, bold, italic, font });
}
function para(children, opts = {}) {
  return new Paragraph({ children, ...opts });
}
function empty(spacing = 120) {
  return new Paragraph({ children: [run("")], spacing: { after: spacing } });
}
function hrLine() {
  return new Paragraph({
    children: [],
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: TEAL, space: 1 } },
    spacing: { after: 120 },
  });
}

// ─── Slide block ────────────────────────────────────────────────────────────
function slideBlock(num, title, duration, script) {
  const paragraphs = [];

  // Header row: "Slide N — Titre" and "⏱ X min"
  paragraphs.push(
    new Table({
      width: { size: CONT_W, type: WidthType.DXA },
      columnWidths: [Math.round(CONT_W * 0.78), Math.round(CONT_W * 0.22)],
      rows: [new TableRow({
        children: [
          new TableCell({
            borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
            shading: { fill: NAVY, type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 180, right: 60 },
            width: { size: Math.round(CONT_W * 0.78), type: WidthType.DXA },
            children: [new Paragraph({
              children: [
                new TextRun({ text: `Slide ${num}  —  `, size: 24, bold: true, color: TEAL, font: "Calibri" }),
                new TextRun({ text: title, size: 24, bold: true, color: WHITE, font: "Calibri" }),
              ],
            })],
          }),
          new TableCell({
            borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
            shading: { fill: NAVY, type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 60, right: 120 },
            width: { size: Math.round(CONT_W * 0.22), type: WidthType.DXA },
            verticalAlign: "center",
            children: [new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({ text: `⏱  ${duration}`, size: 20, color: MINT, italic: true, font: "Calibri" })],
            })],
          }),
        ],
      })],
    })
  );

  // Script body — each line starting with "—" becomes a new bullet
  const lines = script.trim().split("\n");
  let currentBlock = [];

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      if (currentBlock.length) {
        paragraphs.push(new Paragraph({
          children: currentBlock,
          spacing: { before: 60, after: 80 },
        }));
        currentBlock = [];
      }
      continue;
    }

    // Section label (starts with "---")
    if (line.startsWith("###")) {
      if (currentBlock.length) {
        paragraphs.push(new Paragraph({ children: currentBlock, spacing: { before: 60, after: 80 } }));
        currentBlock = [];
      }
      paragraphs.push(new Paragraph({
        children: [new TextRun({ text: line.replace(/^###\s*/, ""), size: 20, bold: true, color: TEAL, font: "Calibri" })],
        spacing: { before: 140, after: 40 },
      }));
      continue;
    }

    // Bullet point (starts with "—" or "-")
    if (line.startsWith("—") || line.startsWith("-")) {
      if (currentBlock.length) {
        paragraphs.push(new Paragraph({ children: currentBlock, spacing: { before: 60, after: 80 } }));
        currentBlock = [];
      }
      paragraphs.push(new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun({ text: line.replace(/^[—\-]\s*/, ""), size: 22, color: "1A252F", font: "Calibri" })],
        spacing: { before: 40, after: 40 },
      }));
      continue;
    }

    // Sub-bullet (starts with "  •")
    if (line.startsWith("•")) {
      if (currentBlock.length) {
        paragraphs.push(new Paragraph({ children: currentBlock, spacing: { before: 60, after: 80 } }));
        currentBlock = [];
      }
      paragraphs.push(new Paragraph({
        numbering: { reference: "subbullets", level: 0 },
        children: [new TextRun({ text: line.replace(/^•\s*/, ""), size: 20, color: GRAY, font: "Calibri" })],
        spacing: { before: 20, after: 20 },
      }));
      continue;
    }

    // Bold label pattern: "**Label :** text"
    if (line.includes("**")) {
      if (currentBlock.length) {
        paragraphs.push(new Paragraph({ children: currentBlock, spacing: { before: 60, after: 80 } }));
        currentBlock = [];
      }
      const parts = line.split(/\*\*/);
      const runs = parts.map((p, i) =>
        new TextRun({ text: p, size: 22, bold: i % 2 === 1, color: i % 2 === 1 ? NAVY : "1A252F", font: "Calibri" })
      );
      paragraphs.push(new Paragraph({ children: runs, spacing: { before: 60, after: 60 } }));
      continue;
    }

    // Regular text — accumulate into block
    if (currentBlock.length > 0) {
      currentBlock.push(new TextRun({ text: " ", size: 22, font: "Calibri" }));
    }
    currentBlock.push(new TextRun({ text: line, size: 22, color: "1A252F", font: "Calibri" }));
  }

  if (currentBlock.length) {
    paragraphs.push(new Paragraph({ children: currentBlock, spacing: { before: 60, after: 80 } }));
  }

  paragraphs.push(empty(60));
  paragraphs.push(hrLine());
  paragraphs.push(empty(80));

  return paragraphs;
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDES DATA
// ════════════════════════════════════════════════════════════════════════════

const slides = [
  {
    num: 1, title: "Titre", duration: "~30 sec",
    script: `
Bonjour à tous. Je m'appelle Ahadj Idouae, et je vous présente aujourd'hui mon projet intitulé
**« Analyse automatique de la qualité d'images produits pour l'e-commerce marocain ».**

Ce projet s'inscrit dans le contexte du marché numérique marocain, en ciblant
principalement les plateformes Jumia Maroc et Avito.

La présentation dure environ **15 minutes**, suivies de vos questions.

*[Attendre que le jury soit prêt, maintenir le contact visuel.]*
`,
  },
  {
    num: 2, title: "Contexte et Objectifs", duration: "~1 min 30",
    script: `
Commençons par la **problématique.**

Le marché e-commerce au Maroc est en forte croissance, mais de nombreux vendeurs —
notamment les petites entreprises et les particuliers — publient des annonces avec des
photos de mauvaise qualité.

### Problèmes constatés
— Images floues ou sur-exposées
— Produit mal cadré ou fond encombré
— Fiches produit incomplètes ou rédigées en anglais
— Aucun outil d'aide accessible pour les PME marocaines

Une **mauvaise image réduit directement le taux de conversion** — un client qui ne voit
pas clairement le produit n'achète pas.

### Notre réponse
Notre solution est un système automatique à trois dimensions :
— Évaluer objectivement la qualité de l'image via six critères techniques
— Générer automatiquement une fiche produit complète en français
— Comparer le produit avec les offres concurrentes déjà présentes sur Jumia

*[Faire un pause pour laisser le jury lire les deux colonnes.]*
`,
  },
  {
    num: 3, title: "Architecture du Système", duration: "~2 min",
    script: `
Voici l'**architecture complète** du système.

Le pipeline de traitement comporte **sept étapes enchaînées** :

### Étape 1 à 3 — Entrée et analyse texte
— L'utilisateur uploade une image JPEG ou PNG via l'interface Streamlit.
— Le module **OCR** (EasyOCR) lit le texte visible sur l'image : marque, modèle,
  prix imprimés sur le packaging.
— Le module **NLP** structure ce texte en entités : marque, modèle, couleur, stockage, prix.

### Étape 4 — Détection du produit
— **Grounding DINO** localise le produit dans l'image via une description textuelle,
  puis **GrabCut** affine le masque pixel par pixel.
— Si DINO est indisponible, un fallback par seuillage Otsu prend le relais.

### Étapes 5 à 7 — Analyse, génération et comparaison
— L'**analyseur** calcule six critères de qualité et produit un score global A–F.
— **BLIP** génère une légende visuelle traduite en fiche produit française.
— Le **scraper** recherche les produits similaires sur Jumia pour l'analyse concurrentielle.

Tout ceci est orchestré par l'interface **Streamlit**, accessible depuis n'importe quel
navigateur sans installation côté utilisateur.
`,
  },
  {
    num: 4, title: "Modules Développés", duration: "~1 min",
    script: `
Le projet est structuré en **neuf modules Python indépendants**, chacun avec une
responsabilité unique et une interface publique claire.

### Modules centraux
— **src/detector.py** — Isolation du produit (DINO + GrabCut + Otsu)
— **src/analyzer.py** — Calcul des six critères et du score global
— **src/scorer.py** — Façade qui unifie détection + analyse + grade A–F

### Modules périphériques
— **src/ocr.py** — Lecture du texte visible sur l'image (EasyOCR bilingue)
— **src/nlp.py** — Extraction des entités structurées par regex
— **src/caption.py** — Génération de la fiche produit via BLIP
— **src/n8n_search.py** — Recherche concurrents Jumia (scraping)
— **src/visualizer.py** — Annotation de l'image avec les scores
— **app.py** — Interface Streamlit, gestion de session

Tous les modules sont **terminés, testés, et commentés.** La conception modulaire facilite
les tests unitaires et les évolutions futures.
`,
  },
  {
    num: 5, title: "Les 6 Critères d'Analyse", duration: "~3 min",
    script: `
Parlons du cœur du système : les **six critères d'analyse qualité**.

Chaque critère retourne un **score entre 0 et 1**, une valeur brute mesurée, et un
**message d'explication en français** destiné directement au vendeur.

### Critère 1 — Netteté (poids 20 %)
Nous utilisons la **variance du filtre Laplacien**. Ce filtre de dérivée seconde est très
sensible aux hautes fréquences, donc au flou et à la compression excessive.
Nous avons calibré les seuils en **échelle logarithmique** sur 300 images réelles du CDN
Jumia, car la distribution des variances est log-normale (seuils : 200 → 3000).

### Critère 2 — Uniformité d'éclairage (poids 20 %)
On divise la zone produit en une **grille 3×3** et on mesure l'écart-type des
luminosités moyennes par zone. Un écart-type faible signifie un éclairage homogène.
Seuils : std < 15 = parfait, std > 60 = éclairage très irrégulier.

### Critère 3 — Qualité des bords (poids 20 %)
Détection **Canny** dans la zone frontière entre le masque produit et le fond.
On mesure la densité des bords détectés. Les seuils sont adaptatifs selon la résolution
de l'image : réduits de 40 % pour les images inférieures à 400 pixels.

### Critère 4 — Cohérence des couleurs (poids 15 %)
On applique l'**hypothèse du monde gris** (grey world) : dans un éclairage neutre,
les moyennes R, G, B devraient être proches. On vérifie aussi que la saturation HSV
se situe dans la plage naturelle (50 à 150 sur 255).

### Critère 5 — Résolution effective (poids 15 %)
Deux composantes égales :
— **Détection d'upscaling** : ratio de variance Laplacienne entre l'image originale
  et une copie downscalée puis remontée. Un ratio élevé trahit un faux agrandissement.
— **Taille absolue** : Jumia recommande 500px minimum, 800px idéal.

### Critère 6 — Cohérence image-texte (poids 10 %)
Utilisation du modèle **CLIP d'OpenAI (ViT-B/32)** pour mesurer la similarité cosinus
entre l'embedding image et l'embedding texte du prompt.
En l'absence de prompt, le score est neutre à 0,5 — aucune pénalité.

*[Inviter le jury à poser des questions sur les algorithmes si souhaité.]*
`,
  },
  {
    num: 6, title: "Résultats Clés", duration: "~1 min",
    script: `
En termes de **résultats concrets** :

### Score global et grades
Le score global est calculé par **moyenne pondérée** des six critères.
Les pondérations ont été choisies pour refléter l'impact perçu par l'acheteur :
la netteté et l'éclairage ont le poids le plus élevé — 20 % chacun — car ce sont
les premiers signaux visuels captés.

### Barème
— **Grade A** (≥ 0,85) : image professionnelle, prête à publier
— **Grade B** (≥ 0,70) : bonne qualité, légères améliorations possibles
— **Grade C** (≥ 0,55) : acceptable, mais des corrections sont recommandées
— **Grade D** (≥ 0,40) : qualité insuffisante, reprise nécessaire
— **Grade F** (< 0,40) : image rejetée

### Modèles IA intégrés
Cinq modèles d'intelligence artificielle fonctionnent ensemble : Grounding DINO,
BLIP, CLIP, EasyOCR, et GrabCut.
Tous fonctionnent en **mode CPU**, sans nécessité de GPU, ce qui facilite le déploiement
sur n'importe quelle machine.
`,
  },
  {
    num: 7, title: "Défis Techniques et Solutions", duration: "~2 min 30",
    script: `
Je vais vous détailler les **six défis techniques majeurs** rencontrés et leurs solutions.

### Défi 1 — Score de netteté constant (0,673)
**Problème :** Toutes les images du CDN Jumia ont la même table de quantification JPEG
à quality=75 — le critère était donc identique pour toutes.
**Solution :** Remplacement par la **variance du Laplacien en échelle log**, qui produit
29 valeurs distinctes sur 300 images et un score moyen de 0,525.

### Défi 2 — Ordre grammatical français incorrect
**Problème :** Le titre généré affichait "Portable Chargeur" au lieu de "Chargeur Portable"
car les mots-clés BLIP étaient insérés dans l'ordre de la légende anglaise.
**Solution :** Classification des mots-clés en deux ensembles — **_TYPES** (noms de produit)
et **_ATTRS** (adjectifs) — avec les noms toujours en premier.

### Défi 3 — Description en anglais brut
**Problème :** La légende BLIP ("the power bank is a portable charger...") était insérée
directement dans la description française.
**Solution :** Traduction via le dictionnaire **_EN_FR** et génération de phrases françaises
structurées ("Ce chargeur portable est idéal pour un usage quotidien.").

### Défi 4 — Watermark "fallback" visible
**Problème :** La fonction de visualisation appelait le détecteur sans le prompt
utilisateur, ce qui forçait toujours le mode fallback avec une étiquette visible.
**Solution :** Passage du text_prompt à visualize_detection() et suppression du label.

### Défi 5 — Analyse concurrentielle absente pour certaines images
**Problème :** La section retournait vide si la requête NLP était vide.
**Solution :** Chaîne de fallback à **trois niveaux** : NLP → session_state → champ manuel.

### Défi 6 — Scraper Jumia retournant zéro résultat
**Problème :** Le sélecteur CSS article[data-sku] était obsolète et le User-Agent
était détecté comme robot.
**Solution :** Sélecteur article.prd, gestion du lazy-loading img[data-src],
User-Agent Chrome réel.

*[Ces problèmes ont été diagnostiqués lors de tests réels sur l'application — montrer les
screenshots si disponibles.]*
`,
  },
  {
    num: 8, title: "État d'Avancement Global", duration: "~30 sec",
    script: `
L'état d'avancement global est de **100 %**.

Les quatre grandes catégories sont toutes complètes :

— **Infrastructure et interface :** pipeline bout-en-bout, gestion de session Streamlit,
  déploiement local testé sur port 8507.
— **Analyse qualité :** six critères implémentés et calibrés sur données réelles.
— **Intelligence artificielle :** cinq modèles intégrés avec dégradation gracieuse —
  si un modèle est indisponible hors ligne, le système continue à fonctionner.
— **Documentation :** README complet en français, DOCUMENTATION.md technique
  pour le jury, commentaires inline dans le code.

*[Cette slide peut être commentée rapidement — le jury voit que tout est vert.]*
`,
  },
  {
    num: 9, title: "Stack Technologique", duration: "~45 sec",
    script: `
La stack technologique s'articule autour de **quatre domaines.**

### Vision par ordinateur
OpenCV 4 pour les opérations morphologiques, GrabCut, la détection Canny et le filtre
Laplacien. Pillow pour le chargement et la conversion des images. NumPy pour les
opérations matricielles sur les masques.

### Modèles Transformers (HuggingFace)
Grounding DINO pour la détection zéro-shot guidée par texte, BLIP pour la génération
de légende, CLIP pour la cohérence sémantique. Tous chargés en lazy-loading.

### Traitement du texte et web
EasyOCR pour la reconnaissance bilingue français-anglais, les expressions régulières
Python pour l'extraction d'entités, BeautifulSoup4 pour le scraping HTML de Jumia.

### Interface et déploiement
Streamlit pour l'interface web interactive, Requests pour les appels HTTP.
Python 3.11 avec environnement virtuel isolé — déploiement en une commande.
`,
  },
  {
    num: 10, title: "Limites et Perspectives", duration: "~1 min 30",
    script: `
Abordons maintenant les **limites actuelles** et les **pistes d'amélioration.**

### Limites
— Les seuils du critère de netteté ont été calibrés sur des images **300×300 pixels**
  (format standard CDN Jumia). Pour des images haute résolution, il faudrait recalibrer.
— **EasyOCR est lent** en mode CPU — environ 3 secondes par image. PaddleOCR
  serait 5 fois plus rapide.
— Le scraping Jumia peut être bloqué par des mécanismes anti-bot. Une API officielle
  serait plus robuste pour une mise en production.
— Le modèle CLIP nécessite une connexion pour le premier téléchargement.
— La fiche produit est générée **en français uniquement** pour l'instant.
— Le score n'a pas été corrélé avec des données réelles de taux de clics.

### Perspectives
— **Recalibrer** sur des images haute résolution (800×800+)
— Remplacer EasyOCR par **PaddleOCR** (5× plus rapide)
— Intégrer l'**API officielle Jumia** via n8n pour une recherche fiable
— Ajouter le support du **darija** (arabe marocain) pour toucher un public plus large
— Corréler les scores avec les **taux de clics réels** pour valider empiriquement
— Déployer sur **cloud** (Streamlit Cloud ou Azure) pour un accès partagé

*[Ces perspectives montrent que le projet est extensible et pensé pour le long terme.]*
`,
  },
  {
    num: 11, title: "Conclusion", duration: "~45 sec",
    script: `
En **conclusion**, nous avons développé un système complet et fonctionnel qui répond à
un besoin concret du marché e-commerce marocain.

### Bilan
— **Six critères techniques** calibrés sur 300 images réelles Jumia
— **Pipeline IA** bout-en-bout : DINO · GrabCut · BLIP · CLIP · EasyOCR · NLP
— **Génération automatique** de fiches produit en français
— **Analyse concurrentielle** Jumia en temps réel
— **Interface Streamlit** accessible sans compétences techniques
— **Documentation complète** : README, DOCUMENTATION.md, commentaires inline

Ce système permet à n'importe quel vendeur sur Jumia ou Avito d'améliorer
objectivement la qualité de ses photos et d'augmenter ses chances de vente.

**Je vous remercie pour votre attention et reste disponible pour vos questions.**

*[Rester debout, sourire, maintenir le contact visuel avec les membres du jury.]*
`,
  },
];

// ════════════════════════════════════════════════════════════════════════════
// BUILD DOCUMENT
// ════════════════════════════════════════════════════════════════════════════

const children = [];

// ─── Cover ──────────────────────────────────────────────────────────────────
children.push(
  new Table({
    width: { size: CONT_W, type: WidthType.DXA },
    columnWidths: [CONT_W],
    rows: [new TableRow({
      children: [new TableCell({
        borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 320, bottom: 320, left: 360, right: 360 },
        width: { size: CONT_W, type: WidthType.DXA },
        children: [
          new Paragraph({
            alignment: AlignmentType.LEFT,
            children: [new TextRun({ text: "Script Oral — Soutenance", size: 36, bold: true, color: MINT, font: "Calibri" })],
            spacing: { after: 120 },
          }),
          new Paragraph({
            alignment: AlignmentType.LEFT,
            children: [new TextRun({ text: "Analyse de Qualité d’Images E-commerce", size: 30, color: WHITE, font: "Calibri" })],
            spacing: { after: 80 },
          }),
          new Paragraph({
            alignment: AlignmentType.LEFT,
            children: [new TextRun({ text: "Jumia Maroc  ·  Avito Maroc", size: 22, color: TEAL, italic: true, font: "Calibri" })],
            spacing: { after: 80 },
          }),
          new Paragraph({
            alignment: AlignmentType.LEFT,
            children: [new TextRun({ text: "Ahadj Idouae  —  Mai 2026", size: 20, color: "94A3B8", font: "Calibri" })],
          }),
        ],
      })],
    })],
  })
);

children.push(empty(200));

// ─── Notice box ─────────────────────────────────────────────────────────────
children.push(
  new Table({
    width: { size: CONT_W, type: WidthType.DXA },
    columnWidths: [Math.round(CONT_W * 0.06), Math.round(CONT_W * 0.94)],
    rows: [new TableRow({
      children: [
        new TableCell({
          borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
          shading: { fill: TEAL, type: ShadingType.CLEAR },
          width: { size: Math.round(CONT_W * 0.06), type: WidthType.DXA },
          children: [new Paragraph({ children: [] })],
        }),
        new TableCell({
          borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
          shading: { fill: LIGHT, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 200, right: 160 },
          width: { size: Math.round(CONT_W * 0.94), type: WidthType.DXA },
          children: [
            new Paragraph({
              children: [new TextRun({ text: "Comment utiliser ce document", size: 22, bold: true, color: NAVY, font: "Calibri" })],
              spacing: { after: 80 },
            }),
            new Paragraph({
              numbering: { reference: "bullets", level: 0 },
              children: [new TextRun({ text: "Durée totale estimée : 12–15 minutes de présentation", size: 20, color: "334155", font: "Calibri" })],
              spacing: { after: 40 },
            }),
            new Paragraph({
              numbering: { reference: "bullets", level: 0 },
              children: [new TextRun({ text: "Les indicateurs ⏱ donnent le temps cible par slide", size: 20, color: "334155", font: "Calibri" })],
              spacing: { after: 40 },
            }),
            new Paragraph({
              numbering: { reference: "bullets", level: 0 },
              children: [new TextRun({ text: "Les notes en italique entre [ ] sont des indications de mise en scène", size: 20, color: "334155", font: "Calibri" })],
              spacing: { after: 40 },
            }),
            new Paragraph({
              numbering: { reference: "bullets", level: 0 },
              children: [new TextRun({ text: "Les mots en gras sont les termes clés à prononcer clairement", size: 20, color: "334155", font: "Calibri" })],
              spacing: { after: 40 },
            }),
            new Paragraph({
              numbering: { reference: "bullets", level: 0 },
              children: [new TextRun({ text: "Les notes orateur sont également intégrées dans le .pptx (mode présentateur)", size: 20, color: "334155", font: "Calibri" })],
            }),
          ],
        }),
      ],
    })],
  })
);

children.push(empty(240));
children.push(hrLine());
children.push(empty(160));

// ─── Slides ─────────────────────────────────────────────────────────────────
for (const slide of slides) {
  const blocks = slideBlock(slide.num, slide.title, slide.duration, slide.script);
  children.push(...blocks);
}

// ─── Tips box ───────────────────────────────────────────────────────────────
children.push(
  new Table({
    width: { size: CONT_W, type: WidthType.DXA },
    columnWidths: [Math.round(CONT_W * 0.06), Math.round(CONT_W * 0.94)],
    rows: [new TableRow({
      children: [
        new TableCell({
          borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
          shading: { fill: MINT, type: ShadingType.CLEAR },
          width: { size: Math.round(CONT_W * 0.06), type: WidthType.DXA },
          children: [new Paragraph({ children: [] })],
        }),
        new TableCell({
          borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
          shading: { fill: "EBF7F4", type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 200, right: 160 },
          width: { size: Math.round(CONT_W * 0.94), type: WidthType.DXA },
          children: [
            new Paragraph({
              children: [new TextRun({ text: "Conseils pour la soutenance", size: 22, bold: true, color: "007A5E", font: "Calibri" })],
              spacing: { after: 80 },
            }),
            ...[
              "Parlez lentement et articulez — le jury note en même temps qu'il écoute.",
              "Ne lisez pas le script mot pour mot — utilisez-le comme guide, gardez le contact visuel.",
              "Anticipez les questions sur les choix d'algorithmes (Laplacien, log-scale, pondérations).",
              "Si une question porte sur la précision : mentionnez la calibration sur 300 images réelles.",
              "Si on vous demande pourquoi BLIP et pas GPT-4 Vision : coût zéro, fonctionnement hors ligne.",
              "Montrez la démo live si possible — un exemple réel vaut mieux qu'une slide.",
            ].map(tip => new Paragraph({
              numbering: { reference: "tips", level: 0 },
              children: [new TextRun({ text: tip, size: 20, color: "334155", font: "Calibri" })],
              spacing: { after: 40 },
            })),
          ],
        }),
      ],
    })],
  })
);

// ════════════════════════════════════════════════════════════════════════════
// DOCUMENT
// ════════════════════════════════════════════════════════════════════════════

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "–",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 560, hanging: 280 } },
                   run: { font: "Calibri", size: 22, color: "0E8C9B" } },
        }],
      },
      {
        reference: "subbullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "·",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 900, hanging: 280 } },
                   run: { font: "Calibri", size: 20, color: "94A3B8" } },
        }],
      },
      {
        reference: "tips",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "✔",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 560, hanging: 280 } },
                   run: { font: "Calibri", size: 20, color: "00B98A" } },
        }],
      },
    ],
  },
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22, color: "1A252F" } },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: 16838 },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "Script Oral — Soutenance", size: 18, color: TEAL, font: "Calibri", bold: true }),
            new TextRun({ text: "\tAhadj Idouae  ·  Mai 2026", size: 18, color: "94A3B8", font: "Calibri" }),
          ],
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: TEAL, space: 1 } },
          spacing: { after: 120 },
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "Analyse Qualité Images E-commerce", size: 16, color: "94A3B8", font: "Calibri" }),
            new TextRun({ text: "\tPage ", size: 16, color: "94A3B8", font: "Calibri" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: TEAL, font: "Calibri" }),
          ],
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          border: { top: { style: BorderStyle.SINGLE, size: 3, color: TEAL, space: 1 } },
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("script_oral.docx", buf);
  console.log("✅  script_oral.docx créé avec succès");
}).catch(err => {
  console.error("❌  Erreur:", err);
  process.exit(1);
});
