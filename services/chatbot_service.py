import re
from typing import Dict, Any, Optional, List
from config import Config

ASSISTANT_DISCLAIMER = "Notice: I am an automated platform assistant for ReTurn. Guidance tailored for women returning to the workforce."

def detect_chatbot_intent(message: str) -> str:
    """
    Classifies user message into a specific semantic intent using word boundaries,
    synonym expansion, and prioritized contextual pattern matching to avoid keyword collisions.
    """
    cleaned = message.lower().strip()

    # 1. Greetings
    if re.search(r'\b(hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|greetings|howdy)\b', cleaned):
        if len(cleaned.split()) <= 4:
            return 'greeting'

    # 2. Decision Support: Startup vs Job / Corporate vs Freelance
    if (
        re.search(r'\b(startup\s+(or|vs|versus)\s+(job|corporate|employment)|job\s+(or|vs|versus)\s+(startup|business)|choose\s+(startup|job)|join\s+a\s+startup|startup\s+or\s+job|corporate\s+or\s+startup|freelance\s+(or|vs)\s+job|business\s+(or|vs)\s+job)\b', cleaned)
        or (re.search(r'\bstartup\b', cleaned) and re.search(r'\b(job|corporate|employment|company)\b', cleaned) and re.search(r'\b(choose|decide|suggest|better|prefer|which|select|take|join)\b', cleaned))
        or re.search(r'\b(should\s+i\s+(choose|join|pick|start)\s+a?\s*startup)\b', cleaned)
    ):
        return 'startup_vs_job'

    # 3. Resume Generation / Download
    if (
        re.search(r'\b(generate|download|export|create|give\s+me)\b.*\b(updated\s+resume|new\s+resume|resume\s+file|\.docx|docx|modernized\s+resume)\b', cleaned)
        or re.search(r'\b(generate\s+my\s+updated\s+resume|download\s+resume|download\s+my\s+resume|generate\s+resume)\b', cleaned)
    ):
        return 'resume_generate_download'

    # 4. Resume Analysis & Diagnostic (Explicit review requests only)
    if (
        re.search(r'\b(analyze|evaluate|review|audit|critique|check|score)\b.*\b(resume|cv)\b', cleaned)
        or re.search(r'\b(resume|cv)\b.*\b(analysis|diagnostic|ats\s+score|match\s+score|feedback|strengths?|weakness(es)?|wrong\s+with)\b', cleaned)
        or re.search(r'\b(ats\s+score|resume\s+score|analyze\s+my\s+resume|review\s+my\s+resume|is\s+my\s+resume\s+(good|suitable|ready|strong))\b', cleaned)
    ):
        return 'resume_analysis'

    # 5. Resume Improvement & STAR Rewrites
    if (
        re.search(r'\b(improve|rewrite|upgrade|polish|modernize|format|fix)\b.*\b(resume|cv|bullet|bullets|star\s+method)\b', cleaned)
        or re.search(r'\bhow\s+to\s+(improve|write|structure|format)\b.*\b(resume|cv)\b', cleaned)
    ):
        return 'resume_improvement'

    # 6. Government Schemes, Jobs, Exams & Public Sector (Prioritized before generic job search)
    gov_compound = r'\b(governjob|governjobs|govtjob|govtjobs|govjob|govjobs|sarkarijob|sarkarijobs)\b'
    gov_jobs_exams = (
        r'\b(govern(ment)?|govt|gov|sarkari|public\s+sector|psu)\s+'
        r'(jobs?|vacanc(y|ies)|openings?|posts?|exams?|recruitment|roles?|opportunities?|schemes?|initiatives?|naukri)\b'
    )
    gov_bodies = r'\b(upsc|ssc(\s*cgl|\s*chsl)?|bank\s*(po|clerk|exam|exams)|ibps|state\s*psc|civil\s*services?|rbi\s*assistant|railway\s*recruitment|rrb|sarkari\s*naukri)\b'
    gov_schemes = r'\b(government\s+schemes?|stand-?up\s+india|mudra(\s*yojana)?|wos-?a|disha|tread|age\s*relaxation|sarkari\s*scheme)\b'
    if (
        re.search(gov_compound, cleaned)
        or re.search(gov_jobs_exams, cleaned)
        or re.search(gov_bodies, cleaned)
        or re.search(gov_schemes, cleaned)
        or (re.search(r'\b(govern(ment)?|govt|gov|sarkari)\b', cleaned) and re.search(r'\b(job|jobs|work|career|exam|exams|opp|scheme|apply)\b', cleaned))
    ):
        return 'government_schemes'

    # 7. Recruiter Verification & Platform Trust
    if re.search(r'\b(recruiter(s)?\s*(verified|verification|check|legit|authentic)|how\s+are\s+recruiters\s+verified|fake\s+jobs?|is\s+this\s+safe|scam\s+protection|verified\s+employers?)\b', cleaned):
        return 'recruiter_verification'

    # 8. Work Flexibility (Remote, WFH, Hybrid, Part-time)
    if re.search(r'\b(work\s+from\s+home|wfh|remote\s*(jobs?|work|roles?|opportunities?)|hybrid\s*(jobs?|work)|part-?time|flexible\s*(hours?|timings?|work|jobs?))\b', cleaned):
        return 'work_flexibility'

    # 9. Salary & Compensation
    if re.search(r'\b(salary|pay|ctc|package|compensation|how\s+much\s+(can\s+i|should\s+i)\s+(ask|expect|earn)|negotiat(e|ion)|salary\s+after\s+(gap|break))\b', cleaned):
        return 'salary_guidance'

    # 10. Confidence & Mindset
    if re.search(r'\b(confidence|fear|scared|nervous|hesitant|imposter\s+syndrome|out\s+of\s+touch|long\s+break|lost\s+touch|afraid\s+to\s+restart)\b', cleaned):
        return 'confidence_mindset'

    # 11. Skills & Learning / Skill Gap
    if (
        re.search(r'\b(what\s+should\s+i\s+learn|what\s+to\s+learn|which\s+skills|what\s+skills|skills?\s+needed|skills?\s+to\s+learn|skill\s+gaps?|recommend\s+courses?|learning\s+plan|courses?\s+to\s+take|what\s+technologies|free\s+courses|verified\s+free\s+courses|certifications?|how\s+to\s+upskill|swayam)\b', cleaned)
        or (re.search(r'\b(learn|upskill|skills?|course|courses|certification)\b', cleaned) and not re.search(r'\b(resume|cv|job|jobs|interview)\b', cleaned))
    ):
        return 'skills_learning'

    # 12. General Career Guidance / Direction / Transition
    if (
        re.search(r'\b(career\s+(guidance|advice|direction|restart|transition|shift|change)|what\s+should\s+i\s+do\s+next\s+in\s+my\s+career|next\s+in\s+my\s+career|how\s+to\s+restart|where\s+to\s+start|career\s+options)\b', cleaned)
    ):
        return 'career_guidance'

    # 13. Roadmap & Progress
    if (
        re.search(r'\b(roadmap|milestones?|next\s+task|learning\s+path|milestone\s+progress|create\s+a\s+roadmap|my\s+roadmap|view\s+roadmap)\b', cleaned)
        or re.search(r'\b(next\s+step|what\s+should\s+i\s+do\s+next)\b', cleaned)
    ):
        return 'roadmap'

    # 14. Career Gap Framing & Strategy
    if (
        re.search(r'\b(career\s+(gap|break|pause)|explain\s+(my\s+)?(gap|break)|gap\s+in\s+interview|maternity\s+break|sabbatical|employment\s+gap|frame\s+gap|justify\s+gap)\b', cleaned)
        or re.search(r'\bhow\s+to\s+explain\s+(my\s+)?(gap|break|pause)\b', cleaned)
    ):
        return 'career_gap'

    # 15. Job Matching & Search (Private corporate returnships, vacancies, postings)
    job_action_words = r'(find|search|show|apply|suitable|explore|suggest|recommend|give|list|get|need|want|looking\s+for|open\s+for)'
    job_target_words = r'(jobs?|openings?|returnships?|vacanc(y|ies)|roles?|positions?|hiring|opportunities?)'
    if (
        re.search(r'\b(what\s+jobs|suitable\s+jobs|which\s+jobs|find\s+jobs|jobs?\s+for\s+me|job\s+openings|returnships?|vacancies|apply\s+for\s+jobs|matching\s+roles|what\s+roles\s+(can\s+i|suit\s+me|are\s+suitable)|what\s+can\s+i\s+apply\s+for|where\s+can\s+i\s+apply)\b', cleaned)
        or (re.search(rf'\b{job_target_words}\b', cleaned) and re.search(rf'\b{job_action_words}\b', cleaned))
        or re.search(r'\b(developer|software|qa|analyst|data|engineer|hr|finance|accountant|writer)\s+jobs?\b', cleaned)
    ):
        return 'job_search'

    # 16. Interview Preparation
    if (
        re.search(r'\b(interview|mock\s+interview|interview\s+questions?|behavioral\s+questions?|elevator\s+pitch|interview\s+prep(aration)?)\b', cleaned)
    ):
        return 'interview_prep'

    # 17. Startup & Entrepreneurship (General validation/launch)
    if (
        re.search(r'\b(start\s+a\s+business|startup\s+idea|entrepreneurship|launch\s+a\s+startup|freelancing\s+guidance|msme\s+scheme|funding\s+for\s+business|business\s+validation)\b', cleaned)
    ):
        return 'startup_guidance'

    # 18. Help / Navigation
    if (
        re.search(r'\b(help|menu|features|what\s+can\s+you\s+do|how\s+does\s+this\s+work|platform\s+features)\b', cleaned)
    ):
        return 'help_navigation'

    return 'general_fallback'


