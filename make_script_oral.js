const { Document, Packer, Paragraph, TextRun, HeadingLevel } = require("docx");
const fs = require("fs");

function title(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_1,
    spacing: { after: 220 },
  });
}

function heading(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 220, after: 120 },
  });
}

function body(text) {
  return new Paragraph({
    children: [new TextRun({ text, size: 24 })],
    spacing: { after: 120 },
  });
}

function bullet(text) {
  return new Paragraph({
    text,
    bullet: { level: 0 },
    spacing: { after: 60 },
  });
}

const sections = [
  {
    title: "Ouverture",
    body: [
      "Bonjour. Je vais presenter un systeme zero-shot qui evalue automatiquement la qualite d'une photo produit e-commerce et qui fournit un score avec des conseils en francais et en darija.",
      "Le point central de ce projet est simple : je n'entraine aucun modele dans ce depot. La valeur du travail vient de l'architecture multimodale et de l'explicabilite."
    ],
  },
  {
    title: "Probleme vise",
    body: [
      "De nombreux vendeurs publient des photos floues, mal exposees, mal cadrees ou trop petites pour une fiche produit convaincante.",
      "L'objectif est donc de repondre a trois questions : la photo est-elle bonne, pourquoi, et que faut-il corriger concretement."
    ],
  },
  {
    title: "Hypothese principale",
    body: [
      "Le texte de l'annonce, c'est-a-dire le titre et la description, est la source de verite principale.",
      "Au lieu d'utiliser l'OCR comme signal central, le systeme prend ce texte deja disponible et l'utilise pour guider la selection du bon produit dans l'image."
    ],
  },
  {
    title: "Scope reduit",
    bullets: [
      "shoes",
      "clothing",
      "portable_electronics",
      "pas de meubles, bijoux, cosmetiques ou produits transparents dans cette version"
    ],
  },
  {
    title: "Pipeline actuel",
    body: [
      "Le pipeline est le suivant : text processor, candidate region generator, selector, analyzer, score global, recommandations, puis application Streamlit.",
      "Chaque bloc a un role precise et reste interpretable."
    ],
  },
  {
    title: "Text processor",
    bullets: [
      "nettoyage du texte",
      "extraction de couleur, categorie et marque",
      "embedding texte CLIP",
      "cache pour eviter les recalculs"
    ],
  },
  {
    title: "Candidate region generator",
    bullets: [
      "propose des regions candidates sans labels",
      "saliency OpenCV par defaut",
      "fallback contours si necessaire",
      "Grounding DINO disponible comme filet de securite, mais desactive par defaut"
    ],
  },
  {
    title: "Selector",
    body: [
      "Le selector compare chaque crop candidat au texte annonce.",
      "Il combine trois signaux : similarite CLIP image-texte, score visuel base sur taille et centralite, et coherence categorie."
    ],
    bullets: [
      "score = 0.6 * CLIP + 0.25 * visuel + 0.15 * categorie",
      "le score CLIP est le signal principal",
      "les details intermediaires sont conserves pour l'explicabilite"
    ],
  },
  {
    title: "Analyzer",
    bullets: [
      "sharpness",
      "exposure",
      "contrast",
      "color_balance",
      "effective_resolution",
      "coherence image / texte"
    ],
  },
  {
    title: "Explicabilite",
    body: [
      "Le systeme n'affiche pas seulement une note finale. Il montre le crop selectionne, les sous-scores et les recommandations.",
      "C'est important pour le jury, mais aussi pour l'utilisateur final qui doit comprendre quoi corriger."
    ],
  },
  {
    title: "Donnees et validation",
    body: [
      "Les bonnes images servent de references. Les mauvaises images sont produites par degradation controlee : flou, sous-exposition, surexposition, mauvais recadrage, basse resolution et compression JPEG.",
      "Cette logique donne une verite-terrain forte pour verifier que le bon critere baisse quand on applique la bonne degradation."
    ],
  },
  {
    title: "Message final",
    body: [
      "La contribution principale du projet n'est pas d'entrainer un nouveau modele, mais de construire une architecture zero-shot multimodale explicable.",
      "Le projet reste donc realiste pour un PFE de deux mois, defendable scientifiquement, et directement orienté usage e-commerce."
    ],
  },
];

const children = [
  title("Script oral - Pipeline zero-shot de qualite photo e-commerce"),
  body("Version alignee avec le projet actuel, sans OCR central et sans entrainement de modele."),
];

for (const section of sections) {
  children.push(heading(section.title));
  for (const line of section.body || []) {
    children.push(body(line));
  }
  for (const line of section.bullets || []) {
    children.push(bullet(line));
  }
}

const doc = new Document({
  sections: [{ children }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("script_oral.docx", buffer);
  console.log("script_oral.docx generated");
});
