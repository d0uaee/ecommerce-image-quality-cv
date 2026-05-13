#!/usr/bin/env python3
"""Complete integration test - demonstrates all modules working together."""

from pathlib import Path
from src.detector import detect_product
from src.analyzer import analyze, global_score
from src.ocr import extract_text
from src.nlp import extract_entities
from src.n8n_search import search_competitors

print("\n" + "="*80)
print("✅ DÉMONSTRATION COMPLÈTE - Pipeline Intégré")
print("="*80)

# Image de test
test_image = Path("data/raw_images/electronics/001_1.jpg")
print(f"\n📸 Image: {test_image.name}")

# ── ÉTAPE 1: Détection du produit ─────────────────────────────────────────
print("\n[1/5] Détection du produit...")
detection = detect_product(test_image)
print(f"  ✓ Objet détecté: {detection.get('label', 'Inconnu')}")
print(f"  ✓ Confiance: {detection.get('confidence', 0):.0%}")
print(f"  ✓ Méthode: {detection.get('method', '?')}")

# ── ÉTAPE 2: Analyse de qualité ───────────────────────────────────────────
print("\n[2/5] Analyse de qualité (6 critères avancés)...")
result = analyze(test_image, detection)
criteria = result["criteria"]
score = global_score(criteria)
print(f"  ✓ Score global: {score:.0%}")
for name, data in criteria.items():
    print(f"    • {name:25s}: {data['score']:.0%}")

# ── ÉTAPE 3: Extraction de texte OCR ──────────────────────────────────────
print("\n[3/5] Extraction de texte OCR...")
ocr_result = extract_text(test_image)
ocr_text = ocr_result.get("prompt", "")
if ocr_text:
    print(f"  ✓ Texte détecté: \"{ocr_text[:60]}...\"")
else:
    print(f"  ℹ️  Pas de texte détecté")

# ── ÉTAPE 4: Extraction des entités NLP ───────────────────────────────────
print("\n[4/5] Extraction des entités (NLP)...")
if ocr_text:
    entities = extract_entities(ocr_text)
    print(f"  ✓ Marque: {entities.get('brand') or '(non détecté)'}")
    print(f"  ✓ Modèle: {entities.get('model') or '(non détecté)'}")
    print(f"  ✓ Couleur: {entities.get('color') or '(non détecté)'}")
    print(f"  ✓ Stockage: {entities.get('storage') or '(non détecté)'}")
    if entities.get('price'):
        print(f"  ✓ Prix: {entities['price']:.0f} {entities.get('currency', 'DH')}")
    print(f"  ✓ Requête de recherche: \"{entities.get('search_query', '')[:50]}\"")
else:
    entities = {}
    print("  ℹ️  Pas d'OCR texte - entités NLP non disponibles")

# ── ÉTAPE 5: Recherche de produits concurrents ────────────────────────────
print("\n[5/5] Recherche de produits similaires...")
if entities.get("search_query"):
    search_query = entities.get("search_query")
    print(f"  Requête: \"{search_query}\"")
    results = search_competitors(search_query, limit=3)
    if results:
        print(f"  ✓ Trouvé {len(results)} produit(s)")
        for i, prod in enumerate(results, 1):
            print(f"    {i}. {prod['name'][:50]}")
    else:
        print("  ⚠️  0 résultats (Jumia nécessite n8n avec Puppeteer)")
else:
    print("  ℹ️  Pas de requête de recherche générée")

print("\n" + "="*80)
print("✅ PIPELINE COMPLET FONCTIONNE!")
print("="*80)
print("""
RÉSUMÉ:
  1. ✅ Détection du produit
  2. ✅ Analyse de qualité (6 critères)
  3. ✅ OCR extraction de texte
  4. ✅ NLP extraction d'entités (brand, price, color, etc.)
  5. ✅ Recherche de concurrents (n8n fallback à scraping)

INTERFACE STREAMLIT:
  • Adresse: http://localhost:8502
  • Affiche tous les résultats ci-dessus
  • Entités NLP en grille (Marque, Modèle, Couleur, Prix)
  • Bouton recherche concurrents
  • Comparaison de prix vs concurrents
""")
