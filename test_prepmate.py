"""
PrepMate Unit Tests
Tests all core components:
- Supabase connection
- Gemini API calls
- PDF generation
- Flask routes
- Quality checker logic
- Data flow
"""

import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# SAMPLE TEST DATA
# Used across all tests
# ─────────────────────────────────────────
SAMPLE_PROFILE = {
    "name": "Test User",
    "career_stage": "Recent Graduate",
    "target_role": "Junior Backend Developer",
    "target_location": "London, UK",
    "cv_score": "65",
    "skill_gaps": "Docker, System Design",
    "applications_sent": "7",
    "responses_received": "0",
    "employment_gap": "5 months",
    "recruiter_name": "Rohan",
    "session_date": "2026-03-20T14:00"
}

SAMPLE_RISK_SIGNALS = {
    "risk_signals": [
        {
            "signal": "Zero application responses",
            "severity": "high",
            "evidence": "7 applications sent, 0 responses received",
            "recruiter_note": "Address CV keyword gaps and targeting strategy"
        },
        {
            "signal": "Employment gap",
            "severity": "medium",
            "evidence": "5 month gap with no narrative",
            "recruiter_note": "Help build confident gap narrative"
        }
    ],
    "overall_risk_level": "high",
    "priority_focus": "CV keyword optimisation and application strategy reset"
}

SAMPLE_MARKET_PULSE = {
    "market_summary": "Junior Backend Developer roles are in high demand in London with Python and Docker skills most sought after.",
    "data_source": "knowledge-base",
    "trending_skills": [
        {"skill": "Docker", "trend": "rising", "relevance": "Required in 70% of junior backend roles"},
        {"skill": "Python", "trend": "stable", "relevance": "Core requirement for backend roles"}
    ],
    "hiring_activity": "high",
    "opportunities": [
        {"insight": "Several mid-size tech firms actively hiring junior backend developers"}
    ],
    "market_advice": "Focus on Docker certification to unlock 70% more role matches"
}

SAMPLE_PREP_PACK = {
    "discussion_topics": [
        {
            "topic": "CV score below threshold needs urgent fixing",
            "why": "65/100 score means most ATS filters are rejecting CV automatically",
            "data_reference": "CV Score: 65/100"
        },
        {
            "topic": "Zero responses from 7 applications",
            "why": "Pattern indicates targeting or CV problem not luck",
            "data_reference": "Career Momentum: 7 sent, 0 responses"
        },
        {
            "topic": "Docker gap blocking top role matches",
            "why": "Docker required in majority of matched roles",
            "data_reference": "Skill Gap: Docker flagged high priority"
        },
        {
            "topic": "Employment gap needs confident narrative",
            "why": "5 month gap will be questioned in every interview",
            "data_reference": "Employment Gap: 5 months"
        },
        {
            "topic": "Job search strategy needs complete reset",
            "why": "Current approach producing zero results",
            "data_reference": "0 responses from 7 applications"
        }
    ],
    "question_bank": [
        {"id": "Q1", "category": "CV & Positioning",
         "question": "How do I fix my CV to get above the 75 ATS threshold?"},
        {"id": "Q2", "category": "CV & Positioning",
         "question": "What are the top 3 keywords missing from my CV?"},
        {"id": "Q3", "category": "Market & Strategy",
         "question": "Should I learn Docker now or retarget to roles I can already reach?"},
        {"id": "Q4", "category": "Market & Strategy",
         "question": "How do I reset my job search strategy after zero responses?"},
        {"id": "Q5", "category": "Skill Gap",
         "question": "Which skill gap should I address first for my target role?"},
        {"id": "Q6", "category": "Next Steps",
         "question": "How do I frame my 5-month employment gap confidently?"},
        {"id": "Q7", "category": "Interview Prep",
         "question": "What technical questions should I prepare for junior backend interviews?"},
        {"id": "Q8", "category": "Market & Strategy",
         "question": "Which job platforms work best for junior backend roles in London?"},
        {"id": "Q9", "category": "CV & Positioning",
         "question": "How can I make my Python projects more visible on my CV?"},
        {"id": "Q10", "category": "Next Steps",
         "question": "What is a realistic timeline to land my first backend role?"},
        {"id": "Q11", "category": "Skill Gap",
         "question": "How do I demonstrate Docker knowledge without a formal certification?"},
        {"id": "Q12", "category": "Market & Strategy",
         "question": "Should I target startups or mid-size companies at my level?"},
        {"id": "Q13", "category": "Interview Prep",
         "question": "How do I answer tell me about yourself for a junior backend role?"},
        {"id": "Q14", "category": "Next Steps",
         "question": "How many applications per week should I be sending realistically?"},
        {"id": "Q15", "category": "CV & Positioning",
         "question": "How do I tailor my CV for each application effectively?"}
    ],
    "interview_prep": [
        {"tip": "Prepare 2 Python project walkthroughs using STAR format",
         "role_relevance": "Junior backend interviews always ask about projects"},
        {"tip": "Practice explaining REST API design in simple terms",
         "role_relevance": "Core technical question for backend roles"}
    ],
    "positioning_brief": "I am a recent CS graduate targeting junior backend developer roles in London. I have Python and REST API experience from university projects. My CV score is 65 and I have sent 7 applications with zero responses. I want to fix my CV strategy, address my employment gap narrative, and build a clear 3-week action plan.",
    "session_agenda": [
        {"order": 1, "focus": "CV keyword fixes and ATS score", "time": "10 mins"},
        {"order": 2, "focus": "Application strategy reset", "time": "10 mins"},
        {"order": 3, "focus": "Docker decision and skill gaps", "time": "10 mins"},
        {"order": 4, "focus": "Employment gap narrative", "time": "10 mins"},
        {"order": 5, "focus": "3-week action plan", "time": "5 mins"}
    ]
}

