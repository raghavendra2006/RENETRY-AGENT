from typing import Dict, Any, List

VERIFIED_SCHEMES = [
    {
        'name': 'Stand-Up India Scheme for Women',
        'sponsor': 'Department of Financial Services, Ministry of Finance',
        'focus': 'Greenfield enterprises in manufacturing, services, or trading sector.',
        'details': 'Offers collateral-backed commercial bank loans from Rs. 10 Lakh to Rs. 1 Crore to at least one woman entrepreneur per bank branch.',
        'official_url': 'https://www.standupmitra.in',
        'eligibility': 'Adult woman entrepreneur with at least 51% shareholding and controlling stake in greenfield business.'
    },
    {
        'name': 'Pradhan Mantri Mudra Yojana (PMMY) - Mahila Udyami Initiative',
        'sponsor': 'Ministry of MSME & National Credit Guarantee Trustee Co.',
        'focus': 'Micro and small non-corporate enterprises.',
        'details': 'Provides collateral-free loans up to Rs. 10 Lakhs through banks and microfinance institutions across Shishu, Kishore, and Tarun categories.',
        'official_url': 'https://www.mudra.org.in',
        'eligibility': 'Small business owners, artisans, home-based producers, and service providers.'
    },
    {
        'name': 'Trade Related Entrepreneurship Assistance and Development (TREAD) for Women',
        'sponsor': 'Ministry of Micro, Small & Medium Enterprises (MSME)',
        'focus': 'Micro-enterprises, self-help groups, and cooperative economic ventures.',
        'details': 'Provides Government of India grant up to 30% of the total project cost appraised by lending institutions through eligible non-profit organizations.',
        'official_url': 'https://msme.gov.in',
        'eligibility': 'Women entrepreneurs and self-help groups working through registered non-governmental organizations.'
    },
    {
        'name': 'Udyam Registration Portal (MSME Registration)',
        'sponsor': 'Ministry of MSME, Govt. of India',
        'focus': 'Statutory recognition as a Micro, Small, or Medium Enterprise.',
        'details': 'Free paperless online registration granting access to priority sector lending, exemption under direct tax laws, and protection against delayed payments.',
        'official_url': 'https://udyamregistration.gov.in',
        'eligibility': 'Any individual proprietor or registered partnership/LLP.'
    }
]

