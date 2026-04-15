"""
utils/ai_engine.py
Wrapper for Grok API (xAI) — generates clinical interpretations from scores only.
Reads API key from st.secrets["GROK_API_KEY"].
"""

import json
import re
from typing import Any

import requests
import streamlit as st


GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-3-latest"


# ─────────────────────────────────────────────
# PROMPT BUILDERS
# ─────────────────────────────────────────────

def _build_system_prompt(language: str) -> str:
    if language == "Arabic":
        return (
            "أنت طبيب نفسي إكلينيكي متخصص في تقييم وتفسير نتائج الاختبارات النفسية. "
            "مهمتك هي كتابة تقرير تفسيري سريري احترافي بناءً على الدرجات المُقدَّمة فقط. "
            "القواعد الصارمة:\n"
            "1. استخدم الدرجات المُقدَّمة فقط — لا تُضف أي درجات أو بيانات غير موجودة.\n"
            "2. لا تختلق ملاحظات أو نتائج غير مدعومة بالبيانات المُقدَّمة.\n"
            "3. اكتب بأسلوب سريري رسمي، مناسب للتقارير النفسية المهنية.\n"
            "4. قسّم تفسيرك إلى أقسام واضحة: ملخص تنفيذي، تفسير النتائج، توصيات.\n"
            "5. استخدم اللغة العربية الفصحى بالكامل.\n"
            "6. لا تُضمِّن أي معلومات ديموغرافية أو تفسيرات من الملف الأصلي."
        )
    else:
        return (
            "You are a licensed clinical psychologist specializing in psychoeducational "
            "and neuropsychological assessment. Your task is to write a professional, "
            "clinically sound interpretation of test results based ONLY on the scores provided.\n\n"
            "STRICT RULES:\n"
            "1. Use ONLY the scores provided — do NOT invent or add missing scores.\n"
            "2. Do NOT fabricate observations unsupported by the data.\n"
            "3. Write in formal clinical language appropriate for psychological reports.\n"
            "4. Structure your output with clear sections: "
            "Executive Summary, Interpretation of Results, Recommendations.\n"
            "5. Do NOT include demographic details or any interpretation copied from the source file.\n"
            "6. Be specific: reference actual score values and what they mean clinically."
        )


def _build_user_prompt(demographics: dict, scores: list[dict], language: str) -> str:
    # Format scores as a clean table string
    score_lines = []
    for s in scores:
        score_str = str(s.get("score", "N/A"))
        pct_str = str(s.get("percentile", "")) if s.get("percentile", "") != "" else "N/A"
        cls_str = s.get("classification", "N/A") or "N/A"
        score_lines.append(
            f"  - {s['test']}: Score = {score_str}, Percentile = {pct_str}, Classification = {cls_str}"
        )

    scores_block = "\n".join(score_lines) if score_lines else "  No scores provided."

    demo_parts = []
    if demographics.get("age"):
        demo_parts.append(f"Age: {demographics['age']}")
    if demographics.get("gender"):
        demo_parts.append(f"Gender: {demographics['gender']}")
    if demographics.get("education"):
        demo_parts.append(f"Education: {demographics['education']}")
    demo_str = " | ".join(demo_parts) if demo_parts else "Not specified"

    if language == "Arabic":
        return (
            f"معلومات ديموغرافية محدودة (للسياق فقط): {demo_str}\n\n"
            f"الدرجات المُقدَّمة:\n{scores_block}\n\n"
            "اكتب التفسير السريري الشامل بناءً على هذه الدرجات فقط. "
            "الرجاء تقسيم التقرير إلى:\n"
            "1. ملخص تنفيذي\n"
            "2. تفسير النتائج (تناول كل مجال بشكل منفصل)\n"
            "3. التوصيات\n"
            "لا تُضف أي درجات غير موجودة في القائمة أعلاه."
        )
    else:
        return (
            f"Limited demographic context (for framing only): {demo_str}\n\n"
            f"Test Scores Provided:\n{scores_block}\n\n"
            "Write a comprehensive clinical interpretation based ONLY on these scores. "
            "Structure your report as follows:\n"
            "1. Executive Summary\n"
            "2. Interpretation of Results (address each domain separately)\n"
            "3. Recommendations\n\n"
            "Do NOT add any scores not listed above."
        )


# ─────────────────────────────────────────────
# API CALL
# ─────────────────────────────────────────────

def _call_grok_api(messages: list[dict], api_key: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROK_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2500,
    }

    response = requests.post(
        GROK_API_URL,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if response.status_code != 200:
        error_detail = ""
        try:
            error_detail = response.json().get("error", {}).get("message", response.text)
        except Exception:
            error_detail = response.text
        raise RuntimeError(
            f"Grok API error ({response.status_code}): {error_detail}"
        )

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def generate_interpretation(
    demographics: dict,
    scores: list[dict],
    language: str = "English",
) -> str:
    """
    Generate clinical interpretation using Grok API.

    Args:
        demographics: dict of demographic fields (used for context only)
        scores: list of score dicts with keys: test, score, percentile, classification
        language: "English" or "Arabic"

    Returns:
        Interpretation text as a string.

    Raises:
        RuntimeError on API failure.
        ValueError if no API key is configured.
    """
    # Get API key from Streamlit secrets
    try:
        api_key = st.secrets["GROK_API_KEY"]
    except (KeyError, FileNotFoundError):
        raise ValueError(
            "Grok API key not found. Please add GROK_API_KEY to your Streamlit secrets.\n"
            "See README.md for instructions."
        )

    if not api_key or not str(api_key).strip():
        raise ValueError("GROK_API_KEY is empty. Please set a valid API key.")

    # Filter to only scores that have actual values
    valid_scores = [s for s in scores if str(s.get("score", "")).strip() not in ("", "None")]

    if not valid_scores:
        raise ValueError(
            "No valid scores to interpret. Please ensure at least one score "
            "has a numeric value before generating the interpretation."
        )

    system_prompt = _build_system_prompt(language)
    user_prompt = _build_user_prompt(demographics, valid_scores, language)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    interpretation = _call_grok_api(messages, api_key.strip())
    return interpretation
