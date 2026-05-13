const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Ahadj Idouae";
pres.title = "État d'Avancement — Analyse Qualité Images E-commerce";

// ─── Palette ────────────────────────────────────────────────────────────────
const C = {
  navy:    "0D2137",
  blue:    "1060A0",
  teal:    "0E8C9B",
  mint:    "00B98A",
  light:   "F0F5FA",
  white:   "FFFFFF",
  offwhite:"F7F9FC",
  gray:    "94A3B8",
  dark:    "1A252F",
  card:    "FFFFFF",
  border:  "E2E8F0",
  warn:    "F59E0B",
};

// Helpers
const makeShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.10 });

function card(slide, x, y, w, h, accentColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: C.card },
    line: { color: C.border, width: 0.5 },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h,
    fill: { color: accentColor },
    line: { color: accentColor, width: 0 },
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 1 — TITRE
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Top teal bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });

  // Left accent strip
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.2, w: 0.07, h: 2.5, fill: { color: C.teal }, line: { color: C.teal, width: 0 } });

  // Main title
  s.addText("Analyse de Qualité\nd'Images E-commerce", {
    x: 0.85, y: 1.15, w: 7.5, h: 2.6,
    fontSize: 40, bold: true, color: C.white,
    fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Subtitle
  s.addText("État d'Avancement du Projet", {
    x: 0.85, y: 3.65, w: 7.5, h: 0.55,
    fontSize: 18, color: C.mint, fontFace: "Calibri", italic: true, margin: 0,
  });

  // Divider
  s.addShape(pres.shapes.LINE, { x: 0.85, y: 4.22, w: 6, h: 0, line: { color: C.teal, width: 1 } });

  // Meta info
  s.addText("Jumia Maroc  ·  Avito Maroc  ·  Intelligence Artificielle  ·  Vision par Ordinateur", {
    x: 0.85, y: 4.35, w: 8, h: 0.4, fontSize: 11, color: C.gray, fontFace: "Calibri", margin: 0,
  });

  // Author & date bottom-right
  s.addText("Ahadj Idouae  |  Mai 2026", {
    x: 6.5, y: 5.1, w: 3.3, h: 0.35,
    fontSize: 10, color: C.gray, align: "right", fontFace: "Calibri", margin: 0,
  });

  // Decorative circles (top-right)
  s.addShape(pres.shapes.OVAL, { x: 8.2, y: -0.4, w: 2.8, h: 2.8, fill: { color: C.teal, transparency: 85 }, line: { color: C.teal, width: 0 } });
  s.addShape(pres.shapes.OVAL, { x: 8.8, y: 0.2, w: 1.8, h: 1.8, fill: { color: C.mint, transparency: 75 }, line: { color: C.mint, width: 0 } });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 2 — CONTEXTE ET OBJECTIFS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  // Header band
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("Contexte et Objectifs", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  // --- LEFT CARD: Problématique ---
  card(s, 0.35, 1.3, 4.45, 3.9, C.blue);

  s.addText("Problématique", {
    x: 0.6, y: 1.38, w: 4, h: 0.45, fontSize: 16, bold: true, color: C.blue, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Les vendeurs sur Jumia/Avito Maroc publient des milliers d'annonces quotidiennement.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "❌  Images floues ou mal éclairées", options: { breakLine: true } },
    { text: "❌  Produit mal cadré ou fond encombré", options: { breakLine: true } },
    { text: "❌  Fiches produit incomplètes ou en anglais", options: { breakLine: true } },
    { text: "❌  Aucun outil d'aide disponible pour les PME", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Une mauvaise image réduit significativement le taux de conversion.", options: { italic: true } },
  ], {
    x: 0.55, y: 1.88, w: 4.1, h: 3.1,
    fontSize: 12.5, color: C.dark, fontFace: "Calibri", valign: "top", margin: 0,
  });

  // --- RIGHT CARD: Objectifs ---
  card(s, 5.2, 1.3, 4.45, 3.9, C.mint);

  s.addText("Notre Solution", {
    x: 5.45, y: 1.38, w: 4, h: 0.45, fontSize: 16, bold: true, color: C.teal, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Un système automatique qui :", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "✅  Évalue la qualité de l'image (score + grade)", options: { breakLine: true } },
    { text: "✅  Analyse 6 critères techniques objectifs", options: { breakLine: true } },
    { text: "✅  Génère une fiche produit en français", options: { breakLine: true } },
    { text: "✅  Compare avec les concurrents Jumia", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Cible : Jumia Maroc · Avito Maroc", options: { italic: true } },
  ], {
    x: 5.45, y: 1.88, w: 4.1, h: 3.1,
    fontSize: 12.5, color: C.dark, fontFace: "Calibri", valign: "top", margin: 0,
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 3 — ARCHITECTURE DU SYSTÈME
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("Architecture du Système", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  // Pipeline boxes
  const steps = [
    { label: "Image\nProduit",      color: C.navy,  sub: "Upload JPEG/PNG" },
    { label: "OCR\nEasyOCR",        color: C.blue,  sub: "Texte visible" },
    { label: "NLP\nEntités",        color: C.teal,  sub: "Marque, prix..." },
    { label: "DETECTOR\nDINO",      color: C.teal,  sub: "Masque produit" },
    { label: "ANALYZER\n6 critères",color: C.blue,  sub: "Score + Grade" },
    { label: "CAPTION\nBLIP",       color: C.mint,  sub: "Fiche produit FR" },
    { label: "SEARCH\nJumia",       color: C.mint,  sub: "Concurrents" },
  ];

  const bw = 1.08, bh = 1.0, by = 1.55, startX = 0.2;
  const gap = 0.12;

  steps.forEach((step, i) => {
    const bx = startX + i * (bw + gap);
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx, y: by, w: bw, h: bh,
      fill: { color: step.color },
      line: { color: step.color, width: 0 },
      shadow: makeShadow(),
    });
    s.addText(step.label, {
      x: bx, y: by + 0.08, w: bw, h: 0.7,
      fontSize: 9.5, bold: true, color: C.white, align: "center", fontFace: "Calibri",
      valign: "middle", margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx, y: by + bh - 0.28, w: bw, h: 0.28,
      fill: { color: "000000", transparency: 30 },
      line: { color: "000000", transparency: 30, width: 0 },
    });
    s.addText(step.sub, {
      x: bx, y: by + bh - 0.28, w: bw, h: 0.28,
      fontSize: 8, color: C.white, align: "center", fontFace: "Calibri", margin: 0,
    });

    // Arrow between boxes
    if (i < steps.length - 1) {
      const ax = bx + bw;
      s.addShape(pres.shapes.LINE, {
        x: ax, y: by + bh / 2, w: gap, h: 0,
        line: { color: C.gray, width: 1.5 },
      });
      s.addText("▶", { x: ax + gap - 0.12, y: by + bh / 2 - 0.12, w: 0.15, h: 0.24, fontSize: 8, color: C.gray, margin: 0 });
    }
  });

  // Subtitle describing flow
  s.addText("Pipeline de traitement : de l'image brute à la fiche produit publiable", {
    x: 0.4, y: 2.72, w: 9.2, h: 0.3,
    fontSize: 11, color: C.gray, italic: true, align: "center", fontFace: "Calibri", margin: 0,
  });

  // Bottom: main components description
  const comps = [
    { t: "Interface\nStreamlit (app.py)", c: C.navy },
    { t: "src/scorer.py\nFaçade de scoring", c: C.blue },
    { t: "src/visualizer.py\nAnnotation image", c: C.teal },
    { t: "src/__init__.py\nAPI publique", c: C.mint },
  ];
  comps.forEach((comp, i) => {
    const cx = 0.5 + i * 2.3;
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 3.2, w: 2.1, h: 0.65, fill: { color: comp.c, transparency: 10 }, line: { color: comp.c, width: 0 } });
    s.addText(comp.t, { x: cx, y: 3.2, w: 2.1, h: 0.65, fontSize: 9, bold: false, color: C.white, align: "center", fontFace: "Calibri", valign: "middle", margin: 0 });
  });

  s.addText("Modules support", { x: 0.4, y: 3.1, w: 3, h: 0.25, fontSize: 9.5, color: C.gray, fontFace: "Calibri", margin: 0 });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 4 — MODULES DÉVELOPPÉS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("Modules Développés", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  const modules = [
    { file: "src/detector.py",   role: "Détection produit (DINO + GrabCut + Otsu)",        tech: "Transformers · OpenCV",     status: "✅ TERMINÉ" },
    { file: "src/analyzer.py",   role: "Analyse 6 critères qualité (score pondéré)",         tech: "NumPy · OpenCV · CLIP",     status: "✅ TERMINÉ" },
    { file: "src/ocr.py",        role: "Extraction texte visible (marque, prix...)",          tech: "EasyOCR",                   status: "✅ TERMINÉ" },
    { file: "src/nlp.py",        role: "Extraction d'entités produit (regex + dictionnaire)", tech: "Python re",                 status: "✅ TERMINÉ" },
    { file: "src/caption.py",    role: "Génération fiche produit en français (BLIP)",         tech: "Transformers · PIL",        status: "✅ TERMINÉ" },
    { file: "src/n8n_search.py", role: "Recherche concurrents Jumia (scraping)",             tech: "Requests · BeautifulSoup",  status: "✅ TERMINÉ" },
    { file: "src/scorer.py",     role: "Façade score global + grade A–F",                    tech: "Python",                    status: "✅ TERMINÉ" },
    { file: "src/visualizer.py", role: "Annotation image avec overlay critères",             tech: "OpenCV · Pillow",           status: "✅ TERMINÉ" },
    { file: "app.py",            role: "Interface Streamlit — upload, analyse, fiche, search","tech": "Streamlit",               status: "✅ TERMINÉ" },
  ];

  const rowH = 0.44, startY = 1.22;
  const colW = [2.5, 3.8, 2.2, 1.2];
  const colX = [0.15, 2.7, 6.55, 8.8];

  // Header row
  const headers = ["Fichier", "Rôle", "Technologie", "Statut"];
  headers.forEach((h, i) => {
    s.addShape(pres.shapes.RECTANGLE, { x: colX[i], y: startY, w: colW[i], h: 0.36, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
    s.addText(h, { x: colX[i] + 0.05, y: startY, w: colW[i], h: 0.36, fontSize: 10.5, bold: true, color: C.white, valign: "middle", fontFace: "Calibri", margin: 0 });
  });

  modules.forEach((mod, ri) => {
    const ry = startY + 0.36 + ri * rowH;
    const bg = ri % 2 === 0 ? C.white : C.light;
    // Row bg
    s.addShape(pres.shapes.RECTANGLE, { x: 0.15, y: ry, w: 9.7, h: rowH, fill: { color: bg }, line: { color: C.border, width: 0.3 } });
    const rows = [mod.file, mod.role, mod.tech, mod.status];
    const colors = [C.blue, C.dark, C.gray, mod.status.startsWith("✅") ? "1A7A45" : C.warn];
    const bolds = [true, false, false, true];
    rows.forEach((txt, ci) => {
      s.addText(txt, {
        x: colX[ci] + 0.08, y: ry, w: colW[ci] - 0.1, h: rowH,
        fontSize: 9.5, color: colors[ci], bold: bolds[ci], valign: "middle", fontFace: "Calibri", margin: 0,
      });
    });
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 5 — LES 6 CRITÈRES D'ANALYSE
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("Les 6 Critères d'Analyse Qualité", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  const criteria = [
    { name: "Netteté / JPEG",          poids: "20%", algo: "Variance du Laplacien (log-scale)\nSeuils calibrés sur 300 images Jumia\nlog10(var): [200 → 3000]",          color: C.blue },
    { name: "Uniformité d'éclairage",  poids: "20%", algo: "Grille 3×3 sur bbox produit\nÉcart-type des luminosités moyennes\nstd < 15 → parfait, std > 60 → mauvais",  color: C.blue },
    { name: "Qualité des bords",        poids: "20%", algo: "Canny sur masque boundary\nDensité de bords dans la zone frontière\nSeuils adaptatifs selon résolution",     color: C.teal },
    { name: "Cohérence couleur",        poids: "15%", algo: "Hypothèse grey-world\nÉcart-type des canaux R,G,B\n+ plage de saturation HSV [50–150]",                      color: C.teal },
    { name: "Résolution effective",     poids: "15%", algo: "Détection d'upscaling (ratio Laplacien)\n+ taille absolue min(H,W)\nJumia : 500px min, 800px idéal",         color: C.mint },
    { name: "Cohérence image-texte",    poids: "10%", algo: "CLIP (ViT-B/32)\nSimilarité cosinus image ↔ texte\nsigmoid(logit) → [0,1]",                                 color: C.mint },
  ];

  const cw = 3.0, ch = 1.75, startX = 0.35;
  criteria.forEach((cr, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const cx = startX + col * (cw + 0.25);
    const cy = 1.3 + row * (ch + 0.2);

    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: cw, h: ch, fill: { color: C.card }, line: { color: C.border, width: 0.5 }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: cw, h: 0.06, fill: { color: cr.color }, line: { color: cr.color, width: 0 } });

    // Badge poids
    s.addShape(pres.shapes.RECTANGLE, { x: cx + cw - 0.62, y: cy + 0.1, w: 0.55, h: 0.3, fill: { color: cr.color }, line: { color: cr.color, width: 0 } });
    s.addText(cr.poids, { x: cx + cw - 0.62, y: cy + 0.1, w: 0.55, h: 0.3, fontSize: 9, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });

    s.addText(cr.name, { x: cx + 0.1, y: cy + 0.12, w: cw - 0.75, h: 0.4, fontSize: 11, bold: true, color: C.dark, fontFace: "Calibri", margin: 0 });
    s.addText(cr.algo, { x: cx + 0.1, y: cy + 0.55, w: cw - 0.2, h: 1.1, fontSize: 9.5, color: C.gray, fontFace: "Calibri", valign: "top", margin: 0 });
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 6 — RÉSULTATS ET PERFORMANCES
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("Résultats Clés", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  // Big stat cards
  const stats = [
    { val: "6",     label: "Critères\nd'analyse",         color: C.blue },
    { val: "300",   label: "Images\ncalibrées",            color: C.teal },
    { val: "A–F",   label: "Grades de\nqualité",           color: C.mint },
    { val: "3",     label: "Modes de\ndétection",          color: C.blue },
  ];

  stats.forEach((st, i) => {
    const sx = 0.4 + i * 2.3;
    s.addShape(pres.shapes.RECTANGLE, { x: sx, y: 1.25, w: 2.1, h: 1.4, fill: { color: st.color }, line: { color: st.color, width: 0 }, shadow: makeShadow() });
    s.addText(st.val, { x: sx, y: 1.32, w: 2.1, h: 0.7, fontSize: 38, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(st.label, { x: sx, y: 2.0, w: 2.1, h: 0.55, fontSize: 10, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
  });

  // Scoring example
  card(s, 0.35, 2.9, 4.5, 2.45, C.blue);
  s.addText("Barème des Grades", { x: 0.6, y: 3.0, w: 4, h: 0.38, fontSize: 13, bold: true, color: C.blue, fontFace: "Calibri", margin: 0 });

  const grades = [
    { g: "A", range: "≥ 0.85", label: "Image professionnelle", bar: 95, color: "22C55E" },
    { g: "B", range: "≥ 0.70", label: "Bonne qualité",          bar: 75, color: "84CC16" },
    { g: "C", range: "≥ 0.55", label: "Acceptable",             bar: 60, color: "EAB308" },
    { g: "D", range: "≥ 0.40", label: "Insuffisant",            bar: 45, color: "F97316" },
    { g: "F", range: "< 0.40", label: "Rejetée",                bar: 20, color: "EF4444" },
  ];

  grades.forEach((g, i) => {
    const gy = 3.42 + i * 0.37;
    // Grade badge
    s.addShape(pres.shapes.RECTANGLE, { x: 0.55, y: gy, w: 0.28, h: 0.28, fill: { color: g.color }, line: { color: g.color, width: 0 } });
    s.addText(g.g, { x: 0.55, y: gy, w: 0.28, h: 0.28, fontSize: 11, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
    // Range
    s.addText(g.range, { x: 0.9, y: gy + 0.02, w: 0.65, h: 0.25, fontSize: 9.5, color: C.gray, fontFace: "Calibri", margin: 0 });
    // Progress bar bg
    s.addShape(pres.shapes.RECTANGLE, { x: 1.65, y: gy + 0.06, w: 2.8, h: 0.15, fill: { color: C.border }, line: { color: C.border, width: 0 } });
    // Progress bar fill
    s.addShape(pres.shapes.RECTANGLE, { x: 1.65, y: gy + 0.06, w: 2.8 * g.bar / 100, h: 0.15, fill: { color: g.color }, line: { color: g.color, width: 0 } });
    // Label
    s.addText(g.label, { x: 4.0, y: gy + 0.02, w: 0.8, h: 0.25, fontSize: 9, color: C.dark, fontFace: "Calibri", margin: 0 });
  });

  // CLIP + BLIP info right card
  card(s, 5.15, 2.9, 4.5, 2.45, C.teal);
  s.addText("Modèles IA Intégrés", { x: 5.4, y: 3.0, w: 4, h: 0.38, fontSize: 13, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });

  const models = [
    { name: "Grounding DINO Tiny", role: "Détection zéro-shot (texte → bbox)", status: "✅" },
    { name: "BLIP Base (Salesforce)", role: "Légende image → fiche produit FR", status: "✅" },
    { name: "CLIP ViT-B/32 (OpenAI)", role: "Cohérence image–texte (cosinus)", status: "✅" },
    { name: "EasyOCR (fr + en)", role: "Lecture texte visible sur image", status: "✅" },
    { name: "GrabCut (OpenCV)", role: "Segmentation masque pixel-précis", status: "✅" },
  ];

  models.forEach((m, i) => {
    const my = 3.42 + i * 0.37;
    s.addText(m.status, { x: 5.4, y: my + 0.02, w: 0.3, h: 0.25, fontSize: 11, color: "22C55E", fontFace: "Calibri", margin: 0 });
    s.addText(m.name, { x: 5.75, y: my + 0.02, w: 2.0, h: 0.25, fontSize: 9.5, bold: true, color: C.dark, fontFace: "Calibri", margin: 0 });
    s.addText(m.role, { x: 5.75, y: my + 0.19, w: 3.8, h: 0.2, fontSize: 8.5, color: C.gray, fontFace: "Calibri", margin: 0 });
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 7 — DÉFIS TECHNIQUES & SOLUTIONS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("Défis Techniques & Solutions", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  const issues = [
    {
      prob: "Score jpeg_artifacts constant (0.673) sur 300 images",
      cause: "Table de quantification JPEG identique (quality=75 CDN Jumia)",
      fix: "Remplacement par variance du Laplacien en échelle log → 29 valeurs uniques",
    },
    {
      prob: "Titre en mauvais ordre français (\"Portable Chargeur\")",
      cause: "Mots-clés BLIP non classés : adjectifs avant noms",
      fix: "Classificateurs _TYPES (noms) et _ATTRS (adj.) → types d'abord, attributs ensuite",
    },
    {
      prob: "Description en anglais brut (\"the power bank is a portable charger...\")",
      cause: "Légende BLIP insérée directement dans la description",
      fix: "Traduction via dictionnaire _EN_FR + génération de phrases françaises structurées",
    },
    {
      prob: "Watermark \"fallback\" visible sur l'image de détection",
      cause: "visualize_detection() appelait detect_product() sans text_prompt",
      fix: "Passage du text_prompt à visualize_detection() + suppression du label fallback",
    },
    {
      prob: "Analyse concurrentielle absente pour les images sans texte",
      cause: "Section retournait vide si search_query NLP était vide",
      fix: "Fallback 3 niveaux : NLP → session_state[_text_prompt] → champ manuel",
    },
    {
      prob: "Scraper Jumia retournait 0 résultats",
      cause: "Sélecteur CSS obsolète article[data-sku] + User-Agent détecté",
      fix: "Sélecteur article.prd, balise img[data-src] lazy, User-Agent Chrome réel",
    },
  ];

  issues.forEach((issue, i) => {
    const iy = 1.2 + i * 0.7;
    // Background alternating
    const bg = i % 2 === 0 ? C.white : C.light;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.2, y: iy, w: 9.6, h: 0.65, fill: { color: bg }, line: { color: C.border, width: 0.3 } });
    // Left: problem pill
    s.addShape(pres.shapes.RECTANGLE, { x: 0.2, y: iy, w: 0.06, h: 0.65, fill: { color: "EF4444" }, line: { color: "EF4444", width: 0 } });
    s.addText("❌ " + issue.prob, { x: 0.35, y: iy + 0.04, w: 3.5, h: 0.28, fontSize: 9, bold: true, color: C.dark, fontFace: "Calibri", margin: 0 });
    s.addText("Cause : " + issue.cause, { x: 0.35, y: iy + 0.32, w: 3.5, h: 0.28, fontSize: 8.5, color: C.gray, fontFace: "Calibri", margin: 0 });
    // Arrow
    s.addText("→", { x: 3.88, y: iy + 0.18, w: 0.3, h: 0.28, fontSize: 16, color: C.teal, align: "center", fontFace: "Calibri", margin: 0 });
    // Right: fix
    s.addShape(pres.shapes.RECTANGLE, { x: 4.15, y: iy + 0.12, w: 0.06, h: 0.42, fill: { color: "22C55E" }, line: { color: "22C55E", width: 0 } });
    s.addText("✅ " + issue.fix, { x: 4.3, y: iy + 0.12, w: 5.4, h: 0.42, fontSize: 9, color: C.dark, fontFace: "Calibri", valign: "middle", margin: 0 });
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 8 — ÉTAT D'AVANCEMENT
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("État d'Avancement Global", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  // Global progress bar
  s.addText("Avancement global du projet", { x: 0.4, y: 1.22, w: 5, h: 0.3, fontSize: 12, bold: true, color: C.dark, fontFace: "Calibri", margin: 0 });
  s.addText("100%", { x: 9.0, y: 1.22, w: 0.8, h: 0.3, fontSize: 13, bold: true, color: "22C55E", align: "right", fontFace: "Calibri", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 1.55, w: 9.2, h: 0.28, fill: { color: C.border }, line: { color: C.border, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 1.55, w: 9.2, h: 0.28, fill: { color: "22C55E" }, line: { color: "22C55E", width: 0 } });
  s.addText("✅ Toutes les fonctionnalités développées et testées", {
    x: 0.4, y: 1.87, w: 9, h: 0.28, fontSize: 10, color: "22C55E", italic: true, fontFace: "Calibri", margin: 0,
  });

  // Checklist categories
  const cats = [
    {
      title: "Infrastructure & Interface", color: C.navy,
      items: ["Interface Streamlit (upload, analyse, fiche, comparatif)", "Gestion état session (session_state)", "Pipeline complet bout-en-bout", "Déploiement local testé"],
      done: [true, true, true, true],
    },
    {
      title: "Analyse Qualité", color: C.blue,
      items: ["6 critères techniques implémentés", "Calibration sur 300 images Jumia", "Score global pondéré + grade A-F", "Visualisation détection (overlay)"],
      done: [true, true, true, true],
    },
    {
      title: "IA & NLP", color: C.teal,
      items: ["Grounding DINO + GrabCut + Otsu", "BLIP captioning → fiche FR", "CLIP cohérence image-texte", "EasyOCR + extracteur entités NLP"],
      done: [true, true, true, true],
    },
    {
      title: "Documentation", color: C.mint,
      items: ["README.md complet (FR)", "DOCUMENTATION.md technique", "Commentaires inline dans le code", "Guide jury technique"],
      done: [true, true, true, true],
    },
  ];

  cats.forEach((cat, ci) => {
    const cx = 0.2 + ci * 2.42;
    const cy = 2.3;
    const cw = 2.28, ch = 2.85;

    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: cw, h: ch, fill: { color: C.card }, line: { color: C.border, width: 0.5 }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: cw, h: 0.42, fill: { color: cat.color }, line: { color: cat.color, width: 0 } });
    s.addText(cat.title, { x: cx + 0.08, y: cy + 0.02, w: cw - 0.1, h: 0.38, fontSize: 9.5, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

    cat.items.forEach((item, ii) => {
      const iy = cy + 0.5 + ii * 0.55;
      const statusColor = cat.done[ii] ? "22C55E" : C.warn;
      const statusIcon  = cat.done[ii] ? "✅" : "⏳";
      s.addText(statusIcon, { x: cx + 0.1, y: iy, w: 0.3, h: 0.4, fontSize: 11, color: statusColor, fontFace: "Calibri", margin: 0 });
      s.addText(item, { x: cx + 0.42, y: iy + 0.05, w: cw - 0.52, h: 0.38, fontSize: 8.5, color: C.dark, fontFace: "Calibri", valign: "top", margin: 0 });
    });
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 9 — TECHNOLOGIES UTILISÉES
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("Stack Technologique", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  const stacks = [
    {
      cat: "Vision par Ordinateur", color: C.blue,
      items: ["OpenCV 4 — morphologie, GrabCut, Canny, Laplacien", "Pillow (PIL) — chargement, conversion formats", "NumPy — opérations matricielles sur masques"],
    },
    {
      cat: "Modèles Transformers", color: C.teal,
      items: ["Grounding DINO Tiny — IDEA-Research/HuggingFace", "BLIP Base — Salesforce/blip-image-captioning-base", "CLIP ViT-B/32 — openai/clip-vit-base-patch32"],
    },
    {
      cat: "Traitement Texte & OCR", color: C.mint,
      items: ["EasyOCR — Reconnaissance FR + EN (CPU mode)", "Regex Python — Extraction entités (prix, marque...)", "BeautifulSoup4 — Scraping HTML Jumia Maroc"],
    },
    {
      cat: "Interface & Déploiement", color: C.navy,
      items: ["Streamlit — Interface web interactive (sidebar, session)", "Requests — HTTP (scraping Jumia + download images)", "Python 3.11 + venv — Environnement isolé"],
    },
  ];

  stacks.forEach((st, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const sx = 0.3 + col * 4.85;
    const sy = 1.25 + row * 2.1;
    const sw = 4.55, sh = 1.95;

    s.addShape(pres.shapes.RECTANGLE, { x: sx, y: sy, w: sw, h: sh, fill: { color: C.card }, line: { color: C.border, width: 0.5 }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: sx, y: sy, w: sw, h: 0.42, fill: { color: st.color }, line: { color: st.color, width: 0 } });
    s.addText(st.cat, { x: sx + 0.1, y: sy + 0.02, w: sw - 0.15, h: 0.38, fontSize: 12, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

    st.items.forEach((item, ii) => {
      s.addText("▸  " + item, {
        x: sx + 0.18, y: sy + 0.5 + ii * 0.46, w: sw - 0.3, h: 0.4,
        fontSize: 10.5, color: C.dark, fontFace: "Calibri", margin: 0,
      });
    });
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 10 — PERSPECTIVES ET AMÉLIORATIONS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 1.05, w: 10, h: 0.06, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addText("Limites & Perspectives", { x: 0.4, y: 0, w: 9, h: 1.05, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  // Left: Limitations
  card(s, 0.3, 1.25, 4.5, 3.95, "EF4444");
  s.addText("Limites actuelles", { x: 0.55, y: 1.33, w: 4, h: 0.4, fontSize: 14, bold: true, color: "EF4444", fontFace: "Calibri", margin: 0 });

  const limits = [
    "Images 300×300 px CDN → seuils calibrés petite résolution",
    "EasyOCR lent en CPU (~3s / image)",
    "Scraping Jumia peut être bloqué (anti-bot)",
    "CLIP indisponible hors connexion (modèle cloud)",
    "Fiche produit en français uniquement",
    "Score non validé par A/B test e-commerce réel",
  ];
  limits.forEach((l, i) => {
    s.addText("⚠ " + l, { x: 0.55, y: 1.82 + i * 0.53, w: 4.1, h: 0.42, fontSize: 10.5, color: C.dark, fontFace: "Calibri", margin: 0 });
  });

  // Right: Perspectives
  card(s, 5.2, 1.25, 4.5, 3.95, "22C55E");
  s.addText("Pistes d'amélioration", { x: 5.45, y: 1.33, w: 4, h: 0.4, fontSize: 14, bold: true, color: "22C55E", fontFace: "Calibri", margin: 0 });

  const persp = [
    "Recalibrer sur images haute résolution (800×800+)",
    "Remplacer EasyOCR par PaddleOCR (5x plus rapide)",
    "Intégrer API officielle Jumia via n8n",
    "Ajouter cache CLIP local (offline)",
    "Fiches en darija / arabe marocain",
    "Corrélation score ↔ taux de clics réels",
  ];
  persp.forEach((p, i) => {
    s.addText("✦ " + p, { x: 5.45, y: 1.82 + i * 0.53, w: 4.1, h: 0.42, fontSize: 10.5, color: C.dark, fontFace: "Calibri", margin: 0 });
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 11 — CONCLUSION (dark)
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.54, w: 10, h: 0.08, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });

  // Title
  s.addText("Conclusion", { x: 0.5, y: 0.5, w: 9, h: 0.6, fontSize: 30, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 0.5, y: 1.1, w: 4, h: 0, line: { color: C.mint, width: 2 } });

  // Summary bullets
  const summary = [
    "Système complet d'analyse qualité d'images e-commerce développé et testé",
    "6 critères techniques calibrés sur données réelles Jumia Maroc",
    "Pipeline IA : DINO · GrabCut · BLIP · CLIP · EasyOCR · NLP",
    "Génération automatique de fiches produit en français",
    "Analyse concurrentielle Jumia en temps réel",
    "Interface Streamlit opérationnelle et documentée",
  ];

  summary.forEach((line, i) => {
    const ly = 1.25 + i * 0.58;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: ly + 0.1, w: 0.06, h: 0.28, fill: { color: C.mint }, line: { color: C.mint, width: 0 } });
    s.addText(line, { x: 0.72, y: ly + 0.05, w: 8.5, h: 0.42, fontSize: 12.5, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });
  });

  // Bottom tag
  s.addText("Merci pour votre attention", {
    x: 0, y: 4.9, w: 10, h: 0.55,
    fontSize: 16, bold: true, color: C.mint, align: "center", fontFace: "Calibri", margin: 0,
  });

  // Decorative circles
  s.addShape(pres.shapes.OVAL, { x: 7.8, y: 1.0, w: 3.2, h: 3.2, fill: { color: C.teal, transparency: 88 }, line: { color: C.teal, width: 0 } });
  s.addShape(pres.shapes.OVAL, { x: 8.5, y: 2.0, w: 1.8, h: 1.8, fill: { color: C.mint, transparency: 80 }, line: { color: C.mint, width: 0 } });
}

// ════════════════════════════════════════════════════════════════════════════
// NOTES ORATEUR (visibles en mode présentateur PowerPoint)
// ════════════════════════════════════════════════════════════════════════════

const notes = [

  // Slide 1 — Titre
  `Bonjour à tous. Je m'appelle Ahadj Idouae, et je vais vous présenter mon projet intitulé « Analyse automatique de la qualité d'images produits pour l'e-commerce marocain ».

Ce projet a été développé dans le contexte du marché e-commerce au Maroc, en ciblant principalement les plateformes Jumia et Avito.

La présentation durera environ 15 minutes, suivies de vos questions.`,

  // Slide 2 — Contexte et Objectifs
  `Commençons par la problématique.

Le marché e-commerce au Maroc est en pleine croissance, mais de nombreux vendeurs — notamment les petites entreprises et les particuliers — publient des annonces avec des photos de mauvaise qualité : floues, mal éclairées, mal cadrées, ou avec un fond encombré.

Ces images réduisent directement le taux de conversion. Un client qui ne voit pas clairement le produit n'achète pas.

Notre réponse est un système automatique à trois dimensions :
  1. Évaluer objectivement la qualité de l'image via six critères techniques,
  2. Générer automatiquement une fiche produit complète en français,
  3. Comparer le produit avec les offres concurrentes déjà présentes sur Jumia.`,

  // Slide 3 — Architecture
  `Voici l'architecture complète du système.

Le pipeline comporte sept étapes enchaînées :

Étape 1 — L'utilisateur uploade une image JPEG ou PNG.
Étape 2 — Le module OCR (EasyOCR) lit le texte visible sur l'image : marque, modèle, prix imprimés sur le packaging.
Étape 3 — Le module NLP structure ce texte en entités : marque, modèle, couleur, stockage, prix.
Étape 4 — Le détecteur isole le produit dans l'image grâce à Grounding DINO, puis affine le masque avec GrabCut.
Étape 5 — L'analyseur calcule six critères de qualité sur l'image et le masque, et produit un score global avec un grade de A à F.
Étape 6 — BLIP génère une légende visuelle en anglais, qui est traduite et structurée en fiche produit française.
Étape 7 — Le scraper recherche les produits similaires sur Jumia pour l'analyse concurrentielle.

Tout ceci est orchestré par l'interface Streamlit accessible depuis un navigateur.`,

  // Slide 4 — Modules développés
  `Le projet est structuré en neuf modules Python indépendants, chacun avec une responsabilité unique.

Les deux modules centraux sont :
  - src/detector.py : il isole le produit dans l'image,
  - src/analyzer.py : il calcule les six critères qualité.

Les modules périphériques gèrent l'OCR, le NLP, la génération de fiche, la recherche concurrentielle, et le scoring.

Le fichier app.py est l'interface Streamlit qui orchestre l'ensemble et présente les résultats à l'utilisateur.

Tous les modules sont terminés, testés, et commentés.`,

  // Slide 5 — 6 Critères
  `Parlons du cœur du système : les six critères d'analyse qualité.

Chaque critère retourne un score entre 0 et 1, une valeur brute mesurée, et un message d'explication en français destiné au vendeur.

Critère 1 — Netteté : nous utilisons la variance du filtre Laplacien. Ce filtre de dérivée seconde est très sensible aux hautes fréquences, donc au flou. Nous avons calibré les seuils en échelle logarithmique sur 300 images réelles du CDN Jumia, car la distribution des variances est log-normale.

Critère 2 — Uniformité d'éclairage : on divise la zone produit en une grille 3×3 et on mesure l'écart-type des luminosités moyennes par zone. Un écart-type faible signifie un éclairage homogène.

Critère 3 — Qualité des bords : on applique la détection Canny dans la zone de frontière entre le masque produit et le fond, et on mesure la densité des bords détectés.

Critère 4 — Cohérence des couleurs : on applique l'hypothèse du monde gris et on vérifie que la saturation HSV est dans la plage naturelle.

Critère 5 — Résolution effective : deux composantes — détection d'upscaling par ratio de variance Laplacienne, et vérification de la taille absolue recommandée par Jumia (500px minimum).

Critère 6 — Cohérence image-texte : on utilise CLIP d'OpenAI pour mesurer la similarité cosinus entre l'embedding image et l'embedding texte du prompt.`,

  // Slide 6 — Résultats clés
  `En termes de résultats concrets :

Le système analyse six critères et attribue des grades de A à F, avec un score global calculé par moyenne pondérée.

Les pondérations ont été choisies pour refléter l'impact perçu par l'acheteur : la netteté et l'éclairage ont le poids le plus élevé — 20% chacun — car ce sont les premiers signaux visuels.

Cinq modèles d'intelligence artificielle sont intégrés : Grounding DINO pour la détection, BLIP pour la génération de légende, CLIP pour la cohérence sémantique, EasyOCR pour la lecture de texte, et GrabCut pour la segmentation précise.

Tous fonctionnent en mode CPU, sans nécessité de GPU, ce qui facilite le déploiement.`,

  // Slide 7 — Défis techniques
  `Je vais vous détailler les principaux défis techniques rencontrés.

Premier défi — Score de netteté constant : toutes les images du CDN Jumia ont la même table de quantification JPEG à quality=75, ce qui rendait le score identique pour toutes les images. Solution : remplacement par la variance du Laplacien en échelle log, qui donne 29 valeurs distinctes sur 300 images.

Deuxième défi — Ordre grammatical français incorrect dans les titres : par exemple "Portable Chargeur" au lieu de "Chargeur Portable". Solution : classification des mots-clés BLIP en deux catégories — les noms de type produit en premier, puis les adjectifs attributs.

Troisième défi — Description en anglais brut : la légende BLIP était insérée directement. Solution : traduction via dictionnaire et génération de phrases françaises structurées.

Quatrième défi — Watermark "fallback" visible : la fonction de visualisation appelait le détecteur sans le prompt utilisateur, ce qui forçait toujours le mode fallback. Solution : passage du text_prompt à la fonction de visualisation.

Cinquième et sixième défis — Analyse concurrentielle absente et scraper retournant zéro résultats : le sélecteur CSS était obsolète et le User-Agent était détecté comme bot. Solutions : mise à jour des sélecteurs article.prd, gestion du lazy-loading des images, User-Agent Chrome réel, et trois niveaux de fallback pour la requête de recherche.`,

  // Slide 8 — État d'avancement
  `L'état d'avancement global est de 100%.

Les quatre grandes catégories sont toutes complètes :

Infrastructure et interface : le pipeline bout-en-bout fonctionne, la gestion de l'état Streamlit est correcte, le déploiement local est testé.

Analyse qualité : les six critères sont implémentés et calibrés sur données réelles.

Intelligence artificielle : les cinq modèles sont intégrés avec dégradation gracieuse — si un modèle est indisponible, le système continue à fonctionner.

Documentation : README complet en français, documentation technique pour le jury, et commentaires inline dans le code.`,

  // Slide 9 — Stack technologique
  `La stack technologique s'articule autour de quatre domaines.

Vision par ordinateur : OpenCV 4 pour les opérations morphologiques, GrabCut, Canny et Laplacien. Pillow pour le chargement et la conversion des images. NumPy pour les opérations matricielles sur les masques.

Modèles Transformers : Grounding DINO pour la détection zéro-shot, BLIP pour la génération de légende, CLIP pour la cohérence sémantique. Tous chargés via HuggingFace Transformers.

Traitement du texte : EasyOCR pour la reconnaissance bilingue français-anglais, les expressions régulières Python pour l'extraction d'entités, et BeautifulSoup pour le scraping HTML de Jumia.

Interface et déploiement : Streamlit pour l'interface web, Requests pour les appels HTTP, Python 3.11 avec environnement virtuel isolé.`,

  // Slide 10 — Limites & Perspectives
  `Quelques limites importantes à mentionner.

Les seuils du critère de netteté ont été calibrés sur des images 300×300 pixels, le format standard du CDN Jumia. Pour des images haute résolution, il faudrait recalibrer.

EasyOCR est relativement lent en CPU — environ 3 secondes par image. PaddleOCR serait 5 fois plus rapide.

Le scraping Jumia peut être bloqué par des mécanismes anti-bot. Une API officielle serait plus robuste pour un déploiement en production.

Côté perspectives : ajouter le support du darija marocain pour rendre le système accessible à un plus large public, corréler les scores avec les taux de clics réels pour valider empiriquement le système, et déployer sur cloud pour un accès partagé.`,

  // Slide 11 — Conclusion
  `En conclusion, nous avons développé un système complet et fonctionnel qui répond à un besoin concret du marché e-commerce marocain.

Le système intègre des modèles d'IA de pointe — Grounding DINO, BLIP, CLIP — dans un pipeline accessible à des vendeurs non-techniques via une interface Streamlit simple.

Les six critères qualité sont calibrés sur des données réelles, et le système produit des recommandations actionnables en français.

Les principaux défis techniques ont été identifiés et résolus pendant le développement, ce qui a renforcé notre compréhension de chaque composant.

Je vous remercie pour votre attention et reste disponible pour répondre à vos questions.`,
];

// Attach notes to each slide
pres.slides.forEach((slide, i) => {
  if (notes[i]) slide.addNotes(notes[i]);
});

// ─── Write file ──────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "etat_avancement.pptx" })
  .then(() => console.log("✅  etat_avancement.pptx créé avec succès"))
  .catch(err => { console.error("❌  Erreur:", err); process.exit(1); });
