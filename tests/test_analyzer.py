import unittest

from app import create_app
from analyzer import categorize_skills, extract_skills, load_skills, normalize_skill


class SkillAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = load_skills()

    def test_extracts_canonical_names_and_aliases_once(self):
        found = extract_skills(
            "Python, Python 3, and Amazon Web Services (AWS); also use K8s.",
            self.skills,
        )
        self.assertEqual(
            found,
            ["Amazon Web Services (AWS)", "Kubernetes", "Python"],
        )

    def test_matching_requires_skill_word_boundaries(self):
        self.assertEqual(extract_skills("I enjoy going for walks.", self.skills), [])
        self.assertNotIn("Go", extract_skills("We will go to the office.", self.skills))
        self.assertIn("Go", extract_skills("Golang developer", self.skills))

    def test_normalization_and_categorization(self):
        self.assertEqual(normalize_skill("postgres", self.skills), "PostgreSQL")
        self.assertIsNone(normalize_skill("not a skill", self.skills))
        self.assertEqual(
            categorize_skills(["Python", "PostgreSQL"], self.skills),
            {"Databases": ["PostgreSQL"], "Programming languages": ["Python"]},
        )

    def test_gap_analysis_calculates_categories_and_percentage(self):
        from analyzer import analyze

        result = analyze(
            "Python and PostgreSQL experience",
            "Python, AWS, and Docker required",
            self.skills,
        )
        self.assertEqual(result["matched_skills"], ["Python"])
        self.assertEqual(
            result["missing_skills"],
            ["Amazon Web Services (AWS)", "Docker"],
        )
        self.assertEqual(result["match_percentage"], 33)
        self.assertEqual(result["required_skill_count"], 3)
        self.assertIn("Programming languages", result["candidate_categories"])

    def test_duplicate_skills_are_removed_and_normalized(self):
        result = extract_skills("Python, python, python 3, JS, js, NodeJS, nodejs", self.skills)
        self.assertEqual(result, ["JavaScript", "Node.js", "Python"])

    def test_priority_is_calculated_for_missing_skills(self):
        from analyzer import analyze

        result = analyze(
            "Python and AWS and Docker and PostgreSQL and FastAPI and REST API",
            "Python and Docker",
            self.skills,
        )
        self.assertIn("priority", result)
        self.assertTrue(result["priority"])

    def test_empty_input_is_validated(self):
        from analyzer import analyze

        with self.assertRaises(ValueError):
            analyze("   ", "Python")
        with self.assertRaises(ValueError):
            analyze("Python", "   ")


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    def test_analyze_endpoint_returns_result(self):
        response = self.client.post(
            "/api/analyze",
            json={"candidate_text": "Python", "job_text": "Python and AWS"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["matched_skills"], ["Python"])
        self.assertEqual(payload["missing_skills"], ["Amazon Web Services (AWS)"])

    def test_validates_missing_fields_and_input_types(self):
        missing = self.client.post(
            "/api/analyze", json={"candidate_text": "Python", "job_text": " "}
        )
        wrong_type = self.client.post(
            "/api/analyze", json={"candidate_text": [], "job_text": "Python"}
        )
        self.assertEqual(missing.status_code, 400)
        self.assertIn("job description", missing.get_json()["error"])
        self.assertEqual(wrong_type.status_code, 400)

    def test_rejects_non_json_and_oversized_fields(self):
        non_json = self.client.post("/api/analyze", data="not json")
        oversized = self.client.post(
            "/api/analyze",
            json={"candidate_text": "x" * 30_001, "job_text": "Python"},
        )
        self.assertEqual(non_json.status_code, 415)
        self.assertEqual(oversized.status_code, 413)


if __name__ == "__main__":
    unittest.main()
