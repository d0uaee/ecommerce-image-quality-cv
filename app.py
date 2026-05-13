"""Interface Streamlit — Analyse qualité d'images produit e-commerce."""

from __future__ import annotations

import csv
import io
import logging
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Qualité Image Produit",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Imports from project modules (cached so model loads once)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Chargement du modèle de détection…")
def _load_detector():
    from src.detector import detect_product, visualize_detection
    return detect_product, visualize_detection


@st.cache_resource(show_spinner=False)
def _load_analyzer():
    from src.analyzer import analyze, global_score
    return analyze, global_score


@st.cache_resource(show_spinner=False)
def _load_ocr():
    from src.ocr import extract_text
    return extract_text


@st.cache_resource(show_spinner=False)
def _load_nlp():
    from src.nlp import extract_entities
    return extract_entities


@st.cache_resource(show_spinner=False)
def _load_search():
    from src.n8n_search import search_competitors, download_competitor_images
    return search_competitors, download_competitor_images


@st.cache_resource(show_spinner=False)
def _load_caption():
    from src.caption import generate_listing
    return generate_listing


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITERION_LABELS = {
    "jpeg_artifacts":      "Artefacts JPEG",
    "lighting_uniformity": "Uniformité d'éclairage",
    "edge_quality":        "Qualité des contours",
    "color_consistency":   "Cohérence des couleurs",
    "effective_resolution": "Résolution effective",
    "clip_coherence":      "Cohérence image-texte",
}

RECOMMENDATIONS = {
    "jpeg_artifacts":      "Reprenez la photo avec un meilleur appareil ou activez le mode haute qualité",
    "lighting_uniformity": "Photographiez votre produit près d'une fenêtre ou ajoutez de la lumière",
    "edge_quality":        "Rapprochez-vous du produit et stabilisez votre appareil",
    "color_consistency":   "Photographiez sous une lumière blanche naturelle",
    "effective_resolution": "Utilisez un smartphone récent pour prendre la photo",
    "clip_coherence":      "Assurez-vous que la photo montre bien le produit de votre annonce",
}

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

SCORE_THRESHOLD_GOOD   = 0.75
SCORE_THRESHOLD_MEDIUM = 0.50
RECOMMENDATION_THRESHOLD = 0.70


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_color(score: float) -> str:
    if score >= SCORE_THRESHOLD_GOOD:
        return "#27ae60"    # green
    if score >= SCORE_THRESHOLD_MEDIUM:
        return "#e67e22"    # orange
    return "#e74c3c"        # red


def _score_label(score: float) -> str:
    if score >= SCORE_THRESHOLD_GOOD:
        return "Bonne qualité"
    if score >= SCORE_THRESHOLD_MEDIUM:
        return "Qualité moyenne"
    return "Mauvaise qualité"


def _run_analysis(
    image_bytes: bytes,
    filename: str,
    text_prompt: str | None = None,
    entities: dict | None = None,
) -> dict | None:
    """
    Save bytes to a temp file, run detection + analysis + caption, return full report.
    Returns None on unrecoverable error.
    """
    detect_product, visualize_detection = _load_detector()
    analyze, global_score = _load_analyzer()

    suffix = Path(filename).suffix or ".jpg"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(image_bytes)
            tmp_src = Path(f.name)

        tmp_vis = tmp_src.with_name(tmp_src.stem + "_vis.jpg")

        detection = detect_product(tmp_src, text_prompt=text_prompt)
        result    = analyze(tmp_src, detection, text_prompt=text_prompt)
        result["detection"] = detection
        result["global"]    = global_score(result["criteria"])

        # Build annotated image
        visualize_detection(tmp_src, tmp_vis, text_prompt=text_prompt)
        if tmp_vis.exists():
            result["vis_image"] = Image.open(tmp_vis).copy()
            tmp_vis.unlink(missing_ok=True)
        else:
            result["vis_image"] = Image.open(tmp_src).convert("RGB")

        # Caption / listing generation (before tmp_src is deleted)
        if entities is not None:
            try:
                generate_listing = _load_caption()
                result["listing"] = generate_listing(tmp_src, entities)
            except Exception as exc:
                logging.warning("Listing generation failed: %s", exc)
                result["listing"] = None

        tmp_src.unlink(missing_ok=True)
        return result

    except Exception as exc:
        logging.exception("Analyse échouée pour %s: %s", filename, exc)
        return None


