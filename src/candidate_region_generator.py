from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from config import REGION_PROPOSAL_CONFIG


_DINO_PROCESSOR = None
_DINO_MODEL = None
_DINO_LOAD_ATTEMPTED = False


def _load_image(image: str | Path | np.ndarray) -> np.ndarray:
    if isinstance(image, np.ndarray):
        array = image.copy()
    else:
        array = cv2.imread(str(image), cv2.IMREAD_COLOR)
        if array is None:
            raise FileNotFoundError(f"Impossible de lire l'image: {image}")

    if array.ndim == 2:
        array = cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
    return array.astype(np.uint8)


def _clamp_bbox(bbox: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(x1 + 1, min(x2, width))
    y2 = max(y1 + 1, min(y2, height))
    return int(x1), int(y1), int(x2), int(y2)


def _bbox_area(bbox: tuple[int, int, int, int]) -> int:
    x1, y1, x2, y2 = bbox
    return max(0, x2 - x1) * max(0, y2 - y1)


def _bbox_centrality(bbox: tuple[int, int, int, int], image_shape: tuple[int, int, int]) -> float:
    x1, y1, x2, y2 = bbox
    height, width = image_shape[:2]
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    dx = abs(cx - width / 2.0) / max(width / 2.0, 1.0)
    dy = abs(cy - height / 2.0) / max(height / 2.0, 1.0)
    distance = min(1.0, float(np.sqrt(dx * dx + dy * dy)))
    return round(1.0 - distance, 4)


def _merge_overlapping_boxes(boxes: list[tuple[int, int, int, int]], iou_threshold: float = 0.55) -> list[tuple[int, int, int, int]]:
    merged: list[tuple[int, int, int, int]] = []
    for candidate in boxes:
        keep = True
        cx1, cy1, cx2, cy2 = candidate
        c_area = _bbox_area(candidate)
        for existing in merged:
            ex1, ey1, ex2, ey2 = existing
            ix1 = max(cx1, ex1)
            iy1 = max(cy1, ey1)
            ix2 = min(cx2, ex2)
            iy2 = min(cy2, ey2)
            inter = _bbox_area((ix1, iy1, ix2, iy2))
            union = c_area + _bbox_area(existing) - inter
            iou = inter / union if union else 0.0
            if iou >= iou_threshold:
                keep = False
                break
        if keep:
            merged.append(candidate)
    return merged


def _saliency_map(image_bgr: np.ndarray) -> np.ndarray | None:
    if not hasattr(cv2, "saliency"):
        return None

    try:
        saliency = cv2.saliency.StaticSaliencyFineGrained_create()
        success, saliency_map = saliency.computeSaliency(image_bgr)
    except Exception:
        return None

    if not success or saliency_map is None:
        return None
    saliency_map = cv2.GaussianBlur(saliency_map, (7, 7), 0)
    return saliency_map


def _regions_from_saliency(image_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
    saliency_map = _saliency_map(image_bgr)
    if saliency_map is None:
        return []

    saliency_uint8 = np.clip(saliency_map * 255.0, 0, 255).astype(np.uint8)
    threshold = int(REGION_PROPOSAL_CONFIG["saliency_threshold"] * 255)
    _, mask = cv2.threshold(saliency_uint8, threshold, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return _regions_from_mask(mask, image_bgr.shape)


def _regions_from_contours(image_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        6,
    )
    edges = cv2.Canny(blurred, 40, 140)
    mask = cv2.bitwise_or(thresh, edges)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=1)
    return _regions_from_mask(mask, image_bgr.shape)


def _regions_from_mask(mask: np.ndarray, image_shape: tuple[int, int, int]) -> list[tuple[int, int, int, int]]:
    height, width = image_shape[:2]
    image_area = height * width
    min_area = image_area * REGION_PROPOSAL_CONFIG["min_region_area_ratio"]
    max_area = image_area * REGION_PROPOSAL_CONFIG["max_region_area_ratio"]

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < min_area or area > max_area:
            continue
        boxes.append(_clamp_bbox((x, y, x + w, y + h), width, height))

    boxes.sort(key=_bbox_area, reverse=True)
    return _merge_overlapping_boxes(boxes)


def propose_regions(image: str | Path | np.ndarray) -> list[dict[str, Any]]:
    image_bgr = _load_image(image)
    height, width = image_bgr.shape[:2]

    candidate_boxes = _regions_from_saliency(image_bgr)
    if not candidate_boxes:
        candidate_boxes = _regions_from_contours(image_bgr)

    if not candidate_boxes:
        fallback = (0, 0, width, height)
        candidate_boxes = [fallback]

    candidates: list[dict[str, Any]] = []
    image_area = float(height * width)
    for bbox in candidate_boxes[: REGION_PROPOSAL_CONFIG["max_regions"]]:
        area_ratio = round(_bbox_area(bbox) / max(image_area, 1.0), 4)
        candidates.append(
            {
                "bbox": bbox,
                "area": area_ratio,
                "centrality": _bbox_centrality(bbox, image_bgr.shape),
            }
        )

    candidates.sort(key=lambda item: (item["centrality"] * 0.6 + item["area"] * 0.4), reverse=True)
    return candidates[: REGION_PROPOSAL_CONFIG["max_regions"]]


def refine_crop(image: str | Path | np.ndarray, bbox: tuple[int, int, int, int]) -> dict[str, Any]:
    image_bgr = _load_image(image)
    height, width = image_bgr.shape[:2]
    x1, y1, x2, y2 = _clamp_bbox(bbox, width, height)

    if (x2 - x1) < 12 or (y2 - y1) < 12:
        crop = image_bgr[y1:y2, x1:x2]
        return {"bbox": (x1, y1, x2, y2), "crop": crop, "mask": None}

    mask = np.zeros(image_bgr.shape[:2], np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    rect = (x1, y1, max(1, x2 - x1), max(1, y2 - y1))

    try:
        cv2.grabCut(image_bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        binary_mask = np.where(
            (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD),
            255,
            0,
        ).astype("uint8")
        coords = cv2.findNonZero(binary_mask)
        if coords is None:
            crop = image_bgr[y1:y2, x1:x2]
            return {"bbox": (x1, y1, x2, y2), "crop": crop, "mask": binary_mask[y1:y2, x1:x2]}

        rx, ry, rw, rh = cv2.boundingRect(coords)
        refined_bbox = _clamp_bbox((rx, ry, rx + rw, ry + rh), width, height)
        fx1, fy1, fx2, fy2 = refined_bbox
        crop = image_bgr[fy1:fy2, fx1:fx2]
        return {
            "bbox": refined_bbox,
            "crop": crop,
            "mask": binary_mask[fy1:fy2, fx1:fx2],
        }
    except Exception:
        crop = image_bgr[y1:y2, x1:x2]
        return {"bbox": (x1, y1, x2, y2), "crop": crop, "mask": None}


def _load_dino_once():
    global _DINO_PROCESSOR, _DINO_MODEL, _DINO_LOAD_ATTEMPTED
    if _DINO_PROCESSOR is not None and _DINO_MODEL is not None:
        return _DINO_PROCESSOR, _DINO_MODEL
    if _DINO_LOAD_ATTEMPTED:
        return None, None

    _DINO_LOAD_ATTEMPTED = True
    try:
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

        model_id = REGION_PROPOSAL_CONFIG["dino_model_id"]
        _DINO_PROCESSOR = AutoProcessor.from_pretrained(model_id)
        _DINO_MODEL = AutoModelForZeroShotObjectDetection.from_pretrained(model_id)
    except Exception:
        _DINO_PROCESSOR = None
        _DINO_MODEL = None
    return _DINO_PROCESSOR, _DINO_MODEL


def detect_with_dino(image: str | Path | np.ndarray, prompt: str) -> list[dict[str, Any]]:
    image_bgr = _load_image(image)
    processor, model = _load_dino_once()
    if processor is None or model is None:
        return []

    try:
        from PIL import Image
        import torch
    except Exception:
        return []

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb)

    try:
        inputs = processor(images=pil_image, text=prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)

        target_sizes = torch.tensor([pil_image.size[::-1]])
        results = processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            box_threshold=REGION_PROPOSAL_CONFIG["dino_box_threshold"],
            text_threshold=REGION_PROPOSAL_CONFIG["dino_text_threshold"],
            target_sizes=target_sizes,
        )
    except Exception:
        return []

    candidates: list[dict[str, Any]] = []
    for box in results[0]["boxes"][: REGION_PROPOSAL_CONFIG["max_regions"]]:
        x1, y1, x2, y2 = [int(value) for value in box.tolist()]
        bbox = _clamp_bbox((x1, y1, x2, y2), image_bgr.shape[1], image_bgr.shape[0])
        area = round(_bbox_area(bbox) / float(image_bgr.shape[0] * image_bgr.shape[1]), 4)
        candidates.append(
            {
                "bbox": bbox,
                "area": area,
                "centrality": _bbox_centrality(bbox, image_bgr.shape),
            }
        )

    candidates.sort(key=lambda item: (item["centrality"] * 0.6 + item["area"] * 0.4), reverse=True)
    return candidates[: REGION_PROPOSAL_CONFIG["max_regions"]]
