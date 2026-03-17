import google.generativeai as genai
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def clean_json(text):
    """Remove markdown fences if Gemini adds them"""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


# ─────────────────────────────────────────
# SERPER — Real-Time Market Data
# ─────────────────────────────────────────
def get_real_market_data(target_role, location):
    serper_key = os.getenv("SERPER_API_KEY")
    if not serper_key or serper_key == "your_serper_api_key_here":
        return ""
    try:
        r1 = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": serper_key,
                     "Content-Type": "application/json"},
            json={"q": f"{target_role} hiring trends {location} 2026",
                  "num": 5},
            timeout=8
        )
        r2 = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": serper_key,
                     "Content-Type": "application/json"},
            json={"q": f"{target_role} in demand skills {location} 2026",
                  "num": 5},
            timeout=8
        )
        snippets = []
        if r1.status_code == 200:
            for r in r1.json().get("organic", [])[:5]:
                if r.get("snippet"):
                    snippets.append(r["snippet"])
        if r2.status_code == 200:
            for r in r2.json().get("organic", [])[:5]:
                if r.get("snippet"):
                    snippets.append(r["snippet"])
        return "\n".join(snippets) if snippets else ""
    except Exception as e:
        print(f"Serper error: {e}")
        return ""


# ─────────────────────────────────────────
# CALL 1 — Risk Signal Detector
# ─────────────────────────────────────────
def run_risk_signal_detector(profile, cv_text):
    prompt = f"""
You are a career risk analyst for JSO (Job Search Optimiser).
Scan the user profile and identify hiring risk signals before
their 1:1 recruiter consultation session.

USER PROFILE:
- Name: {profile['name']}
- Career Stage: {profile['career_stage']}
- Target Role: {profile['target_role']}
- Target Location: {profile['target_location']}
- CV Score: {profile['cv_score']}/100
- Skill Gaps: {profile['skill_gaps']}
- Applications Sent: {profile['applications_sent']}
- Responses Received: {profile['responses_received']}
- Employment Gap: {profile['employment_gap']}

CV CONTENT: {cv_text[:2000]}

Scan for:
1. Zero or very low application response rate
2. Skill gaps appearing across target roles
3. CV score below 75 threshold
4. Employment gap with no clear narrative
5. No CV optimisation attempts
6. Applying to roles beyond current capability

Return ONLY valid JSON:
{{
  "risk_signals": [
    {{
      "signal": "string",
      "severity": "high | medium | low",
      "evidence": "string (20 words max)",
      "recruiter_note": "string (20 words max)"
    }}
  ],
  "overall_risk_level": "high | medium | low",
  "priority_focus": "string"
}}"""
    response = model.generate_content(prompt)
    try:
        return json.loads(clean_json(response.text))
    except Exception:
        return {"risk_signals": [], "overall_risk_level": "low",
                "priority_focus": "General career guidance"}


# ─────────────────────────────────────────
# CALL 2 — Market Pulse
# ─────────────────────────────────────────
def run_market_pulse(profile):
    real_data = get_real_market_data(
        profile['target_role'],
        profile['target_location']
    )

    real_data_section = f"""
REAL-TIME MARKET DATA (live Google Search):
{real_data[:3000]}
Use this as your primary source.""" if real_data else \
        "Use your training knowledge for market intelligence."

    prompt = f"""
You are a job market analyst for JSO (Job Search Optimiser).
Generate current market intelligence for this job seeker.

USER TARGET:
- Target Role: {profile['target_role']}
- Target Location: {profile['target_location']}
- Career Stage: {profile['career_stage']}
- Skill Gaps: {profile['skill_gaps']}

{real_data_section}

Return ONLY valid JSON:
{{
  "market_summary": "string (40 words max)",
  "data_source": "real-time" | "knowledge-base",
  "trending_skills": [
    {{
      "skill": "string",
      "trend": "rising | stable | declining",
      "relevance": "string (15 words max)"
    }}
  ],
  "hiring_activity": "high | medium | low",
  "opportunities": [{{"insight": "string (20 words max)"}}],
  "market_advice": "string (25 words max)"
}}"""
    response = model.generate_content(prompt)
    try:
        return json.loads(clean_json(response.text))
    except Exception:
        return {"market_summary": "Market data unavailable.",
                "data_source": "knowledge-base",
                "trending_skills": [], "hiring_activity": "medium",
                "opportunities": [],
                "market_advice": "Research current job postings."}