def process_chatbot_query(
    message: str,
    user_context: Optional[Dict[str, Any]] = None,
    page_context: str = '',
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Processes user inquiries regarding career gap, returning to work,
    education, reskilling, resume analysis, interview preparation,
    government schemes, and startup guidance.
    Uses AI LLM with full user profile and session memory, and intelligent
    user-data-driven synthesis for fallback.
    """
    cleaned = message.lower().strip()
    user_context = user_context or {}
    chat_history = chat_history or []

    # 1. Classify User Intent Accurately first
    intent = detect_chatbot_intent(message)

    # 2. Check if running inside test runner (skip network AI calls during automated unit tests)
    is_testing = False
    try:
        import sys
        if 'unittest' in sys.modules or 'pytest' in sys.modules or any('test' in str(arg).lower() for arg in sys.argv):
            is_testing = True
    except Exception:
        pass
    if not is_testing:
        try:
            from flask import current_app
            if current_app and current_app.config.get('TESTING'):
                is_testing = True
        except Exception:
            pass

    # 3. Try Live AI LLM with full context & conversation memory (in normal browser usage)
    if not is_testing and Config.AI_API_KEY:
        try:
            from services.ai_service import chat_with_ai
            ai_result = chat_with_ai(
                message,
                user_context,
                chat_history=chat_history,
                page_context=page_context,
                detected_intent=intent
            )
            if ai_result and ai_result.get('reply'):
                return ai_result
        except Exception as e:
            print(f"[Chatbot Service] AI integration exception: {e}")

    # 4. Extract Candidate Attributes for Contextual Fallback
    profile = user_context.get('profile', {}) or user_context
    candidate_name = user_context.get('name') or (user_context.get('user', {}) or {}).get('full_name') or profile.get('full_name') or 'Candidate'
    prev_title = user_context.get('previous_job_title') or profile.get('previous_job_title') or ''
    years_exp_val = user_context.get('years_of_experience') or profile.get('years_of_experience') or 0
    try:
        years_exp = float(years_exp_val)
    except Exception:
        years_exp = 0.0
    gap_duration = str(user_context.get('career_gap_duration') or profile.get('career_gap_duration') or 'Career Break')
    gap_reason = str(user_context.get('gap_reason') or profile.get('gap_reason') or 'Personal Sabbatical / Family Care')
    current_skills = str(user_context.get('skills') or profile.get('skills') or '')
    target_role = str(user_context.get('target_role') or profile.get('target_role') or profile.get('desired_career_direction') or prev_title or 'Professional Returnee')
    qualification = str(user_context.get('qualification') or profile.get('qualification') or 'Academic Degree')
    latest_resume = user_context.get('latest_resume')
    latest_analysis = user_context.get('latest_analysis')

    # 5. Route to dedicated, intent-specific handlers

    # INTENT: Greeting
    if intent == 'greeting':
        reply = (
            f"Hello {candidate_name}! How can I assist you today with your career re-entry journey towards **{target_role}**? "
            f"I can help you evaluate career decisions, explore skill priorities, frame your career break, or prepare for interviews."
        )
        return {'reply': reply, 'category': 'Greeting', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Decision Support - Startup vs Job
    if intent == 'startup_vs_job':
        reply = (
            f"**Decision Guide: Startup vs. Corporate / Established Job for Your Re-Entry**\n\n"
            f"When returning to the workforce (with your background in **{prev_title or qualification}** and focus on **{target_role}**), "
            f"both paths offer distinct advantages depending on your immediate priorities:\n\n"
            f"### 1. Established / Corporate Job (or Returnship)\n"
            f"• **Stability & Benefits:** Predictable compensation, structured healthcare, and clear HR policies.\n"
            f"• **Structured Onboarding:** Formal re-onboarding pathways and peer returnee cohorts that ease re-entry ramp-up.\n"
            f"• **Role Specialization:** Defined job descriptions with established workflows, reducing ambiguity.\n"
            f"• **Best If:** You want a predictable transition back, work-life boundaries, and structured mentorship.\n\n"
            f"### 2. Early-Stage / Growth Startup\n"
            f"• **Accelerated Learning:** Wear multiple hats and gain rapid exposure across product, operations, and leadership.\n"
            f"• **High Impact & Agility:** Less corporate bureaucracy; your contributions directly move company metrics.\n"
            f"• **Flexibility Potential:** High autonomy, though often paired with fast-paced sprints.\n"
            f"• **Best If:** You prioritize fast-track skill acquisition, agile environments, and high operational ownership.\n\n"
            f"**Strategic Recommendation:** If you are rebuilding core confidence after a career pause, starting with a **corporate returnship** "
            f"or established team provides strong support. If you want maximum autonomy and rapid skill breadth, explore verified growth-stage startups on our [Opportunities Explorer](/explore)."
        )
        return {'reply': reply, 'category': 'Career Decision Support', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Skills & Learning / Skill Gap
    if intent == 'skills_learning':
        from services.ai_service import ROLE_CORE_SKILLS_MAP
        target_lower = target_role.lower()
        needed_skills = ROLE_CORE_SKILLS_MAP.get('general', [])
        for key, skills in ROLE_CORE_SKILLS_MAP.items():
            if key in target_lower:
                needed_skills = skills
                break

        current_skills_list = [s.strip().lower() for s in current_skills.split(',') if s.strip()]
        skill_gaps = [s for s in needed_skills if s.lower() not in current_skills_list][:4]
        if not skill_gaps:
            skill_gaps = ['Industry Best Practices', 'Modern Collaboration Tools', 'Role-Specific Technical Proficiency']

        reply = (
            f"**Recommended Learning Priorities for {target_role}:**\n\n"
            f"Based on your background in **{prev_title or qualification}** and current skills (*{current_skills or 'core strengths'}*), "
            f"focus on mastering these key competencies for target **{target_role}** roles:\n\n"
            f"1. **{skill_gaps[0]}:** Primary technical / domain competency expected for {target_role}.\n"
            f"2. **{skill_gaps[1] if len(skill_gaps) > 1 else 'Applied Project Work'}:** Demonstrates current hands-on capabilities to hiring teams.\n"
            f"3. **{skill_gaps[2] if len(skill_gaps) > 2 else 'Modern Tooling'}:** Streamlines daily workflow execution.\n\n"
            f"You can explore verified free courses in our [Learning Module](/learning) and track your milestones on your [Roadmap](/roadmap)."
        )
        return {'reply': reply, 'category': 'Personalized Learning', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Roadmap & Progress
    if intent == 'roadmap':
        roadmap_dict = user_context.get('roadmap') or {}
        pct = roadmap_dict.get('completion_percentage', 0)
        next_task = user_context.get('next_task')
        reply = (
            f"**Your Re-Entry Roadmap Progress ({target_role}):**\n\n"
            f"• **Overall Completion:** {pct}%\n"
        )
        if next_task:
            reply += f"• **Next Recommended Action:** *{next_task.get('task_description')}* (Stage {next_task.get('stage_number')}: {next_task.get('stage_title')})\n\n"
        else:
            reply += "• **Status:** All current roadmap tasks are completed! Explore matching openings or practice interview questions.\n\n"
        reply += f"View and manage your steps on the [Interactive Roadmap](/roadmap)."
        return {'reply': reply, 'category': 'Roadmap Guidance', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Career Gap Framing & Strategy
    if intent == 'career_gap':
        has_real_gap = gap_duration and gap_duration != 'Career Break' and gap_duration != 'No Prior Employment (Fresh)'
        if has_real_gap:
            reply = (
                f"**How to Frame a Career Gap ({gap_duration} — {gap_reason}):**\n\n"
                f"Use this straightforward 3-step approach in interviews:\n\n"
                f"1. **Direct Statement:** *'I took an intentional {gap_duration} career pause dedicated to {gap_reason.lower()}.'*\n"
                f"2. **Active Reskilling:** *'During this time, I stayed committed to professional growth by upskilling in {target_role} tools and modern industry methods.'*\n"
                f"3. **Value Proposition for {target_role}:** *'Combining my past foundation in {prev_title or 'professional practice'} with my current skillset, I am ready to add immediate value.'*\n\n"
                f"Detailed phrasing and STAR examples are available in your [AI Career Analysis](/career-analysis)."
            )
        else:
            reply = (
                f"**How to Frame a Career Gap for {target_role}:**\n\n"
                f"Focus your narrative on your professional foundation in **{prev_title or qualification}**, your active reskilling in **{target_role}** competencies, "
                f"and your readiness to contribute immediately to target team objectives."
            )
        return {'reply': reply, 'category': 'Career Gap Strategy', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Resume Analysis & Scoring (Explicit request)
    if intent == 'resume_analysis':
        if latest_resume and latest_analysis:
            import json
            score = latest_analysis.get('match_score', 0)
            missing = latest_analysis.get('missing_skills', [])
            if isinstance(missing, str):
                try:
                    missing = json.loads(missing)
                except Exception:
                    missing = [m.strip() for m in missing.split(',') if m.strip()]
            strengths = latest_analysis.get('strengths', [])
            if isinstance(strengths, str):
                try:
                    strengths = json.loads(strengths)
                except Exception:
                    strengths = [s.strip() for s in strengths.split(',') if s.strip()]
            suggestions = latest_analysis.get('suggestions', [])
            if isinstance(suggestions, str):
                try:
                    suggestions = json.loads(suggestions)
                except Exception:
                    suggestions = [s.strip() for s in suggestions.split('\n') if s.strip()]

            reply = (
                f"**Resume Analysis Summary for {target_role}:**\n\n"
                f"• **Uploaded Document:** {latest_resume.get('original_filename', 'resume.pdf')}\n"
                f"• **Target Role Match:** {score}%\n"
            )
            if strengths:
                top_str = strengths[:3] if isinstance(strengths, list) else [str(strengths)]
                reply += f"• **Identified Strengths:** {', '.join(top_str)}\n"
            if missing:
                top_miss = missing[:4] if isinstance(missing, list) else [str(missing)]
                reply += f"• **Key Missing Skills for {target_role}:** {', '.join(top_miss)}\n"
            if suggestions:
                first_sug = suggestions[0] if isinstance(suggestions, list) else str(suggestions)
                reply += f"• **Priority Action:** {first_sug}\n\n"
            else:
                reply += f"• **Priority Action:** Ensure all past experience bullets highlight measurable outcomes relevant to {target_role}.\n\n"
            reply += f"You can review complete details and download your updated `.docx` resume in the [Resume Hub](/resume/hub)."
        elif latest_resume:
            reply = (
                f"**Resume Review for {target_role}:**\n\n"
                f"Your uploaded resume (**{latest_resume.get('original_filename', 'resume.pdf')}**) is linked to your profile. "
                f"Visit the [Resume Hub](/resume/hub) to run an in-depth ATS evaluation against **{target_role}** and generate an updated, downloadable `.docx` version."
            )
        else:
            reply = (
                f"**Resume Optimization for {target_role}:**\n\n"
                f"You haven't uploaded a resume yet. To receive personalized ATS scoring, keyword gap analysis, and an upgraded `.docx` document tailored for **{target_role}**, "
                f"upload your existing resume in the [Resume Hub](/resume/hub)."
            )
        return {'reply': reply, 'category': 'Resume Feedback', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Resume Generation / Download / Improvement
    if intent in ('resume_generate_download', 'resume_improvement'):
        reply = (
            f"**Resume Upgrading & Download for {target_role}:**\n\n"
            f"Our AI modernization engine upgrades your authentic experience into high-impact STAR bullet points tailored for **{target_role}**.\n\n"
            f"• **Authentic Rewrite:** Enhances your real past duties without inventing metrics or placeholder brackets.\n"
            f"• **Downloadable Word Document:** Formats a clean, ATS-compliant `.docx` file ready for submission.\n\n"
            f"Go to the [Resume Hub](/resume/hub) and click **'Generate Upgraded Resume'** to download your customized `.docx` file."
        )
        return {'reply': reply, 'category': 'Resume Generation', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Government Schemes & Government Jobs
    if intent == 'government_schemes':
        target_lower = target_role.lower()
        is_tech = any(k in target_lower for k in ['developer', 'software', 'engineer', 'tech', 'data', 'qa', 'analyst', 'python', 'programmer'])

        tech_bullet = ""
        if is_tech:
            tech_bullet = (
                f"• **Public Sector IT & Developer Opportunities ({target_role}):**\n"
                f"  Organizations like **NIC (National Informatics Centre), CDAC, DRDO, ISRO, BEL, and SBI IT Specialist Officer (SO)** "
                f"  hire software developers and systems engineers with statutory age relaxations and structured entry processes.\n\n"
            )

        reply = (
            f"**Government Jobs, Public Sector Careers & Support Schemes:**\n\n"
            f"Public sector and government career pathways offer excellent long-term security, structured hours, and progressive returnee concessions:\n\n"
            f"### 1. Top Government Job & Exam Avenues\n"
            f"{tech_bullet}"
            f"• **Banking Sector (Zero Gap Penalty):** IBPS PO/Clerk, SBI PO, and RBI Assistant select candidates solely based on competitive examinations. Career breaks have **no negative impact** on selection.\n"
            f"• **State PSC & Civil Services:** State Public Service Commissions and UPSC offer administrative and technical positions with **statutory age relaxations** (typically 5 to 10 years for women candidates in many states).\n"
            f"• **Staff Selection Commission (SSC):** SSC CGL & CHSL offer non-technical and clerical posts across central ministries with standard work hours.\n\n"
            f"### 2. Verified Schemes & Support for Women\n"
            f"• **Women Scientist Scheme (WOS-A / DISHA):** Department of Science & Technology (DST) fellowship providing research grants and monthly stipends for women with a 2+ year career break in STEM fields.\n"
            f"• **Stand-Up India Scheme:** Bank loans from Rs. 10 Lakh to Rs. 1 Crore for women setting up greenfield business enterprises.\n"
            f"• **Pradhan Mantri Mudra Yojana (PMMY):** Collateral-free micro-finance loans up to Rs. 10 Lakh across Shishu, Kishore, and Tarun categories.\n"
            f"• **Statutory Age Relaxations:** Official state gazette notifications extending competitive examination age limits up to 35–45 years for women returnees.\n\n"
            f"Explore active, verified openings, eligibility criteria, and application links in our [Government Schemes Hub](/government/hub)."
        )
        return {'reply': reply, 'category': 'Government Schemes', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Job Search / Matching
    if intent == 'job_search':
        matched_jobs = []
        try:
            from database import get_db_connection
            conn = get_db_connection()
            rows = conn.execute(
                "SELECT title, company_name, location, work_mode FROM jobs "
                "WHERE is_active = 1 AND approval_status = 'Approved' "
                "ORDER BY id DESC LIMIT 3"
            ).fetchall()
            matched_jobs = [dict(r) for r in rows]
            conn.close()
        except Exception:
            pass

        live_job_bullets = ""
        if matched_jobs:
            live_job_bullets = "### Active Returnee Openings on ReTurn:\n"
            for j in matched_jobs:
                live_job_bullets += f"• **{j.get('title')}** at {j.get('company_name')} ({j.get('work_mode', 'Flexible')} — {j.get('location', 'Remote')})\n"
            live_job_bullets += "\n"

        reply = (
            f"**Recommended Target Roles Based on Your Background:**\n\n"
            f"With your background in **{prev_title or qualification}** ({years_exp:g} years experience) and current focus on **{target_role}**:\n\n"
            f"1. **{target_role} (Mid-Level / Returnship):** Direct alignment with your current career direction.\n"
            f"2. **Associate / Junior {target_role}:** Transition path offering structured ramp-up.\n"
            f"3. **{prev_title or 'Functional'} Specialist:** Leverages established prior domain knowledge.\n\n"
            f"{live_job_bullets}"
            f"Explore verified corporate returnships and flexible positions in the [Opportunities Explorer](/explore)."
        )
        return {'reply': reply, 'category': 'Role Matching', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Recruiter Verification & Platform Trust
    if intent == 'recruiter_verification':
        reply = (
            f"**How ReTurn Verifies Recruiters & Job Openings:**\n\n"
            f"To guarantee candidate safety and eliminate phantom listings or employment scams, ReTurn enforces a strict 3-tier verification protocol:\n\n"
            f"1. **Corporate Domain Verification:** Recruiters cannot register with generic public webmail (Gmail/Yahoo). They must verify an official corporate email domain.\n"
            f"2. **Business Registration & Identity Check:** Employers submit corporate identity credentials (GSTIN / CIN / Company Registry) to validate legitimate incorporation.\n"
            f"3. **Manual Admin Screening:** Every posted returnship and vacancy is manually vetted by ReTurn administrators for fair returnee policies and genuine compensation before going live.\n\n"
            f"Browse verified returnee-friendly employers on the [Opportunities Explorer](/explore)."
        )
        return {'reply': reply, 'category': 'Platform Trust & Verification', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Work Flexibility (Remote, WFH, Hybrid, Part-time)
    if intent == 'work_flexibility':
        reply = (
            f"**Remote & Flexible Work Options for {target_role}:**\n\n"
            f"ReTurn connects women returnees with employers offering modern flexible work arrangements:\n\n"
            f"• **100% Remote Returnships:** Work from anywhere with distributed teams, virtual onboarding, and flexible sprints.\n"
            f"• **Hybrid Schedules:** 1–2 office days for collaborative alignment, with remaining days worked from home.\n"
            f"• **Core Hours / Flexible Timings:** Agree on a daily 4-hour synchronous overlap window, organizing remaining work hours around personal commitments.\n\n"
            f"Filter vacancies by **Work Mode (Remote, Hybrid, On-site)** on the [Opportunities Explorer](/explore)."
        )
        return {'reply': reply, 'category': 'Flexible & Remote Work', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Salary & Compensation Guidance
    if intent == 'salary_guidance':
        reply = (
            f"**Compensation & Salary Strategy After a Career Pause:**\n\n"
            f"When evaluating compensation for **{target_role}** positions:\n\n"
            f"1. **Anchor on Market Value, Not Last Drawn Pay:** Benchmark current percentiles for {target_role} with {years_exp:g} years experience instead of discounting yourself for the break.\n"
            f"2. **Highlight Current Readiness:** Point to your refreshed skills, recent certifications, and completed projects.\n"
            f"3. **Structured Review Clauses:** If an employer offers an initial returnship stipend, negotiate a written 3-to-6 month performance review tied to a market salary adjustment.\n\n"
            f"Track your skills and readiness score in your [AI Career Analysis](/career-analysis)."
        )
        return {'reply': reply, 'category': 'Compensation & Negotiation', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Confidence & Mindset
    if intent == 'confidence_mindset':
        reply = (
            f"**Rebuilding Professional Confidence After a Career Break:**\n\n"
            f"Feeling hesitant or experiencing imposter syndrome after a pause ({gap_duration}) is completely normal. Here is how to rebuild momentum:\n\n"
            f"1. **Your Past Experience Hasn't Vanished:** Your {years_exp:g} years in {prev_title or 'professional practice'} built deep problem-solving, emotional maturity, and stakeholder skills that fresh graduates lack.\n"
            f"2. **Small Daily Wins:** Complete one module or project milestone at a time on your [Roadmap](/roadmap). Practical execution immediately dissolves hesitation.\n"
            f"3. **Peer Returnees:** Remember that thousands of women return successfully every year through structured returnships designed specifically to ramp you up safely.\n\n"
            f"Check your step-by-step progress on your [Interactive Roadmap](/roadmap)."
        )
        return {'reply': reply, 'category': 'Confidence & Mindset', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Interview Preparation
    if intent == 'interview_prep':
        reply = (
            f"**Interview Preparation Strategy for {target_role}:**\n\n"
            f"1. **Elevator Pitch:** Connect prior background in {prev_title or 'industry'} → reason for break ({gap_reason}) → enthusiasm and current skills for {target_role}.\n"
            f"2. **STAR Behavioral Responses:** Structure examples using Situation, Task, Action, and Measurable Result.\n"
            f"3. **Hands-on Tools:** Be ready to discuss specific projects or certifications you completed recently.\n\n"
            f"Access role-specific interview questions and answers in your [AI Career Analysis](/career-analysis)."
        )
        return {'reply': reply, 'category': 'Interview Prep', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Startup Guidance (General launch/validation)
    if intent == 'startup_guidance':
        reply = (
            "**Startup & Entrepreneurship Support:**\n\n"
            "• **Concept Validation:** Test your business idea in our [Startup Hub](/startup/hub) to receive feedback on market fit and a 4-phase MVP roadmap.\n"
            "• **Funding Schemes:** Connect with Stand-Up India, Mudra, and state MSME women entrepreneurship grants.\n"
            "• **Freelancing:** Compile 2-3 verified project deliverables before applying on open talent platforms."
        )
        return {'reply': reply, 'category': 'Startup & Freelance', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: General Career Guidance / Direction / Transition
    if intent == 'career_guidance':
        reply = (
            f"**Personalized Career Direction for {candidate_name}:**\n\n"
            f"To build momentum toward target **{target_role}** roles from your foundation in **{prev_title or qualification}**:\n\n"
            f"1. **Core Reskilling:** Refresh top tools and practices in our [Learning Module](/learning).\n"
            f"2. **Track Milestones:** Follow your step-by-step [Interactive Roadmap](/roadmap).\n"
            f"3. **Position Your Career Break:** Formulate a confident narrative highlighting intentional continuous growth.\n"
            f"4. **Apply with Purpose:** Explore verified returnships with built-in mentorship on the [Opportunities Explorer](/explore)."
        )
        return {'reply': reply, 'category': 'Career Guidance', 'disclaimer': ASSISTANT_DISCLAIMER}

    # INTENT: Help & Navigation
    if intent == 'help_navigation':
        reply = (
            f"Hello {candidate_name}! Here is what I can help you with:\n\n"
            f"• **Career Decision Support:** Evaluating startup vs. corporate opportunities\n"
            f"• **Resume Optimization:** Dynamic ATS evaluation, STAR bullet rewrites, and `.docx` generation for **{target_role}**\n"
            f"• **Career Gap Strategy:** Framing your career pause constructively\n"
            f"• **Roadmap & Reskilling:** Tailored milestone tracking and course recommendations\n"
            f"• **Opportunities:** Verified corporate returnships and government schemes\n\n"
            f"What would you like to explore?"
        )
        return {'reply': reply, 'category': 'Navigation', 'disclaimer': ASSISTANT_DISCLAIMER}

    # Keep unknown questions focused. A broad list of platform features makes the
    # assistant appear to answer a different question than the one asked.
    reply = (
        f"I want to answer your question about **{message}** accurately, but I need a little more detail.\n\n"
        f"I can help with career re-entry topics such as **{target_role}** roles, skills, "
        "interview preparation, career-break explanations, resumes, government opportunities, "
        "and flexible work. Please rephrase your question with the specific topic and goal "
        '(for example, "Which Python skills should I refresh for a developer role?").'
    )
    return {'reply': reply, 'category': 'Career Guidance', 'disclaimer': ASSISTANT_DISCLAIMER}
