import json
import re
from typing import Dict, Any, List, Optional
import requests
from config import Config
from database import get_db_connection
from services.resume_analyzer import (
    analyze_resume_text,
    parse_resume_data,
    generate_improved_resume_draft,
    generate_updated_resume_docx,
)

ROLE_CORE_SKILLS_MAP = {
    'software': ['Python', 'SQL', 'Git', 'REST APIs', 'System Design', 'Testing & CI/CD', 'Docker'],
    'developer': ['Python', 'SQL', 'Git', 'REST APIs', 'System Design', 'Testing & CI/CD', 'Docker'],
    'engineer': ['Python', 'SQL', 'Git', 'REST APIs', 'Problem Solving', 'Unit Testing'],
    'qa': ['Test Automation', 'Selenium', 'Python', 'Jira', 'API Testing (Postman)', 'SQL', 'Bug Lifecycle'],
    'test': ['Test Automation', 'Selenium', 'Python', 'Jira', 'API Testing (Postman)', 'SQL', 'Bug Lifecycle'],
    'quality': ['Test Automation', 'Selenium', 'Python', 'Jira', 'API Testing (Postman)', 'SQL', 'Bug Lifecycle'],
    'data': ['SQL', 'Python (Pandas)', 'Power BI / Tableau', 'Excel Modeling', 'Data Cleaning', 'Statistics'],
    'analyst': ['SQL', 'Python (Pandas)', 'Power BI / Tableau', 'Excel Modeling', 'Data Cleaning', 'Statistics'],
    'product': ['User Stories', 'Roadmapping', 'Agile / Scrum', 'Metrics & KPI Tracking', 'Stakeholder Communication'],
    'project': ['Agile / Scrum', 'Jira', 'Budget & Resource Management', 'Risk Management', 'Milestone Tracking'],
    'content': ['SEO Optimization', 'Markdown / CMS', 'Copywriting', 'Content Strategy', 'Editorial Guidelines'],
    'writer': ['SEO Optimization', 'Markdown / CMS', 'Copywriting', 'Content Strategy', 'Editorial Guidelines'],
    'hr': ['Talent Acquisition', 'HRIS Systems', 'Employee Onboarding', 'Compliance & Labour Laws', 'Interviewing'],
    'human resources': ['Talent Acquisition', 'HRIS Systems', 'Employee Onboarding', 'Compliance', 'Interviewing'],
    'accountant': ['Tally Prime', 'GST & Taxation', 'Balance Sheet Reconciliation', 'Auditing', 'Advanced Excel'],
    'finance': ['Financial Modeling', 'Budget Forecasting', 'GST / Tax Compliance', 'Tally Prime', 'MIS Reporting'],
    'operations': ['Process Optimization', 'SLA Management', 'Vendor Management', 'CRM (Salesforce/HubSpot)', 'Excel / Sheets'],
    'support': ['Customer Empathy', 'Zendesk / Freshdesk', 'Conflict Resolution', 'Technical Troubleshooting', 'Escalations'],
    'general': ['Professional Communication', 'Spreadsheets (Excel/Sheets)', 'Collaboration Tools (Slack/Teams)', 'Time Management', 'Project Coordination']
}

