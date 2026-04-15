"""
utils/validator.py
Validates extracted data, identifies issues, and formats for display.
"""

from typing import Any


REQUIRED_DEMO_FIELDS = ["name", "age", "gender"]
RECOMMENDED_DEMO_FIELDS = ["date_assessed", "referral_reason"]

FIELD_LABELS = {
    "name": "Patient Name",
    "age": "Age",
    "gender": "Gender",
    "dob": "Date of Birth",
    "date_assessed": "Date Assessed",
    "referral_reason": "Referral Reason",
    "education": "Education Level",
    "clinician": "Clinician",
}

FIELD_LABELS_AR = {
    "name": "اسم المريض",
    "age": "العمر",
    "gender": "الجنس",
    "dob": "تاريخ الميلاد",
    "date_assessed": "تاريخ التقييم",
    "referral_reason": "سبب الإحالة",
    "education": "المستوى التعليمي",
    "clinician": "الأخصائي",
}


def validate_extracted_data(demographics: dict, scores: list[dict]) -> dict:
    """
    Returns a validation report:
    {
        "demo_issues": list of {field, severity, message},
        "score_issues": list of {test, severity, message},
        "is_valid": bool,
        "warnings": int,
        "errors": int,
    }
    """
    demo_issues = []
    score_issues = []

    # Check required demographics
    for field in REQUIRED_DEMO_FIELDS:
        val = demographics.get(field, "")
        if not val or str(val).strip() == "":
            demo_issues.append({
                "field": field,
                "label": FIELD_LABELS.get(field, field),
                "severity": "error",
                "message": f"Required field '{FIELD_LABELS.get(field, field)}' is missing.",
            })

    # Check recommended demographics
    for field in RECOMMENDED_DEMO_FIELDS:
        val = demographics.get(field, "")
        if not val or str(val).strip() == "":
            demo_issues.append({
                "field": field,
                "label": FIELD_LABELS.get(field, field),
                "severity": "warning",
                "message": f"Recommended field '{FIELD_LABELS.get(field, field)}' is missing.",
            })

    # Validate age
    age = demographics.get("age", "")
    if age:
        try:
            age_int = int(str(age).strip())
            if not (1 <= age_int <= 120):
                demo_issues.append({
                    "field": "age",
                    "label": "Age",
                    "severity": "warning",
                    "message": f"Age '{age}' seems unusual. Please verify.",
                })
        except ValueError:
            demo_issues.append({
                "field": "age",
                "label": "Age",
                "severity": "warning",
                "message": f"Age value '{age}' may not be numeric.",
            })

    # Validate scores
    if len(scores) == 0:
        score_issues.append({
            "test": "All",
            "severity": "warning",
            "message": "No test scores were automatically detected. Please add scores manually.",
        })

    for s in scores:
        score_val = s.get("score", "")
        if score_val == "" or score_val is None:
            score_issues.append({
                "test": s.get("test", "Unknown"),
                "severity": "warning",
                "message": f"Score for '{s.get('test')}' could not be extracted. Please enter manually.",
            })
        else:
            try:
                sv = int(str(score_val))
                if not (1 <= sv <= 200):
                    score_issues.append({
                        "test": s.get("test", "Unknown"),
                        "severity": "warning",
                        "message": f"Score {sv} for '{s.get('test')}' is outside typical range (1–200).",
                    })
            except (ValueError, TypeError):
                score_issues.append({
                    "test": s.get("test", "Unknown"),
                    "severity": "warning",
                    "message": f"Score value '{score_val}' for '{s.get('test')}' is not numeric.",
                })

    errors = sum(1 for i in demo_issues + score_issues if i["severity"] == "error")
    warnings = sum(1 for i in demo_issues + score_issues if i["severity"] == "warning")

    return {
        "demo_issues": demo_issues,
        "score_issues": score_issues,
        "is_valid": errors == 0,
        "warnings": warnings,
        "errors": errors,
    }


def highlight_issues(df_row: dict, issues: list[dict]) -> str:
    """Return CSS background color for a field based on issue severity."""
    for issue in issues:
        if issue.get("field") == df_row.get("field"):
            if issue["severity"] == "error":
                return "background-color: #fef2f2"
            elif issue["severity"] == "warning":
                return "background-color: #fffbeb"
    return ""


def get_field_label(field: str, language: str = "English") -> str:
    if language == "Arabic":
        return FIELD_LABELS_AR.get(field, field)
    return FIELD_LABELS.get(field, field)