def analyze_startup_idea(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Substantive analysis of a business or freelance concept.
    Does NOT invent investors, fake grants, or guaranteed approvals.
    """
    business_name = data.get('business_name', '').strip() or "Untitled Concept"
    problem = data.get('problem_statement', '').strip()
    solution = data.get('solution_description', '').strip()
    target_users = data.get('target_users', '').strip()
    skills = data.get('skills_available', '').strip()
    budget = data.get('budget_range', '').strip()
    location = data.get('location', '').strip()
    # Try AI evaluation if configured
    try:
        from services.ai_service import evaluate_startup_idea_ai
        ai_eval = evaluate_startup_idea_ai(data)
        if ai_eval and ai_eval.get('problem_clarity_level'):
            ai_eval['business_name'] = business_name
            ai_eval['verified_schemes'] = VERIFIED_SCHEMES
            skill_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            skill_label = ", ".join(skill_list[:3]) or "your strongest verified skills"
            ai_eval['freelance_launch_plan'] = [
                {'step': 'Define your offer', 'action': f"Turn {skill_label} into one outcome-focused service for {target_users or 'a narrowly defined client segment'}."},
                {'step': 'Build proof', 'action': "Publish three representative samples with scope, process, and tools actually used."},
                {'step': 'Qualify clients', 'action': "Confirm scope, deadline, ownership, revisions, and payment milestones in writing before starting."},
                {'step': 'Deliver and grow', 'action': "Invoice each engagement, collect feedback, and pursue retainers only after reliable delivery."}
            ]
            ai_eval['freelance_advice'] = [
                "Use reputable channels such as LinkedIn Services, Contra, Upwork, or direct local-business outreach.",
                "Label portfolio work honestly and never claim clients, results, or credentials you cannot verify.",
                "Use a written scope and payment milestone plan, and never pay a fee to obtain freelance work."
            ]
            ai_eval['funding_disclaimer'] = "IMPORTANT: Funding eligibility depends on the specific scheme, formal application, business viability, and official institutional approval. ReTurn does not guarantee loan sanctions, subsidies, or investor commitments."
            return ai_eval
    except Exception as e:
        print(f"[Startup Analyzer] AI evaluation fallback: {e}")

    # 1. Problem Clarity Evaluation
    word_count = len(problem.split())
    if word_count < 15:
        clarity_level = "Needs Refinement"
        clarity_feedback = "The problem statement is very concise. Specify the exact pain point, who suffers from it most frequently, and what happens when it is left unaddressed."
    elif word_count < 40:
        clarity_level = "Moderate"
        clarity_feedback = "Good baseline description. Next, articulate why existing solutions or substitutes fail to solve this problem adequately."
    else:
        clarity_level = "Well-Defined"
        clarity_feedback = "Comprehensive problem definition articulating context and user pain points."

    # 2. Target Audience Analysis
    user_words = len(target_users.split())
    if any(broad in target_users.lower() for broad in ['everyone', 'all people', 'anyone', 'general public']):
        target_feedback = "Target audience is defined too broadly ('everyone'). In early stages, narrow down to a specific initial niche (e.g. working parents in Tier 2 cities, boutique retail shops, freelance professionals)."
    elif user_words < 6:
        target_feedback = "Please define target users with demographic or behavioral specificity (e.g., job roles, age brackets, geographic or budget constraints)."
    else:
        target_feedback = f"Identified audience segment: '{target_users}'. Focus initial customer interviews specifically on this cohort."

    # 3. Suggested Business Models
    suggested_models = [
        {
            'model': 'Direct B2C / Client Service',
            'rationale': 'Lowest capital requirement. Bill directly for services or bespoke deliverables before investing in complex product infrastructure.'
        },
        {
            'model': 'Retainer / Subscription Tier',
            'rationale': 'Provides predictable monthly recurring revenue for continuous consulting, content, coaching, or maintenance support.'
        },
        {
            'model': 'Micro-Batch Product or Commission Marketplace',
            'rationale': 'Validate demand using pre-orders or low-inventory batches before committing significant manufacturing or procurement capital.'
        }
    ]

    # 4. Step-by-Step Minimum Viable Product (MVP) Execution Roadmap
    mvp_steps = [
        {
            'phase': 'Phase 1: Customer Discovery (Week 1-2)',
            'action': f"Conduct 8 to 10 informal 15-minute interviews with representative {target_users if target_users else 'prospective clients'} to validate that they actively seek a solution for: '{problem[:80]}...'."
        },
        {
            'phase': 'Phase 2: Lean Proof-of-Concept (Week 3-4)',
            'action': "Deliver the core service manually or via a simple no-code / low-cost landing page, WhatsApp Business channel, or prototype without upfront software expenditure."
        },
        {
            'phase': 'Phase 3: First Paying Customer Validation (Week 5-6)',
            'action': "Secure 2 to 3 paid engagements or advance commitments. Pricing validation is the only real proof of genuine market demand."
        },
        {
            'phase': 'Phase 4: Formal Registration & Scheme Exploration (Week 7+)',
            'action': "Register your enterprise on the official Udyam portal to obtain your MSME certificate, open a dedicated business current account, and assess relevant credit facilities."
        }
    ]

    # 5. Freelance Pathways
    skill_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
    skill_label = ", ".join(skill_list[:3]) or "your strongest verified skills"
    freelance_advice = [
        f"Package one clear service around {skill_label}; describe the client problem, deliverable, turnaround, and revision policy in one short offer.",
        "Create three portfolio samples from real work, clearly labelled as client work, personal work, or a sample project. Do not claim results or clients you cannot verify.",
        "Start with a fixed-scope pilot, confirm requirements and payment terms in writing, then request a testimonial after delivery before pursuing a retainer.",
        "Use reputable channels such as LinkedIn Services, Contra, Upwork, or direct local-business outreach. Verify the client identity and never pay a fee to obtain work.",
    ]
    freelance_launch_plan = [
        {
            'step': 'Define your offer',
            'action': f"Turn {skill_label} into one outcome-focused service for a specific client group: {target_users or 'a narrowly defined client segment'}."
        },
        {
            'step': 'Build proof',
            'action': "Publish three representative samples with your process, scope, tools actually used, and a clear contact method."
        },
        {
            'step': 'Find and qualify clients',
            'action': "Contact relevant businesses or apply to matching briefs. Confirm scope, deadline, ownership, revisions, and payment milestones before starting."
        },
        {
            'step': 'Deliver and grow',
            'action': "Use a simple written agreement, invoice every engagement, collect feedback, and convert repeat work into a monthly retainer only after reliable delivery."
        }
    ]

    disclaimer = "IMPORTANT: Funding eligibility depends on the specific scheme, formal application, business viability, and official institutional approval. ReTurn does not guarantee loan sanctions, subsidies, or investor commitments."

    return {
        'business_name': business_name,
        'problem_clarity_level': clarity_level,
        'problem_clarity_feedback': clarity_feedback,
        'target_audience_feedback': target_feedback,
        'suggested_models': suggested_models,
        'mvp_steps': mvp_steps,
        'verified_schemes': VERIFIED_SCHEMES,
        'freelance_advice': freelance_advice,
        'freelance_launch_plan': freelance_launch_plan,
        'funding_disclaimer': disclaimer
    }
