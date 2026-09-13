import os
import json
import uuid
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.pdf_extractor import PDFExtractor
from services.ai_processor import AIProcessor
from services.question_generator import QuestionGenerator
from services.test_manager import TestManager

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "studymate_secure_development_secret_2026")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB max file size
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Helper function to check allowed file extensions
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# Frontend Page Routes
# ==========================================

@app.route("/")
def index():
    bank = QuestionGenerator.load_question_bank()
    has_bank = bool(bank.get("questions") and len(bank["questions"]) > 0)
    bank_meta = bank.get("metadata", {})
    provider_info = AIProcessor.get_provider_info()
    return render_template(
        "index.html",
        has_bank=has_bank,
        bank_meta=bank_meta,
        provider_info=provider_info
    )

@app.route("/upload")
def upload_page():
    return render_template("upload.html")

@app.route("/processing")
def processing_page():
    return render_template("processing.html")

@app.route("/setup-test")
def setup_test_page():
    bank = QuestionGenerator.load_question_bank()
    questions = bank.get("questions", [])
    if not questions:
        return redirect(url_for("upload_page"))
    
    metadata = bank.get("metadata", {})
    topics = list(set(q.get("topic", "General Concepts") for q in questions))
    
    # Count questions per difficulty
    diff_counts = {"Easy": 0, "Medium": 0, "Hard": 0}
    for q in questions:
        d = q.get("difficulty", "Medium")
        if d in diff_counts:
            diff_counts[d] += 1
        else:
            diff_counts["Medium"] += 1

    return render_template(
        "setup_test.html",
        total_questions=len(questions),
        metadata=metadata,
        topics=topics,
        diff_counts=diff_counts
    )

@app.route("/test")
def test_page():
    return render_template("test.html")

@app.route("/result/<test_id>")
def result_page(test_id):
    result = TestManager.get_result_by_id(test_id)
    return render_template("result.html", test_id=test_id, result_found=bool(result))

# ==========================================
# REST API Endpoints
# ==========================================

@app.route("/api/upload", methods=["POST"])
def api_upload_pdf():
    if "pdf_file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded in the request."}), 400

    file = request.files["pdf_file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file."}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Invalid file format. Only PDF documents are supported."}), 400

    orig_filename = secure_filename(file.filename) or "study_material.pdf"
    unique_name = f"{uuid.uuid4().hex[:8]}_{orig_filename}"
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(saved_path)

    # Store uploaded path in session
    session["uploaded_pdf_path"] = saved_path
    session["uploaded_pdf_name"] = orig_filename

    # Quick inspection of page count & size
    file_size_mb = round(os.path.getsize(saved_path) / (1024 * 1024), 2)

    return jsonify({
        "success": True,
        "filename": orig_filename,
        "file_size_mb": file_size_mb,
        "redirect_url": url_for("processing_page")
    })

@app.route("/api/process", methods=["POST"])
def api_process_pdf():
    pdf_path = session.get("uploaded_pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        # Check if sample exists
        sample_path = os.path.join(app.config["UPLOAD_FOLDER"], "sample_machine_learning_primer.pdf")
        if os.path.exists(sample_path):
            pdf_path = sample_path
        else:
            return jsonify({"success": False, "error": "No active PDF upload found. Please upload a file first."}), 400

    try:
        # Step 1: Extract and chunk PDF
        extraction_data = PDFExtractor.extract_from_file(pdf_path)

        # Step 2: Generate Question Bank
        bank_data = QuestionGenerator.generate_question_bank(extraction_data)

        return jsonify({
            "success": True,
            "filename": extraction_data.get("filename"),
            "total_pages": extraction_data.get("total_pages"),
            "total_words": extraction_data.get("total_words"),
            "total_questions": len(bank_data.get("questions", [])),
            "topics": extraction_data.get("topics", []),
            "redirect_url": url_for("setup_test_page")
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/start-test", methods=["POST"])
def api_start_test():
    data = request.get_json() or {}
    question_count = int(data.get("question_count", 20))
    difficulty = data.get("difficulty", "Mixed")
    topics = data.get("topics", [])

    try:
        session_data = TestManager.create_test_session(
            question_count=question_count,
            difficulty=difficulty,
            topics_filter=topics
        )
        return jsonify({"success": True, "test_session": session_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/submit-test", methods=["POST"])
def api_submit_test():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    answers = data.get("answers", {})
    client_test_data = data.get("client_test_data")

    if not session_id:
        return jsonify({"success": False, "error": "Missing session_id."}), 400

    try:
        evaluation = TestManager.evaluate_test_session(
            session_id=session_id,
            user_answers=answers,
            client_test_data=client_test_data
        )
        return jsonify({
            "success": True,
            "test_id": evaluation["test_id"],
            "redirect_url": url_for("result_page", test_id=evaluation["test_id"])
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/result/<test_id>")
def api_get_result(test_id):
    result = TestManager.get_result_by_id(test_id)
    if not result:
        return jsonify({"success": False, "error": "Test result not found."}), 404
    return jsonify({"success": True, "result": result})

@app.route("/api/sample-demo", methods=["POST"])
def api_sample_demo():
    from sample_pdf_creator import generate_sample_academic_pdf
    sample_path = generate_sample_academic_pdf()
    session["uploaded_pdf_path"] = sample_path
    session["uploaded_pdf_name"] = "sample_machine_learning_primer.pdf"
    return jsonify({"success": True, "redirect_url": url_for("processing_page")})

@app.route("/api/status")
def api_status():
    bank = QuestionGenerator.load_question_bank()
    return jsonify({
        "success": True,
        "has_bank": bool(bank.get("questions")),
        "total_questions": len(bank.get("questions", [])),
        "metadata": bank.get("metadata", {}),
        "provider_info": AIProcessor.get_provider_info()
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
