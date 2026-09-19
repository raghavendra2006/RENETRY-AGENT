import re
from typing import List, Dict, Any, Optional

def match_jobs_for_candidate(jobs: List[Any], profile: Optional[Any]) -> List[Dict[str, Any]]:
    """
    Dynamically ranks and scores jobs against the candidate's actual profile.
    Computes a realistic match score (0-100%) and explicit match rationale.
    """
    if not jobs:
        return []

    if not profile:
        # Default ranking without profile context
        ranked = []
        for j in jobs:
            jd = dict(j)
            jd['match_score'] = 70
            jd['match_reasons'] = ["Standard platform listing"]
            ranked.append(jd)
        return ranked

    # Extract candidate attributes
    profile_dict = dict(profile)
    skills_raw = profile_dict.get('skills') or ''
    candidate_skills = set(s.strip().lower() for s in skills_raw.split(',') if s.strip())

    desired_role = (profile_dict.get('desired_career_direction') or '').lower().strip()
    work_mode_pref = (profile_dict.get('work_mode_preference') or 'Flexible / Any').lower().strip()
    preferred_loc = (profile_dict.get('preferred_work_location') or profile_dict.get('location') or '').lower().strip()
    pref_sector = (profile_dict.get('preferences_sector') or 'Private').lower().strip()

    ranked_jobs = []

    for j in jobs:
        job = dict(j)
        score = 50  # Baseline
        reasons = []

        # 1. Skill Matching
        job_skills_raw = job.get('skills_required') or ''
        job_skills = [s.strip() for s in job_skills_raw.split(',') if s.strip()]
        matched_skills = []
        for js in job_skills:
            js_clean = js.lower()
            if any(cs in js_clean or js_clean in cs for cs in candidate_skills):
                matched_skills.append(js)

        if matched_skills:
            skill_boost = min(30, len(matched_skills) * 10)
            score += skill_boost
            reasons.append(f"Skill match: {', '.join(matched_skills[:3])}")
        elif candidate_skills:
            score -= 5

        # 2. Desired Role Alignment
        title = (job.get('title') or '').lower()
        desc = (job.get('description') or '').lower()
        if desired_role:
            role_keywords = [w for w in re.split(r'\s+|,', desired_role) if len(w) > 2]
            title_matches = [w for w in role_keywords if w in title]
            if title_matches:
                score += 15
                reasons.append(f"Direct role alignment: {job['title'][:35]}")
            elif any(w in desc for w in role_keywords):
                score += 8
                reasons.append("Field relevance in job description")

        # 3. Work Mode Preference
        job_work_mode = (job.get('work_mode') or '').lower()
        if 'flexible' in work_mode_pref or 'any' in work_mode_pref:
            score += 5
        elif work_mode_pref in job_work_mode or job_work_mode in work_mode_pref:
            score += 10
            reasons.append(f"Preferred work mode: {job.get('work_mode')}")
        else:
            score -= 5

        # 4. Location Match
        job_loc = (job.get('location') or '').lower()
        if 'remote' in job_work_mode:
            score += 5
            reasons.append("Remote eligibility")
        elif preferred_loc and any(loc_part in job_loc for loc_part in preferred_loc.split(',')):
            score += 10
            reasons.append("Preferred city match")

        # 5. Sector Preference
        source_type = job.get('source_type') or ''
        if 'private' in pref_sector and source_type in ['VERIFIED_RECRUITER', 'PLATFORM_REVIEWED', 'EXTERNAL_SOURCE']:
            score += 5
        elif 'government' in pref_sector and source_type == 'GOVERNMENT_SOURCE':
            score += 15
            reasons.append("Government sector match")

        # Clamp score between 45% and 98%
        final_score = max(45, min(98, score))
        job['match_score'] = final_score
        if not reasons:
            reasons.append("General opportunity match for your pathway")
        job['match_reasons'] = reasons

        ranked_jobs.append(job)

    # Sort by match_score descending, then by id descending
    ranked_jobs.sort(key=lambda x: (x['match_score'], x.get('id', 0)), reverse=True)
    return ranked_jobs
