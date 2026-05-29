from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from config import ASSISTANT_CONFIG, DATASET_DIR, RAW_IMAGES_DIR, STREAMLIT_DEFAULTS, STREAMLIT_THEME
from src.analyzer import analyze
from src.candidate_region_generator import detect_with_dino, propose_regions
from src.listing_assistant import generate_listing_assistance
from src.selector import select_product
from src.text_processor import process_text


st.set_page_config(
    page_title=STREAMLIT_DEFAULTS["page_title"],
    layout=STREAMLIT_DEFAULTS["layout"],
)


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
METADATA_CSV = DATASET_DIR / "metadata.csv"

CRITERION_LABELS = {
    "sharpness": "Nettete",
    "exposure": "Exposition",
    "contrast": "Contraste",
    "color_balance": "Balance couleurs",
    "effective_resolution": "Resolution effective",
    "framing": "Cadrage produit",
    "coherence": "Coherence image/texte",
}


def _init_session_state() -> None:
    st.session_state.setdefault("analysis_history", [])


def _push_history(entry: dict[str, Any]) -> None:
    history = list(st.session_state.get("analysis_history", []))
    history.insert(0, entry)
    st.session_state["analysis_history"] = history[: ASSISTANT_CONFIG["history_limit"]]


def _score_color(score: float) -> str:
    if score >= 75:
        return "#1f7a3a"
    if score >= 50:
        return "#d97a16"
    return "#c0392b"


