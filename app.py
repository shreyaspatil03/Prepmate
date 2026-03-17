from flask import (Flask, render_template, request,
                   session, redirect, url_for, send_file, jsonify)
from gemini import (run_risk_signal_detector,
                    run_market_pulse,
                    run_pack_generator,
                    run_quality_checker)
from pdf_generator import generate_pdf
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import threading
import uuid
import tempfile
import PyPDF2

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "prepmate_jso_secret")

# ─────────────────────────────────────────
# SUPABASE CLIENT
# ─────────────────────────────────────────
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


# ─────────────────────────────────────────
# SUPABASE HELPERS
# ─────────────────────────────────────────
def get_session_id():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    return session["sid"]


def save_all(sid, data):
    """Save multiple fields to Supabase in one query"""
    try:
        existing = supabase.table("sessions") \
            .select("id").eq("sid", sid).execute()
        if existing.data:
            supabase.table("sessions") \
                .update(data).eq("sid", sid).execute()
        else:
            data["sid"] = sid
            supabase.table("sessions").insert(data).execute()
    except Exception as e:
        print(f"Supabase save error: {e}")


def load_all(sid):
    """Load all fields for this session in one query"""
    try:
        result = supabase.table("sessions") \
            .select("*").eq("sid", sid).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        print(f"Supabase load error: {e}")
        return {}


def apply_quality_fixes(prep_pack, quality_result):
    """Auto-replace flagged questions with improved versions"""
    if not (quality_result and quality_result.get("flags")
            and prep_pack and prep_pack.get("question_bank")):
        return prep_pack, quality_result

    flags_map = {
        flag["question_id"]: flag["improved_version"]
        for flag in quality_result["flags"]
        if flag.get("question_id") and flag.get("improved_version")
    }

    for q in prep_pack["question_bank"]:
        if q.get("id") in flags_map:
            q["question"] = flags_map[q["id"]]

    quality_result["flags"] = []
    quality_result["quality_summary"] = (
        "All questions reviewed and optimised by PrepMate Quality Checker."
    )
    return prep_pack, quality_result


# ─────────────────────────────────────────
# ROUTE 1 — Landing Page
# ─────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────
# ROUTE 2 — CV Upload + Profile Form
# ─────────────────────────────────────────
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        sid = get_session_id()

        profile = {
            "name": request.form.get("name", ""),
            "career_stage": request.form.get("career_stage", ""),
            "target_role": request.form.get("target_role", ""),
            "target_location": request.form.get("target_location", ""),
            "cv_score": request.form.get("cv_score", "Not provided"),
            "skill_gaps": request.form.get("skill_gaps", "Not specified"),
            "applications_sent": request.form.get("applications_sent", "0"),
            "responses_received": request.form.get("responses_received", "0"),
            "employment_gap": request.form.get("employment_gap", "None"),
            "recruiter_name": request.form.get("recruiter_name", "Your Recruiter"),
            "session_date": request.form.get("session_date", ""),
        }

        # Extract CV text from PDF
        # Using BytesIO — works on Windows, Linux, and Render
        # No tempfile needed — reads directly from memory
        cv_text = ""
        if "cv_file" in request.files:
            cv_file = request.files["cv_file"]
            if cv_file and cv_file.filename.endswith(".pdf"):
                try:
                    from io import BytesIO
                    pdf_bytes = BytesIO(cv_file.read())
                    reader = PyPDF2.PdfReader(pdf_bytes)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            cv_text += extracted
                except Exception as e:
                    print(f"CV extraction error: {e}")
                    cv_text = "CV uploaded but text extraction failed."

        # Save to Supabase
        save_all(sid, {
            "profile": profile,
            "cv_text": cv_text[:3000]
        })

        session["sid"] = sid
        session["has_profile"] = True
        return redirect(url_for("intent"))

    return render_template("upload.html")


# ─────────────────────────────────────────
# ROUTE 3 — Intent Detector
# ─────────────────────────────────────────
@app.route("/intent", methods=["GET", "POST"])
def intent():
    if not session.get("has_profile"):
        return redirect(url_for("upload"))

    if request.method == "POST":
        sid = get_session_id()
        intent_value = request.form.get(
            "intent",
            "Build my overall job search strategy"
        )
        save_all(sid, {"intent": intent_value})
        session["has_intent"] = True
        return redirect(url_for("loading"))

    return render_template("intent.html")


# ─────────────────────────────────────────
# ROUTE 4 — Loading Page
# ─────────────────────────────────────────
@app.route("/loading")
def loading():
    if not session.get("has_intent"):
        return redirect(url_for("intent"))
    return render_template("loading.html")


