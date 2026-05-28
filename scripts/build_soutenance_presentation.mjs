import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const artifactToolUtils = await import(
  pathToFileURL(
    "C:/Users/ahadj/.codex/plugins/cache/openai-primary-runtime/presentations/26.521.10419/skills/presentations/scripts/artifact_tool_utils.mjs",
  ).href,
);

const {
  createSlideContext,
  ensureArtifactToolWorkspace,
  importArtifactTool,
} = artifactToolUtils;

if (!process.env.HOME && process.env.USERPROFILE) {
  process.env.HOME = process.env.USERPROFILE;
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const outputDir = path.join(projectRoot, "deliverables");
const outputFile = path.join(outputDir, "presentation_soutenance_pfe_zero_shot_1h.pptx");
const workspace = path.join(projectRoot, "outputs", "manual-presentation", "presentations", "soutenance-1h");

const W = 1280;
const H = 720;

const COLORS = {
  bg: "#0B1020",
  panel: "#131B2E",
  panel2: "#18233A",
  accent: "#D3A96A",
  accentSoft: "#F1E0C6",
  text: "#F7F3EA",
  muted: "#B7C0D8",
  faint: "#7E89A6",
  green: "#4AC27A",
  yellow: "#F0C85A",
  red: "#E66969",
  blue: "#6DA6FF",
  white: "#FFFFFF",
};

const deckStats = {
  totalOriginals: 180,
  perCategory: 60,
  totalDegraded: 3240,
  categories: ["shoes", "clothing", "portable_electronics"],
  spearman: 0.3799,
  pvalue: 0.006497,
};

const sensitivity = [
  { key: "blur", criterion: "sharpness", avgDrop: 65.3, success: 99.63, color: COLORS.green },
  { key: "lowres", criterion: "effective_resolution", avgDrop: 20.95, success: 100.0, color: COLORS.blue },
  { key: "bad_crop", criterion: "effective_resolution", avgDrop: 14.2, success: 92.96, color: COLORS.yellow },
  { key: "overexposure", criterion: "exposure", avgDrop: 14.35, success: 55.56, color: COLORS.yellow },
  { key: "jpeg", criterion: "sharpness", avgDrop: 5.95, success: 47.96, color: COLORS.red },
  { key: "underexposure", criterion: "exposure", avgDrop: -6.99, success: 47.59, color: COLORS.red },
];

const assets = {
  shoe: path.join(projectRoot, "dataset", "originals", "shoes", "SHO_001.jpg"),
  clothing: path.join(projectRoot, "dataset", "originals", "clothing", "CLO_001.jpg"),
  electronics: path.join(projectRoot, "dataset", "originals", "portable_electronics", "POR_001.jpg"),
  clothingClean: path.join(projectRoot, "dataset", "originals", "clothing", "CLO_038.jpg"),
  blur: path.join(projectRoot, "dataset", "degraded", "clothing", "001_blur_high.jpg"),
  lowres: path.join(projectRoot, "dataset", "degraded", "clothing", "001_lowres_high.jpg"),
  crop: path.join(projectRoot, "dataset", "degraded", "clothing", "001_bad_crop_high.jpg"),
  spearman: path.join(projectRoot, "output", "reports", "spearman_correlation.png"),
};

function line(ctx, color, width = 1) {
  return ctx.line(color, width, "solid");
}

function addBackground(ctx, slide, variant = "default") {
  const fill = variant === "panel" ? COLORS.panel : COLORS.bg;
  ctx.addShape(slide, {
    x: 0,
    y: 0,
    w: W,
    h: H,
    fill,
    line: ctx.line(fill, 0),
  });
  ctx.addShape(slide, {
    x: 0,
    y: 0,
    w: W,
    h: 18,
    fill: COLORS.accent,
    line: ctx.line(COLORS.accent, 0),
  });
}

function addFooter(ctx, slide, index) {
  ctx.addText(slide, {
    text: `PFE Zero-Shot | Soutenance detaillee | ${String(index).padStart(2, "0")}`,
    x: 46,
    y: 682,
    w: 400,
    h: 18,
    fontSize: 10,
    color: COLORS.faint,
    face: "Aptos",
  });
  ctx.addText(slide, {
    text: `${index}`,
    x: 1210,
    y: 676,
    w: 28,
    h: 24,
    fontSize: 12,
    color: COLORS.accentSoft,
    face: "Aptos",
    align: "right",
  });
}

function addKicker(ctx, slide, text) {
  ctx.addText(slide, {
    text,
    x: 56,
    y: 40,
    w: 240,
    h: 24,
    fontSize: 14,
    color: COLORS.accentSoft,
    face: "Aptos",
  });
}

function addTitle(ctx, slide, title, subtitle = "") {
  ctx.addText(slide, {
    text: title,
    x: 56,
    y: 76,
    w: 1140,
    h: 84,
    fontSize: 30,
    color: COLORS.text,
    face: "Aptos Display",
    bold: true,
  });
  if (subtitle) {
    ctx.addText(slide, {
      text: subtitle,
      x: 56,
      y: 152,
      w: 1080,
      h: 52,
      fontSize: 16,
      color: COLORS.muted,
      face: "Aptos",
    });
  }
}

function addBulletList(ctx, slide, items, x, y, w, options = {}) {
  const fontSize = options.fontSize ?? 18;
  const color = options.color ?? COLORS.text;
  const gap = options.gap ?? 34;
  items.forEach((item, idx) => {
    ctx.addShape(slide, {
      x,
      y: y + idx * gap + 6,
      w: 8,
      h: 8,
      fill: COLORS.accent,
      line: ctx.line(COLORS.accent, 0),
    });
    ctx.addText(slide, {
      text: item,
      x: x + 18,
      y: y + idx * gap,
      w: w - 18,
      h: gap + 6,
      fontSize,
      color,
      face: "Aptos",
    });
  });
}

function addPanel(ctx, slide, x, y, w, h, title = "", body = []) {
  ctx.addShape(slide, {
    x,
    y,
    w,
    h,
    fill: COLORS.panel,
    line: line(ctx, "#273454", 1),
  });
  if (title) {
    ctx.addText(slide, {
      text: title,
      x: x + 18,
      y: y + 16,
      w: w - 36,
      h: 28,
      fontSize: 18,
      color: COLORS.accentSoft,
      face: "Aptos Display",
      bold: true,
    });
  }
  if (body.length) {
    addBulletList(ctx, slide, body, x + 18, y + 56, w - 36, {
      fontSize: 16,
      color: COLORS.text,
      gap: 28,
    });
  }
}

async function addImageCard(ctx, slide, imagePath, x, y, w, h, caption = "") {
  ctx.addShape(slide, {
    x,
    y,
    w,
    h,
    fill: COLORS.panel,
    line: line(ctx, "#24314E", 1),
  });
  await ctx.addImage(slide, {
    path: imagePath,
    x: x + 8,
    y: y + 8,
    w: w - 16,
    h: h - (caption ? 46 : 16),
    fit: "contain",
    alt: caption || path.basename(imagePath),
  });
  if (caption) {
    ctx.addText(slide, {
      text: caption,
      x: x + 12,
      y: y + h - 34,
      w: w - 24,
      h: 22,
      fontSize: 12,
      color: COLORS.muted,
      face: "Aptos",
      align: "center",
    });
  }
}

function addStatCard(ctx, slide, x, y, w, h, value, label, tone = COLORS.accent) {
  ctx.addShape(slide, {
    x,
    y,
    w,
    h,
    fill: COLORS.panel,
    line: line(ctx, "#273454", 1),
  });
  ctx.addText(slide, {
    text: value,
    x: x + 18,
    y: y + 18,
    w: w - 36,
    h: 40,
    fontSize: 28,
    color: tone,
    face: "Aptos Display",
    bold: true,
    align: "center",
  });
  ctx.addText(slide, {
    text: label,
    x: x + 18,
    y: y + 66,
    w: w - 36,
    h: 34,
    fontSize: 14,
    color: COLORS.muted,
    face: "Aptos",
    align: "center",
  });
}

function addHorizontalBar(ctx, slide, x, y, w, label, value, max, color, note) {
  ctx.addText(slide, {
    text: label,
    x,
    y: y - 2,
    w: 200,
    h: 20,
    fontSize: 14,
    color: COLORS.text,
    face: "Aptos",
  });
  ctx.addShape(slide, {
    x: x + 210,
    y,
    w,
    h: 14,
    fill: "#202B45",
    line: ctx.line("#202B45", 0),
  });
  ctx.addShape(slide, {
    x: x + 210,
    y,
    w: Math.max(8, (w * value) / max),
    h: 14,
    fill: color,
    line: ctx.line(color, 0),
  });
  ctx.addText(slide, {
    text: `${value.toFixed(2)}`,
    x: x + 210 + w + 10,
    y: y - 4,
    w: 60,
    h: 22,
    fontSize: 14,
    color: COLORS.accentSoft,
    face: "Aptos",
    align: "right",
  });
  if (note) {
    ctx.addText(slide, {
      text: note,
      x: x + 290,
      y: y + 18,
      w: 520,
      h: 18,
      fontSize: 11,
      color: COLORS.faint,
      face: "Aptos",
    });
  }
}

function addProcessBox(ctx, slide, x, y, w, h, title, body) {
  ctx.addShape(slide, {
    x,
    y,
    w,
    h,
    fill: COLORS.panel2,
    line: line(ctx, "#2C3B5E", 1),
  });
  ctx.addText(slide, {
    text: title,
    x: x + 14,
    y: y + 14,
    w: w - 28,
    h: 24,
    fontSize: 17,
    color: COLORS.accentSoft,
    face: "Aptos Display",
    bold: true,
    align: "center",
  });
  ctx.addText(slide, {
    text: body,
    x: x + 16,
    y: y + 44,
    w: w - 32,
    h: h - 56,
    fontSize: 13,
    color: COLORS.text,
    face: "Aptos",
    align: "center",
  });
}

function addArrow(ctx, slide, x1, y1, x2, y2) {
  const left = Math.min(x1, x2);
  const top = Math.min(y1, y2) - 1;
  const width = Math.abs(x2 - x1);
  ctx.addShape(slide, {
    geometry: "rect",
    x: left,
    y: top,
    w: width,
    h: 2,
    fill: COLORS.accent,
    line: ctx.line(COLORS.accent, 0),
  });
  ctx.addShape(slide, {
    geometry: "chevron",
    x: x2 - 8,
    y: y2 - 6,
    w: 14,
    h: 14,
    fill: COLORS.accent,
    line: ctx.line(COLORS.accent, 0),
  });
}

async function buildDeck() {
  await ensureArtifactToolWorkspace(workspace);
  const artifact = await importArtifactTool(workspace);
  const { Presentation, PresentationFile } = artifact;

  const presentation = Presentation.create({
    slideSize: { width: W, height: H },
  });
  const ctx = createSlideContext(artifact, {
    slideSize: { width: W, height: H },
    outputDir,
    assetDir: path.join(workspace, "assets"),
    workspaceDir: workspace,
    titleFont: "Aptos Display",
    bodyFont: "Aptos",
  });

  const slides = [];

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    ctx.addShape(slide, {
      x: 56,
      y: 106,
      w: 10,
      h: 420,
      fill: COLORS.accent,
      line: ctx.line(COLORS.accent, 0),
    });
    ctx.addText(slide, {
      text: "Soutenance PFE",
      x: 86,
      y: 110,
      w: 300,
      h: 34,
      fontSize: 20,
      color: COLORS.accentSoft,
      face: "Aptos",
    });
    ctx.addText(slide, {
      text: "Systeme zero-shot d'evaluation automatique de la qualite d'images produit e-commerce",
      x: 86,
      y: 156,
      w: 650,
      h: 164,
      fontSize: 34,
      color: COLORS.text,
      face: "Aptos Display",
      bold: true,
    });
    ctx.addText(slide, {
      text: "Pipeline multimodal explicable combinant NLP, region proposal, CLIP, heuristiques visuelles et recommandations vendeur",
      x: 86,
      y: 336,
      w: 600,
      h: 72,
      fontSize: 18,
      color: COLORS.muted,
      face: "Aptos",
    });
    addStatCard(ctx, slide, 748, 134, 180, 110, "0", "entrainement local", COLORS.green);
    addStatCard(ctx, slide, 948, 134, 220, 110, "180", "images propres finales", COLORS.blue);
    addStatCard(ctx, slide, 748, 266, 180, 110, "3240", "images degradees", COLORS.yellow);
    addStatCard(ctx, slide, 948, 266, 220, 110, "rho = 0.38", "correlation Spearman", COLORS.accent);
    ctx.addText(slide, {
      text: "Duree cible de la soutenance : environ 1 heure",
      x: 86,
      y: 610,
      w: 420,
      h: 28,
      fontSize: 16,
      color: COLORS.accentSoft,
      face: "Aptos",
    });
    addFooter(ctx, slide, 1);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "PLAN");
    addTitle(ctx, slide, "Plan detaille de la soutenance", "Une progression en 8 chapitres pour couvrir le probleme, la conception, l'evaluation et les limites.");
    addPanel(ctx, slide, 56, 220, 360, 196, "Partie 1 - Cadrage", [
      "Contexte e-commerce et motivation du sujet",
      "Problematique, question de recherche et objectifs",
      "Hypotheses scientifiques et contraintes du PFE",
    ]);
    addPanel(ctx, slide, 460, 220, 360, 196, "Partie 2 - Conception", [
      "Architecture globale du pipeline zero-shot",
      "Description detaillee de chaque module",
      "Choix techniques et configuration",
    ]);
    addPanel(ctx, slide, 864, 220, 360, 196, "Partie 3 - Donnees et validation", [
      "Construction du dataset final et degradations",
      "Protocoles d'evaluation auto et humaine",
      "Resultats, limites et perspectives",
    ]);
    addBulletList(ctx, slide, [
      "Temps moyen recommande : 2 a 3 minutes par slide technique",
      "Deux moments demo possibles : architecture et application Streamlit",
      "Les chiffres montres dans le deck viennent des rapports du projet final",
    ], 72, 470, 1130, { fontSize: 17, gap: 34, color: COLORS.muted });
    addFooter(ctx, slide, 2);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "CONTEXTE");
    addTitle(ctx, slide, "Pourquoi ce sujet est utile pour le e-commerce ?", "Les petits vendeurs ont rarement des moyens professionnels pour produire des photos produit constantes.");
    addPanel(ctx, slide, 56, 220, 370, 230, "Problemes observes", [
      "Photos floues ou mal exposees",
      "Cadrage incomplet ou produit trop petit",
      "Incoherence entre image et fiche produit",
      "Qualite visuelle tres heterogene d'une annonce a l'autre",
    ]);
    addPanel(ctx, slide, 456, 220, 370, 230, "Impact metier", [
      "Moindre confiance du client",
      "Baisse du taux de conversion",
      "Retours plus probables si le produit est mal represente",
      "Temps perdu a corriger ou republier des fiches",
    ]);
    addPanel(ctx, slide, 856, 220, 370, 230, "Besoin reel", [
      "Un outil simple, rapide et interpretable",
      "Sans entrainement couteux",
      "Capable de donner un score et des conseils concrets",
      "Utilisable par un non-expert de la photographie",
    ]);
    addFooter(ctx, slide, 3);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "QUESTION");
    addTitle(ctx, slide, "Problematique et question de recherche", "Comment evaluer automatiquement la qualite d'une photo produit sans entrainer un modele specifique ?");
    addPanel(ctx, slide, 56, 220, 560, 180, "Question de recherche", [
      "Peut-on construire un score de qualite pertinent en combinant texte, vision classique et CLIP ?",
      "Peut-on garder un systeme explicable et defendable scientifiquement dans un delai court ?",
    ]);
    addPanel(ctx, slide, 650, 220, 574, 180, "Reponse proposee", [
      "Oui, via une architecture zero-shot multimodale",
      "Le texte de l'annonce sert de verite d'entree",
      "Le produit cible est selectionne avant l'analyse de qualite",
      "Les mesures sont interpretable et visibles",
    ]);
    addBulletList(ctx, slide, [
      "Objectif principal : score global de qualite photo",
      "Objectif secondaire : conseils d'amelioration directement actionnables",
      "Objectif methodologique : eviter l'entrainement local tout en gardant une evaluation quantitative",
    ], 72, 456, 1120, { fontSize: 18, gap: 34 });
    addFooter(ctx, slide, 4);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "CONTRIBUTIONS");
    addTitle(ctx, slide, "Contributions du projet", "Le projet apporte une solution complete, explicable et evaluee experimentalement.");
    addPanel(ctx, slide, 56, 220, 360, 210, "Contribution 1", [
      "Architecture zero-shot complete pour l'evaluation photo e-commerce",
      "Aucun entrainement de modele dans le depot",
    ]);
    addPanel(ctx, slide, 460, 220, 360, 210, "Contribution 2", [
      "Selection du bon produit via regions candidates + CLIP + heuristiques",
      "Explicabilite du crop retenu et des sous-scores",
    ]);
    addPanel(ctx, slide, 864, 220, 360, 210, "Contribution 3", [
      "Dataset final propre + degradations controlees",
      "Validation automatique et evaluation humaine finale",
    ]);
    addBulletList(ctx, slide, [
      "Valeur scientifique : combinaison multimodale explicable",
      "Valeur pratique : application Streamlit demonstrable pour un vendeur",
      "Valeur experimentale : protocoles reproductibles et rapport final",
    ], 72, 470, 1120, { fontSize: 17, gap: 34, color: COLORS.muted });
    addFooter(ctx, slide, 5);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "HYPOTHESES");
    addTitle(ctx, slide, "Hypotheses structurantes et contraintes du PFE", "Ces choix delimitent le scope et rendent le projet realisable sur environ deux mois.");
    addPanel(ctx, slide, 56, 220, 560, 230, "Hypotheses fortes", [
      "Le texte de l'annonce est la source de verite principale",
      "Pas d'OCR dans le chemin critique du scoring",
      "Pas d'entrainement local de modele",
      "Les mauvaises images sont generees par degradations controlees",
    ]);
    addPanel(ctx, slide, 650, 220, 574, 230, "Contraintes de scope", [
      "Trois familles seulement : shoes, clothing, portable_electronics",
      "Le systeme doit rester interpretable et presentable",
      "Le temps disponible impose des choix pragmatiques",
      "Les recommandations doivent rester simples pour un vendeur",
    ]);
    addFooter(ctx, slide, 6);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "POSITIONNEMENT");
    addTitle(ctx, slide, "Pourquoi une approche zero-shot plutot qu'une approche supervisee ?", "Le choix n'est pas de battre un benchmark deep learning, mais de construire une solution credible, legere et explicable.");
    addPanel(ctx, slide, 56, 220, 560, 250, "Approche supervisee classique", [
      "Besoin d'un grand dataset annote manuellement",
      "Cout de preparation et d'entrainement eleve",
      "Moins interpretable pour un petit PFE",
      "Risque d'etre hors delai pour 2 mois",
    ]);
    addPanel(ctx, slide, 650, 220, 574, 250, "Approche retenue ici", [
      "Reutilisation de modeles pre-entraines",
      "Fusion texte + image + heuristiques",
      "Explicabilite des etapes de decision",
      "Validation via degradations controlees et corrrelation humaine",
    ]);
    addFooter(ctx, slide, 7);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "ARCHITECTURE");
    addTitle(ctx, slide, "Architecture globale du systeme", "Le pipeline suit une logique simple : comprendre le texte, localiser le produit, analyser sa qualite, puis expliquer le resultat.");
    addProcessBox(ctx, slide, 48, 250, 180, 145, "Entree", "Image produit\n+\nTitre + description");
    addProcessBox(ctx, slide, 278, 250, 190, 145, "Text Processor", "Nettoyage\nExtraction couleur / categorie / marque\nEmbedding CLIP texte");
    addProcessBox(ctx, slide, 518, 250, 190, 145, "Region Generator", "Saliency OpenCV\nContours fallback\nMaximum 5 regions");
    addProcessBox(ctx, slide, 758, 250, 190, 145, "Selector", "CLIP image/texte\nScore visuel\nCoherence categorie");
    addProcessBox(ctx, slide, 998, 250, 190, 145, "Analyzer", "Nettete\nExposition\nContraste\nResolution\nCoherence");
    addArrow(ctx, slide, 228, 322, 278, 322);
    addArrow(ctx, slide, 468, 322, 518, 322);
    addArrow(ctx, slide, 708, 322, 758, 322);
    addArrow(ctx, slide, 948, 322, 998, 322);
    ctx.addText(slide, {
      text: "Sorties finales : crop selectionne, score global, sous-scores explicables, recommandations FR / Darija",
      x: 140,
      y: 456,
      w: 1000,
      h: 34,
      fontSize: 17,
      color: COLORS.accentSoft,
      face: "Aptos",
      align: "center",
    });
    addFooter(ctx, slide, 8);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "PIPELINE");
    addTitle(ctx, slide, "Pipeline detaille et circulation de l'information", "Chaque bloc repond a une question precise : de quoi parle l'annonce, ou est le produit, et la photo est-elle de bonne qualite ?");
    addPanel(ctx, slide, 56, 210, 360, 260, "1. Comprendre l'annonce", [
      "Le texte est nettoye et normalise",
      "Extraction de couleur, categorie et marque",
      "Creation d'un embedding texte reutilisable",
    ]);
    addPanel(ctx, slide, 460, 210, 360, 260, "2. Proposer des zones", [
      "Le systeme propose plusieurs regions candidates",
      "Pas de detection supervisee imposee par defaut",
      "Seulement 5 regions max pour maitriser le cout CLIP",
    ]);
    addPanel(ctx, slide, 864, 210, 360, 260, "3. Analyser le bon crop", [
      "Le selector choisit la region la plus coherente",
      "L'analyzer note la qualite visuelle du crop",
      "Le score final est justifie par criteres",
    ]);
    addBulletList(ctx, slide, [
      "Le texte intervient deux fois : selection du produit et verification de coherence",
      "Le crop selectionne est central pour rendre l'IA compréhensible a l'utilisateur",
      "Le scoring global n'est jamais une boite noire pure",
    ], 72, 500, 1120, { fontSize: 16, gap: 30, color: COLORS.muted });
    addFooter(ctx, slide, 9);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "MODULE 1");
    addTitle(ctx, slide, "Text Processor : transformer le texte en signal exploitable", "Cette brique donne au systeme sa source de verite principale.");
    addPanel(ctx, slide, 56, 220, 380, 240, "Entree", [
      "Titre du produit",
      "Description de l'annonce",
      "Texte libre fourni par le vendeur ou le dataset",
    ]);
    addPanel(ctx, slide, 450, 220, 380, 240, "Traitements", [
      "Normalisation du texte",
      "spaCy fr_core_news_md si disponible",
      "rapidfuzz + dictionnaires pour couleur / categorie / marque",
      "Embedding CLIP multilingue texte",
    ]);
    addPanel(ctx, slide, 844, 220, 380, 240, "Sortie", [
      "clean_text",
      "color",
      "category",
      "brand",
      "text_embedding",
    ]);
    addFooter(ctx, slide, 10);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "MODULE 2");
    addTitle(ctx, slide, "Candidate Region Generator : proposer des zones sans detection supervisee", "Le projet ne suppose pas un detecteur entraine sur classes produit.");
    addPanel(ctx, slide, 56, 220, 560, 250, "Strategie par defaut", [
      "Saliency OpenCV si le module est disponible",
      "Sinon fallback par seuillage adaptatif et contours",
      "Regions triees par aire et centralite",
      "Maximum 5 regions candidates",
    ]);
    addPanel(ctx, slide, 650, 220, 574, 250, "Filet de securite", [
      "Grounding DINO est disponible comme fallback activable",
      "Desactive par defaut pour garder une methode legere",
      "Utilisable si la saliency se revele insuffisante sur certaines photos",
      "Le refine final du gagnant repose sur GrabCut",
    ]);
    addFooter(ctx, slide, 11);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "MODULE 3");
    addTitle(ctx, slide, "Selector : choisir le bon produit parmi les regions candidates", "Le selector est la piece centrale qui relie region proposal et score qualite.");
    addPanel(ctx, slide, 56, 220, 420, 240, "Formule de score", [
      "score = 0.6 * score_clip + 0.25 * score_visuel + 0.15 * score_categorie",
      "Poids stockes dans config.py",
      "Calibration empirique assumee et explicite",
    ]);
    addPanel(ctx, slide, 496, 220, 350, 240, "Score CLIP", [
      "Embedding image du crop",
      "Similarite cosinus avec l'embedding texte",
      "Signal principal de selection semantique",
    ]);
    addPanel(ctx, slide, 866, 220, 360, 240, "Scores heuristiques", [
      "Visuel : aire normalisee x centralite",
      "Categorie : coherence faible mais utile",
      "GrabCut applique seulement sur le gagnant",
    ]);
    ctx.addText(slide, {
      text: "Correctif important du projet final : eviter qu'un mini-crop tres contraste gagne artificiellement sur une grande zone produit plus plausible.",
      x: 72,
      y: 500,
      w: 1120,
      h: 36,
      fontSize: 15,
      color: COLORS.accentSoft,
      face: "Aptos",
      align: "center",
    });
    addFooter(ctx, slide, 12);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "MODULE 4");
    addTitle(ctx, slide, "Analyzer : decomposition du score de qualite", "Le score final est obtenu a partir de criteres lisibles et independants.");
    addPanel(ctx, slide, 56, 220, 360, 250, "Criteres visuels", [
      "Nettete : variance du Laplacien",
      "Exposition : statistiques de luminance",
      "Contraste : ecart-type du niveau de gris",
      "Balance couleurs : deviation inter-canaux",
    ]);
    addPanel(ctx, slide, 460, 220, 360, 250, "Criteres structurels", [
      "Resolution effective : taille utile + detail reel",
      "Coherence image/texte : CLIP + couleur dominante",
      "La couleur reste un signal leger",
    ]);
    addPanel(ctx, slide, 864, 220, 360, 250, "Sorties", [
      "Sous-scores 0 a 100",
      "Messages explicatifs",
      "Score global pondere",
      "Recommandations FR / Darija",
    ]);
    addFooter(ctx, slide, 13);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "APPLICATION");
    addTitle(ctx, slide, "Application Streamlit : interface de demonstration", "L'application est volontairement sobre pour mettre l'accent sur l'explicabilite du resultat.");
    addPanel(ctx, slide, 56, 220, 360, 230, "Analyse unique", [
      "Image + titre + description",
      "Affichage du crop selectionne en priorite",
      "Score global et sous-scores",
      "Bloc coherence image / texte",
    ]);
    addPanel(ctx, slide, 456, 220, 360, 230, "Mode batch", [
      "Traitement d'un dossier d'images",
      "Tableau recapitulatif",
      "Export CSV des resultats",
    ]);
    addPanel(ctx, slide, 856, 220, 368, 230, "Mode debug", [
      "Regions candidates",
      "Scores intermediaires du selector",
      "Etat du backend CLIP",
      "Informations sur la coherence",
    ]);
    addBulletList(ctx, slide, [
      "Le crop selectionne est l'element d'interface le plus important",
      "L'utilisateur peut comprendre pourquoi la note est bonne ou mauvaise",
      "Le systeme peut etre montre en direct en soutenance",
    ], 72, 490, 1120, { fontSize: 17, gap: 32, color: COLORS.muted });
    addFooter(ctx, slide, 14);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "DONNEES");
    addTitle(ctx, slide, "Strategie dataset : construire un jeu de donnees defendable sans annotation lourde", "Le choix cle est de partir d'images propres et de generer les mauvaises images de facon controlee.");
    addPanel(ctx, slide, 56, 220, 560, 250, "Principes", [
      "Limiter le scope a trois familles de produits",
      "Conserver des images suffisamment grandes et lisibles",
      "Eviter l'annotation exhaustive manuelle de defauts reels",
      "Construire une verite-terrain exacte via degradations controlees",
    ]);
    addPanel(ctx, slide, 650, 220, 574, 250, "Sources reelles du projet final", [
      "Base historique curatee du projet pour une partie des originaux",
      "Complement Shopify/product-catalogue pour finir les quotas",
      "Pipeline de build final reproductible",
      "metadata.csv et degraded_metadata.csv pour tracer les sources",
    ]);
    addFooter(ctx, slide, 15);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "DATASET FINAL");
    addTitle(ctx, slide, "Composition du dataset final", "Le jeu final est volontairement compact, mais suffisant pour calibrer et valider le systeme.");
    addStatCard(ctx, slide, 72, 210, 200, 120, "60", "shoes", COLORS.accent);
    addStatCard(ctx, slide, 294, 210, 200, 120, "60", "clothing", COLORS.blue);
    addStatCard(ctx, slide, 516, 210, 260, 120, "60", "portable_electronics", COLORS.green);
    addStatCard(ctx, slide, 798, 210, 180, 120, "180", "images propres", COLORS.yellow);
    addStatCard(ctx, slide, 1000, 210, 200, 120, "3240", "images degradees", COLORS.red);
    addPanel(ctx, slide, 72, 374, 540, 228, "Metadata principal", [
      "filename, filepath, category, source_dataset",
      "title, description, width, height",
      "human_score, degradation_type, degradation_level",
    ]);
    addPanel(ctx, slide, 646, 374, 556, 228, "Interet experimental", [
      "Chaque image degradee peut etre reliee a son original",
      "Le protocole permet des comparaisons propres image propre vs image degradee",
      "Le dataset reste assez petit pour etre inspecte manuellement",
    ]);
    addFooter(ctx, slide, 16);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "EXEMPLES");
    addTitle(ctx, slide, "Exemples d'images propres dans le dataset final", "Trois familles ont ete retenues pour maximiser la lisibilite du produit et la pertinence de CLIP.");
    await addImageCard(ctx, slide, assets.shoe, 70, 220, 350, 330, "SHO_001 - shoes");
    await addImageCard(ctx, slide, assets.clothing, 465, 220, 350, 330, "CLO_001 - clothing");
    await addImageCard(ctx, slide, assets.electronics, 860, 220, 350, 330, "POR_001 - portable_electronics");
    ctx.addText(slide, {
      text: "Le scope reduit est volontaire : produits reconnaissables, formes nettes, photos standardisables et evaluation plus defendable en 2 mois.",
      x: 72,
      y: 592,
      w: 1120,
      h: 34,
      fontSize: 16,
      color: COLORS.muted,
      face: "Aptos",
      align: "center",
    });
    addFooter(ctx, slide, 17);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "DEGRADATIONS");
    addTitle(ctx, slide, "Degradations controlees utilisees pour creer les mauvaises images", "Chaque degradation vise un defaut reele de photo produit e-commerce.");
    await addImageCard(ctx, slide, assets.clothingClean, 60, 220, 280, 300, "Image propre");
    await addImageCard(ctx, slide, assets.blur, 370, 220, 280, 300, "Blur high");
    await addImageCard(ctx, slide, assets.lowres, 680, 220, 280, 300, "Lowres high");
    await addImageCard(ctx, slide, assets.crop, 990, 220, 230, 300, "Bad crop high");
    addBulletList(ctx, slide, [
      "Flou gaussien : verifie la sensibilite de la nettete",
      "Sous/sur-exposition : verifie l'exposition",
      "Mauvais recadrage et lowres : verifient la resolution utile et le cadrage",
      "Compression JPEG : simule des artefacts de sauvegarde ou reupload",
    ], 72, 560, 1120, { fontSize: 15, gap: 28, color: COLORS.muted });
    addFooter(ctx, slide, 18);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "PROTOCOLE");
    addTitle(ctx, slide, "Protocole d'evaluation experimental", "Le projet combine une validation automatique ciblee et une validation humaine finale.");
    addPanel(ctx, slide, 56, 220, 360, 250, "Evaluation 1", [
      "Comparer chaque image degradee a son image propre",
      "Mesurer si le bon critere chute reellement",
      "Exporter des tableaux de sensibilite par degradation",
    ]);
    addPanel(ctx, slide, 460, 220, 360, 250, "Evaluation 2", [
      "Selection de 50 images pour annotation humaine",
      "Score humain renseigne manuellement",
      "Calcul de la corrrelation de Spearman",
    ]);
    addPanel(ctx, slide, 864, 220, 360, 250, "Objectif", [
      "Montrer que le systeme detecte bien certains defauts",
      "Montrer que son score reste lie au jugement humain",
      "Assumer les limites de l'approche zero-shot",
    ]);
    addFooter(ctx, slide, 19);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "RESULTATS 1");
    addTitle(ctx, slide, "Sensibilite par critere : ce que le systeme detecte bien ou mal", "Le tableau suivant resume la baisse moyenne du bon critere sur les images degradees.");
    addHorizontalBar(ctx, slide, 70, 220, 410, "blur -> sharpness", 65.3, 70, COLORS.green, "Tres bon resultat, quasi parfait.");
    addHorizontalBar(ctx, slide, 70, 278, 410, "lowres -> effective_resolution", 20.95, 70, COLORS.blue, "Bonne sensibilite apres recalibration.");
    addHorizontalBar(ctx, slide, 70, 336, 410, "bad_crop -> effective_resolution", 14.2, 70, COLORS.yellow, "Sensibilite correcte mais perfectible.");
    addHorizontalBar(ctx, slide, 70, 394, 410, "overexposure -> exposure", 14.35, 70, COLORS.yellow, "Resultat moyen.");
    addHorizontalBar(ctx, slide, 70, 452, 410, "jpeg -> sharpness", 5.95, 70, COLORS.red, "Impact faible sur la moyenne.");
    addHorizontalBar(ctx, slide, 70, 510, 410, "underexposure -> exposure", -6.99, 70, COLORS.red, "Critere encore fragile dans ce cas.");
    addPanel(ctx, slide, 620, 220, 590, 350, "Lecture du resultat", [
      "Le flou est la degradation la mieux capturee par le systeme.",
      "Le lowres et le bad crop sont correctement detectes apres les derniers ajustements.",
      "L'exposition reste plus delicate, surtout pour la sous-exposition.",
      "Le JPEG a un effet plus faible et moins stable sur le score de nettete.",
    ]);
    addFooter(ctx, slide, 20);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "RESULTATS 2");
    addTitle(ctx, slide, "Validation humaine finale", "Le score automatique est compare a 50 jugements humains sur un echantillon d'images.");
    await addImageCard(ctx, slide, assets.spearman, 70, 210, 560, 360, "Graphe de corrrelation Spearman");
    addStatCard(ctx, slide, 700, 228, 220, 110, "50", "annotations humaines", COLORS.accent);
    addStatCard(ctx, slide, 960, 228, 220, 110, "0.3799", "Spearman rho", COLORS.blue);
    addStatCard(ctx, slide, 700, 362, 220, 110, "0.006497", "p-value", COLORS.green);
    addStatCard(ctx, slide, 960, 362, 220, 110, "significatif", "statut", COLORS.yellow);
    addBulletList(ctx, slide, [
      "Le score automatique suit partiellement le jugement humain.",
      "La corrrelation est positive et statistiquement significative.",
      "Le resultat reste modere, ce qui est coherent avec une approche zero-shot explicable.",
    ], 676, 516, 520, { fontSize: 16, gap: 30, color: COLORS.muted });
    addFooter(ctx, slide, 21);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "CAS PRATIQUE");
    addTitle(ctx, slide, "Exemple de lecture d'une image par le systeme", "Le systeme ne rend pas seulement une note : il fournit aussi une lecture interpretable du cas.");
    await addImageCard(ctx, slide, assets.clothingClean, 72, 222, 340, 320, "Exemple clothing");
    addPanel(ctx, slide, 454, 220, 350, 320, "Lecture du selector", [
      "Plusieurs regions candidates proposees",
      "Le crop final retenu est celui juge le plus coherent avec le texte",
      "Le debug permet d'afficher les scores intermediaires",
    ]);
    addPanel(ctx, slide, 834, 220, 380, 320, "Lecture de l'analyzer", [
      "Nettete et contraste souvent bien notes sur les bonnes images",
      "Resolution effective et coherence sont plus discriminantes",
      "Les conseils generes sont directement exploitables par un vendeur",
    ]);
    addFooter(ctx, slide, 22);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "DISCUSSION");
    addTitle(ctx, slide, "Ce que montrent les resultats du projet", "Le systeme est utile, interpretable et defendable, mais il ne doit pas etre survendu.");
    addPanel(ctx, slide, 56, 220, 360, 250, "Ce qui marche bien", [
      "Architecture zero-shot operationnelle",
      "Selection produit + score qualite en chaine complete",
      "Tres bonne sensibilite au flou",
      "Application demonstrable et lisible",
    ]);
    addPanel(ctx, slide, 460, 220, 360, 250, "Ce qui marche de facon moyenne", [
      "Detection de lowres et bad crop correcte mais pas parfaite",
      "Coherence image/texte depend de la qualite du crop et du texte",
      "Signal couleur volontairement secondaire",
    ]);
    addPanel(ctx, slide, 864, 220, 360, 250, "Ce qui reste fragile", [
      "Sous-exposition moins bien capturee",
      "JPEG peu discriminant dans certains cas",
      "Extraction heuristique de marque encore approximative",
    ]);
    addFooter(ctx, slide, 23);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "LIMITES");
    addTitle(ctx, slide, "Limites honnetes a assumer en soutenance", "La qualite du PFE est meilleure quand les limites sont expliquees clairement.");
    addBulletList(ctx, slide, [
      "Le scope est volontairement limite a trois familles de produits.",
      "Le systeme ne cherche pas a remplacer un modele supervise specialise.",
      "La corrrelation humaine est significative mais reste moderee.",
      "La detection de certains defauts depend encore du contenu visuel et du texte fourni.",
      "Le dataset final est pertinent pour la validation du projet, mais reste de taille modeste.",
    ], 72, 220, 1120, { fontSize: 20, gap: 46 });
    ctx.addText(slide, {
      text: "Message cle a tenir : la valeur du projet est l'architecture zero-shot multimodale explicable, pas la promesse d'une perfection universelle.",
      x: 72,
      y: 556,
      w: 1120,
      h: 44,
      fontSize: 18,
      color: COLORS.accentSoft,
      face: "Aptos",
      align: "center",
    });
    addFooter(ctx, slide, 24);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide);
    addKicker(ctx, slide, "EXTENSIONS");
    addTitle(ctx, slide, "Perspectives et extensions possibles", "Le projet peut etre etendu sans casser le coeur scientifique deja realise.");
    addPanel(ctx, slide, 56, 220, 360, 260, "Extensions techniques", [
      "Mieux exploiter HSV pour certaines comparaisons couleur",
      "Ameliorer encore l'analyse de l'exposition",
      "Rendre le fallback DINO plus strategique",
    ]);
    addPanel(ctx, slide, 460, 220, 360, 260, "Extensions produit", [
      "Ajouter d'autres familles de produits",
      "Mieux structurer les attributs de marque et de categorie",
      "Renforcer le batch sur de gros dossiers",
    ]);
    addPanel(ctx, slide, 864, 220, 360, 260, "Extension business", [
      "Ajouter un assistant d'annonce separé du scoring",
      "Generer titre, description et conseils via LLM vision",
      "Connecter un workflow n8n pour l'automatisation vendeur",
    ]);
    addFooter(ctx, slide, 25);
  });

  slides.push(async () => {
    const slide = presentation.slides.add();
    addBackground(ctx, slide, "panel");
    addKicker(ctx, slide, "CONCLUSION");
    addTitle(ctx, slide, "Conclusion generale", "Le projet atteint son objectif principal : evaluer automatiquement la qualite d'une photo produit sans entrainement local.");
    addBulletList(ctx, slide, [
      "Le pipeline zero-shot complet fonctionne de bout en bout.",
      "Le crop selectionne rend le systeme interpretable.",
      "Le dataset final propre et degrade permet une validation defendable.",
      "La corrrelation humaine finale est positive et significative.",
      "Le projet est suffisamment solide pour etre demontre et discute en soutenance.",
    ], 72, 240, 1120, { fontSize: 21, gap: 50 });
    ctx.addText(slide, {
      text: "Merci pour votre attention",
      x: 72,
      y: 596,
      w: 1130,
      h: 38,
      fontSize: 28,
      color: COLORS.accent,
      face: "Aptos Display",
      bold: true,
      align: "center",
    });
    addFooter(ctx, slide, 26);
  });

  for (const buildSlide of slides) {
    await buildSlide();
  }

  await fs.mkdir(outputDir, { recursive: true });
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputFile);
}

buildDeck().catch((error) => {
  console.error(error);
  process.exit(1);
});
