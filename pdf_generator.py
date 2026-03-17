from fpdf import FPDF
import os

# Page width = 210mm, margins = 15mm each side
# Usable width = 210 - 15 - 15 = 180mm
W = 180


class PrepMatePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(14, 165, 233)
        self.set_x(15)
        self.cell(W, 8, "PrepMate -- JSO Phase-2 Agentic Career Intelligence",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 45, 69)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 116, 139)
        self.set_x(15)
        self.cell(W, 8,
                  f"Page {self.page_no()} | Powered by Google Gemini API | AariyaTech UK",
                  align="C")

    def section_title(self, title, color=(14, 165, 233)):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*color)
        self.set_x(15)
        self.cell(W, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*color)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def body_text(self, text, size=10):
        self.set_font("Helvetica", "", size)
        self.set_text_color(50, 50, 50)
        self.set_x(15)
        self.multi_cell(W, 6, str(text))
        self.ln(1)

    def label(self, text):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 116, 139)
        self.set_x(15)
        self.cell(W, 6, text.upper(), new_x="LMARGIN", new_y="NEXT")

    def numbered_item(self, number, title, subtitle=""):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.set_x(15)
        self.multi_cell(W, 6, f"{number}. {title}")
        if subtitle:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(100, 116, 139)
            self.set_x(15)
            self.multi_cell(W, 5, f"   {subtitle}")
        self.ln(1)

    def question_item(self, q_id, category, question):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(14, 165, 233)
        self.set_x(15)
        self.cell(W, 5, f"[{category}]", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(15)
        self.multi_cell(W, 6, f"{q_id}. {question}")
        self.ln(1)

    def tip_item(self, tip, relevance=""):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(15)
        self.multi_cell(W, 6, f"- {tip}")
        if relevance:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(16, 185, 129)
            self.set_x(15)
            self.multi_cell(W, 5, f"  -> {relevance}")
        self.ln(1)

    def info_chip(self, label, value):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 116, 139)
        self.set_x(15)
        self.cell(40, 6, f"{label}:", new_x="RIGHT", new_y="LAST")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(140, 6, str(value))


def safe(text):
    """Remove characters Helvetica cannot render"""
    if not text:
        return ""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def generate_pdf(profile, prep_pack, market_pulse, output_path=None):
    pdf = PrepMatePDF()
    pdf.set_margins(15, 20, 15)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── TITLE ──
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(14, 165, 233)
    pdf.set_x(15)
    pdf.cell(W, 12, "Consultation Prep Pack",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    name = profile.get("name", "User") if profile else "User"
    role = profile.get("target_role", "") if profile else ""
    session_date = profile.get("session_date", "") if profile else ""
    pdf.set_x(15)
    pdf.cell(W, 7,
             safe(f"Prepared for: {name}  |  Target: {role}  |  Session: {session_date}"),
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── PROFILE SUMMARY ──
    if profile:
        pdf.section_title("Profile Summary")
        pdf.info_chip("Career Stage", safe(profile.get("career_stage", "N/A")))
        pdf.info_chip("Location", safe(profile.get("target_location", "N/A")))
        pdf.info_chip("CV Score", f"{profile.get('cv_score', 'N/A')}/100")
        pdf.info_chip("Applications",
                      f"{profile.get('applications_sent', 0)} sent | "
                      f"{profile.get('responses_received', 0)} responses")
        pdf.info_chip("Skill Gaps", safe(profile.get("skill_gaps", "N/A")))
        gap = profile.get("employment_gap", "None")
        if gap and gap != "None":
            pdf.info_chip("Employment Gap", safe(gap))

    # ── DISCUSSION TOPICS ──
    if prep_pack and prep_pack.get("discussion_topics"):
        pdf.section_title("Discussion Topics")
        for i, topic in enumerate(prep_pack["discussion_topics"], 1):
            pdf.numbered_item(
                i,
                safe(topic.get("topic", "")),
                safe(topic.get("why", ""))
            )

    # ── QUESTION BANK ──
    if prep_pack and prep_pack.get("question_bank"):
        pdf.section_title("Your Question Bank")
        for q in prep_pack["question_bank"]:
            pdf.question_item(
                safe(q.get("id", "")),
                safe(q.get("category", "")),
                safe(q.get("question", ""))
            )

    # ── INTERVIEW PREP ──
    if prep_pack and prep_pack.get("interview_prep"):
        pdf.section_title("Interview Articulation Tips", color=(16, 185, 129))
        for tip in prep_pack["interview_prep"]:
            pdf.tip_item(
                safe(tip.get("tip", "")),
                safe(tip.get("role_relevance", ""))
            )

    # ── MARKET PULSE ──
    if market_pulse:
        pdf.section_title("Market Pulse", color=(139, 92, 246))
        source = market_pulse.get("data_source", "knowledge-base")
        source_label = "Real-Time Data" if source == "real-time" else "Knowledge Base"
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(139, 92, 246)
        pdf.set_x(15)
        pdf.cell(W, 5, f"Data Source: {source_label}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        if market_pulse.get("market_summary"):
            pdf.body_text(safe(market_pulse["market_summary"]))

        if market_pulse.get("trending_skills"):
            pdf.label("Trending Skills")
            for skill in market_pulse["trending_skills"]:
                trend = skill.get("trend", "stable")
                arrow = "^ " if trend == "rising" else ("v " if trend == "declining" else "- ")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(30, 30, 30)
                pdf.set_x(15)
                pdf.multi_cell(W, 6,
                               safe(f"{arrow}{skill.get('skill', '')} -- "
                                    f"{skill.get('relevance', '')}"))
            pdf.ln(2)

        if market_pulse.get("market_advice"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(139, 92, 246)
            pdf.set_x(15)
            pdf.multi_cell(W, 6,
                           safe(f"Market Advice: {market_pulse['market_advice']}"))

    # ── POSITIONING BRIEF ──
    if prep_pack and prep_pack.get("positioning_brief"):
        pdf.section_title("Your 90-Second Positioning Brief",
                          color=(245, 158, 11))
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.set_x(15)
        pdf.multi_cell(W, 7,
                       safe(f"\"{prep_pack['positioning_brief']}\""))

    # ── SESSION AGENDA ──
    if prep_pack and prep_pack.get("session_agenda"):
        pdf.section_title("Suggested Session Agenda")
        for item in prep_pack["session_agenda"]:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            time_str = f"({item.get('time', '')})" if item.get("time") else ""
            pdf.set_x(15)
            pdf.multi_cell(W, 6,
                           safe(f"{item.get('order', '')}. "
                                f"{item.get('focus', '')} {time_str}"))
            pdf.ln(1)

    # ── SAVE ──
    os.makedirs("static/uploads", exist_ok=True)
    path = output_path if output_path else "/tmp/PrepMate_Pack.pdf"
    pdf.output(path)
    return path