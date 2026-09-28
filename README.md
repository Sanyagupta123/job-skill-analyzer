# Job Skill Analyzer

## Overview

Job Skill Analyzer is a rule-based web application that compares a job description against a user's skill list, identifies required skills, highlights gaps, and prioritizes the most important learning opportunities. It is designed as a simple, transparent skill-gap tool for job preparation, not as a hiring prediction engine.

## Features

- Parse job descriptions and extract relevant skills
- Normalize common aliases like Postgres, JS, TS, NodeJS, Mongo, and REST API
- Categorize skills into groups such as Programming Language, Framework, Database, Cloud, DevOps, and API
- Compare job requirements against the user's known skills
- Show matched, missing, and priority items
- Provide a clean, light-themed dashboard with copy/download/reset actions
- Validate empty or invalid input and return friendly error messages

## Tech Stack

- Python
- Flask
- HTML
- CSS
- JavaScript
- Rule-based NLP
- JSON
- Pytest

## Architecture

Input
 ↓
Preprocessing
 ↓
Skill Extraction
 ↓
Normalization
 ↓
Categorization
 ↓
Gap Analysis
 ↓
Priority Calculation
 ↓
Report

## Installation

```bash
git clone <repository-url>
cd job-skill-analyzer

python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Open http://127.0.0.1:5000

## API

POST /api/analyze

Request body:

```json
{
  "job_description": "Looking for a Python developer with FastAPI, PostgreSQL, Docker, AWS and REST API experience.",
  "user_skills": "Python, FastAPI, PostgreSQL, Docker, REST API, Git"
}
```

Example response:

```json
{
  "detected_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "REST API"],
  "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"],
  "missing_skills": ["AWS"],
  "match_percentage": 83.33,
  "priority": [
    {
      "skill": "AWS",
      "category": "Cloud",
      "priority": "High",
      "reason": "This skill appears in the job description and is not yet in your skill set."
    }
  ]
}
```

## Testing

Run the test suite:

```bash
pytest
```

## Future Improvements

The current version focuses on rule-based extraction and gap analysis. Future enhancements could include:

- Resume comparison
- LLM-based extraction
- Semantic similarity matching
- Personalized learning recommendations
- Job matching and trend analysis

## Current Scope vs Future Work

Current scope is a transparent rule-based analyzer with real validation, normalization, gap analysis, and a clean frontend. The items above are future capabilities and are intentionally not part of the first version.
