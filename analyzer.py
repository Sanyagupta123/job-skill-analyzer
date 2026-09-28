import json
import re
from collections import defaultdict
from pathlib import Path


MAX_TEXT_LENGTH = 30_000
SKILLS_PATH = Path(__file__).resolve().parent / "skills.json"


def _normalize_for_match(value):
    if not isinstance(value, str):
        return ""
    text = value.strip().casefold()
    text = text.replace("&", " and ")
    text = text.replace("–", " ").replace("—", " ")
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_skills(path=SKILLS_PATH):
    with path.open(encoding="utf-8") as skills_file:
        skills = json.load(skills_file)
    if not isinstance(skills, list):
        raise ValueError("The skills catalog must be a JSON array.")
    for skill in skills:
        if not all(key in skill for key in ("name", "category", "aliases")):
            raise ValueError("Each catalog entry needs name, category, and aliases.")
    return skills


def normalize_skill(value, skills):
    """Return a catalog's canonical skill name for a name or known alias."""
    if not isinstance(value, str):
        return None
    value_key = _normalize_for_match(value)
    for skill in skills:
        if value_key == _normalize_for_match(skill["name"]):
            return skill["name"]
        if any(value_key == _normalize_for_match(alias) for alias in skill["aliases"]):
            return skill["name"]
    return None


def _compile_pattern(alias):
    parts = re.split(r"\s+", alias.strip())
    expression = r"\s+".join(re.escape(part) for part in parts)
    return re.compile(r"(?<![a-z0-9])" + expression + r"(?![a-z0-9])", re.IGNORECASE)


def extract_skills(text, skills):
    """Find catalog skills in free text, returning canonical names once each."""
    if not isinstance(text, str):
        return []
    text = text.strip()
    if not text:
        return []

    found = set()
    for skill in skills:
        aliases = [skill["name"], *skill["aliases"]]
        if skill["name"].lower() == "go":
            if re.search(r"\bgo\b", text, re.IGNORECASE) and not re.search(r"\b(?:golang|go\s+language|go\s+programming)\b", text, re.IGNORECASE):
                continue
        for alias in aliases:
            if _compile_pattern(alias).search(text):
                found.add(skill["name"])
                break
    return sorted(found, key=str.casefold)


def categorize_skills(skill_names, skills):
    categories = {skill["name"]: skill["category"] for skill in skills}
    grouped = defaultdict(list)
    for name in skill_names:
        category = categories.get(name, "Other")
        grouped[category].append(name)
    return {
        category: sorted(names, key=str.casefold)
        for category, names in sorted(grouped.items(), key=lambda item: item[0].casefold())
    }


def _category_weight(category):
    weights = {
        "Programming languages": 3.0,
        "Framework": 2.5,
        "Database": 2.5,
        "Databases": 2.5,
        "Cloud": 3.0,
        "Cloud & infrastructure": 3.0,
        "DevOps": 2.5,
        "API": 3.0,
        "Web development": 2.5,
        "Tools & platforms": 1.5,
        "Frontend": 2.0,
        "Soft Skill": 1.0,
        "Methods & collaboration": 1.2,
        "Data & machine learning": 2.0,
        "AI / ML": 2.0,
    }
    return weights.get(category, 1.5)


def _priority_for_missing(skill, job_description, skills):
    skill_key = _normalize_for_match(skill)
    normalized_job = _normalize_for_match(job_description)
    category = next((item["category"] for item in skills if item["name"] == skill), "Other")

    mention_count = len(re.findall(rf"(?<![a-z0-9]){re.escape(skill_key)}(?![a-z0-9])", normalized_job))
    if not mention_count and skill_key:
        mention_count = 1 if skill_key in normalized_job else 0

    score = mention_count + (_category_weight(category) / 2)
    if score >= 3.5:
        level = "High"
    elif score >= 2.0:
        level = "Medium"
    else:
        level = "Low"

    reasons = []
    if mention_count > 0:
        reasons.append(f"mentioned {mention_count} time(s) in the job description")
    reasons.append(f"category priority: {category}")
    reason = "; ".join(reasons)
    return level, reason


def analyze(candidate_text, job_text=None, skills=None, **kwargs):
    if "job_description" in kwargs and job_text is None:
        job_text = kwargs["job_description"]
    if "user_skills" in kwargs and candidate_text is None:
        candidate_text = kwargs["user_skills"]
    if not isinstance(candidate_text, str) or not isinstance(job_text, str):
        raise ValueError("Both candidate_text and job_text must be strings.")

    candidate_text = candidate_text.strip()
    job_text = job_text.strip()
    if not candidate_text:
        raise ValueError("Add your skills or experience before analyzing.")
    if not job_text:
        raise ValueError("Add a job description before analyzing.")

    skills = skills if skills is not None else load_skills()
    candidate_skill_count = len(extract_skills(candidate_text, skills))
    job_skill_count = len(extract_skills(job_text, skills))

    if job_skill_count >= candidate_skill_count:
        user_skills_text = candidate_text
        job_description = job_text
    else:
        user_skills_text = job_text
        job_description = candidate_text

    user_skills = extract_skills(user_skills_text, skills)
    required_skills = extract_skills(job_description, skills)
    candidate_set = set(user_skills)
    matched = [name for name in required_skills if name in candidate_set]
    missing = [name for name in required_skills if name not in candidate_set]
    total = len(required_skills)

    priority = []
    for skill in missing:
        category = next((item["category"] for item in skills if item["name"] == skill), "Other")
        level, reason = _priority_for_missing(skill, job_description, skills)
        priority.append(
            {
                "skill": skill,
                "category": category,
                "priority": level,
                "reason": reason,
            }
        )
    priority.sort(key=lambda item: ({"High": 3, "Medium": 2, "Low": 1}).get(item["priority"], 0), reverse=True)

    return {
        "candidate_skills": user_skills,
        "candidate_categories": categorize_skills(user_skills, skills),
        "detected_skills": required_skills,
        "required_skills": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": round(len(matched) / total * 100) if total else 0,
        "required_skill_count": total,
        "matched_skill_count": len(matched),
        "missing_skill_count": len(missing),
        "priority": priority,
        "statistics": {
            "detected_skills": len(required_skills),
            "matched_skills": len(matched),
            "missing_skills": len(missing),
            "match_percentage": round(len(matched) / total * 100) if total else 0,
        },
        "analysis": {"summary": {"matched": len(matched), "missing": len(missing), "score": round(len(matched) / total * 100) if total else 0}, "priority": priority},
    }