def _criterion_bar(name: str, data: dict):
    """Render one criterion row: label | progress bar | score | message."""
    label = CRITERION_LABELS.get(name, name)
    score = data["score"]
    color = _score_color(score)

    col_label, col_bar, col_score, col_msg = st.columns([2, 3, 1, 3])
    with col_label:
        st.markdown(f"**{label}**")
    with col_bar:
        # HTML progress bar (st.progress doesn't support custom colours)
        pct = int(score * 100)
        st.markdown(
            f"""
            <div style="background:#ecf0f1;border-radius:6px;height:16px;margin-top:6px">
              <div style="width:{pct}%;background:{color};height:16px;border-radius:6px"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_score:
        st.markdown(
            f"<span style='color:{color};font-weight:bold'>{score:.0%}</span>",
            unsafe_allow_html=True,
        )
    with col_msg:
        st.caption(data["message"])


def _render_listing(listing: dict):
    """Render the generated French product listing with editable fields."""
    st.subheader("Description suggérée pour Jumia")
    st.caption("Généré automatiquement — modifiez avant de publier")

    st.text_input("Titre", value=listing.get("title", ""), key="listing_title")
    st.text_area("Description", value=listing.get("description", ""), height=120, key="listing_desc")

    keywords = listing.get("keywords", [])
    if keywords:
        tags_html = " ".join(
            f"<span style='background:#2980b9;color:white;padding:2px 10px;"
            f"border-radius:12px;font-size:12px;margin:2px'>{kw}</span>"
            for kw in keywords
        )
        st.markdown(f"**Mots-clés** : {tags_html}", unsafe_allow_html=True)


def _render_nlp_entities(entities: dict):
    """Display extracted product entities from NLP module."""
    st.subheader("Entités détectées")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if entities.get("brand"):
            st.metric("Marque", entities["brand"])
        else:
            st.caption("💭 Marque : inconnue")
    
    with col2:
        if entities.get("model"):
            st.caption(f"**Modèle**\n{entities['model'][:30]}..." if len(entities['model']) > 30 else f"**Modèle**\n{entities['model']}")
        else:
            st.caption("💭 Modèle : inconnue")
    
    with col3:
        if entities.get("color"):
            st.caption(f"**Couleur**\n{entities['color']}")
        else:
            st.caption("💭 Couleur : inconnue")
    
    with col4:
        if entities.get("price"):
            price_str = f"{entities['price']:.0f} {entities.get('currency', 'DH')}"
            st.metric("Prix", price_str)
        else:
            st.caption("💭 Prix : inconnu")


def _render_competitor_comparison(entities: dict):
    """Display competitor products comparison section."""
    search_competitors, download_competitor_images = _load_search()

    search_query = (
        entities.get("search_query", "")
        or st.session_state.get("_text_prompt", "")
    )

    st.subheader("Analyse concurrentielle")
    if not search_query:
        search_query = st.text_input("Terme de recherche Jumia", placeholder="ex : chargeur portable Samsung")
        if not search_query:
            return
    else:
        st.caption(f"Recherche de produits similaires : *{search_query}*")
    
    if st.button("🔍 Rechercher produits similaires sur Jumia", key="search_competitors"):
        with st.spinner("Recherche de concurrents en cours…"):
            try:
                results = search_competitors(search_query, limit=5)
                
                if not results:
                    st.warning("Aucun produit concurrent trouvé. (Jumia nécessite n8n avec Puppeteer)")
                else:
                    st.success(f"Trouvé {len(results)} produit(s) similaire(s)")
                    
                    # Display comparison grid
                    user_price = entities.get("price")
                    cols = st.columns(min(3, len(results)))
                    
                    for idx, (col, product) in enumerate(zip(cols, results)):
                        with col:
                            st.markdown(f"**{idx+1}. {product['name'][:50]}**")
                            
                            # Price comparison
                            prod_price = product.get("price")
                            if prod_price and user_price:
                                diff = prod_price - user_price
                                if diff < 0:
                                    st.markdown(f"💚 **{prod_price:.0f} DH** (-{abs(diff):.0f} DH)")
                                elif diff > 0:
                                    st.markdown(f"🔴 **{prod_price:.0f} DH** (+{diff:.0f} DH)")
                                else:
                                    st.markdown(f"💛 **{prod_price:.0f} DH** (identique)")
                            elif prod_price:
                                st.markdown(f"💰 **{prod_price:.0f} DH**")
                            
                            if product.get("image_url"):
                                st.caption(f"[Lien produit]({product.get('product_url', '#')})")
                    
                    st.markdown("*Comparaison de prix vs votre produit détecté*")
            
            except Exception as exc:
                logging.exception("Erreur lors de la recherche concurrente: %s", exc)
                st.error(f"Erreur : {exc}")


def _render_single_analysis(report: dict, nlp_entities: dict | None = None):
    """Render the left/right layout for a single-image analysis."""
    col_img, col_dash = st.columns([1, 1], gap="large")

    # ── Left: images ────────────────────────────────────────────────────────
    with col_img:
        st.subheader("Image analysée")
        tab_orig, tab_det = st.tabs(["Original", "Détection"])
        with tab_orig:
            st.image(report.get("vis_image"), use_container_width=True)
        with tab_det:
            vis = report.get("vis_image")
            if vis is not None:
                st.image(vis, use_container_width=True)

        det = report.get("detection", {})
        method = det.get("method", "")
        if method == "grounding_dino":
            badge = "<span style='background:#27ae60;color:white;padding:2px 8px;border-radius:10px;font-size:12px'>DINO ✓</span>"
        elif method == "fallback":
            badge = "<span style='background:#95a5a6;color:white;padding:2px 8px;border-radius:10px;font-size:12px'>Fallback</span>"
        else:
            badge = ""

        if det.get("success") and det.get("label"):
            label = det["label"]
            conf  = det["confidence"]
            if conf > 0:
                st.markdown(f"Objet détecté : **{label}** ({conf:.0%}) {badge}", unsafe_allow_html=True)
            else:
                st.markdown(f"Détection par soustraction de fond {badge}", unsafe_allow_html=True)
        else:
            if badge:
                st.markdown(badge, unsafe_allow_html=True)
            st.warning("Aucun produit détecté — résultats basés sur l'image entière.")

    # ── Right: dashboard ────────────────────────────────────────────────────
    with col_dash:
        score  = report["global"]
        color  = _score_color(score)
        slabel = _score_label(score)

        st.subheader("Score de qualité")
        st.markdown(
            f"""
            <div style="text-align:center;padding:20px 0 10px">
              <span style="font-size:72px;font-weight:900;color:{color}">{score:.0%}</span><br>
              <span style="font-size:20px;color:{color}">{slabel}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("**Détail des critères**")
        for name, data in report["criteria"].items():
            _criterion_bar(name, data)

        # ── Recommendations ─────────────────────────────────────────────────
        poor = {
            name: data
            for name, data in report["criteria"].items()
            if data["score"] < RECOMMENDATION_THRESHOLD
        }
        if poor:
            st.divider()
            st.markdown("**Recommandations**")
            for name in poor:
                rec = RECOMMENDATIONS.get(name, "")
                if rec:
                    criterion_score = poor[name]["score"]
                    color_rec = _score_color(criterion_score)
                    st.markdown(
                        f"<span style='color:{color_rec}'>●</span> {rec}",
                        unsafe_allow_html=True,
                    )
        else:
            st.divider()
            st.success("Tous les critères sont satisfaisants.")
    
    # ── NLP Entities and Competitor Comparison ──────────────────────────────
    if nlp_entities:
        st.divider()
        _render_nlp_entities(nlp_entities)
        st.divider()
        _render_competitor_comparison(nlp_entities)

    # ── Generated listing ────────────────────────────────────────────────────
    listing = report.get("listing")
    if listing:
        # Reset widget session state so fresh values always display
        for k in ("listing_title", "listing_desc"):
            st.session_state.pop(k, None)
        st.divider()
        _render_listing(listing)


# ---------------------------------------------------------------------------
# Batch analysis helpers
# ---------------------------------------------------------------------------

def _worst_criterion(criteria: dict) -> str:
    if not criteria:
        return "-"
    worst = min(criteria, key=lambda k: criteria[k]["score"])
    return CRITERION_LABELS.get(worst, worst)


def _batch_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["fichier", "score_global", "pire_critere"] + list(CRITERION_LABELS.keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")   # utf-8-sig for Excel compatibility


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    st.title("Analyse qualité d'images produit")
    st.caption("Système d'analyse automatique pour images e-commerce — projet universitaire")

    # ── Single image upload ─────────────────────────────────────────────────
    st.header("Analyse d'une image")
    uploaded = st.file_uploader(
        "Charger une image produit",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        key="single_upload",
    )

    if uploaded is not None:
        img_bytes = uploaded.read()
        file_key  = f"{uploaded.name}_{len(img_bytes)}"

        # Run OCR and NLP once per uploaded file and cache results in session_state
        if st.session_state.get("_ocr_key") != file_key:
            suffix = Path(uploaded.name).suffix or ".jpg"
            try:
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                    f.write(img_bytes)
                    tmp_ocr = Path(f.name)
                extract_text = _load_ocr()
                ocr = extract_text(tmp_ocr)
                ocr_text = ocr.get("prompt", "")
                st.session_state["_ocr_prompt"] = ocr_text
                
                # Extract NLP entities from full OCR text (all detected blocks joined)
                text_for_nlp = " ".join(ocr.get("text_found", [])) or ocr_text
                if text_for_nlp:
                    try:
                        extract_entities = _load_nlp()
                        nlp_result = extract_entities(text_for_nlp)
                        st.session_state["_nlp_entities"] = nlp_result
                    except Exception as e:
                        logging.warning("NLP extraction failed: %s", e)
                        st.session_state["_nlp_entities"] = {}
                else:
                    st.session_state["_nlp_entities"] = {}
            except Exception:
                st.session_state["_ocr_prompt"] = ""
                st.session_state["_nlp_entities"] = {}
            finally:
                try:
                    tmp_ocr.unlink(missing_ok=True)
                except Exception:
                    pass
            st.session_state["_ocr_key"]   = file_key
            st.session_state["_ocr_bytes"] = img_bytes
            st.session_state["_report"]    = None

        detected_prompt = st.session_state.get("_ocr_prompt", "")
        text_prompt = st.text_input(
            "Produit détecté / décrit",
            value=detected_prompt,
            placeholder="ex: téléphone Samsung, chaise en bois…",
            key="prompt_input",
        )

        if st.button("Analyser", key="single_run"):
            with st.spinner("Analyse en cours…"):
                report = _run_analysis(
                    st.session_state.get("_ocr_bytes", img_bytes),
                    uploaded.name,
                    text_prompt=text_prompt.strip() or None,
                    entities=st.session_state.get("_nlp_entities") or {},
                )
            st.session_state["_report"] = report
            st.session_state["_text_prompt"] = text_prompt.strip()

        report = st.session_state.get("_report")
        if report is not None:
            if not report.get("success"):
                st.error("Impossible d'analyser cette image. Vérifiez qu'elle n'est pas corrompue.")
            else:
                nlp_entities = st.session_state.get("_nlp_entities", {})
                _render_single_analysis(report, nlp_entities=nlp_entities or None)

    st.divider()

    # ── Batch analysis ──────────────────────────────────────────────────────
    st.header("Analyse par lot")

    folder_input = st.text_input(
        "Chemin du dossier contenant les images",
        placeholder="ex : data/raw_images/electronics",
        key="batch_folder",
    )

    if st.button("Lancer l'analyse par lot", key="batch_run"):
        folder = Path(folder_input.strip()) if folder_input.strip() else None

        if folder is None or not folder.exists():
            st.error("Dossier introuvable. Vérifiez le chemin.")
        elif not folder.is_dir():
            st.error("Le chemin indiqué n'est pas un dossier.")
        else:
            image_files = sorted(
                p for p in folder.iterdir()
                if p.suffix.lower() in SUPPORTED_EXTENSIONS
            )
            if not image_files:
                st.warning("Aucune image trouvée dans ce dossier.")
            else:
                st.info(f"{len(image_files)} image(s) trouvée(s) — analyse en cours…")
                progress = st.progress(0)
                status   = st.empty()
                rows     = []

                for i, img_path in enumerate(image_files):
                    status.caption(f"Analyse : {img_path.name} ({i+1}/{len(image_files)})")
                    try:
                        img_bytes = img_path.read_bytes()
                        report    = _run_analysis(img_bytes, img_path.name)
                    except Exception:
                        report = None

                    if report and report.get("success"):
                        criteria = report["criteria"]
                        row = {
                            "fichier":       img_path.name,
                            "score_global":  f"{report['global']:.3f}",
                            "pire_critere":  _worst_criterion(criteria),
                        }
                        for crit_key in CRITERION_LABELS:
                            row[crit_key] = f"{criteria[crit_key]['score']:.3f}"
                    else:
                        row = {
                            "fichier":      img_path.name,
                            "score_global": "erreur",
                            "pire_critere": "-",
                            **{k: "-" for k in CRITERION_LABELS},
                        }
                    rows.append(row)
                    progress.progress((i + 1) / len(image_files))

                status.empty()
                progress.empty()
                st.success(f"Analyse terminée — {len(rows)} image(s) traitée(s).")

                # Summary table
                st.subheader("Résultats")
                col_headers = (
                    ["Fichier", "Score global", "Pire critère"]
                    + list(CRITERION_LABELS.values())
                )
                display_rows = [
                    [
                        r["fichier"],
                        r["score_global"],
                        r["pire_critere"],
                        *[r[k] for k in CRITERION_LABELS],
                    ]
                    for r in rows
                ]
                st.dataframe(
                    data=display_rows,
                    column_config={i: col_headers[i] for i in range(len(col_headers))},
                    use_container_width=True,
                    hide_index=True,
                )

                # CSV download
                st.download_button(
                    label="Télécharger CSV",
                    data=_batch_csv(rows),
                    file_name="analyse_qualite.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
