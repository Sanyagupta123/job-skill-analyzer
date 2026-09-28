from flask import Flask, jsonify, render_template, request

from analyzer import MAX_TEXT_LENGTH, analyze


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(MAX_CONTENT_LENGTH=MAX_TEXT_LENGTH * 2 + 4096)
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return render_template("index.html", max_text_length=MAX_TEXT_LENGTH)

    @app.post("/api/analyze")
    def analyze_job():
        if not request.is_json:
            return jsonify(error="Request body must be JSON."), 415

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Request body must be a JSON object."), 400

        if "job_description" in payload or "user_skills" in payload:
            job_description = payload.get("job_description")
            user_skills = payload.get("user_skills")
        else:
            job_description = payload.get("job_text")
            user_skills = payload.get("candidate_text")

        if not isinstance(job_description, str) or not isinstance(user_skills, (str, list)):
            return jsonify(
                error="Both job_description and user_skills must be provided as strings or arrays."
            ), 400

        job_description = job_description.strip()
        if not job_description:
            return jsonify(error="Please enter a job description before analyzing."), 400
        if len(job_description) > MAX_TEXT_LENGTH:
            return jsonify(error=f"Job description must be {MAX_TEXT_LENGTH:,} characters or fewer."), 413

        user_skills_value = user_skills.strip() if isinstance(user_skills, str) else user_skills
        if isinstance(user_skills_value, str) and not user_skills_value:
            return jsonify(error="Please add your skills before analyzing."), 400
        if isinstance(user_skills_value, str) and len(user_skills_value) > MAX_TEXT_LENGTH:
            return jsonify(error=f"User skills must be {MAX_TEXT_LENGTH:,} characters or fewer."), 413

        try:
            result = analyze(candidate_text=user_skills_value if isinstance(user_skills_value, str) else user_skills, job_text=job_description)
            return jsonify(result)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except Exception:
            return jsonify(error="The analyzer could not process that request. Please try again."), 500

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify(error="The request is too large. Shorten the text and try again."), 413

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=False)