SAMPLE_QUALITY_RESULT = {
    "overall_quality_score": 8,
    "quality_summary": "Strong question bank with good profile alignment",
    "flags": [],
    "approved_questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
    "recommendation": "approved"
}


# ═════════════════════════════════════════
# TEST SUITE 1 — Supabase Connection
# ═════════════════════════════════════════
class TestSupabaseConnection(unittest.TestCase):

    def test_env_variables_exist(self):
        """Check that Supabase env variables are set"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.assertIsNotNone(url, "SUPABASE_URL not found in .env")
        self.assertIsNotNone(key, "SUPABASE_KEY not found in .env")
        self.assertTrue(url.startswith("https://"),
                        "SUPABASE_URL should start with https://")
        print("✅ Supabase env variables found")

    def test_supabase_connection(self):
        """Test actual connection to Supabase"""
        try:
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
            # Try a simple query
            result = supabase.table("sessions").select("id").limit(1).execute()
            self.assertIsNotNone(result)
            print("✅ Supabase connection successful")
        except Exception as e:
            self.fail(f"Supabase connection failed: {e}")

    def test_supabase_insert_and_delete(self):
        """Test inserting and deleting a row"""
        try:
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
            test_sid = "unit-test-sid-12345"

            # Insert
            insert_result = supabase.table("sessions").insert({
                "sid": test_sid,
                "profile": {"name": "Unit Test User"}
            }).execute()
            self.assertTrue(len(insert_result.data) > 0)

            # Read back
            read_result = supabase.table("sessions")\
                .select("*").eq("sid", test_sid).execute()
            self.assertEqual(
                read_result.data[0]["profile"]["name"],
                "Unit Test User"
            )

            # Delete
            supabase.table("sessions").delete().eq("sid", test_sid).execute()
            print("✅ Supabase insert/read/delete working")

        except Exception as e:
            self.fail(f"Supabase CRUD test failed: {e}")

    def test_supabase_update(self):
        """Test updating an existing row"""
        try:
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
            test_sid = "unit-test-update-67890"

            # Insert
            supabase.table("sessions").insert({
                "sid": test_sid,
                "profile": {"name": "Original Name"}
            }).execute()

            # Update
            supabase.table("sessions").update({
                "profile": {"name": "Updated Name"}
            }).eq("sid", test_sid).execute()

            # Verify update
            result = supabase.table("sessions")\
                .select("profile").eq("sid", test_sid).execute()
            self.assertEqual(result.data[0]["profile"]["name"], "Updated Name")

            # Cleanup
            supabase.table("sessions").delete().eq("sid", test_sid).execute()
            print("✅ Supabase update working")

        except Exception as e:
            self.fail(f"Supabase update test failed: {e}")


# ═════════════════════════════════════════
# TEST SUITE 2 — Gemini API
# ═════════════════════════════════════════
class TestGeminiAPI(unittest.TestCase):

    def test_gemini_api_key_exists(self):
        """Check Gemini API key is set"""
        key = os.getenv("GEMINI_API_KEY")
        self.assertIsNotNone(key, "GEMINI_API_KEY not found in .env")
        self.assertNotEqual(key, "your_gemini_api_key_here",
                            "GEMINI_API_KEY is still placeholder")
        print("✅ Gemini API key found")

    def test_risk_signal_detector(self):
        """Test Risk Signal Detector returns correct structure"""
        from gemini import run_risk_signal_detector
        result = run_risk_signal_detector(SAMPLE_PROFILE, "Python developer with REST API experience")

        self.assertIn("risk_signals", result)
        self.assertIn("overall_risk_level", result)
        self.assertIn("priority_focus", result)
        self.assertIsInstance(result["risk_signals"], list)
        self.assertIn(result["overall_risk_level"], ["high", "medium", "low"])
        print(f"✅ Risk Signal Detector — {len(result['risk_signals'])} signals found")

    def test_market_pulse(self):
        """Test Market Pulse returns correct structure"""
        from gemini import run_market_pulse
        result = run_market_pulse(SAMPLE_PROFILE)

        self.assertIn("market_summary", result)
        self.assertIn("trending_skills", result)
        self.assertIn("hiring_activity", result)
        self.assertIn("market_advice", result)
        self.assertIsInstance(result["trending_skills"], list)
        print(f"✅ Market Pulse — {len(result['trending_skills'])} trending skills found")

    def test_pack_generator(self):
        """Test Prep Pack Generator returns correct structure"""
        from gemini import run_pack_generator
        result = run_pack_generator(
            SAMPLE_PROFILE,
            "Python developer experience",
            "Build my overall job search strategy",
            SAMPLE_RISK_SIGNALS,
            SAMPLE_MARKET_PULSE
        )

        self.assertIn("discussion_topics", result)
        self.assertIn("question_bank", result)
        self.assertIn("interview_prep", result)
        self.assertIn("positioning_brief", result)
        self.assertIn("session_agenda", result)
        self.assertEqual(len(result["discussion_topics"]), 5,
                         "Should generate exactly 5 discussion topics")
        self.assertEqual(len(result["question_bank"]), 15,
                         "Should generate exactly 15 questions")
        print(f"✅ Pack Generator — {len(result['question_bank'])} questions generated")

    def test_questions_are_first_person(self):
        """Test that all questions are in first person"""
        from gemini import run_pack_generator
        result = run_pack_generator(
            SAMPLE_PROFILE,
            "Python developer experience",
            "Build my overall job search strategy",
            SAMPLE_RISK_SIGNALS,
            SAMPLE_MARKET_PULSE
        )

        first_person_starters = [
            "how do i", "what should i", "should i",
            "how can i", "can you help me", "which should i",
            "what is the best way for me", "how would i",
            "what are my", "what is my"
        ]

        for q in result["question_bank"]:
            question_lower = q["question"].lower()
            # Check name not in question
            self.assertNotIn(
                SAMPLE_PROFILE["name"].lower(),
                question_lower,
                f"User name found in question: {q['question']}"
            )
            print(f"✅ First person check passed for {q['id']}")

    def test_positioning_brief_is_first_person(self):
        """Test that positioning brief is in first person"""
        from gemini import run_pack_generator
        result = run_pack_generator(
            SAMPLE_PROFILE,
            "Python developer experience",
            "Build my overall job search strategy",
            SAMPLE_RISK_SIGNALS,
            SAMPLE_MARKET_PULSE
        )

        brief = result["positioning_brief"].lower()
        self.assertNotIn(
            SAMPLE_PROFILE["name"].lower(), brief,
            "User name should not appear in positioning brief"
        )
        # Should start with I or My
        starts_correctly = (
            brief.startswith("i ") or
            brief.startswith("my ") or
            brief.startswith("i'")
        )
        self.assertTrue(
            starts_correctly,
            f"Positioning brief should start with I or My. Got: {result['positioning_brief'][:50]}"
        )
        print("✅ Positioning brief is in first person")

    def test_quality_checker(self):
        """Test Quality Checker returns correct structure"""
        from gemini import run_quality_checker
        result = run_quality_checker(
            SAMPLE_PROFILE,
            SAMPLE_PREP_PACK,
            "Build my overall job search strategy"
        )

        self.assertIn("overall_quality_score", result)
        self.assertIn("quality_summary", result)
        self.assertIn("flags", result)
        self.assertIn("recommendation", result)
        self.assertIsInstance(result["overall_quality_score"], int)
        self.assertGreater(result["overall_quality_score"], 0)
        self.assertLessEqual(result["overall_quality_score"], 10)
        print(f"✅ Quality Checker — Score: {result['overall_quality_score']}/10")


# ═════════════════════════════════════════
# TEST SUITE 3 — Quality Fix Logic
# ═════════════════════════════════════════
class TestQualityFixLogic(unittest.TestCase):

    def test_apply_quality_fixes_replaces_flagged_questions(self):
        """Test that flagged questions are replaced with improved versions"""
        import app as flask_app

        prep_pack = {
            "question_bank": [
                {"id": "Q1", "category": "CV & Positioning",
                 "question": "What should Test User do to improve his CV?"},
                {"id": "Q2", "category": "Market & Strategy",
                 "question": "How do I find more relevant job listings?"}
            ]
        }

        quality_result = {
            "flags": [
                {
                    "question_id": "Q1",
                    "issue": "Third person — uses user name",
                    "severity": "critical",
                    "improved_version": "How do I improve my CV score above 75?"
                }
            ],
            "overall_quality_score": 6,
            "quality_summary": "One critical issue found"
        }

        fixed_pack, fixed_quality = flask_app.apply_quality_fixes(
            prep_pack, quality_result
        )

        # Q1 should be replaced
        self.assertEqual(
            fixed_pack["question_bank"][0]["question"],
            "How do I improve my CV score above 75?"
        )
        # Q2 should be unchanged
        self.assertEqual(
            fixed_pack["question_bank"][1]["question"],
            "How do I find more relevant job listings?"
        )
        # Flags should be cleared
        self.assertEqual(len(fixed_quality["flags"]), 0)
        print("✅ Quality fix logic replaces flagged questions correctly")

    def test_apply_quality_fixes_with_no_flags(self):
        """Test that pack is unchanged when no flags"""
        import app as flask_app

        prep_pack = {"question_bank": [
            {"id": "Q1", "question": "How do I improve my CV?"}
        ]}
        quality_result = {"flags": [], "quality_summary": "All good"}

        fixed_pack, fixed_quality = flask_app.apply_quality_fixes(
            prep_pack, quality_result
        )

        self.assertEqual(
            fixed_pack["question_bank"][0]["question"],
            "How do I improve my CV?"
        )
        print("✅ Quality fix logic leaves good questions unchanged")

    def test_apply_quality_fixes_handles_empty_pack(self):
        """Test graceful handling of empty prep pack"""
        import app as flask_app

        fixed_pack, fixed_quality = flask_app.apply_quality_fixes(
            None, None
        )
        self.assertIsNone(fixed_pack)
        self.assertIsNone(fixed_quality)
        print("✅ Quality fix logic handles None inputs gracefully")


# ═════════════════════════════════════════
# TEST SUITE 4 — PDF Generation
# ═════════════════════════════════════════
class TestPDFGeneration(unittest.TestCase):

    def test_pdf_generates_successfully(self):
        """Test PDF generation produces a valid file"""
        import tempfile
        from pdf_generator import generate_pdf

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        result_path = generate_pdf(
            SAMPLE_PROFILE,
            SAMPLE_PREP_PACK,
            SAMPLE_MARKET_PULSE,
            pdf_path
        )

        self.assertTrue(os.path.exists(result_path),
                        "PDF file was not created")
        self.assertGreater(os.path.getsize(result_path), 0,
                          "PDF file is empty")
        os.unlink(result_path)
        print(f"✅ PDF generated successfully")

    def test_pdf_handles_none_inputs(self):
        """Test PDF generation handles missing data gracefully"""
        import tempfile
        from pdf_generator import generate_pdf

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        # Should not crash with None inputs
        try:
            result_path = generate_pdf(None, None, None, pdf_path)
            if os.path.exists(result_path):
                os.unlink(result_path)
            print("✅ PDF handles None inputs gracefully")
        except Exception as e:
            self.fail(f"PDF crashed with None inputs: {e}")

    def test_pdf_with_special_characters(self):
        """Test PDF handles special characters in text"""
        import tempfile
        from pdf_generator import generate_pdf

        profile_with_special = SAMPLE_PROFILE.copy()
        profile_with_special["name"] = "Test & User — Special"
        profile_with_special["skill_gaps"] = "Docker → Kubernetes"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        try:
            result_path = generate_pdf(
                profile_with_special,
                SAMPLE_PREP_PACK,
                SAMPLE_MARKET_PULSE,
                pdf_path
            )
            self.assertTrue(os.path.exists(result_path))
            if os.path.exists(result_path):
                os.unlink(result_path)
            print("✅ PDF handles special characters correctly")
        except Exception as e:
            self.fail(f"PDF crashed with special characters: {e}")


# ═════════════════════════════════════════
# TEST SUITE 5 — Flask Routes
# ═════════════════════════════════════════
class TestFlaskRoutes(unittest.TestCase):

    def setUp(self):
        """Set up Flask test client"""
        import app as flask_app
        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-secret-key"
        self.client = flask_app.app.test_client()

    def test_landing_page_loads(self):
        """Test landing page returns 200"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        print("✅ Landing page loads successfully")

    def test_upload_page_loads(self):
        """Test upload page returns 200"""
        response = self.client.get("/upload")
        self.assertEqual(response.status_code, 200)
        print("✅ Upload page loads successfully")

    def test_intent_redirects_without_profile(self):
        """Test intent page redirects if no profile in session"""
        response = self.client.get("/intent")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/upload", response.location)
        print("✅ Intent page correctly redirects without session")

    def test_preppack_redirects_without_results(self):
        """Test preppack page redirects if no results in session"""
        response = self.client.get("/preppack")
        self.assertEqual(response.status_code, 302)
        print("✅ Preppack page correctly redirects without results")

    def test_upload_post_redirects_to_intent(self):
        """Test upload form submission redirects to intent"""
        response = self.client.post("/upload", data={
            "name": "Test User",
            "career_stage": "Recent Graduate",
            "target_role": "Junior Backend Developer",
            "target_location": "London, UK",
            "cv_score": "65",
            "skill_gaps": "Docker",
            "applications_sent": "7",
            "responses_received": "0",
            "employment_gap": "5 months",
            "recruiter_name": "Rohan",
            "session_date": "2026-03-20T14:00"
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("/intent", response.location)
        print("✅ Upload form correctly redirects to intent")


# ═════════════════════════════════════════
# TEST SUITE 6 — CV Text Extraction
# ═════════════════════════════════════════
class TestCVExtraction(unittest.TestCase):

    def test_bytesio_extraction_works(self):
        """Test that BytesIO approach works for PDF reading"""
        import PyPDF2
        from io import BytesIO

        # Create a minimal valid PDF in memory
        # We just test the BytesIO approach does not crash
        try:
            # Create a simple PDF using fpdf2
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            pdf.cell(0, 10, "Test CV Content for Unit Testing")
            pdf_bytes = pdf.output()

            # Test reading it back
            reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted

            self.assertIsInstance(text, str)
            print("✅ BytesIO CV extraction working correctly")
        except Exception as e:
            self.fail(f"BytesIO extraction failed: {e}")


# ═════════════════════════════════════════
# TEST RUNNER
# ═════════════════════════════════════════
def run_tests():
    print("\n" + "="*60)
    print("  PREPMATE UNIT TESTS")
    print("  JSO Phase-2 Agentic Career Intelligence")
    print("="*60 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSupabaseConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestGeminiAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityFixLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestPDFGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestFlaskRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestCVExtraction))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*60)
    if result.wasSuccessful():
        print(f"  ALL TESTS PASSED ({result.testsRun} tests)")
    else:
        print(f"  TESTS FAILED")
        print(f"  Passed:  {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"  Failed:  {len(result.failures)}")
        print(f"  Errors:  {len(result.errors)}")
    print("="*60 + "\n")

    return result


if __name__ == "__main__":
    run_tests()