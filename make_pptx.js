const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_16X9";
pptx.author = "Ahadj Idouae";
pptx.company = "PFE";
pptx.subject = "Pipeline zero-shot de qualite photo e-commerce";
pptx.title = "Systeme zero-shot d'evaluation de qualite photo e-commerce";

const C = {
  navy: "0F172A",
  teal: "0F766E",
  mint: "14B8A6",
  blue: "1D4ED8",
  white: "FFFFFF",
  light: "F5F7FB",
  line: "DDE3EA",
  text: "18212F",
  muted: "5F6B7A",
  amber: "D97706",
};

function baseSlide(title, subtitle = "") {
  const slide = pptx.addSlide();
  slide.background = { color: C.light };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 0.85,
    fill: { color: C.navy },
    line: { color: C.navy, width: 0 },
  });
  slide.addText(title, {
    x: 0.45,
    y: 0.16,
    w: 8.8,
    h: 0.36,
    fontFace: "Calibri",
    fontSize: 24,
    bold: true,
    color: C.white,
    margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.45,
      y: 0.95,
      w: 10.8,
      h: 0.25,
      fontFace: "Calibri",
      fontSize: 10,
      italic: true,
      color: C.muted,
      margin: 0,
    });
  }
  return slide;
}

function addCard(slide, x, y, w, h, title, lines, accent = C.teal) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: C.white },
    line: { color: C.line, width: 1 },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w: 0.08, h,
    fill: { color: accent },
    line: { color: accent, width: 0 },
  });
  slide.addText(title, {
    x: x + 0.2,
    y: y + 0.12,
    w: w - 0.25,
    h: 0.25,
    fontSize: 15,
    bold: true,
    color: accent,
    margin: 0,
  });
  slide.addText(lines.map((text) => ({ text, options: { breakLine: true } })), {
    x: x + 0.2,
    y: y + 0.45,
    w: w - 0.28,
    h: h - 0.55,
    fontSize: 11,
    color: C.text,
    valign: "top",
    margin: 0,
    breakLine: false,
  });
}

function addBulletList(slide, x, y, w, items, color = C.text, size = 16) {
  slide.addText(
    items.map((text) => ({ text: `• ${text}`, options: { breakLine: true } })),
    {
      x, y, w, h: items.length * 0.34 + 0.2,
      fontSize: size,
      color,
      margin: 0,
      valign: "top",
    }
  );
}

// Slide 1
{
  const s = baseSlide("Systeme zero-shot d'evaluation de qualite photo e-commerce");
  s.addText("Projet PFE axe sur l'explicabilite et la fusion multimodale", {
    x: 0.55, y: 1.45, w: 8.2, h: 0.4,
    fontSize: 22, bold: true, color: C.navy, margin: 0,
  });
  addBulletList(s, 0.7, 2.0, 6.8, [
    "Aucun entrainement de modele dans le depot",
    "Texte de l'annonce = source de verite",
    "Pas d'OCR dans le chemin critique",
    "Score + sous-scores + recommandations",
    "Cible : petits vendeurs e-commerce",
  ], C.text, 16);
  addCard(s, 8.1, 1.65, 4.45, 2.7, "Scope", [
    "shoes",
    "clothing",
    "portable_electronics",
    "",
    "Le projet reste volontairement reduit pour tenir dans la contrainte PFE.",
  ], C.mint);
}

// Slide 2
{
  const s = baseSlide("Probleme et hypothese");
  addCard(s, 0.45, 1.35, 6.0, 3.3, "Probleme vise", [
    "Beaucoup de vendeurs publient des photos floues, mal exposees, mal cadrees ou trop petites.",
    "",
    "Le systeme doit dire si la photo est exploitable, pourquoi, et quoi corriger."
  ], C.blue);
  addCard(s, 6.8, 1.35, 6.05, 3.3, "Hypothese principale", [
    "Le titre et la description de l'annonce servent de verite metier principale.",
    "",
    "CLIP sert ensuite a verifier si l'image selectionnee correspond bien au produit decrit."
  ], C.teal);
}

// Slide 3
{
  const s = baseSlide("Pipeline actuel");
  const steps = [
    "1. annonce : image + titre + description",
    "2. text_processor",
    "3. candidate_region_generator",
    "4. selector",
    "5. analyzer",
    "6. score global + recommandations",
    "7. application Streamlit",
  ];
  addCard(s, 0.55, 1.35, 5.6, 4.1, "Flux", steps, C.teal);
  addCard(s, 6.45, 1.35, 6.3, 4.1, "Message cle", [
    "Le projet ne cherche pas a entrainer un classifieur de qualite.",
    "",
    "La contribution principale est architecturale : NLP + vision + CLIP + heuristiques qualite + explicabilite."
  ], C.blue);
}

// Slide 4
{
  const s = baseSlide("Selection du bon produit");
  addCard(s, 0.55, 1.35, 6.0, 3.9, "Candidate region generator", [
    "Propose des regions candidates sans labels.",
    "",
    "Saliency OpenCV par defaut.",
    "Fallback contours si la saliency est insuffisante.",
    "Grounding DINO disponible comme filet de securite, desactive par defaut."
  ], C.teal);
  addCard(s, 6.8, 1.35, 6.0, 3.9, "Selector", [
    "Score = 0.6 * CLIP + 0.25 * visuel + 0.15 * categorie",
    "",
    "Le selector garde les details intermediaires pour expliquer pourquoi un crop a ete retenu."
  ], C.blue);
}

// Slide 5
{
  const s = baseSlide("Analyse de qualite");
  addCard(s, 0.55, 1.35, 6.1, 3.95, "Criteres calcules", [
    "sharpness",
    "exposure",
    "contrast",
    "color_balance",
    "effective_resolution",
    "coherence image / texte"
  ], C.mint);
  addCard(s, 6.9, 1.35, 5.9, 3.95, "Explicabilite", [
    "Le systeme montre le crop selectionne, le score global, les sous-scores et les recommandations.",
    "",
    "La couleur reste un signal leger, jamais un critere dominant."
  ], C.amber);
}

// Slide 6
{
  const s = baseSlide("Donnees et validation");
  addCard(s, 0.55, 1.35, 6.1, 4.0, "Strategie dataset", [
    "Bonnes images de reference",
    "Mauvaises images generees par degradations controlees",
    "",
    "Exemples : flou, sous-exposition, surexposition, mauvais recadrage, basse resolution, compression JPEG"
  ], C.blue);
  addCard(s, 6.9, 1.35, 5.9, 4.0, "Validation", [
    "evaluate_analyzer.py : sensibilite par critere",
    "evaluate_full.py : echantillon annotable humainement + Spearman",
    "",
    "La verite-terrain est forte car on sait quelle degradation a ete appliquee."
  ], C.teal);
}

// Slide 7
{
  const s = baseSlide("Conclusion");
  s.addText("Contribution principale", {
    x: 0.65, y: 1.5, w: 4.1, h: 0.28,
    fontSize: 20, bold: true, color: C.navy, margin: 0,
  });
  addBulletList(s, 0.75, 2.0, 7.0, [
    "architecture zero-shot multimodale",
    "texte comme verite metier",
    "selection explicable du crop",
    "analyse qualite interpretable",
    "recommandations actionnables",
  ], C.text, 17);
  addCard(s, 8.0, 1.7, 4.4, 2.8, "Message final", [
    "Le projet est defendable scientifiquement sans entrainement local.",
    "",
    "Sa force vient de la fusion zero-shot et de l'explicabilite visible pour le jury et pour l'utilisateur."
  ], C.mint);
}

pptx.writeFile({ fileName: "etat_avancement.pptx" });