def get_complete_user_context(user_id: int) -> Dict[str, Any]:
    """
    Constructs a single reliable, centralized user profile data object for all AI services.
    Aggregates user account, profile details, pathway, resume, analysis, and roadmap status.
    """
    if not user_id:
        return {}

    conn = get_db_connection()
    try:
        user_row = conn.execute("SELECT id, email, role, full_name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            return {}

        user_dict = dict(user_row)
        profile_row = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        profile_dict = dict(profile_row) if profile_row else {}

        career_row = conn.execute("SELECT * FROM career_selections WHERE user_id = ?", (user_id,)).fetchone()
        pathway = career_row['pathway'] if career_row else 'EXPERIENCED_GAP'

        resume_row = conn.execute(
            "SELECT * FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone()
        resume_dict = dict(resume_row) if resume_row else None

        analysis_dict = None
        if resume_dict:
            analysis_row = conn.execute(
                "SELECT * FROM resume_analyses WHERE resume_id = ?", (resume_dict['id'],)
            ).fetchone()
            if analysis_row:
                analysis_dict = dict(analysis_row)

        gap_row = conn.execute(
            "SELECT * FROM career_gap_analyses WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone()
        gap_dict = dict(gap_row) if gap_row else None

        roadmap_row = conn.execute(
            "SELECT * FROM user_roadmaps WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone()
        roadmap_dict = dict(roadmap_row) if roadmap_row else None
        roadmap_tasks = []
        next_task = None
        if roadmap_dict:
            t_rows = conn.execute(
                "SELECT * FROM roadmap_tasks WHERE roadmap_id = ? ORDER BY stage_number ASC, id ASC",
                (roadmap_dict['id'],)
            ).fetchall()
            roadmap_tasks = [dict(t) for t in t_rows]
            next_task = next((t for t in roadmap_tasks if t['is_completed'] == 0), None)

        # Build clean consolidated context
        context = {
            'user_id': user_id,
            'name': user_dict.get('full_name', 'Candidate'),
            'email': user_dict.get('email', ''),
            'role': user_dict.get('role', 'USER'),
            'education_level': profile_dict.get('education', "Bachelor's Degree"),
            'qualification': profile_dict.get('qualification', 'General Degree'),
            'graduation_year': profile_dict.get('graduation_year'),
            'location': profile_dict.get('location', ''),
            'preferred_work_location': profile_dict.get('preferred_work_location', ''),
            'work_mode_preference': profile_dict.get('work_mode_preference', 'Flexible / Any'),
            'previous_job_title': profile_dict.get('previous_job_title', ''),
            'years_of_experience': float(profile_dict.get('years_of_experience') or 0),
            'career_gap_duration': profile_dict.get('career_gap_duration', '1 - 3 years'),
            'gap_reason': profile_dict.get('gap_reason', 'Personal Sabbatical / Family Care'),
            'previous_industry': profile_dict.get('previous_industry', 'Corporate Services'),
            'skills': profile_dict.get('skills', ''),
            'current_skills_list': [s.strip() for s in (profile_dict.get('skills') or '').split(',') if s.strip()],
            'target_role': profile_dict.get('target_role') or profile_dict.get('desired_career_direction') or profile_dict.get('previous_job_title') or 'Professional Returnee',
            'desired_career_direction': profile_dict.get('desired_career_direction', ''),
            'career_goal': profile_dict.get('career_goal', ''),
            'learning_preference': profile_dict.get('learning_preference', 'Self-paced'),
            'cost_preference': profile_dict.get('cost_preference', 'Free Only'),
            'preferences_sector': profile_dict.get('preferences_sector', 'Private'),
            'pathway': pathway,
            'profile_completed': bool(profile_dict.get('profile_completed', 0)),
            'user': user_dict,
            'profile': profile_dict,
            'latest_resume': resume_dict,
            'latest_analysis': analysis_dict,
            'latest_gap_analysis': gap_dict,
            'roadmap': roadmap_dict,
            'roadmap_tasks': roadmap_tasks,
            'next_task': next_task
        }
        return context
    finally:
        conn.close()

def _call_gemini_api(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """Invokes Google Gemini REST API using AI_API_KEY with robust multi-model fallback."""
    api_key = Config.AI_API_KEY
    if not api_key:
        return None

    candidate_models = []
    preferred = Config.AI_MODEL.strip() if Config.AI_MODEL else 'gemini-flash-latest'
    if preferred and preferred != 'gemini-1.5-flash':
        candidate_models.append(preferred)
    for fallback in ['gemini-flash-latest', 'gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-2.5-pro']:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    contents = []
    if system_instruction:
        contents.append({"role": "user", "parts": [{"text": f"System Context: {system_instruction}"}]})
        contents.append({"role": "model", "parts": [{"text": "Understood. I will act strictly according to this context and format."}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
        }
    }

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=18)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        text = parts[0].get('text', '')
                        if text:
                            return text
            elif response.status_code in (404, 429, 503):
                continue
            else:
                print(f"[AI Service] Gemini model {model} returned status {response.status_code}")
        except Exception as e:
            print(f"[AI Service] Gemini request exception for {model}: {e}")
            continue

    return None

def _call_openai_api(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """Invokes OpenAI-compatible Chat Completions API."""
    api_key = Config.AI_API_KEY
    if not api_key:
        return None

    url = "https://api.openai.com/v1/chat/completions"
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": Config.AI_MODEL if Config.AI_MODEL != 'gemini-1.5-flash' else 'gpt-4o-mini',
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2048
    }

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            data = response.json()
            choices = data.get('choices', [])
            if choices:
                return choices[0].get('message', {}).get('content', '')
    except Exception as e:
        print(f"[AI Service] OpenAI API request failed: {e}")
    return None

def call_ai_llm(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """Dispatches to configured server-side AI provider (Gemini or OpenAI)."""
    # Skip live network LLM calls during automated unit test execution
    import sys
    if 'unittest' in sys.modules or 'pytest' in sys.modules or any('test' in str(arg).lower() for arg in sys.argv):
        return None

    if not Config.AI_API_KEY:
        return None
    if Config.AI_PROVIDER == 'openai':
        return _call_openai_api(prompt, system_instruction)
    return _call_gemini_api(prompt, system_instruction)

def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extracts JSON structure from model text responses."""
    if not text:
        return None
    try:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        match = re.search(r'(\{[\s\S]*\})', text)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print(f"[AI Service] JSON parse error: {e}")
    return None

# ==============================================================================
# 1. DYNAMIC CAREER GAP ANALYSIS
# ==============================================================================

def generate_career_gap_analysis(profile_data: Dict[str, Any], pathway: str = 'EXPERIENCED_GAP') -> Dict[str, Any]:
    """
    Generates a personalized Career-Gap Analysis, Skill Gap Diagnostic,
    Suggested Roles, 90-Day Roadmap, and Learning Recommendations based on
    the user's real profile data.
    """
    candidate_name = profile_data.get('full_name') or profile_data.get('name') or 'Candidate'
    prev_title = (profile_data.get('previous_job_title') or '').strip()
    years_exp = float(profile_data.get('years_of_experience') or 0)
    gap_duration = (profile_data.get('career_gap_duration') or '1 - 3 years').strip()
    gap_reason = (profile_data.get('gap_reason') or 'Personal Break / Family Care').strip()
    prev_industry = (profile_data.get('previous_industry') or 'Corporate Services').strip()
    current_skills_raw = (profile_data.get('skills') or profile_data.get('current_skills') or '').strip()
    desired_role = (profile_data.get('target_role') or profile_data.get('desired_career_direction') or prev_title or 'Professional Returnee').strip()
    work_mode = (profile_data.get('work_mode_preference') or 'Flexible').strip()
    location = (profile_data.get('location') or 'National / Remote').strip()
    qualification = (profile_data.get('qualification') or profile_data.get('education') or "Bachelor's Degree").strip()
    career_goal = (profile_data.get('career_goal') or '').strip()

    candidate_skills = [s.strip() for s in current_skills_raw.split(',') if s.strip()] if current_skills_raw else []

    # Attempt real AI call first
    system_prompt = (
        "You are a Senior Corporate Career Transition Architect for the Women Career Gap — Reskill & Opportunity Platform. "
        "Analyze the candidate's actual background, career gap, skills, and target role. "
        "Reason dynamically from: Previous experience + current skills + career break duration and reason + target role. "
        "Never give generic advice when candidate details are available. "
        "Return ONLY a valid JSON object matching the requested schema."
    )

    user_prompt = f"""
Analyze this candidate for career re-entry and return ONLY a JSON object:
Candidate Profile:
- Candidate Name: {candidate_name}
- Highest Qualification: {qualification}
- Previous Job Role: {prev_title or 'Entry-Level / Non-formal background'}
- Previous Industry: {prev_industry}
- Years of Prior Experience: {years_exp} years
- Career Break Duration: {gap_duration}
- Reason for Career Pause: {gap_reason}
- Current Skills: {', '.join(candidate_skills) if candidate_skills else 'Foundational workplace skills'}
- Target Return Role: {desired_role}
- Primary Career Goal: {career_goal or 'Secure re-entry in target role'}
- Preferred Work Mode: {work_mode}
- Location: {location}
- Pathway: {pathway}

Required JSON Schema:
{{
  "readiness_level": "High - Strong Foundation" | "Moderate - Refresher Recommended" | "Foundational - Guided Transition",
  "readiness_score": 75,
  "current_position_analysis": "Substantive 3-4 sentence analysis analyzing how their {years_exp} years in {prev_industry} and skills in {', '.join(candidate_skills[:3]) if candidate_skills else 'problem solving'} transfer to {desired_role}, addressing their {gap_duration} pause for {gap_reason}.",
  "skill_gaps": ["Skill 1", "Skill 2", "Skill 3", "Skill 4"],
  "suggested_roles": [
    {{"title": "{desired_role} (Returnship / Mid-level)", "fit_reason": "Specific reason linking prior {prev_title or prev_industry} background."}},
    {{"title": "Role Title 2", "fit_reason": "Specific reason."}},
    {{"title": "Role Title 3", "fit_reason": "Specific reason."}}
  ],
  "roadmap_90_days": {{
    "phase1_weeks_1_2": {{"title": "Phase 1: Foundations & Tool Refresh", "tasks": ["Specific Task 1", "Specific Task 2", "Specific Task 3"]}},
    "phase2_weeks_3_6": {{"title": "Phase 2: Applied Work Samples & Portfolio", "tasks": ["Specific Task 1", "Specific Task 2", "Specific Task 3"]}},
    "phase3_weeks_7_12": {{"title": "Phase 3: Targeted Applications & Interviews", "tasks": ["Specific Task 1", "Specific Task 2", "Specific Task 3"]}}
  }},
  "resume_advice": "Detailed guidance on framing their {gap_duration} career pause ({gap_reason}) and highlighting transferable skills.",
  "interview_focus_areas": [
    "90-Second Re-Entry Pitch for {desired_role}",
    "Explaining the {gap_duration} break ({gap_reason}) constructively",
    "Technical/Practical demonstration question"
  ],
  "learning_recommendations": [
    {{"title": "Course/Skill Name 1", "provider": "SWAYAM / Coursera / FreeCodeCamp", "skill_addressed": "Skill Gap 1"}},
    {{"title": "Course/Skill Name 2", "provider": "Skill India / NPTEL / LinkedIn", "skill_addressed": "Skill Gap 2"}}
  ]
}}
"""
    ai_raw = call_ai_llm(user_prompt, system_prompt)
    if ai_raw:
        parsed_ai = _extract_json_from_text(ai_raw)
        if parsed_ai and 'readiness_level' in parsed_ai and 'skill_gaps' in parsed_ai:
            return parsed_ai

    # ==========================================================================
    # DYNAMIC PROFILE-DRIVEN CALCULATION (Intelligent User-Data Fallback)
    # ==========================================================================
    desired_lower = desired_role.lower()
    expected_skills = ROLE_CORE_SKILLS_MAP.get('general', [])
    for key, skills in ROLE_CORE_SKILLS_MAP.items():
        if key in desired_lower:
            expected_skills = skills
            break

    existing_skills_lower = [s.lower() for s in candidate_skills]
    skill_gaps = [s for s in expected_skills if s.lower() not in existing_skills_lower][:5]
    if not skill_gaps:
        skill_gaps = ['Modern Tooling & Cloud Collaboration', 'Agile Methodology', 'Role-Specific Best Practices']

    # Compute realistic readiness score
    base_score = 60
    if years_exp >= 5: base_score += 20
    elif years_exp >= 2: base_score += 15
    elif years_exp >= 1: base_score += 10

    if '5+' in gap_duration or '8+' in gap_duration or '5 - 8' in gap_duration:
        base_score -= 10
    elif '3 - 5' in gap_duration:
        base_score -= 6
    elif '1 - 2' in gap_duration or '1 - 3' in gap_duration:
        base_score -= 3

    if len(candidate_skills) >= 4: base_score += 10
    elif len(candidate_skills) >= 2: base_score += 5

    readiness_score = max(45, min(95, base_score))
    if readiness_score >= 80:
        readiness_level = "High - Strong Foundation"
    elif readiness_score >= 65:
        readiness_level = "Moderate - Refresher Recommended"
    else:
        readiness_level = "Foundational - Guided Transition"

    role_display = desired_role if desired_role else (prev_title if prev_title else "Corporate Professional")
    current_position_analysis = (
        f"With {years_exp:g} years of prior professional experience in {prev_industry} "
        f"and academic credentials in {qualification}, you hold solid transferable capabilities for {role_display}. "
        f"Following your {gap_duration} career break for {gap_reason}, the primary focus is closing targeted tool gaps "
        f"in {', '.join(skill_gaps[:2])} and assembling 1-2 verified work samples demonstrating current operational readiness."
    )

    suggested_roles = [
        f"{desired_role} (Returnship / Mid-level)",
        f"Associate {desired_role}",
        f"Operations & Project Specialist ({prev_industry})"
    ]

    roadmap_90_days = {
        "month_1": f"Phase 1 (Days 1-30): Refresh foundational competencies in {skill_gaps[0] if skill_gaps else 'core tools'}. Restructure resume with modern re-entry format framing '{gap_reason}'.",
        "month_2": f"Phase 2 (Days 31-60): Build an applied practice project demonstrating {skill_gaps[1] if len(skill_gaps) > 1 else 'functional expertise'}. Complete 1 verified technical assessment.",
        "month_3": f"Phase 3 (Days 61-90): Apply to verified returnship vacancies supporting {work_mode} arrangements. Conduct mock interviews focusing on STAR behavioral responses."
    }

    if any(k in gap_reason.lower() for k in ['childcare', 'maternity', 'family']):
        resume_advice = (
            f"Frame your {gap_duration} break ({gap_reason}) transparently as 'Career Pause & Continuous Professional Development'. "
            f"Highlight self-managed learning, resilience, and recent coursework in {skill_gaps[0] if skill_gaps else 'modern tooling'}."
        )
    elif 'health' in gap_reason.lower():
        resume_advice = (
            f"State your career break simply as 'Personal Health Sabbatical' ({gap_duration} - {gap_reason}). "
            "Focus narrative on complete recovery, high energy to re-engage, and newly acquired certifications."
        )
    elif 'relocation' in gap_reason.lower():
        resume_advice = (
            f"Frame the pause as 'Geographic Transition & Professional Alignment' ({gap_duration} - {gap_reason}). "
            f"Highlight settled base in {location} and interest in {work_mode} collaboration."
        )
    else:
        resume_advice = (
            f"Frame the period constructively: 'Career Pause & Targeted Skill Advancement' ({gap_duration} - {gap_reason}). "
            f"Detail independent coursework in {', '.join(skill_gaps[:2])} and practical application projects."
        )

    interview_focus_areas = [
        f"The 90-Second Re-Entry Pitch: Connect {prev_title or prev_industry} background -> {gap_duration} break context ({gap_reason}) -> readiness for {desired_role}.",
        f"Demonstrating Current Competency: Discussing practical experience in {skill_gaps[0] if skill_gaps else 'modern industry standards'}.",
        "STAR Behavioral Stories: Concrete examples illustrating adaptability, resilience, and cross-functional teamwork."
    ]

    learning_recommendations = []
    for gap in skill_gaps[:3]:
        learning_recommendations.append({
            "title": f"Mastering {gap} for Returning Professionals",
            "provider": "SWAYAM / NPTEL / FreeCodeCamp",
            "skill_addressed": gap
        })

    return {
        "readiness_level": readiness_level,
        "readiness_score": readiness_score,
        "current_position_analysis": current_position_analysis,
        "career_analysis": current_position_analysis,
        "skill_gaps": skill_gaps,
        "suggested_roles": suggested_roles,
        "roadmap_plan": roadmap_90_days,
        "roadmap_90_days": roadmap_90_days,
        "resume_advice": resume_advice,
        "interview_prep": interview_focus_areas,
        "interview_focus_areas": interview_focus_areas,
        "learning_recommendations": learning_recommendations
    }

# ==============================================================================
# 2. DYNAMIC RESUME BULLET ENHANCER & UPDATED RESUME GENERATOR
# ==============================================================================

def enhance_resume_with_ai(resume_text: str, target_role: str, profile_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extracts actual lines from the resume and rewrites them into quantified STAR bullets.
    """
    profile_data = profile_data or {}
    lines = [line.strip() for line in resume_text.split('\n') if len(line.strip()) > 25 and not line.strip().startswith(('http', 'Email', 'Phone', 'Address', 'Name:'))]
    
    candidate_lines = []
    for line in lines:
        cleaned = re.sub(r'^[•\-\*\d\.\)]\s*', '', line).strip()
        if 30 < len(cleaned) < 220 and any(w in cleaned.lower() for w in ['manage', 'work', 'create', 'develop', 'lead', 'handle', 'assist', 'support', 'organize', 'analyze', 'test', 'write', 'teach', 'coordinate', 'design', 'execute', 'build']):
            candidate_lines.append(cleaned)
        if len(candidate_lines) >= 3:
            break

    if candidate_lines and Config.AI_API_KEY:
        prompt = f"""
Given the candidate's target role '{target_role}', rewrite these 3 actual resume bullets into quantified, high-impact STAR bullets:
Original Bullets:
1. {candidate_lines[0]}
2. {candidate_lines[1] if len(candidate_lines) > 1 else 'Coordinated operational deliverables and team status reports.'}
3. {candidate_lines[2] if len(candidate_lines) > 2 else 'Handled client communications and daily deliverables.'}

Output ONLY valid JSON:
{{
  "suggested_bullets": [
    {{"original": "original bullet 1", "improved": "STAR rewrite with active verb and impact"}},
    {{"original": "original bullet 2", "improved": "STAR rewrite with active verb and impact"}},
    {{"original": "original bullet 3", "improved": "STAR rewrite with active verb and impact"}}
  ]
}}
"""
        raw = call_ai_llm(prompt)
        if raw:
            data = _extract_json_from_text(raw)
            if data and 'suggested_bullets' in data:
                return data

    return {"suggested_bullets": []}

def generate_updated_resume_ai(resume_text: str, target_role: str, profile_data: Dict[str, Any]) -> str:
    """
    Uses AI LLM to produce a complete modernized re-entry resume text,
    strictly preserving authentic facts without fabricating companies, metrics, or degrees.
    """
    if Config.AI_API_KEY:
        system_prompt = (
            "You are an Executive Resume Writer specializing in women returning to the workforce after a career gap. "
            "Modernize the candidate's resume for the target role. "
            "STRICT RULES: "
            "1. NO USER DATA = NO CLAIM. NEVER invent fake companies, fake job titles, fake degrees, fake certifications, or fake metrics/percentages. "
            "2. Preserve all authentic factual details from the original resume and profile. "
            "3. Rewrite every genuine responsibility into a specific, varied, achievement-oriented bullet. "
            "   Preserve the original facts; do not add metrics, outcomes, tools, scope, or ownership that are not present. "
            "4. Construct a personalized professional summary based on the candidate's actual experience, qualification, skills, and target role. "
            "5. Keep real employers, titles, dates, projects, education, certifications, and contact details; do not replace them with generic placeholders. "
            "6. Use only target-role keywords already supported by the resume or profile. Never add a missing skill as if it were learned. "
            "7. If a career gap exists, present it constructively using only the supplied reason and verified profile information. "
            "8. Return a complete resume with sections for Summary, Skills, Experience, Career Break (only when applicable), Projects, Education, and Certifications when those facts exist. "
            "9. Format cleanly with standard text headers and 3-6 distinct bullets per substantial role."
        )

        user_prompt = f"""
Modernize this candidate's resume for the target role: '{target_role}'

Candidate Profile:
- Name: {profile_data.get('full_name') or profile_data.get('name') or 'Candidate Name'}
- Location: {profile_data.get('location') or 'Location'}
- Prior Role: {profile_data.get('previous_job_title') or 'Professional'}
- Prior Experience: {profile_data.get('years_of_experience') or 0} years in {profile_data.get('previous_industry') or 'Corporate'}
- Career Break: {profile_data.get('career_gap_duration') or ''} ({profile_data.get('gap_reason') or ''})
- Highest Qualification: {profile_data.get('qualification') or profile_data.get('education') or 'Degree'}
- Skills: {profile_data.get('skills') or ''}

Original Resume Text:
{resume_text[:8000]}

Generate the complete, professionally formatted text of the updated re-entry resume using ONLY factual user data. Do not describe the changes or provide a template; output only the resume.
"""
        improved_text = call_ai_llm(user_prompt, system_prompt)
        if improved_text and len(improved_text.strip()) > 200:
            return improved_text.strip()

    # Dynamic fallback generator from resume_analyzer
    analysis = analyze_resume_text(resume_text, target_role, profile_data)
    return generate_improved_resume_draft(
        resume_text,
        target_role,
        profile_data,
        missing_sections=analysis.get('sections_missing'),
        missing_keywords=analysis.get('missing_keywords'),
        suggested_bullets=analysis.get('suggested_bullets')
    )

# ==============================================================================
# 3. DYNAMIC STARTUP FEASIBILITY AI
# ==============================================================================

def evaluate_startup_idea_ai(data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates business or freelance concept using AI or dynamic heuristics."""
    business_name = data.get('business_name', '').strip() or "Untitled Concept"
    problem = data.get('problem_statement', '').strip()
    solution = data.get('solution_description', '').strip()
    target_users = data.get('target_users', '').strip()
    budget = data.get('budget_range', '').strip()
    skills = data.get('skills_available', '').strip()

    if Config.AI_API_KEY:
        prompt = f"""
Evaluate this women-led business or freelance concept:
Business Name: {business_name}
Problem Statement: {problem}
Solution Description: {solution}
Target Users: {target_users}
Budget Range: {budget}
Skills Available: {skills}

Output ONLY valid JSON:
{{
  "problem_clarity_level": "Well-Defined" | "Moderate" | "Needs Refinement",
  "problem_clarity_feedback": "Detailed feedback on problem validity",
  "target_audience_feedback": "Detailed feedback on user segmentation",
  "suggested_models": [
    {{"model": "Model Name", "rationale": "Why this business model works"}},
    {{"model": "Model Name", "rationale": "Why this business model works"}}
  ],
  "mvp_steps": [
    {{"phase": "Phase 1: Customer Discovery (Week 1-2)", "action": "Specific action"}},
    {{"phase": "Phase 2: Lean Proof-of-Concept (Week 3-4)", "action": "Specific action"}},
    {{"phase": "Phase 3: Paying Customer Validation (Week 5-6)", "action": "Specific action"}},
    {{"phase": "Phase 4: Registration & Scheme Exploration (Week 7+)", "action": "Specific action"}}
  ]
}}
"""
        raw = call_ai_llm(prompt)
        if raw:
            parsed = _extract_json_from_text(raw)
            if parsed and 'problem_clarity_level' in parsed:
                return parsed

    return {}

# ==============================================================================
# 4. CONTEXT-AWARE AI CHATBOT WITH CONVERSATION MEMORY
# ==============================================================================

def chat_with_ai(
    user_message: str,
    user_context: Optional[Dict[str, Any]] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    page_context: str = '',
    detected_intent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a personalized, context-aware chatbot response for the ReTurn platform.
    Incorporates full candidate profile, resume, and conversation history.
    """
    user_context = user_context or {}
    chat_history = chat_history or []

    # Extract user attributes
    candidate_name = user_context.get('name') or (user_context.get('user', {}) or {}).get('full_name', 'Candidate')
    education = user_context.get('qualification') or user_context.get('education_level') or (user_context.get('profile', {}) or {}).get('qualification', 'Graduate')
    prev_role = user_context.get('previous_job_title') or (user_context.get('profile', {}) or {}).get('previous_job_title', 'None / First-time')
    years_exp = user_context.get('years_of_experience', 0)
    gap_duration = user_context.get('career_gap_duration') or (user_context.get('profile', {}) or {}).get('career_gap_duration', 'Career Break')
    gap_reason = user_context.get('gap_reason') or (user_context.get('profile', {}) or {}).get('gap_reason', 'Family Care / Personal')
    current_skills = user_context.get('skills') or (user_context.get('profile', {}) or {}).get('skills', '')
    target_role = user_context.get('target_role') or user_context.get('desired_career_direction') or (user_context.get('profile', {}) or {}).get('desired_career_direction', 'Career Re-entry')
    work_mode = user_context.get('work_mode_preference') or (user_context.get('profile', {}) or {}).get('work_mode_preference', 'Flexible')

    # Resume & analysis highlights if available
    latest_resume = user_context.get('latest_resume')
    resume_note = ""
    if latest_resume and latest_resume.get('raw_text'):
        resume_note = f"\n- Uploaded Resume: '{latest_resume.get('original_filename')}' (analyzed for target role '{target_role}')."

    # Map page context to guidance focus
    page_guidance = ""
    if page_context:
        page_map = {
            '/resume': 'The user is currently on the Resume Hub page. Provide direct tips on structural improvement, STAR rewrites, and career break phrasing.',
            '/roadmap': 'The user is on their Career Roadmap page. Help explain roadmap stages, task milestones, and skill priorities.',
            '/path/transition': 'The user is exploring Career Shift options. Focus on transferable skills, transition bridge projects, and functional resume format.',
            '/path/experienced': 'The user is on the Experienced + Career Gap pathway. Focus on reskilling, returnships, and direct employer readiness.',
            '/path/beginner': 'The user is on the Beginner pathway. Focus on entry-level opportunities, first resume compilation, and foundational skills.',
            '/government': 'The user is viewing Government Opportunities. Help clarify eligibility, age relaxations, and application processes.',
            '/startup': 'The user is on the Startup/Freelance Hub. Focus on business validation, MVPs, and verified government funding schemes.',
            '/dashboard': 'The user is on their Dashboard. Help explain recommendations, readiness index, and next practical steps.',
            '/career-analysis': 'The user is viewing their AI Career Analysis. Help explain identified skill gaps, suggested roles, and 90-day execution plan.',
            '/explore': 'The user is browsing job opportunities. Help with search strategy, returnee-friendly application tips, and skill matching.',
            '/learning': 'The user is browsing learning resources. Help recommend accredited courses, explain learning paths, and prioritize skills.'
        }
        for path_key, guidance in page_map.items():
            if path_key in page_context:
                page_guidance = guidance
                break

    system_prompt = (
        "You are the dedicated Career Re-Entry Assistant for the 'Women Career Gap — Reskill & Opportunity Platform' (ReTurn). "
        "Your primary purpose is to help women return to education, employment, or entrepreneurship after a career gap. "
        "STRICT GUIDELINES: "
        "1. ANSWER ONLY THE USER'S ACTUAL QUESTION DIRECTLY AND SUBSTANTIVELY. "
        "2. If the user asks 'suggest me governjob', about government jobs, civil services, public sector exams, or schemes: "
        "   - Give concrete government career pathways tailored to their target role and qualification (e.g. for software/developer roles, highlight NIC, CDAC, DRDO, BEL, and PSU bank IT Specialist Officers). "
        "   - Highlight statutory age relaxations for women returnees (5-10 years above general limits in State PSCs). "
        "   - Highlight banking exams (IBPS/SBI) where selection is 100% exam-score based and career breaks have zero penalty. "
        "   - Mention key schemes: Women Scientist Scheme (WOS-A / DISHA) for STEM returnees, Stand-Up India, Mudra Yojana. "
        "   - Direct them to view verified openings on the ReTurn [Government Schemes Hub](/government/hub). "
        "3. If the user asks 'Should I choose a startup or a job?' or career decision questions, provide a balanced, thoughtful comparison (stability, learning curve, role breadth, risk, work-life balance) tailored to their background. NEVER output an unsolicited Resume Analysis for decision questions. "
        "4. ONLY provide a Resume Analysis / ATS diagnostic if the user explicitly asks to review, analyze, or score their resume. "
        "5. If the user asks 'What should I learn?', provide specific skill priorities for their target role compared to their current skills. "
        "6. If the user asks 'How should I explain my career gap?', use their specific gap duration and reason to formulate a positive narrative. "
        "7. If the user asks for a roadmap, discuss actionable milestones and next steps. "
        "8. If the user sends a greeting ('hello', 'hi'), respond warmly and naturally without dumping unsolicited diagnostic reports. "
        "9. If the user asks about recruiter verification, explain ReTurn's 3-tier validation (corporate domain check, GST/CIN business registry, manual admin vetting). "
        "10. If the user asks about remote/WFH options, describe flexible returnships and guide them to [Opportunities Explorer](/explore). "
        "11. Keep responses warm, encouraging, structured, and easy to read using Markdown bolding, headers, and bullet points."
    )
    if page_guidance:
        system_prompt += f"\n\nCurrent Page Context: {page_guidance}"

    # Build conversation thread
    history_formatted = ""
    if chat_history:
        history_formatted = "\nRecent Conversation History:\n"
        for turn in chat_history[-6:]:
            role_label = "User" if turn.get('role') in ['user', 'candidate'] else "Assistant"
            history_formatted += f"{role_label}: {turn.get('content', '')}\n"

    candidate_context_block = f"""
Candidate Context:
- Name: {candidate_name}
- Highest Qualification: {education}
- Previous Role: {prev_role} ({years_exp} years exp)
- Career Break: {gap_duration}
- Career Break Reason: {gap_reason}
- Current Skills: {current_skills or 'General communication & problem solving'}
- Target Return Role: {target_role}
- Preferred Work Mode: {work_mode}{resume_note}
"""

    full_prompt = f"""{candidate_context_block}{history_formatted}
Detected Intent: {detected_intent or 'general_fallback'}
User Query: "{user_message}"

Answer the User Query directly. The detected intent is only a routing hint; the
quoted User Query is authoritative. Do not introduce advice about resumes, jobs,
government schemes, roadmaps, or any other topic unless the user asks about it or
it is necessary to answer the query. If the question is ambiguous, ask one concise
clarifying question instead of listing unrelated platform features.
"""

    category_map = {
        'greeting': 'Greeting',
        'startup_vs_job': 'Career Decision Support',
        'resume_analysis': 'Resume Feedback',
        'resume_generate_download': 'Resume Generation',
        'resume_improvement': 'Resume Generation',
        'skills_learning': 'Personalized Learning',
        'career_guidance': 'Career Guidance',
        'roadmap': 'Roadmap Guidance',
        'career_gap': 'Career Gap Strategy',
        'job_search': 'Role Matching',
        'interview_prep': 'Interview Prep',
        'government_schemes': 'Government Schemes',
        'startup_guidance': 'Startup & Freelance',
        'help_navigation': 'Navigation',
        'recruiter_verification': 'Platform Trust & Verification',
        'work_flexibility': 'Flexible & Remote Work',
        'salary_guidance': 'Compensation & Negotiation',
        'confidence_mindset': 'Confidence & Mindset',
        'general_fallback': 'Career Guidance',
    }
    assigned_category = category_map.get(detected_intent, 'Career Guidance')

    reply = call_ai_llm(full_prompt, system_prompt)
    if reply and len(reply.strip()) > 10:
        return {
            'reply': reply.strip(),
            'category': assigned_category,
            'disclaimer': 'Notice: Guidance generated by ReTurn Career Assistant based on your profile context.'
        }

    return {}

# ==============================================================================
# 5. PERSONALIZED AI ROADMAP GENERATION
# ==============================================================================

def generate_personalized_roadmap(profile_data: Dict[str, Any], pathway: str = 'EXPERIENCED_GAP') -> Dict[str, Any]:
    """
    Generates a 4-phase personalized learning roadmap based on the user's
    actual profile data, skills, target role, and learning preferences.
    """
    prev_title = (profile_data.get('previous_job_title') or '').strip()
    years_exp = float(profile_data.get('years_of_experience') or 0)
    gap_duration = (profile_data.get('career_gap_duration') or '1 - 3 years').strip()
    current_skills_raw = (profile_data.get('skills') or profile_data.get('current_skills') or '').strip()
    desired_role = (profile_data.get('target_role') or profile_data.get('desired_career_direction') or prev_title or 'Professional Returnee').strip()
    qualification = (profile_data.get('qualification') or profile_data.get('education') or "Bachelor's Degree").strip()
    career_goal = (profile_data.get('career_goal') or '').strip()
    learning_pref = (profile_data.get('learning_preference') or 'Self-paced').strip()
    cost_pref = (profile_data.get('cost_preference') or 'Free Only').strip()
    prev_industry = (profile_data.get('previous_industry') or 'Corporate').strip()

    candidate_skills = [s.strip() for s in current_skills_raw.split(',') if s.strip()] if current_skills_raw else []

    system_prompt = (
        "You are a Career Development Architect specializing in personalized learning roadmaps for women "
        "returning to the workforce. Create practical, phase-based roadmaps with specific skills, resources, "
        "and project suggestions based on the candidate's real profile. Return ONLY a valid JSON object matching the requested schema."
    )

    user_prompt = f"""
Create a personalized 4-phase learning roadmap for this candidate:

Profile:
- Previous Role: {prev_title or 'None'}
- Years Experience: {years_exp}
- Career Gap: {gap_duration}
- Current Skills: {', '.join(candidate_skills) if candidate_skills else 'Foundational skills'}
- Target Role: {desired_role}
- Qualification: {qualification}
- Previous Industry: {prev_industry}
- Career Goal: {career_goal or 'Secure employment in target role'}
- Learning Preference: {learning_pref}
- Budget: {cost_pref}
- Pathway: {pathway}

Required JSON Schema:
{{
  "target_summary": "One sentence describing what this roadmap prepares the candidate for",
  "estimated_duration": "8-12 weeks",
  "phases": [
    {{
      "phase_number": 1,
      "title": "Foundation",
      "duration": "Week 1-2",
      "objective": "What this phase accomplishes",
      "skills": [
        {{"name": "Skill Name", "why": "Why this skill matters for target role", "resource_suggestion": "Platform or course name"}}
      ],
      "practice_activities": ["Activity 1", "Activity 2"],
      "expected_outcome": "What the candidate can do after this phase"
    }},
    {{
      "phase_number": 2,
      "title": "Skill Development",
      "duration": "Week 3-6",
      "objective": "What this phase accomplishes",
      "skills": [
        {{"name": "Skill Name", "why": "Why this skill matters", "resource_suggestion": "Platform or course name"}}
      ],
      "practice_activities": ["Activity 1", "Activity 2"],
      "expected_outcome": "What the candidate can do after this phase"
    }},
    {{
      "phase_number": 3,
      "title": "Project & Portfolio",
      "duration": "Week 7-10",
      "objective": "Build demonstrable work",
      "skills": [
        {{"name": "Skill Name", "why": "Why", "resource_suggestion": "Platform"}}
      ],
      "practice_activities": ["Project 1", "Project 2"],
      "expected_outcome": "Tangible portfolio pieces"
    }},
    {{
      "phase_number": 4,
      "title": "Career Readiness",
      "duration": "Week 11-12",
      "objective": "Prepare for job applications and interviews",
      "skills": [
        {{"name": "Skill Name", "why": "Why", "resource_suggestion": "Platform"}}
      ],
      "practice_activities": ["Activity 1"],
      "expected_outcome": "Ready to apply and interview"
    }}
  ]
}}
"""

    ai_raw = call_ai_llm(user_prompt, system_prompt)
    if ai_raw:
        parsed = _extract_json_from_text(ai_raw)
        if parsed and 'phases' in parsed:
            return parsed

    # Deterministic fallback based on user's actual profile
    desired_lower = desired_role.lower()
    expected_skills = ROLE_CORE_SKILLS_MAP.get('general', [])
    for key, skills in ROLE_CORE_SKILLS_MAP.items():
        if key in desired_lower:
            expected_skills = skills
            break

    existing_lower = [s.lower() for s in candidate_skills]
    skill_gaps = [s for s in expected_skills if s.lower() not in existing_lower][:6]
    if not skill_gaps:
        skill_gaps = ['Cloud Tools', 'Agile Methods', 'Modern Technical Communication']

    foundation_skills = skill_gaps[:2] if len(skill_gaps) >= 2 else skill_gaps
    development_skills = skill_gaps[2:4] if len(skill_gaps) >= 4 else skill_gaps[1:3] if len(skill_gaps) >= 3 else skill_gaps
    advanced_skills = skill_gaps[4:] if len(skill_gaps) > 4 else skill_gaps[-1:]

    cost_note = "Free platforms (SWAYAM, FreeCodeCamp, NPTEL)" if 'free' in cost_pref.lower() else "Platforms like Coursera, Udemy, or LinkedIn Learning"

    return {
        "target_summary": f"This personalized roadmap prepares you for a {desired_role} position, building on your {qualification} and {years_exp:g} years of experience in {prev_industry}.",
        "estimated_duration": "10-12 weeks",
        "phases": [
            {
                "phase_number": 1,
                "title": "Foundation & Tool Refresh",
                "duration": "Week 1-2",
                "objective": f"Refresh foundational knowledge and close immediate gaps in {', '.join(foundation_skills)}",
                "skills": [{"name": s, "why": f"Core requirement for {desired_role} positions", "resource_suggestion": cost_note} for s in foundation_skills],
                "practice_activities": [
                    f"Complete introductory modules on {foundation_skills[0] if foundation_skills else 'core tools'}",
                    "Set up your professional development workspace and study schedule"
                ],
                "expected_outcome": f"Working familiarity with {', '.join(foundation_skills)} and a structured study plan"
            },
            {
                "phase_number": 2,
                "title": "Skill Development",
                "duration": "Week 3-6",
                "objective": f"Build intermediate proficiency in {', '.join(development_skills)}",
                "skills": [{"name": s, "why": f"Differentiating skill for {desired_role} candidates", "resource_suggestion": cost_note} for s in development_skills],
                "practice_activities": [
                    f"Complete structured coursework on {development_skills[0] if development_skills else 'key skills'}",
                    "Solve practice exercises and assessments to validate understanding"
                ],
                "expected_outcome": f"Intermediate competency in {', '.join(development_skills)} with evidence of completion"
            },
            {
                "phase_number": 3,
                "title": "Project & Portfolio",
                "duration": "Week 7-10",
                "objective": "Build 1-2 portfolio projects demonstrating practical capability",
                "skills": [{"name": s, "why": "Demonstrates applied knowledge to employers", "resource_suggestion": "Personal project or case study"} for s in advanced_skills],
                "practice_activities": [
                    f"Build a project applying {', '.join(skill_gaps[:3])} to a real-world scenario",
                    "Document your project with a professional write-up or GitHub repository"
                ],
                "expected_outcome": "1-2 tangible portfolio pieces that demonstrate job-ready skills"
            },
            {
                "phase_number": 4,
                "title": "Career Readiness",
                "duration": "Week 11-12",
                "objective": "Prepare resume, practice interviews, and begin applications",
                "skills": [{"name": "Interview Preparation", "why": "Essential for converting applications to offers", "resource_suggestion": "ReTurn platform interview preparation resources"}],
                "practice_activities": [
                    "Update resume with new skills, projects, and career break framing",
                    f"Practice behavioral and technical interview questions for {desired_role}",
                    "Apply to 5-10 suitable positions through verified channels"
                ],
                "expected_outcome": f"Polished resume, interview confidence, and active applications for {desired_role} roles"
            }
        ]
    }
