"""
PrepMate Intent Alignment Tests
Tests whether the generated prep pack output
is actually tailored to the user's declared intent.

4 intents tested:
1. Fix my CV and positioning
2. Understand the job market
3. Prepare for interviews
4. Build my overall job search strategy
"""

import unittest
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# SAMPLE PROFILE — same user, 4 different intents
# ─────────────────────────────────────────
BASE_PROFILE = {
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

CV_TEXT = "Python developer with REST API and Git experience. Built 3 university projects."

RISK_SIGNALS = {
    "risk_signals": [
        {"signal": "Zero responses", "severity": "high",
         "evidence": "7 apps, 0 responses", "recruiter_note": "Fix CV targeting"}
    ],
    "overall_risk_level": "high",
    "priority_focus": "CV and targeting strategy"
}

MARKET_PULSE = {
    "market_summary": "High demand for junior backend developers in London.",
    "data_source": "knowledge-base",
    "trending_skills": [{"skill": "Docker", "trend": "rising", "relevance": "Core requirement"}],
    "hiring_activity": "high",
    "opportunities": [{"insight": "Several firms hiring junior backend devs"}],
    "market_advice": "Focus on Docker to unlock more opportunities"
}

# ─────────────────────────────────────────
# INTENT KEYWORDS
# What words SHOULD appear for each intent
# What words should NOT dominate for each intent
# ─────────────────────────────────────────
INTENT_RULES = {
    "Fix my CV and positioning": {
        "should_contain": [
            "cv", "resume", "keyword", "ats", "score",
            "formatting", "positioning", "improve"
        ],
        "should_not_dominate": [
            "interview technique", "behavioral question",
            "market trend", "salary negotiation"
        ],
        "min_cv_questions": 4
    },
    "Understand the job market": {
        "should_contain": [
            "market", "trend", "demand", "opportunity",
            "industry", "salary", "hiring", "company"
        ],
        "should_not_dominate": [
            "cv formatting", "ats score", "cover letter"
        ],
        "min_market_questions": 4
    },
    "Prepare for interviews I already have": {
        "should_contain": [
            "interview", "question", "answer", "prepare",
            "technical", "behavioral", "star", "practice"
        ],
        "should_not_dominate": [
            "cv score", "application strategy", "job search"
        ],
        "min_interview_questions": 4
    },
    "Build my overall job search strategy": {
        "should_contain": [
            "strategy", "approach", "plan", "action",
            "search", "application", "target", "method"
        ],
        "should_not_dominate": [],
        "min_strategy_questions": 3
    }
}


class TestIntentAlignment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Generate prep packs for all 4 intents once"""
        from gemini import run_pack_generator
        cls.packs = {}

        intents = [
            "Fix my CV and positioning — I want to improve my CV score, address keyword gaps, and strengthen how I present myself to recruiters.",
            "Understand the job market — I want to know what is happening in my target role market, which skills are trending, and where the best opportunities are.",
            "Prepare for interviews I already have — I want to practice articulation, prepare STAR method answers, and get ready for specific interviews coming up.",
            "Build my overall job search strategy — I want to reset my approach, activate JSO features I haven't used, and build a clear action plan."
        ]

        print("\n Generating prep packs for all 4 intents...")
        print("This will take 30-60 seconds...\n")

        for intent in intents:
            # Get short intent name for dict key
            short_name = intent.split(" — ")[0]
            print(f"  Generating for: {short_name}...")
            pack = run_pack_generator(
                BASE_PROFILE, CV_TEXT, intent,
                RISK_SIGNALS, MARKET_PULSE
            )
            cls.packs[short_name] = {
                "intent": intent,
                "pack": pack
            }
        print("\n All 4 prep packs generated. Running alignment tests...\n")

    # ─────────────────────────────────────
    # TEST 1 — CV Intent Alignment
    # ─────────────────────────────────────
    def test_cv_intent_topics_are_cv_focused(self):
        """CV intent should produce CV-focused discussion topics"""
        pack = self.packs["Fix my CV and positioning"]["pack"]
        topics_text = " ".join([
            t["topic"].lower() + " " + t["why"].lower()
            for t in pack.get("discussion_topics", [])
        ])

        cv_keywords = ["cv", "resume", "keyword", "ats", "score", "format"]
        found = [kw for kw in cv_keywords if kw in topics_text]

        self.assertGreater(
            len(found), 1,
            f"CV intent topics should mention CV keywords. Found: {found}\nTopics: {topics_text[:300]}"
        )
        print(f"✅ CV intent — topics contain CV keywords: {found}")

    def test_cv_intent_questions_are_cv_focused(self):
        """CV intent should produce mostly CV-focused questions"""
        pack = self.packs["Fix my CV and positioning"]["pack"]
        questions = pack.get("question_bank", [])

        cv_questions = [
            q for q in questions
            if q.get("category") == "CV & Positioning"
        ]

        self.assertGreaterEqual(
            len(cv_questions), 4,
            f"CV intent should have at least 4 CV questions. Got {len(cv_questions)}"
        )
        print(f"✅ CV intent — {len(cv_questions)} CV & Positioning questions generated")

    def test_cv_intent_positioning_brief_mentions_cv(self):
        """CV intent brief should mention CV improvement"""
        pack = self.packs["Fix my CV and positioning"]["pack"]
        brief = pack.get("positioning_brief", "").lower()

        self.assertTrue(
            "cv" in brief or "resume" in brief or "score" in brief,
            f"CV intent brief should mention CV. Brief: {brief[:200]}"
        )
        print("✅ CV intent — positioning brief mentions CV")

    # ─────────────────────────────────────
    # TEST 2 — Market Intent Alignment
    # ─────────────────────────────────────
    def test_market_intent_topics_are_market_focused(self):
        """Market intent should produce market-focused topics"""
        pack = self.packs["Understand the job market"]["pack"]
        topics_text = " ".join([
            t["topic"].lower() + " " + t["why"].lower()
            for t in pack.get("discussion_topics", [])
        ])

        market_keywords = ["market", "trend", "demand", "skill", "industry", "opportunity"]
        found = [kw for kw in market_keywords if kw in topics_text]

        self.assertGreater(
            len(found), 1,
            f"Market intent topics should mention market keywords. Found: {found}"
        )
        print(f"✅ Market intent — topics contain market keywords: {found}")

    def test_market_intent_questions_are_market_focused(self):
        """Market intent should produce mostly market-focused questions"""
        pack = self.packs["Understand the job market"]["pack"]
        questions = pack.get("question_bank", [])

        market_questions = [
            q for q in questions
            if q.get("category") == "Market & Strategy"
        ]

        self.assertGreaterEqual(
            len(market_questions), 4,
            f"Market intent should have at least 4 Market questions. Got {len(market_questions)}"
        )
        print(f"✅ Market intent — {len(market_questions)} Market & Strategy questions generated")

    # ─────────────────────────────────────
    # TEST 3 — Interview Intent Alignment
    # ─────────────────────────────────────
    def test_interview_intent_topics_are_interview_focused(self):
        """Interview intent should produce interview-focused topics"""
        pack = self.packs["Prepare for interviews I already have"]["pack"]
        topics_text = " ".join([
            t["topic"].lower() + " " + t["why"].lower()
            for t in pack.get("discussion_topics", [])
        ])

        interview_keywords = [
            "interview", "question", "answer", "technical",
            "behavioral", "prepare", "practice", "articul"
        ]
        found = [kw for kw in interview_keywords if kw in topics_text]

        self.assertGreater(
            len(found), 1,
            f"Interview intent topics should mention interview keywords. Found: {found}"
        )
        print(f"✅ Interview intent — topics contain interview keywords: {found}")

    def test_interview_intent_questions_are_interview_focused(self):
        """Interview intent should produce mostly interview prep questions"""
        pack = self.packs["Prepare for interviews I already have"]["pack"]
        questions = pack.get("question_bank", [])

        interview_questions = [
            q for q in questions
            if q.get("category") == "Interview Prep"
        ]

        self.assertGreaterEqual(
            len(interview_questions), 4,
            f"Interview intent should have at least 4 Interview Prep questions. Got {len(interview_questions)}"
        )
        print(f"✅ Interview intent — {len(interview_questions)} Interview Prep questions generated")

    def test_interview_prep_tips_are_substantial(self):
        """Interview intent should produce detailed interview prep tips"""
        pack = self.packs["Prepare for interviews I already have"]["pack"]
        tips = pack.get("interview_prep", [])

        self.assertGreaterEqual(
            len(tips), 3,
            f"Interview intent should produce at least 3 prep tips. Got {len(tips)}"
        )
        print(f"✅ Interview intent — {len(tips)} interview prep tips generated")

    # ─────────────────────────────────────
    # TEST 4 — Strategy Intent Alignment
    # ─────────────────────────────────────
    def test_strategy_intent_topics_are_strategy_focused(self):
        """Strategy intent should produce strategy-focused topics"""
        pack = self.packs["Build my overall job search strategy"]["pack"]
        topics_text = " ".join([
            t["topic"].lower() + " " + t["why"].lower()
            for t in pack.get("discussion_topics", [])
        ])

        strategy_keywords = [
            "strategy", "approach", "plan", "search",
            "application", "action", "reset", "target"
        ]
        found = [kw for kw in strategy_keywords if kw in topics_text]

        self.assertGreater(
            len(found), 1,
            f"Strategy intent topics should mention strategy keywords. Found: {found}"
        )
        print(f"✅ Strategy intent — topics contain strategy keywords: {found}")

    def test_strategy_intent_has_next_steps(self):
        """Strategy intent should have next steps questions"""
        pack = self.packs["Build my overall job search strategy"]["pack"]
        questions = pack.get("question_bank", [])

        next_steps = [
            q for q in questions
            if q.get("category") == "Next Steps"
        ]

        self.assertGreaterEqual(
            len(next_steps), 2,
            f"Strategy intent should have at least 2 Next Steps questions. Got {len(next_steps)}"
        )
        print(f"✅ Strategy intent — {len(next_steps)} Next Steps questions generated")

    # ─────────────────────────────────────
    # TEST 5 — Cross-Intent Differentiation
    # Different intents should produce different outputs
    # ─────────────────────────────────────
    def test_cv_and_market_intents_produce_different_topics(self):
        """CV intent and Market intent should produce different discussion topics"""
        cv_pack = self.packs["Fix my CV and positioning"]["pack"]
        market_pack = self.packs["Understand the job market"]["pack"]

        cv_topics = set([t["topic"].lower() for t in cv_pack.get("discussion_topics", [])])
        market_topics = set([t["topic"].lower() for t in market_pack.get("discussion_topics", [])])

        # Topics should be different
        overlap = cv_topics.intersection(market_topics)
        overlap_ratio = len(overlap) / max(len(cv_topics), 1)

        self.assertLess(
            overlap_ratio, 0.6,
            f"CV and Market intents are producing too similar topics. Overlap: {overlap}"
        )
        print(f"✅ CV vs Market intent — topics are sufficiently different (overlap: {len(overlap)}/5)")

    def test_interview_and_strategy_intents_produce_different_questions(self):
        """Interview and Strategy intents should produce different question categories"""
        interview_pack = self.packs["Prepare for interviews I already have"]["pack"]
        strategy_pack = self.packs["Build my overall job search strategy"]["pack"]

        interview_cats = [q["category"] for q in interview_pack.get("question_bank", [])]
        strategy_cats = [q["category"] for q in strategy_pack.get("question_bank", [])]

        interview_prep_count_interview = interview_cats.count("Interview Prep")
        interview_prep_count_strategy = strategy_cats.count("Interview Prep")

        # Interview intent should have more interview prep questions than strategy intent
        self.assertGreater(
            interview_prep_count_interview,
            interview_prep_count_strategy,
            "Interview intent should have more Interview Prep questions than Strategy intent"
        )
        print(f"✅ Interview vs Strategy — Interview intent has more prep questions "
              f"({interview_prep_count_interview} vs {interview_prep_count_strategy})")

    # ─────────────────────────────────────
    # TEST 6 — All intents must always have
    # correct structure regardless of intent
    # ─────────────────────────────────────
    def test_all_intents_produce_5_topics(self):
        """All intents should always produce exactly 5 discussion topics"""
        for intent_name, data in self.packs.items():
            pack = data["pack"]
            topics = pack.get("discussion_topics", [])
            self.assertEqual(
                len(topics), 5,
                f"Intent '{intent_name}' produced {len(topics)} topics, expected 5"
            )
        print("✅ All 4 intents produced exactly 5 discussion topics")

    def test_all_intents_produce_15_questions(self):
        """All intents should always produce exactly 15 questions"""
        for intent_name, data in self.packs.items():
            pack = data["pack"]
            questions = pack.get("question_bank", [])
            self.assertEqual(
                len(questions), 15,
                f"Intent '{intent_name}' produced {len(questions)} questions, expected 15"
            )
        print("✅ All 4 intents produced exactly 15 questions")

    def test_all_intents_produce_first_person_questions(self):
        """All intents should produce first person questions"""
        for intent_name, data in self.packs.items():
            pack = data["pack"]
            for q in pack.get("question_bank", []):
                self.assertNotIn(
                    "test user",
                    q["question"].lower(),
                    f"Intent '{intent_name}' has third person question: {q['question']}"
                )
        print("✅ All 4 intents produced first person questions")

    def test_all_intents_produce_first_person_brief(self):
        """All intents should produce first person positioning brief"""
        for intent_name, data in self.packs.items():
            pack = data["pack"]
            brief = pack.get("positioning_brief", "")
            self.assertNotIn(
                "test user",
                brief.lower(),
                f"Intent '{intent_name}' has third person brief: {brief[:100]}"
            )
        print("✅ All 4 intents produced first person positioning brief")

    # ─────────────────────────────────────
    # TEST 7 — Print full comparison report
    # ─────────────────────────────────────
    def test_print_intent_comparison_report(self):
        """Print a readable comparison of all 4 intent outputs"""
        print("\n" + "="*60)
        print("  INTENT ALIGNMENT COMPARISON REPORT")
        print("="*60)

        for intent_name, data in self.packs.items():
            pack = data["pack"]
            questions = pack.get("question_bank", [])

            # Count questions by category
            cats = {}
            for q in questions:
                cat = q.get("category", "Unknown")
                cats[cat] = cats.get(cat, 0) + 1

            print(f"\n Intent: {intent_name}")
            print(f"  Topics: {len(pack.get('discussion_topics', []))}")
            print(f"  Questions by category:")
            for cat, count in sorted(cats.items()):
                bar = "█" * count
                print(f"    {cat:<25} {bar} ({count})")
            print(f"  Brief starts with: {pack.get('positioning_brief', '')[:60]}...")

        print("\n" + "="*60)
        print("  END OF REPORT")
        print("="*60 + "\n")

        # This test always passes — it's just for reporting
        self.assertTrue(True)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PREPMATE INTENT ALIGNMENT TESTS")
    print("  Testing if outputs are tailored to user intent")
    print("="*60)

    unittest.main(verbosity=2)


# ═════════════════════════════════════════
# TEST SUITE 8 — Question Specificity
# Tests whether questions are grounded in
# the user's actual profile data or generic
# ═════════════════════════════════════════
class TestQuestionSpecificity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Generate one prep pack for specificity testing"""
        from gemini import run_pack_generator

        cls.intent = "Build my overall job search strategy — I want to reset my approach and build a clear action plan."

        print("\n Generating prep pack for specificity testing...")
        cls.pack = run_pack_generator(
            BASE_PROFILE,
            CV_TEXT,
            cls.intent,
            RISK_SIGNALS,
            MARKET_PULSE
        )
        print(" Pack generated. Running specificity tests...\n")

    def test_questions_reference_cv_score(self):
        """At least one question should reference the actual CV score (65)"""
        questions_text = " ".join([
            q["question"].lower()
            for q in self.pack.get("question_bank", [])
        ])

        has_score_reference = (
            "65" in questions_text or
            "cv score" in questions_text or
            "score" in questions_text
        )

        self.assertTrue(
            has_score_reference,
            "No question references the user's actual CV score of 65.\n"
            f"Questions: {questions_text[:500]}"
        )
        print("✅ At least one question references the CV score")

    def test_questions_reference_skill_gaps(self):
        """At least one question should reference actual skill gaps"""
        questions_text = " ".join([
            q["question"].lower()
            for q in self.pack.get("question_bank", [])
        ])

        # User's actual skill gaps are Docker and System Design
        has_gap_reference = (
            "docker" in questions_text or
            "system design" in questions_text or
            "skill gap" in questions_text
        )

        self.assertTrue(
            has_gap_reference,
            "No question references the user's actual skill gaps (Docker, System Design).\n"
            f"Questions: {questions_text[:500]}"
        )
        print("✅ At least one question references actual skill gaps")

    def test_questions_reference_application_data(self):
        """At least one question should reference zero responses"""
        questions_text = " ".join([
            q["question"].lower()
            for q in self.pack.get("question_bank", [])
        ])

        has_momentum_reference = (
            "zero response" in questions_text or
            "0 response" in questions_text or
            "no response" in questions_text or
            "response rate" in questions_text or
            "application" in questions_text
        )

        self.assertTrue(
            has_momentum_reference,
            "No question references the zero application response rate.\n"
            f"Questions: {questions_text[:500]}"
        )
        print("✅ At least one question references application data")

    def test_questions_reference_employment_gap(self):
        """At least one question should address the employment gap"""
        questions_text = " ".join([
            q["question"].lower()
            for q in self.pack.get("question_bank", [])
        ])

        has_gap_reference = (
            "gap" in questions_text or
            "employment" in questions_text or
            "5 month" in questions_text
        )

        self.assertTrue(
            has_gap_reference,
            "No question references the 5-month employment gap.\n"
            f"Questions: {questions_text[:500]}"
        )
        print("✅ At least one question references employment gap")

    def test_no_completely_generic_questions(self):
        """Detect and flag completely generic questions"""
        generic_patterns = [
            "how do i improve my cv?",
            "how do i get a job?",
            "what should i do next?",
            "how do i prepare for interviews?",
            "what skills should i learn?",
            "how do i find jobs?",
            "what is the job market like?",
            "how do i write a cover letter?"
        ]

        generic_found = []
        for q in self.pack.get("question_bank", []):
            q_lower = q["question"].lower().strip().rstrip("?")
            for pattern in generic_patterns:
                pattern_clean = pattern.lower().strip().rstrip("?")
                if q_lower == pattern_clean:
                    generic_found.append(q["question"])

        self.assertEqual(
            len(generic_found), 0,
            f"Found completely generic questions: {generic_found}"
        )
        print("✅ No completely generic questions detected")

    def test_questions_are_specific_enough(self):
        """
        Specificity score test.
        A question is considered specific if it contains
        at least one of the user's actual data points.
        Target: at least 10 out of 15 questions should be specific.
        """
        # User's actual data points to look for
        specificity_markers = [
            "65",           # CV score
            "docker",       # Skill gap 1
            "system design",# Skill gap 2
            "7 application",# Applications sent
            "zero response",# Response rate
            "0 response",
            "no response",
            "5 month",      # Employment gap
            "gap",
            "backend",      # Target role
            "london",       # Location
            "junior",       # Career stage
            "graduate",
            "python",       # From CV text
            "rest api",
            "score",
            "application",
            "response rate",
            "skill",
            "interview"
        ]

        specific_count = 0
        generic_questions = []

        for q in self.pack.get("question_bank", []):
            q_lower = q["question"].lower()
            is_specific = any(
                marker in q_lower
                for marker in specificity_markers
            )
            if is_specific:
                specific_count += 1
            else:
                generic_questions.append(q["question"])

        total = len(self.pack.get("question_bank", []))
        specificity_rate = specific_count / total if total > 0 else 0

        print(f"\n  Specificity Report:")
        print(f"  Specific questions:  {specific_count}/{total}")
        print(f"  Specificity rate:    {specificity_rate:.0%}")

        if generic_questions:
            print(f"  Generic questions flagged:")
            for gq in generic_questions:
                print(f"    - {gq}")

        self.assertGreaterEqual(
            specificity_rate, 0.65,
            f"Only {specific_count}/{total} questions are specific to user profile. "
            f"Target is 65%+.\nGeneric questions: {generic_questions}"
        )
        print(f"\n✅ Specificity rate: {specificity_rate:.0%} — {'PASS' if specificity_rate >= 0.65 else 'FAIL'}")

    def test_discussion_topics_reference_profile_data(self):
        """Discussion topics should reference actual profile data points"""
        topics_text = " ".join([
            t["topic"].lower() + " " + t["why"].lower() + " " + t.get("data_reference", "").lower()
            for t in self.pack.get("discussion_topics", [])
        ])

        profile_references = [
            "65", "docker", "system design", "7", "zero",
            "gap", "backend", "application", "response", "score"
        ]

        found = [ref for ref in profile_references if ref in topics_text]

        self.assertGreater(
            len(found), 3,
            f"Discussion topics should reference profile data. Found only: {found}"
        )
        print(f"✅ Discussion topics reference profile data: {found}")

    def test_print_specificity_report(self):
        """Print detailed specificity analysis for each question"""
        specificity_markers = [
            "65", "docker", "system design", "7 application",
            "zero response", "0 response", "no response",
            "5 month", "gap", "backend", "london", "junior",
            "graduate", "python", "rest api", "score",
            "application", "response", "skill", "interview"
        ]

        print("\n" + "="*60)
        print("  QUESTION SPECIFICITY REPORT")
        print("="*60)

        for q in self.pack.get("question_bank", []):
            q_lower = q["question"].lower()
            found_markers = [m for m in specificity_markers if m in q_lower]
            status = "✅ SPECIFIC" if found_markers else "⚠️  GENERIC"
            markers_str = f"[{', '.join(found_markers)}]" if found_markers else "[no data markers found]"
            print(f"\n  {q['id']}. {q['question']}")
            print(f"     {status} {markers_str}")

        print("\n" + "="*60 + "\n")
        self.assertTrue(True)  # Always passes — reporting only


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PREPMATE INTENT ALIGNMENT + SPECIFICITY TESTS")
    print("  Testing output quality and data grounding")
    print("="*60)
    unittest.main(verbosity=2)