def _inject_premium_styles() -> None:
    theme = STREAMLIT_THEME
    st.markdown(
        f"""
        <style>
        :root {{
            --app-surface: {theme['surface']};
            --app-surface-alt: {theme['surface_alt']};
            --app-card: {theme['card']};
            --app-border: {theme['border']};
            --app-text: {theme['text']};
            --app-muted: {theme['muted']};
            --app-accent: {theme['accent']};
            --app-accent-soft: {theme['accent_soft']};
        }}
        .stApp {{
            background:
                radial-gradient(circle at top left, #fff7ea 0%, {theme['surface']} 38%),
                linear-gradient(180deg, {theme['surface']} 0%, #f7f0e7 100%);
            color: {theme['text']};
        }}
        .block-container {{
            padding-top: 1.6rem;
            padding-bottom: 2.6rem;
        }}
        .app-hero {{
            border: 1px solid {theme['border']};
            background: linear-gradient(135deg, {theme['card']} 0%, {theme['surface_alt']} 100%);
            padding: 18px 20px;
            border-radius: 22px;
            box-shadow: 0 12px 35px rgba(54, 35, 13, 0.08);
            margin-bottom: 1rem;
        }}
        .app-badge {{
            display: inline-block;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            background: {theme['accent_soft']};
            color: {theme['accent']};
            margin-bottom: 0.6rem;
        }}
        .soft-card {{
            border: 1px solid {theme['border']};
            background: {theme['card']};
            border-radius: 20px;
            padding: 14px 16px;
            box-shadow: 0 10px 28px rgba(54, 35, 13, 0.06);
        }}
        .metric-card {{
            border: 1px solid {theme['border']};
            background: rgba(255,255,255,0.72);
            backdrop-filter: blur(10px);
            border-radius: 22px;
            padding: 18px;
            box-shadow: 0 14px 34px rgba(54, 35, 13, 0.08);
        }}
        .assistant-grid {{
            display:grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
        }}
        .tiny-label {{
            color: {theme['muted']};
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .history-note {{
            color: {theme['muted']};
            font-size: 0.9rem;
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #f7efe4 0%, #f2e8da 100%);
            border-right: 1px solid {theme['border']};
        }}
        [data-testid="stSidebar"] * {{
            color: {theme['text']} !important;
        }}
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stDateInput input,
        .stTimeInput input {{
            background: #fffaf2 !important;
            color: {theme['text']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 14px !important;
        }}
        .stTextInput label,
        .stTextArea label,
        .stFileUploader label,
        .stRadio label,
        .stSelectbox label,
        .stToggle label,
        .stDownloadButton label,
        .stMarkdown,
        .stCaption,
        .stSubheader,
        .stHeader,
        .stForm label {{
            color: {theme['text']} !important;
        }}
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: {theme['muted']} !important;
            opacity: 0.9 !important;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background: #fffaf2 !important;
            border: 1px dashed {theme['border']} !important;
            color: {theme['text']} !important;
        }}
        [data-testid="stFileUploaderDropzone"] * {{
            color: {theme['text']} !important;
        }}
        button[kind="primary"],
        .stButton button,
        .stDownloadButton button {{
            background: linear-gradient(135deg, {theme['accent']} 0%, #cb7a3d 100%) !important;
            color: #fff7ef !important;
            border: none !important;
            border-radius: 14px !important;
            box-shadow: 0 10px 24px rgba(179, 100, 43, 0.22);
        }}
        .stButton button:hover,
        .stDownloadButton button:hover {{
            filter: brightness(1.03);
        }}
        [data-testid="stRadio"] > div {{
            gap: 0.5rem;
        }}
        [data-testid="stRadio"] label {{
            background: #fffaf2;
            border: 1px solid {theme['border']};
            border-radius: 999px;
            padding: 0.45rem 0.8rem;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.45rem;
        }}
        .stTabs [data-baseweb="tab"] {{
            background: #fffaf2;
            border: 1px solid {theme['border']};
            border-radius: 999px;
            color: {theme['text']} !important;
        }}
        .stTabs [aria-selected="true"] {{
            background: {theme['accent_soft']} !important;
            border-color: {theme['accent']} !important;
        }}
        [data-testid="stAlert"] {{
            border-radius: 16px;
            border: 1px solid {theme['border']};
        }}
        [data-testid="stInfo"] {{
            background: #eef5fc !important;
            color: {theme['text']} !important;
        }}
        [data-testid="stWarning"] {{
            background: #fff5e6 !important;
            color: {theme['text']} !important;
        }}
        [data-testid="stError"] {{
            background: #fdeeee !important;
            color: {theme['text']} !important;
        }}
        [data-testid="stDataFrame"] * {{
            color: {theme['text']} !important;
        }}
        .st-emotion-cache-1r6slb0,
        .st-emotion-cache-16idsys p,
        .st-emotion-cache-10trblm {{
            color: {theme['text']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _load_rgb_image(path: Path) -> np.ndarray:
    image_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise FileNotFoundError(f"Impossible de lire l'image: {path}")
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def _decode_uploaded_image(uploaded_file) -> np.ndarray:
    image = Image.open(uploaded_file).convert("RGB")
    return np.array(image)


@st.cache_data(show_spinner=False)
def _load_dataset_announcements() -> pd.DataFrame:
    if not METADATA_CSV.exists():
        return pd.DataFrame(columns=["title", "description", "image_path"])

    frame = pd.read_csv(METADATA_CSV)
    required = {"title", "description", "image_path"}
    if not required.issubset(frame.columns):
        return pd.DataFrame(columns=["title", "description", "image_path"])
    return frame.fillna("")


def _annotate_selected_region(image_rgb: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    annotated = image_rgb.copy()
    x1, y1, x2, y2 = bbox
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (34, 139, 230), 4)
    cv2.putText(
        annotated,
        "Crop selectionne",
        (x1, max(24, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (34, 139, 230),
        2,
        cv2.LINE_AA,
    )
    return annotated


def _annotate_candidates(image_rgb: np.ndarray, candidates: list[dict[str, Any]]) -> np.ndarray:
    annotated = image_rgb.copy()
    for idx, candidate in enumerate(candidates, start=1):
        x1, y1, x2, y2 = candidate["bbox"]
        color = (40, 167, 69) if idx == 1 else (255, 165, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated,
            f"#{idx} {candidate['score_total']:.2f}",
            (x1, max(20, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
    return annotated


def _render_score_bar(label: str, score: float, message: str) -> None:
    color = _score_color(score)
    st.markdown(
        f"""
        <div style="margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;font-weight:600">
            <span>{label}</span>
            <span style="color:{color}">{score:.1f}/100</span>
          </div>
          <div style="background:#e9ecef;border-radius:999px;height:10px;margin:6px 0 4px">
            <div style="width:{score:.0f}%;background:{color};height:10px;border-radius:999px"></div>
          </div>
          <div style="font-size:0.9rem;color:#5f6368">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_status_badges() -> None:
    assistant_state = "n8n actif" if ASSISTANT_CONFIG["enable_n8n"] else "fallback local"
    st.markdown(
        f"""
        <div class="soft-card" style="margin-bottom:1rem">
          <div class="assistant-grid">
            <div>
              <div class="tiny-label">Pipeline principal</div>
              <div>Zero-shot explicable, sans OCR critique</div>
            </div>
            <div>
              <div class="tiny-label">Assistant annonce</div>
              <div>{assistant_state}</div>
            </div>
            <div>
              <div class="tiny-label">Historique session</div>
              <div>{len(st.session_state.get('analysis_history', []))} entree(s)</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _history_dataframe() -> pd.DataFrame:
    history = st.session_state.get("analysis_history", [])
    if not history:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for item in history:
        rows.append(
            {
                "timestamp": item.get("timestamp", ""),
                "mode": item.get("mode", ""),
                "label": item.get("label", ""),
                "score": item.get("score"),
                "category": item.get("category"),
                "source": item.get("source", ""),
            }
        )
    return pd.DataFrame(rows)


def _render_history_block() -> None:
    history = st.session_state.get("analysis_history", [])
    if not history:
        st.info("L'historique apparaitra ici apres les premieres analyses.")
        return

    tabs = st.tabs(["Historique", "Comparaison avant/apres"])
    with tabs[0]:
        st.dataframe(_history_dataframe(), use_container_width=True)

    with tabs[1]:
        options = {
            f"{idx + 1:02d} | {item.get('timestamp', '')} | {item.get('label', '')}": idx
            for idx, item in enumerate(history)
        }
        if len(options) < 2:
            st.caption("Il faut au moins deux analyses dans l'historique pour comparer.")
            return
        labels = list(options.keys())
        before_label = st.selectbox("Avant", labels, index=min(1, len(labels) - 1), key="compare_before")
        after_label = st.selectbox("Apres", labels, index=0, key="compare_after")
        before = history[options[before_label]]
        after = history[options[after_label]]

        col_before, col_after = st.columns(2)
        with col_before:
            st.markdown("**Avant**")
            st.markdown(
                f"""
                <div class="soft-card">
                  <div class="tiny-label">{before.get('mode','')}</div>
                  <h4 style="margin:0.35rem 0">{before.get('label','')}</h4>
                  <div class="history-note">Score : {before.get('score','-')} | Categorie : {before.get('category','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.json(before)
        with col_after:
            st.markdown("**Apres**")
            st.markdown(
                f"""
                <div class="soft-card">
                  <div class="tiny-label">{after.get('mode','')}</div>
                  <h4 style="margin:0.35rem 0">{after.get('label','')}</h4>
                  <div class="history-note">Score : {after.get('score','-')} | Categorie : {after.get('category','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.json(after)


def _build_user_report(
    title: str,
    description: str,
    analysis: dict[str, Any] | None = None,
    assistant_payload: dict[str, Any] | None = None,
) -> str:
    lines = ["# Rapport utilisateur", ""]
    if title.strip():
        lines.append(f"- Titre source : {title}")
    if description.strip():
        lines.append(f"- Description source : {description}")
    if analysis is not None:
        lines.extend(
            [
                "",
                "## Evaluation qualite",
                "",
                f"- Score global : {analysis['global_score']:.1f}/100",
                f"- Resume : {analysis['summary_fr']}",
                "",
                "### Sous-scores",
            ]
        )
        for key, payload in analysis["criteria"].items():
            lines.append(f"- {CRITERION_LABELS.get(key, key)} : {payload['score']:.1f}/100")
        lines.append("")
        lines.append("### Recommandations")
        for item in analysis["advice_fr"]:
            lines.append(f"- {item}")
    if assistant_payload is not None:
        lines.extend(
            [
                "",
                "## Assistant annonce",
                "",
                f"- Source : {assistant_payload.get('source', 'inconnue')}",
                f"- Categorie estimee : {assistant_payload.get('category', '')}",
                f"- Titre propose : {assistant_payload.get('title', '')}",
                "",
                "### Description proposee",
                assistant_payload.get("description", ""),
                "",
                "### Attributs",
            ]
        )
        for attribute in assistant_payload.get("attributes", []):
            lines.append(f"- {attribute}")
        seller = assistant_payload.get("seller_recommendations", {})
        lines.append("")
        lines.append("### Informations a completer")
        for item in seller.get("missing_info", []):
            lines.append(f"- {item}")
        lines.append("")
        lines.append("### Checklist annonce")
        for item in seller.get("listing_checklist", []):
            lines.append(f"- {item}")
        price_hint = seller.get("price_hint", {})
        if price_hint:
            lines.append("")
            lines.append(
                f"### Prix indicatif prudent\n- {price_hint.get('min')} a {price_hint.get('max')} {price_hint.get('currency', '')}"
            )
            lines.append(f"- Note : {price_hint.get('note', '')}")
    return "\n".join(lines)


def _run_pipeline(image_rgb: np.ndarray, title: str, description: str) -> dict[str, Any]:
    text_data = process_text(title, description)
    candidate_boxes = propose_regions(image_rgb[:, :, ::-1])
    selection = select_product(image_rgb[:, :, ::-1], candidate_boxes, text_data)
    analysis = analyze(
        selection["selected_crop"],
        text_data=text_data,
        selected_bbox=selection["selected_bbox"],
        original_shape=image_rgb.shape,
    )
    return {
        "text_data": text_data,
        "candidate_boxes": candidate_boxes,
        "selection": selection,
        "analysis": analysis,
    }


def _single_image_controls() -> tuple[np.ndarray | None, str, str, str]:
    source_mode = st.radio(
        "Source annonce",
        ["Upload manuel", "Annonce du dataset"],
        horizontal=True,
    )

    if source_mode == "Upload manuel":
        uploaded = st.file_uploader("Image produit", type=["jpg", "jpeg", "png", "webp", "bmp"])
        title = st.text_input("Titre", placeholder="Ex: Nike Air Max homme noir")
        description = st.text_area(
            "Description",
            placeholder="Ex: Chaussure de running confortable, semelle visible, style sport.",
            height=110,
        )
        if uploaded is None:
            return None, title, description, source_mode
        return _decode_uploaded_image(uploaded), title, description, source_mode

    dataset_df = _load_dataset_announcements()
    if dataset_df.empty:
        st.warning("Aucune annonce dataset exploitable dans dataset/metadata.csv.")
        return None, "", "", source_mode

    options = {
        f"{idx + 1:03d} | {row['title'][:80]}": idx
        for idx, row in dataset_df.head(200).iterrows()
    }
    selected_label = st.selectbox("Annonce du dataset", list(options.keys()))
    row = dataset_df.iloc[options[selected_label]]
    image_path = Path(row["image_path"])
    if not image_path.is_absolute():
        image_path = Path.cwd() / image_path
    if not image_path.exists():
        st.error(f"Image introuvable: {image_path}")
        return None, row["title"], row["description"], source_mode
    return _load_rgb_image(image_path), row["title"], row["description"], source_mode


def _render_single_mode() -> None:
    image_rgb, title, description, _ = _single_image_controls()
    debug_mode = st.toggle("Mode debug", value=False)

    if image_rgb is None:
        st.info("Charge une image ou choisis une annonce du dataset pour lancer l'analyse.")
        return

    if not title.strip() and not description.strip():
        st.warning("Le titre ou la description sont necessaires pour la coherence texte/image.")
        return

    with st.spinner("Analyse zero-shot en cours..."):
        report = _run_pipeline(image_rgb, title, description)

    selection = report["selection"]
    analysis = report["analysis"]
    text_data = report["text_data"]

    selected_bbox = tuple(selection["selected_bbox"])
    selected_crop_rgb = cv2.cvtColor(selection["selected_crop"], cv2.COLOR_BGR2RGB)
    highlighted = _annotate_selected_region(image_rgb, selected_bbox)

    st.subheader("Crop selectionne")
    col_crop, col_context = st.columns([1.1, 1], gap="large")
    with col_crop:
        st.image(selected_crop_rgb, use_container_width=True)
    with col_context:
        st.image(highlighted, use_container_width=True)
        st.caption("Le coeur du systeme est ici : le produit effectivement retenu par le selector.")

    st.markdown(
        f"""
        <div class="metric-card" style="padding:18px 20px;margin:14px 0 18px">
          <div class="tiny-label">Score global</div>
          <div style="font-size:3.2rem;font-weight:800;color:{_score_color(analysis['global_score'])};line-height:1.05">
            {analysis['global_score']:.1f}/100
          </div>
          <div style="font-size:1rem;color:{STREAMLIT_THEME['muted']};margin-top:6px">{analysis['summary_fr']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Criteres")
    for criterion_name, payload in analysis["criteria"].items():
        _render_score_bar(
            CRITERION_LABELS.get(criterion_name, criterion_name),
            payload["score"],
            payload["message_fr"],
        )

    coherence = analysis["criteria"]["coherence"]
    st.subheader("Coherence image / texte")
    st.write(f"Score coherence : `{coherence['score']:.1f}/100`")
    st.json(coherence["raw_value"])

    st.subheader("Recommandations")
    rec_col_fr, rec_col_darija = st.columns(2)
    with rec_col_fr:
        st.markdown("**Francais**")
        for item in analysis["advice_fr"]:
            st.write(f"- {item}")
    with rec_col_darija:
        st.markdown("**Darija**")
        for item in analysis["advice_darija"]:
            st.write(f"- {item}")

    if debug_mode:
        st.subheader("Debug")
        debug_tabs = st.tabs(["Regions candidates", "Scores selection", "Texte", "DINO fallback"])
        with debug_tabs[0]:
            st.image(_annotate_candidates(image_rgb, selection["candidates"]), use_container_width=True)
        with debug_tabs[1]:
            st.json(selection["candidates"])
        with debug_tabs[2]:
            st.json(
                {
                    "clean_text": text_data["clean_text"],
                    "brand": text_data["brand"],
                    "category": text_data["category"],
                    "color": text_data["color"],
                }
            )
        with debug_tabs[3]:
            dino_regions = detect_with_dino(image_rgb[:, :, ::-1], text_data["clean_text"] or "product")
            st.json(dino_regions if dino_regions else {"status": "DINO indisponible ou aucune region"})

    _push_history(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "analyse",
            "label": title[:80] or "analyse manuelle",
            "score": round(float(analysis["global_score"]), 2),
            "category": text_data.get("category"),
            "source": "evaluation",
        }
    )

    report_md = _build_user_report(title, description, analysis=analysis)
    st.download_button(
        "Exporter rapport utilisateur",
        data=report_md.encode("utf-8"),
        file_name="rapport_utilisateur.md",
        mime="text/markdown",
    )
    with st.expander("Historique et comparaison"):
        _render_history_block()


def _render_assistant_mode() -> None:
    image_rgb, title, description, source_mode = _single_image_controls()
    seller_hints = st.text_area(
        "Infos vendeur optionnelles",
        value=description if source_mode == "Annonce du dataset" else "",
        height=110,
        placeholder="Ex: marque, etat, taille, capacite, public cible...",
    )

    if image_rgb is None:
        st.info("Charge une image ou choisis une annonce du dataset pour generer une annonce assistee.")
        return

    with st.spinner("Generation de l'assistance annonce..."):
        payload = generate_listing_assistance(image_rgb, seller_hints=seller_hints or title)

    st.markdown(
        f"""
        <div class="app-hero">
          <div class="app-badge">Assistant annonce</div>
          <div class="tiny-label">Source assistant</div>
          <div style="color:{STREAMLIT_THEME['muted']};margin-bottom:8px">{payload.get('source', 'inconnue')}</div>
          <h2 style="margin:0 0 0.35rem 0">{payload.get('title', 'Titre indisponible')}</h2>
          <div style="color:{STREAMLIT_THEME['muted']}">Categorie estimee : {payload.get('category', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Description proposee")
    st.markdown(f'<div class="soft-card">{payload.get("description", "")}</div>', unsafe_allow_html=True)

    col_meta, col_actions = st.columns([1.2, 1])
    with col_meta:
        st.markdown("**Attributs detectes**")
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        for attribute in payload.get("attributes", []):
            st.write(f"- {attribute}")
        st.markdown("**Categorie estimee**")
        st.write(payload.get("category", ""))
        st.markdown("</div>", unsafe_allow_html=True)
    with col_actions:
        seller = payload.get("seller_recommendations", {})
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown("**Infos manquantes**")
        for item in seller.get("missing_info", []):
            st.write(f"- {item}")
        st.markdown("**Checklist annonce**")
        for item in seller.get("listing_checklist", []):
            st.write(f"- {item}")
        price_hint = seller.get("price_hint", {})
        if price_hint:
            st.markdown("**Prix indicatif prudent**")
            st.write(
                f"{price_hint.get('min', '?')} - {price_hint.get('max', '?')} {price_hint.get('currency', '')}"
            )
            st.caption(price_hint.get("note", ""))
        st.markdown("</div>", unsafe_allow_html=True)

    _push_history(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "assistant",
            "label": payload.get("title", title[:80] or "annonce assistee"),
            "score": None,
            "category": payload.get("category"),
            "source": payload.get("source", "assistant"),
        }
    )

    report_md = _build_user_report(title, description, assistant_payload=payload)
    json_bytes = pd.Series(payload).to_json(force_ascii=False, indent=2).encode("utf-8")
    st.download_button(
        "Exporter rapport assistant",
        data=report_md.encode("utf-8"),
        file_name="assistant_annonce.md",
        mime="text/markdown",
        key="assistant_report_md",
    )
    st.download_button(
        "Exporter JSON assistant",
        data=json_bytes,
        file_name="assistant_annonce.json",
        mime="application/json",
        key="assistant_report_json",
    )
    with st.expander("Historique et comparaison"):
        _render_history_block()


def _folder_images(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []
    return [
        path
        for path in sorted(folder.rglob("*"))
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def _batch_record(path: Path, title: str, description: str) -> dict[str, Any]:
    image_rgb = _load_rgb_image(path)
    report = _run_pipeline(image_rgb, title, description)
    analysis = report["analysis"]
    selection = report["selection"]
    return {
        "image": str(path),
        "title": title,
        "category": report["text_data"]["category"],
        "global_score": analysis["global_score"],
        "coherence": analysis["criteria"]["coherence"]["score"],
        "sharpness": analysis["criteria"]["sharpness"]["score"],
        "exposure": analysis["criteria"]["exposure"]["score"],
        "contrast": analysis["criteria"]["contrast"]["score"],
        "color_balance": analysis["criteria"]["color_balance"]["score"],
        "effective_resolution": analysis["criteria"]["effective_resolution"]["score"],
        "framing": analysis["criteria"]["framing"]["score"],
        "selected_bbox": selection["selected_bbox"],
    }


def _styled_batch_table(frame: pd.DataFrame):
    score_cols = [
        "global_score",
        "coherence",
        "sharpness",
        "exposure",
        "contrast",
        "color_balance",
        "effective_resolution",
        "framing",
    ]

    def style_score(value: Any) -> str:
        try:
            numeric = float(value)
        except Exception:
            return ""
        return f"color: {_score_color(numeric)}; font-weight: 700;"

    return frame.style.map(style_score, subset=score_cols)


def _render_batch_mode() -> None:
    st.subheader("Batch")
    folder_value = st.text_input("Dossier images", value=str(RAW_IMAGES_DIR / "clothing"))
    title_template = st.text_input("Titre par defaut", value="Produit e-commerce")
    description_template = st.text_area(
        "Description par defaut",
        value="Annonce produit pour evaluation zero-shot de la qualite photo.",
        height=90,
    )

    if not st.button("Lancer le batch"):
        return

    folder = Path(folder_value)
    image_paths = _folder_images(folder)
    if not image_paths:
        st.error("Aucune image trouvee dans le dossier fourni.")
        return

    rows: list[dict[str, Any]] = []
    progress = st.progress(0.0)
    for index, image_path in enumerate(image_paths, start=1):
        rows.append(_batch_record(image_path, title_template, description_template))
        progress.progress(index / len(image_paths))

    frame = pd.DataFrame(rows)
    st.dataframe(_styled_batch_table(frame), use_container_width=True)

    csv_bytes = frame.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Exporter CSV",
        data=csv_bytes,
        file_name="batch_results_streamlit.csv",
        mime="text/csv",
    )


def main() -> None:
    _init_session_state()
    _inject_premium_styles()
    st.title("Evaluation zero-shot de qualite photo e-commerce")
    st.caption("Pipeline : texte -> regions candidates -> selector -> analyzer. Aucun OCR dans le chemin critique.")
    _render_status_badges()

    mode = st.sidebar.radio("Mode", ["Analyse unique", "Assistant annonce", "Batch"])
    if mode == "Analyse unique":
        _render_single_mode()
    elif mode == "Assistant annonce":
        _render_assistant_mode()
    else:
        _render_batch_mode()


if __name__ == "__main__":
    main()