# ─────────────────────────────────────────
# CALL 3 — Prep Pack Generator
# ─────────────────────────────────────────
def run_pack_generator(profile, cv_text, intent,
                        risk_signals, market_pulse):
    prompt = f"""
You are PrepMate, an AI consultation preparation agent for JSO.
Generate a complete personalized consultation preparation pack.

USER PROFILE:
- Name: {profile['name']}
- Career Stage: {profile['career_stage']}
- Target Role: {profile['target_role']}
- Target Location: {profile['target_location']}
- CV Score: {profile['cv_score']}/100
- Skill Gaps: {profile['skill_gaps']}
- Applications Sent: {profile['applications_sent']}
- Responses Received: {profile['responses_received']}
- Employment Gap: {profile['employment_gap']}
- Recruiter: {profile['recruiter_name']}
- Session: {profile['session_date']}

DECLARED SESSION INTENT: {intent}
RISK SIGNALS: {json.dumps(risk_signals)}
MARKET PULSE: {json.dumps(market_pulse)}
CV: {cv_text[:1500]}

RULES:
1. Every topic must reference a specific profile data point
2. Every question must be specifically answerable by a recruiter
3. Generate exactly 5 discussion topics
4. Generate exactly 15 questions across all categories
5. STRICT INTENT-BASED QUESTION DISTRIBUTION — MANDATORY:
   Based on the declared intent, distribute the 15 questions
   using these EXACT minimum category requirements:

   If intent is CV fixing:
   - CV & Positioning: minimum 8 questions
   - Skill Gap: 3 questions
   - Next Steps: 2 questions
   - Market & Strategy: maximum 2 questions
   - Interview Prep: maximum 1 question

   If intent is Job market understanding:
   - Market & Strategy: minimum 8 questions
   - Skill Gap: 3 questions
   - Next Steps: 2 questions
   - CV & Positioning: maximum 2 questions

   If intent is Interview preparation:
   - Interview Prep: minimum 8 questions
   - CV & Positioning: 3 questions
   - Next Steps: 2 questions
   - Market & Strategy: maximum 2 questions

   If intent is Job search strategy:
   - Next Steps: minimum 5 questions
   - Market & Strategy: 4 questions
   - CV & Positioning: 3 questions
   - Skill Gap: 3 questions

   YOU MUST FOLLOW THESE DISTRIBUTIONS EXACTLY.
   DO NOT default to equal distributions across categories.
6. MANDATORY FIRST PERSON RULE — NO EXCEPTIONS:
   Every question MUST be written in first person as if the
   USER is speaking directly to the recruiter.
   The user NAME must NEVER appear in any question ever.
   CORRECT: How do I improve my CV score from 69 to above 75?
   CORRECT: How should I address my 8-month employment gap?
   CORRECT: Which skill should I prioritise for my target role?
   WRONG: What should Vedant do to improve his CV score?
   WRONG: How should Vedant articulate the employment gap?
   WRONG: What improvements are needed to increase Vedants score?
   Every question MUST start with one of:
   How do I / What should I / Should I / How can I /
   Can you help me / Which should I / What is the best way for me
7. MANDATORY FIRST PERSON RULE FOR POSITIONING BRIEF:
   The positioning_brief must be written in first person.
   The user will READ this out loud to the recruiter.
   CORRECT: I am a recent graduate targeting Junior ML Engineer roles...
   WRONG: Vedant is a recent graduate targeting...
   WRONG: He is targeting... / She is targeting...
   Start with: I am... or My background is... or I have...

Return ONLY valid JSON:
{{
  "discussion_topics": [
    {{
      "topic": "string (10 words max)",
      "why": "string (20 words max)",
      "data_reference": "string"
    }}
  ],
  "question_bank": [
    {{
      "id": "Q1",
      "category": "CV & Positioning | Market & Strategy | Interview Prep | Skill Gap | Next Steps",
      "question": "string (25 words max)"
    }}
  ],
  "interview_prep": [
    {{
      "tip": "string (25 words max)",
      "role_relevance": "string (15 words max)"
    }}
  ],
  "positioning_brief": "string (80 words max) — MANDATORY: Write this in FIRST PERSON as if the user is speaking. Start with I am... or My name is... NEVER write it in third person. WRONG: Vedant is a graduate... RIGHT: I am a recent graduate targeting...",
  "session_agenda": [
    {{
      "order": 1,
      "focus": "string (10 words max)",
      "time": "string"
    }}
  ]
}}"""
    response = model.generate_content(prompt)
    try:
        return json.loads(clean_json(response.text))
    except Exception:
        return {"discussion_topics": [], "question_bank": [],
                "interview_prep": [],
                "positioning_brief": "Unable to generate.",
                "session_agenda": []}


# ─────────────────────────────────────────
# CALL 4 — Quality Checker
# ─────────────────────────────────────────
def run_quality_checker(profile, prep_pack, intent):
    prompt = f"""
You are a senior HR consultant quality-checking a consultation
preparation pack before it reaches a job seeker.

USER PROFILE:
- Career Stage: {profile['career_stage']}
- Target Role: {profile['target_role']}
- CV Score: {profile['cv_score']}/100
- Applications Sent: {profile['applications_sent']}
- Responses Received: {profile['responses_received']}
- Skill Gaps: {profile['skill_gaps']}
- Declared Intent: {intent}

QUESTION BANK: {json.dumps(prep_pack.get('question_bank', []))}

Flag questions that are:
1. Too generic — could apply to any user
2. Misaligned with declared intent
3. Premature given career momentum
4. Duplicate in meaning
5. Too vague for recruiter to answer specifically

Return ONLY valid JSON:
{{
  "overall_quality_score": 8,
  "quality_summary": "string (20 words max)",
  "flags": [
    {{
      "question_id": "string",
      "issue": "string (20 words max)",
      "severity": "minor | moderate | critical",
      "improved_version": "string (25 words max)"
    }}
  ],
  "approved_questions": ["Q1", "Q2"],
  "recommendation": "approved | needs_revision"
}}"""
    response = model.generate_content(prompt)
    try:
        return json.loads(clean_json(response.text))
    except Exception:
        return {"overall_quality_score": 7,
                "quality_summary": "Quality check unavailable.",
                "flags": [], "approved_questions": [],
                "recommendation": "approved"}