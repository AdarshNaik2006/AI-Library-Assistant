import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

from database.db import (
    seed_database,
    search_resources,
    get_all_subjects,
    get_all_education_levels,
    get_all_departments,
    get_resource_by_id,
    get_connection,
)
from assistant import (
    generate_chat_response,
    get_model_name,
    get_ollama_base_url,
    check_ollama_status,
    is_in_domain,
    detect_language,
    OUT_OF_DOMAIN_MESSAGE_EN,
    OUT_OF_DOMAIN_MESSAGE_KN,
    OUT_OF_DOMAIN_MESSAGE,
)

# Initialize Flask app serving the frontend folder as static files
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "frontend"),
    static_url_path="",
)

# Initialize database and seed sample resources on application startup
with app.app_context():
    seed_database()


@app.after_request
def apply_cors_headers(response):
    """Enable CORS headers to allow smooth frontend integration."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/")
def serve_index():
    """Serve the main frontend application."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    Verifies database connectivity and reports local Ollama status and model availability.
    """
    db_status = "error"
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
            db_status = "connected"
    except Exception as e:
        db_status = f"unavailable: {str(e)}"

    ollama_info = check_ollama_status()

    return jsonify({
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "ai_provider": "Ollama (Local)",
        "ai_connected": ollama_info["connected"],
        "model_available": ollama_info["model_available"],
        "model": get_model_name(),
        "ollama_url": get_ollama_base_url(),
        "installed_models": ollama_info.get("installed_models", []),
        "note": "AI assistant runs 100% locally with Ollama (llama3.2:3b). No API keys or internet billing required.",
    }), 200


@app.route("/api/subjects", methods=["GET"])
def list_subjects():
    """Retrieve all available subjects across all educational levels in the catalogue."""
    try:
        subjects = get_all_subjects()
        return jsonify({"subjects": subjects}), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve subjects", "details": str(e)}), 500


@app.route("/api/education-levels", methods=["GET"])
def list_education_levels():
    """Retrieve all distinct educational levels currently in the catalogue."""
    try:
        levels = get_all_education_levels()
        return jsonify({"education_levels": levels}), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve education levels", "details": str(e)}), 500


@app.route("/api/departments", methods=["GET"])
def list_departments():
    """Retrieve all distinct departments in the catalogue."""
    try:
        departments = get_all_departments()
        return jsonify({"departments": departments}), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve departments", "details": str(e)}), 500


@app.route("/api/resources", methods=["GET"])
def list_resources():
    """
    Retrieve and filter library resources across all educational levels.
    Accepts query parameters:
      - q or search: keyword search in title, author, description, subject, department, class_grade
      - subject: filter by subject name (or 'all')
      - level: filter by skill level (e.g. Beginner, Intermediate, Advanced, or 'all')
      - education_level: filter by educational tier (Primary School, Middle School, High School, PUC, Diploma, Undergraduate, Postgraduate)
      - class_grade: filter by class grade (e.g. Class 3, Class 5, Class 10, 2nd PUC)
      - language: filter by language (English, Kannada, Hindi, Bilingual)
    """
    query = request.args.get("q") or request.args.get("search") or ""
    subject = request.args.get("subject") or ""
    level = request.args.get("level") or ""
    education_level = request.args.get("education_level") or ""
    class_grade = request.args.get("class_grade") or ""
    language = request.args.get("language") or ""

    try:
        resources = search_resources(
            query=query,
            subject=subject,
            level=level,
            education_level=education_level,
            class_grade=class_grade,
            language=language,
        )
        return jsonify({
            "success": True,
            "count": len(resources),
            "resources": resources,
        }), 200
    except Exception as e:
        return jsonify({"error": "Failed to query resources", "details": str(e)}), 500


@app.route("/api/resources/<int:resource_id>", methods=["GET"])
def get_resource(resource_id):
    """Retrieve full details of a specific library resource by ID."""
    try:
        resource = get_resource_by_id(resource_id)
        if not resource:
            return jsonify({"error": "Resource not found"}), 404
        return jsonify({"success": True, "resource": resource}), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve resource", "details": str(e)}), 500


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    """
    Chat endpoint for the Universal AI Library Assistant powered by local Ollama.
    Validates request payload, strictly checks domain boundaries in English and Kannada,
    and returns grounded responses with referenced catalogue items.
    """
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({
            "error": "Invalid request body. Expected a JSON object.",
        }), 400

    message = payload.get("message")
    if not message or not isinstance(message, str) or not message.strip():
        return jsonify({
            "error": "The 'message' field is required and must be a non-empty string.",
        }), 400

    history = payload.get("history", [])
    if not isinstance(history, list):
        history = []

    clean_message = message.strip()
    query_lang = detect_language(clean_message)

    # Pre-generation domain-validation check
    if not is_in_domain(clean_message, history):
        reject_reply = OUT_OF_DOMAIN_MESSAGE_KN if query_lang == "Kannada" else OUT_OF_DOMAIN_MESSAGE_EN
        return jsonify({
            "success": True,
            "reply": reject_reply,
            "recommended_resources": [],
            "catalogue_note": None,
            "language": query_lang,
            "model": get_model_name(),
            "status_code": 200,
        }), 200

    # Call AI assistant module using local Ollama with catalogue grounding
    result = generate_chat_response(message=clean_message, history=history)

    status_code = result.get("status_code", 200)
    return jsonify(result), status_code


@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Endpoint not found"}), 404
    return send_from_directory(app.static_folder, "index.html")


@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Local development server
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1" if host == "127.0.0.1" else "0").lower() in ("1", "true")
    print(f"Starting Universal AI Library Assistant at http://{host}:{port}")
    print(f"Connecting to Ollama at {get_ollama_base_url()} (model: {get_model_name()})")
    app.run(host=host, port=port, debug=debug)