# ─────────────────────────────────────────
# BACKGROUND WORKER
# ─────────────────────────────────────────
def _run_gemini_background(sid, profile, cv_text, intent):
    """Runs all Gemini calls in a daemon thread — never blocks HTTP workers."""
    try:
        # Mark processing started
        save_all(sid, {"status": "processing"})

        # Calls 1 & 2 are independent — run in parallel
        results = {}

        def _risk():
            results["risk"] = run_risk_signal_detector(profile, cv_text)

        def _market():
            results["market"] = run_market_pulse(profile)

        t1 = threading.Thread(target=_risk)
        t2 = threading.Thread(target=_market)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        risk_signals = results.get("risk", {})
        market_pulse = results.get("market", {})

        # Calls 3 & 4 depend on the above
        prep_pack = run_pack_generator(
            profile, cv_text, intent, risk_signals, market_pulse
        )
        quality_result = run_quality_checker(profile, prep_pack, intent)

        # Auto-fix flagged questions
        prep_pack, quality_result = apply_quality_fixes(prep_pack, quality_result)

        # Persist everything + mark done
        save_all(sid, {
            "risk_signals": risk_signals,
            "market_pulse": market_pulse,
            "prep_pack": prep_pack,
            "quality_result": quality_result,
            "status": "done"
        })
    except Exception as e:
        print(f"Background processing error: {e}")
        save_all(sid, {"status": "error"})


# ─────────────────────────────────────────
# ROUTE 5 — Start Processing (non-blocking)
# ─────────────────────────────────────────
@app.route("/start-processing")
def start_processing():
    """Kicks off background Gemini work and returns immediately."""
    if not session.get("has_profile"):
        return jsonify({"error": "no_profile"}), 400

    sid = get_session_id()
    row = load_all(sid)
    profile = row.get("profile")
    cv_text = row.get("cv_text") or ""
    intent = row.get("intent") or "Build my overall job search strategy"

    if not profile:
        return jsonify({"error": "no_profile"}), 400

    # Don't re-start if already running or done
    current_status = row.get("status")
    if current_status in ("processing", "done"):
        return jsonify({"status": current_status})

    t = threading.Thread(
        target=_run_gemini_background,
        args=(sid, profile, cv_text, intent),
        daemon=True
    )
    t.start()
    return jsonify({"status": "started"})


# ─────────────────────────────────────────
# ROUTE 5b — Status Polling
# ─────────────────────────────────────────
@app.route("/status")
def status():
    """Polled by the loading page every 2 s to check if results are ready."""
    if not session.get("has_profile"):
        return jsonify({"status": "no_session"})

    sid = get_session_id()
    row = load_all(sid)
    current_status = row.get("status", "idle")

    if current_status == "done":
        session["has_results"] = True
        return jsonify({"status": "done", "redirect": url_for("preppack")})

    return jsonify({"status": current_status})


# ─────────────────────────────────────────
# ROUTE 6 — Prep Pack Output
# ─────────────────────────────────────────
@app.route("/preppack")
def preppack():
    if not session.get("has_results"):
        return redirect(url_for("upload"))

    sid = get_session_id()
    row = load_all(sid)

    return render_template(
        "preppack.html",
        profile=row.get("profile"),
        intent=row.get("intent"),
        prep_pack=row.get("prep_pack"),
        market_pulse=row.get("market_pulse"),
        quality_result=row.get("quality_result")
    )


# ─────────────────────────────────────────
# ROUTE 7 — Recruiter Brief
# ─────────────────────────────────────────
@app.route("/recruiter")
def recruiter():
    sid = get_session_id()
    row = load_all(sid)

    return render_template(
        "recruiter.html",
        profile=row.get("profile"),
        risk_signals=row.get("risk_signals"),
        prep_pack=row.get("prep_pack")
    )


# ─────────────────────────────────────────
# ROUTE 8 — Download PDF
# ─────────────────────────────────────────
@app.route("/download")
def download():
    if not session.get("has_results"):
        return redirect(url_for("preppack"))

    sid = get_session_id()
    row = load_all(sid)

    # Use tempfile for PDF — works on both local and Render
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".pdf"
    ) as tmp:
        pdf_path = tmp.name

    pdf_path = generate_pdf(
        row.get("profile"),
        row.get("prep_pack"),
        row.get("market_pulse"),
        pdf_path
    )

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name="PrepMate_Consultation_Pack.pdf"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)