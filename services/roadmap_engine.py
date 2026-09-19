import sqlite3
import json
from typing import Dict, Any, List, Optional
from config import Config
from database import get_db_connection

def generate_dynamic_stages(profile_dict: Dict[str, Any], pathway: str = 'EXPERIENCED_GAP') -> List[Dict[str, Any]]:
    """
    Dynamically generates customized 7-stage roadmap milestones, practical tasks,
    and stage-specific evaluation tests based on candidate's actual target role, skills,
    experience, career gap, and identified skill gaps.
    """
    target_role = (
        profile_dict.get('target_role') or
        profile_dict.get('desired_career_direction') or
        profile_dict.get('previous_job_title') or
        'Professional Returnee'
    ).strip()

    prev_title = (profile_dict.get('previous_job_title') or '').strip()
    gap_duration = (profile_dict.get('career_gap_duration') or '1 - 3 years').strip()
    gap_reason = (profile_dict.get('gap_reason') or 'Personal Break / Caregiving').strip()
    skills_raw = (profile_dict.get('skills') or '').strip()
    skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
    top_skills_str = ', '.join(skills_list[:3]) if skills_list else f'{target_role} Core Competencies'
    primary_skill = skills_list[0] if skills_list else 'Core Domain Methodology'
    secondary_skill = skills_list[1] if len(skills_list) > 1 else 'Modern Industry Tooling'
    qualification = (profile_dict.get('qualification') or profile_dict.get('education') or 'Degree').strip()
    work_mode = (profile_dict.get('work_mode_preference') or 'Flexible').strip()

    if pathway == 'NO_EXPERIENCE':
        return [
            {
                'stage': 1,
                'title': f'Foundational Clarity for {target_role}',
                'objective': f'Establish core academic alignment and define entry-level competencies required for modern {target_role} positions.',
                'estimated_effort': '1 week (6-8 hours)',
                'skills_to_learn': [f'{target_role} Fundamentals', 'Academic Translation', 'Goal Setting'],
                'topics': ['Industry role hierarchy', 'Key terminology and workflows', 'Competency mapping'],
                'practical_activity': {
                    'title': f'{target_role} Entry Competency Audit',
                    'type': 'Self-Assessment Task',
                    'description': f'Map your academic coursework in {qualification} against 3 verified entry-level job descriptions for {target_role}. Document your top 3 foundational strengths and 2 priority reskilling areas.',
                    'deliverable': 'Documented entry-level competency checklist.'
                },
                'expected_outcome': f'Clear roadmap clarity on essential entry-level expectations for {target_role}.',
                'tasks': [
                    ('noexp_s1_t1', f'Complete academic profile highlighting {qualification} and coursework', '/profile/complete'),
                    ('noexp_s1_t2', f'Define entry-level competencies and target goals for {target_role}', '/path/beginner')
                ],
                'test': [
                    {
                        'id': 'q_noexp_s1_1',
                        'question': f'When entering {target_role} without prior industry experience, what is the most effective way to demonstrate capability to recruiters?',
                        'options': [
                            'Claim previous senior job titles to bypass automated resume filters',
                            'Showcase relevant academic coursework, verified hands-on projects, and documented skills',
                            'Apply only to general administrative jobs without customizing application materials',
                            'Wait until you have completed multiple master degrees before applying'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Career Strategy & Entry Positioning',
                        'explanation': 'Recruiters evaluate entry-level candidates on tangible evidence of capability: coursework, hands-on projects, and quantifiable skill demonstrations.'
                    },
                    {
                        'id': 'q_noexp_s1_2',
                        'question': f'Which core element is essential when analyzing a job description for {target_role}?',
                        'options': [
                            'Focusing solely on salary without reviewing required technical proficiencies',
                            'Identifying recurring required tools, required methodologies, and core deliverables',
                            'Assuming all listed requirements are optional and applying blindly',
                            'Ignoring the preferred qualifications and company sector'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Role Analysis & Requirements Mapping',
                        'explanation': 'Systematically auditing recurring tools and methodologies allows you to tailor your learning directly to market demand.'
                    },
                    {
                        'id': 'q_noexp_s1_3',
                        'question': f'What should be the primary objective of your early learning habit for {target_role}?',
                        'options': [
                            'Memorizing theoretical definitions without practicing any practical application',
                            'Establishing consistent daily practice and building tangible work artifacts',
                            'Switching programming languages or tools every two days',
                            'Relying exclusively on passive video watching without taking notes'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Structured Learning Habit',
                        'explanation': 'Active recall, consistent daily routines, and building verifiable artifacts produce rapid competency acquisition.'
                    }
                ]
            },
            {
                'stage': 2,
                'title': f'Core Competency Selection: {top_skills_str}',
                'objective': f'Master the foundational technical and analytical concepts underpinning {target_role}.',
                'estimated_effort': '2 weeks (12-15 hours)',
                'skills_to_learn': [primary_skill, secondary_skill, 'Problem Decomposition'],
                'topics': [f'{primary_skill} core syntax & principles', 'Standard development environments', 'Algorithmic logic'],
                'practical_activity': {
                    'title': f'{primary_skill} Code / Logic Exercise',
                    'type': 'Hands-on Technical Task',
                    'description': f'Write clean, modular code or structured workflow implementing a fundamental problem-solving routine using {primary_skill}.',
                    'deliverable': 'Working script or verified modular exercise.'
                },
                'expected_outcome': f'Demonstrated proficiency in {primary_skill} fundamentals with clean syntax.',
                'tasks': [
                    ('noexp_s2_t1', f'Select 2 primary foundational skills to master for {target_role}', '/path/beginner'),
                    ('noexp_s2_t2', 'Establish a daily 2-hour structured learning habit', '/path/beginner')
                ],
                'test': [
                    {
                        'id': 'q_noexp_s2_1',
                        'question': f'In practical application of {primary_skill}, why is modular code/workflow design preferred?',
                        'options': [
                            'It makes debugging and maintenance significantly easier by isolating functionality',
                            'It increases file size and makes the program run slower',
                            'It prevents other team members from understanding your solution',
                            'It is required only in academic assignments, not in real industry'
                        ],
                        'correct_index': 0,
                        'topic_tag': f'{primary_skill} Architecture',
                        'explanation': 'Modular architecture divides software into independent units that can be tested, reused, and maintained efficiently.'
                    },
                    {
                        'id': 'q_noexp_s2_2',
                        'question': 'When encountering an unfamiliar error or runtime failure during development, what is the best first step?',
                        'options': [
                            'Delete the entire project and restart from scratch',
                            'Examine the error stack trace, isolate the failing input, and check official documentation',
                            'Ignore the error and comment out the failing function permanently',
                            'Change random variables until the program finishes without error'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Systematic Debugging',
                        'explanation': 'Systematic debugging involves inspecting the exact line, stack trace, and expected vs actual values.'
                    },
                    {
                        'id': 'q_noexp_s2_3',
                        'question': 'Why is version control (e.g., Git) essential even for early individual projects?',
                        'options': [
                            'It is only useful when working in teams larger than 50 engineers',
                            'It tracks iterative changes, prevents loss of working code, and provides proof of progress',
                            'It automatically writes unit tests for your code',
                            'It replaces the need to understand data structures'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Version Control & Workflow',
                        'explanation': 'Git maintains a verifiable history of commits, facilitates branching, and demonstrates collaborative readiness.'
                    }
                ]
            },
            {
                'stage': 3,
                'title': f'Guided Hands-on Learning for {target_role}',
                'objective': f'Apply {primary_skill} and related tools to real-world scenarios through structured coursework.',
                'estimated_effort': '2 weeks (10-14 hours)',
                'skills_to_learn': ['Applied Frameworks', 'API Integration / Data Handling', 'Testing Basics'],
                'topics': ['Component interaction', 'Error handling', 'Data validation'],
                'practical_activity': {
                    'title': 'Guided Case Study Implementation',
                    'type': 'Mini Case Study',
                    'description': f'Complete an interactive scenario solving an authentic business challenge using {primary_skill} and modern standard libraries.',
                    'deliverable': 'Executed case study with verified outputs.'
                },
                'expected_outcome': 'Ability to transform requirements into working technical solutions.',
                'tasks': [
                    ('noexp_s3_t1', f'Enroll in verified free courses aligned with {target_role} requirements', '/learning'),
                    ('noexp_s3_t2', 'Complete weekly self-assessments and practice exercises', '/learning')
                ],
                'test': [
                    {
                        'id': 'q_noexp_s3_1',
                        'question': 'What is the primary benefit of writing unit tests for your functions or modules?',
                        'options': [
                            'It proves that future code changes do not break existing functionality',
                            'It eliminates the need for user input validation',
                            'It replaces the need to compile your program',
                            'It makes the application run twice as fast'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Testing & Quality Assurance',
                        'explanation': 'Unit tests provide automated regression protection, ensuring that modifications do not introduce unintended defects.'
                    },
                    {
                        'id': 'q_noexp_s3_2',
                        'question': 'How should unexpected user inputs or invalid data types be handled in robust applications?',
                        'options': [
                            'Allow the program to crash abruptly so the user notices the error',
                            'Implement proactive input validation and clear, user-friendly exception handling',
                            'Silently swallow all errors and return empty strings',
                            'Disable user input fields permanently'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Error Handling & Resilience',
                        'explanation': 'Graceful exception handling and defensive validation ensure system stability and protect against unexpected crashes.'
                    },
                    {
                        'id': 'q_noexp_s3_3',
                        'question': 'When selecting learning resources, why prioritize interactive, project-driven materials over passive lectures?',
                        'options': [
                            'Active implementation reinforces muscle memory and problem-solving intuition',
                            'Passive lectures guarantee immediate employment without coding',
                            'Interactive exercises require less cognitive effort than watching videos',
                            'There is no difference in knowledge retention'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Effective Learning Methodology',
                        'explanation': 'Constructing real implementations forces active problem decomposition and dramatically improves long-term skill retention.'
                    }
                ]
            },
            {
                'stage': 4,
                'title': 'Applied Exercises & Mini-Projects',
                'objective': f'Design, build, and document a self-directed mini-project simulating entry-level {target_role} tasks.',
                'estimated_effort': '2-3 weeks (15-20 hours)',
                'skills_to_learn': ['Project Architecture', 'Documentation', 'End-to-End Execution'],
                'topics': ['Requirements specification', 'Implementation pipeline', 'README documentation'],
                'practical_activity': {
                    'title': f'{target_role} Portfolio Work Sample',
                    'type': 'Portfolio Project',
                    'description': f'Build a functional application, data analysis report, or automated tool solving a real problem for {target_role}. Write a comprehensive README with setup instructions.',
                    'deliverable': 'GitHub repository / work sample with clear documentation.'
                },
                'expected_outcome': 'Verifiable work sample demonstrating end-to-end technical execution.',
                'tasks': [
                    ('noexp_s4_t1', f'Complete 2 practical projects simulating entry-level {target_role} tasks', '/path/beginner'),
                    ('noexp_s4_t2', 'Document problem-solving methodology and learning milestones', '/path/beginner')
                ],
                'test': [
                    {
                        'id': 'q_noexp_s4_1',
                        'question': 'What makes a technical portfolio project most impressive to engineering hiring managers?',
                        'options': [
                            'A generic clone of a tutorial without any custom features or original architecture',
                            'A well-documented project solving a real problem with clear architecture, tests, and a detailed README',
                            'A repository containing only downloaded zip files without commit history',
                            'A complex project with no instructions on how to install or run it'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Portfolio Quality & Presentation',
                        'explanation': 'Hiring managers value clear problem definition, clean commit history, architecture decisions, and reproducible setup guides.'
                    },
                    {
                        'id': 'q_noexp_s4_2',
                        'question': 'What are the essential sections of a professional project README?',
                        'options': [
                            'Only the author name and date',
                            'Project overview, features, prerequisites, installation steps, usage examples, and architecture overview',
                            'A single screenshot with no text or explanation',
                            'The entire raw source code pasted into markdown'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Technical Documentation',
                        'explanation': 'A complete README allows anyone to understand the project motivation, install dependencies, and run test suites seamlessly.'
                    },
                    {
                        'id': 'q_noexp_s4_3',
                        'question': 'When presenting project achievements on your profile or resume, how should you format your statements?',
                        'options': [
                            'Use vague phrases like "worked on coding" or "helped with backend"',
                            'Quantify scope, highlight specific tools used, and describe the problem solved',
                            'Claim that the project generated millions of dollars in revenue without evidence',
                            'Omit all details so recruiters are forced to ask'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Project Impact Framing',
                        'explanation': 'Factual, quantified descriptions detailing the exact tools and problem solved establish credible competency.'
                    }
                ]
            },
            {
                'stage': 5,
                'title': f'First Professional Resume for {target_role}',
                'objective': f'Structure and generate an authentic, ATS-optimized resume emphasizing {qualification}, skills, and projects.',
                'estimated_effort': '1 week (5-7 hours)',
                'skills_to_learn': ['ATS Optimization', 'STAR Bullet Formulation', 'Keyword Highlighting'],
                'topics': ['Action verb selection', 'Section hierarchy', 'Keyword transparency'],
                'practical_activity': {
                    'title': 'Resume Generation & Keyword Audit',
                    'type': 'Resume Hub Optimization',
                    'description': f'Run Resume Hub analysis for {target_role}, review matching keywords, apply STAR bullet improvements, and download your updated .docx resume.',
                    'deliverable': 'Downloadable updated .docx resume file.'
                },
                'expected_outcome': 'ATS-compliant professional resume tailored for entry-level applications.',
                'tasks': [
                    ('noexp_s5_t1', f'Build entry-level resume highlighting {qualification}, skills, and projects', '/resume/hub'),
                    ('noexp_s5_t2', 'Verify all educational and project details are authentic and quantified', '/resume/hub')
                ],
                'test': [
                    {
                        'id': 'q_noexp_s5_1',
                        'question': 'What is the STAR method for crafting impactful resume bullet points?',
                        'options': [
                            'Skills, Titles, Academics, References',
                            'Situation, Task, Action, Result',
                            'Software, Testing, Automation, Reporting',
                            'Summary, Timeline, Achievements, Recommendations'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'STAR Method & Bullet Optimization',
                        'explanation': 'STAR (Situation, Task, Action, Result) provides a structured narrative illustrating what challenge you faced, the action you took, and the tangible outcome.'
                    },
                    {
                        'id': 'q_noexp_s5_2',
                        'question': 'Why should you never fabricate unverified skills or credentials on your resume?',
                        'options': [
                            'Because ATS systems immediately delete any resume with technical words',
                            'Because technical interviews and background verifications will quickly expose fabrications, ruining professional credibility',
                            'Because companies only hire candidates who know zero skills',
                            'Because resumes should contain only hobbies and personal interests'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Resume Integrity & Compliance',
                        'explanation': 'Maintaining 100% factual integrity protects your professional reputation and ensures you can confidently speak to every item listed.'
                    },
                    {
                        'id': 'q_noexp_s5_3',
                        'question': 'How does our platform ensure your resume remains ATS-compliant?',
                        'options': [
                            'By using complex multi-column graphics and invisible text',
                            'By using clean standard headings, recognized section hierarchy, strong action verbs, and valid DOCX formatting',
                            'By generating a random fake score without analyzing the text',
                            'By submitting applications without candidate approval'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'ATS Compatibility Standards',
                        'explanation': 'Applicant Tracking Systems parse standard textual headings, linear hierarchy, and clean semantic structure.'
                    }
                ]
            },
            {
                'stage': 6,
                'title': f'Entry-Level & Fellowship Search: {target_role}',
                'objective': f'Identify, filter, and track verified entry-level openings and fellowship programs matching {target_role}.',
                'estimated_effort': '1-2 weeks (8-10 hours)',
                'skills_to_learn': ['Job Discovery', 'Opportunity Evaluation', 'Application Tracking'],
                'topics': ['Recruiter verification badges', 'Public sector schemes', 'Application pipeline'],
                'practical_activity': {
                    'title': 'Target Pipeline Formulation',
                    'type': 'Application Strategy',
                    'description': f'Explore verified jobs and bookmark at least 3 matching positions for {target_role}. Track application deadlines and required qualifications.',
                    'deliverable': 'Active bookmarked opportunities in your candidate dashboard.'
                },
                'expected_outcome': 'Curated pipeline of high-alignment opportunities ready for submission.',
                'tasks': [
                    ('noexp_s6_t1', f'Filter opportunities matching entry-level {target_role} positions', '/explore'),
                    ('noexp_s6_t2', 'Explore government apprenticeships and fellowship programs', '/government/hub')
                ],
                'test': [
                    {
                        'id': 'q_noexp_s6_1',
                        'question': 'What does the "Verified Recruiter" badge on the ReTurn platform signify?',
                        'options': [
                            'The job was posted by an automated scraper with no human oversight',
                            'The recruiter corporate domain and identity have been manually verified by platform administrators',
                            'The job is guaranteed to be awarded to the first applicant regardless of qualifications',
                            'The job listing requires an upfront application fee'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Platform Verification & Trust',
                        'explanation': 'The Verified Recruiter badge ensures that the employer is an authenticated organization actively reviewing candidates.'
                    },
                    {
                        'id': 'q_noexp_s6_2',
                        'question': 'When applying to multiple openings, why is tailoring your resume to each job description crucial?',
                        'options': [
                            'It highlights your most relevant competencies and keywords directly matching the role requirements',
                            'It allows you to change your name for every application',
                            'It is required by law in every state',
                            'It makes the application file size smaller'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Targeted Application Strategy',
                        'explanation': 'Tailoring ensures the hiring team immediately recognizes that your specific skills align with their open needs.'
                    },
                    {
                        'id': 'q_noexp_s6_3',
                        'question': 'What is the best approach when tracking multiple active job applications?',
                        'options': [
                            'Apply to hundreds of unrelated jobs without noting company names or dates',
                            'Maintain a structured pipeline tracking company, role, submission date, status, and follow-up milestones',
                            'Never check your email or dashboard notifications after applying',
                            'Assume silence after 24 hours means the company has shut down'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Application Pipeline Management',
                        'explanation': 'Systematic tracking prevents missed interview invitations and keeps your follow-up cadence professional.'
                    }
                ]
            },
            {
                'stage': 7,
                'title': 'Behavioral & Entry-Level Interview Prep',
                'objective': f'Master behavioral and technical interview communication for entry-level {target_role} roles.',
                'estimated_effort': '1-2 weeks (8-12 hours)',
                'skills_to_learn': ['Behavioral Communication', 'Technical Articulation', 'Confidence Building'],
                'topics': ['Elevator pitch', 'Handling lack of prior experience', 'Asking insightful interviewer questions'],
                'practical_activity': {
                    'title': 'Elevator Pitch & Mock Interview Simulation',
                    'type': 'Interview Readiness',
                    'description': f'Formulate and practice a 2-minute introduction highlighting your {qualification}, projects in {primary_skill}, and readiness to deliver value as {target_role}.',
                    'deliverable': 'Recorded or written 2-minute elevator pitch.'
                },
                'expected_outcome': 'Confident interview delivery and clear technical communication.',
                'tasks': [
                    ('noexp_s7_t1', 'Practice foundational behavioral questions on adaptability and teamwork', '/learning?category=Interview+Preparation'),
                    ('noexp_s7_t2', f'Submit tailored applications for verified entry-level {target_role} openings', '/explore')
                ],
                'test': [
                    {
                        'id': 'q_noexp_s7_1',
                        'question': 'How should you answer the interview question: "Tell me about a time you faced a difficult technical obstacle"?',
                        'options': [
                            'State that you have never faced any obstacles and everything you write is perfect',
                            'Describe the specific challenge, your systematic troubleshooting steps, the resolution, and what you learned',
                            'Blame your classmates or professors for giving unclear instructions',
                            'Refuse to answer because it is a personal question'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Behavioral Interview Strategy',
                        'explanation': 'Interviewers want to see self-awareness, problem-solving resilience, and the ability to learn from difficulties.'
                    },
                    {
                        'id': 'q_noexp_s7_2',
                        'question': 'When the interviewer asks: "Do you have any questions for us?", what is the most strategic response?',
                        'options': [
                            '"No, I want to finish the interview as quickly as possible."',
                            'Ask insightful questions about team culture, upcoming technical initiatives, and success metrics for the role',
                            'Ask only about paid vacation days in the first 5 minutes of meeting the hiring manager',
                            '"Can you tell me if I passed the interview right now?"'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Interviewer Engagement & Inquiry',
                        'explanation': 'Thoughtful questions demonstrate genuine engagement, intellectual curiosity, and career intentionality.'
                    },
                    {
                        'id': 'q_noexp_s7_3',
                        'question': 'How should you position your entry-level status during an interview for {target_role}?',
                        'options': [
                            'Apologize repeatedly for not having 10 years of experience',
                            'Emphasize your fresh knowledge of modern tools, rapid learning ability, adaptability, and passion for the domain',
                            'Pretend you were the CEO of a fortune 500 company',
                            'Remain silent whenever technical terms are mentioned'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Entry-Level Value Proposition',
                        'explanation': 'Framing your entry status around eagerness to learn, modern foundation, and disciplined execution creates strong recruiter confidence.'
                    }
                ]
            }
        ]

    elif pathway == 'CAREER_SHIFT':
        return [
            {
                'stage': 1,
                'title': f'Career Pivot Alignment: {prev_title or "Previous Field"} to {target_role}',
                'objective': f'Map transferable competencies from {prev_title or "prior domain"} and establish a clear bridge to {target_role}.',
                'estimated_effort': '1-2 weeks (8-10 hours)',
                'skills_to_learn': ['Transferable Competency Mapping', 'Domain Translation', 'Pivot Strategy'],
                'topics': ['Cross-domain skill translation', 'Addressing industry differences', 'Setting transition milestones'],
                'practical_activity': {
                    'title': 'Transferable Matrix Formulation',
                    'type': 'Skill Audit & Alignment',
                    'description': f'Create a 2-column matrix mapping your past achievements in {prev_title or "prior role"} directly to core responsibilities of {target_role}.',
                    'deliverable': 'Documented transferable competency bridge.'
                },
                'expected_outcome': f'Clear conceptual narrative bridging prior career experience to {target_role}.',
                'tasks': [
                    ('shift_s1_t1', f'Map prior experience in {prev_title or "previous domain"} to {target_role} requirements', '/path/transition'),
                    ('shift_s1_t2', f'Define specific target criteria and {work_mode} requirements for {target_role}', '/profile/complete')
                ],
                'test': [
                    {
                        'id': 'q_shift_s1_1',
                        'question': f'When pivoting from {prev_title or "a different field"} into {target_role}, what is your strongest competitive advantage?',
                        'options': [
                            'Erasing all your past work history completely from memory',
                            'Leveraging established domain expertise, professional maturity, problem-solving, and cross-functional collaboration',
                            'Pretending you just graduated from high school yesterday',
                            'Applying only to senior leadership roles in fields you have never studied'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Transferable Value Proposition',
                        'explanation': 'Career pivoters bring valuable professional maturity, stakeholder communication, and domain context that fresh graduates often lack.'
                    },
                    {
                        'id': 'q_shift_s1_2',
                        'question': 'How should you explain your career shift in your professional summary?',
                        'options': [
                            'State that you hated your previous career and got bored',
                            'Articulate a deliberate narrative: connecting your foundational strengths to your new focus and upskilling in {target_role}',
                            'Leave the summary blank and hope recruiters guess your intent',
                            'Claim that your previous job was secretly identical to {target_role}'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Career Narrative & Framing',
                        'explanation': 'A clear, intentional narrative demonstrates purposeful direction and highlights proactive upskilling.'
                    },
                    {
                        'id': 'q_shift_s1_3',
                        'question': f'What is the first step in bridging technical gaps for {target_role}?',
                        'options': [
                            'Identify specific tooling differences between your past domain and modern {target_role} standards',
                            'Buy 50 textbooks and read them all simultaneously',
                            'Assume your existing tools will never need to be updated',
                            'Wait for recruiters to tell you what skills to study'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Gap Diagnostics',
                        'explanation': 'Pinpointing the exact tool and framework deltas allows targeted, high-efficiency reskilling.'
                    }
                ]
            },
            {
                'stage': 2,
                'title': f'Transferable Skills Mapping: {top_skills_str}',
                'objective': f'Identify existing strengths ({top_skills_str}) and isolate the modern tooling needed for {target_role}.',
                'estimated_effort': '2 weeks (10-14 hours)',
                'skills_to_learn': [primary_skill, 'Workflow Adaptation', 'Tooling Audit'],
                'topics': ['Translating terminology', 'Framework adoption', 'Modern development workflows'],
                'practical_activity': {
                    'title': 'Tooling Audit & Translation Lab',
                    'type': 'Technical Adaptation',
                    'description': f'Complete a hands-on exercise implementing a workflow in {primary_skill} that translates a business problem from your prior industry.',
                    'deliverable': 'Working script or model demonstrating domain crossover.'
                },
                'expected_outcome': f'Demonstrated practical bridge between {prev_title or "past field"} and {primary_skill}.',
                'tasks': [
                    ('shift_s2_t1', f'Identify core transferable strengths from {prev_title or "prior role"} relevant to {target_role}', '/path/transition'),
                    ('shift_s2_t2', f'Audit technical and tooling gaps needed for modern {target_role} roles', '/path/transition')
                ],
                'test': [
                    {
                        'id': 'q_shift_s2_1',
                        'question': 'What is the most effective way to validate your transferable skills in a new technical domain?',
                        'options': [
                            'Build a working proof-of-concept using modern tools that addresses a real problem from your previous industry',
                            'Write a lengthy blog post without writing any code or analyzing real data',
                            'Tell recruiters that technical details do not matter for your role',
                            'Take multiple unverified online surveys'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Proof of Concept Validation',
                        'explanation': 'Applying modern tools to familiar domain challenges produces authentic, impressive work samples.'
                    },
                    {
                        'id': 'q_shift_s2_2',
                        'question': 'When adapting to new industry tooling, why is understanding underlying concepts more important than memorizing syntax?',
                        'options': [
                            'Tools and libraries evolve frequently, but foundational principles (data flow, logic, architecture) remain consistent',
                            'Because syntax is never checked during code execution',
                            'Because hiring managers never ask about programming languages',
                            'It allows you to skip using computers entirely'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Fundamental Engineering Principles',
                        'explanation': 'Foundational conceptual mastery enables rapid acclimation to whatever specific stack a hiring company utilizes.'
                    },
                    {
                        'id': 'q_shift_s2_3',
                        'question': 'How should you document your transferable skills on your profile?',
                        'options': [
                            'List 100 buzzwords in alphabetical order',
                            'Categorize skills into Core Domain, Technical Tools, and Project Leadership with clear context',
                            'Only mention soft skills like "hard worker" and "friendly"',
                            'Leave the skills section completely empty'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Profile Skills Categorization',
                        'explanation': 'Structured skill grouping allows hiring managers and ATS filters to quickly verify technical depth and leadership capability.'
                    }
                ]
            },
            {
                'stage': 3,
                'title': f'Bridge Reskilling for {target_role}',
                'objective': f'Complete focused reskilling modules targeting core competencies in {primary_skill} and modern {target_role} frameworks.',
                'estimated_effort': '2-3 weeks (15-20 hours)',
                'skills_to_learn': [primary_skill, secondary_skill, 'Modern Best Practices'],
                'topics': ['Industry standard frameworks', 'API & Database integration', 'Automated workflows'],
                'practical_activity': {
                    'title': 'Applied Bridge Module Project',
                    'type': 'Hands-on Implementation',
                    'description': f'Complete an integrated project demonstrating {primary_skill} and {secondary_skill} applied to real-world datasets or business logic.',
                    'deliverable': 'Executed project artifact with test assertions.'
                },
                'expected_outcome': f'Verified competence in modern {target_role} methodologies.',
                'tasks': [
                    ('shift_s3_t1', f'Complete targeted bridge modules addressing priority skills for {target_role}', '/learning'),
                    ('shift_s3_t2', 'Engage in verified industry case studies and professional community workshops', '/learning')
                ],
                'test': [
                    {
                        'id': 'q_shift_s3_1',
                        'question': f'In modern {target_role} workflows, what is the role of RESTful APIs and microservice architecture?',
                        'options': [
                            'They allow independent services and applications to communicate reliably over standard HTTP protocols',
                            'They are used exclusively to style website buttons',
                            'They prevent databases from storing user records',
                            'They eliminate the need for server infrastructure'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'API Architecture & Integration',
                        'explanation': 'APIs enable decoupled, scalable services to exchange structured data (e.g. JSON) seamlessly.'
                    },
                    {
                        'id': 'q_shift_s3_2',
                        'question': 'Why is database indexing critical when querying large relational or non-relational datasets?',
                        'options': [
                            'It drastically speeds up data retrieval operations by preventing full table scans',
                            'It encrypts the entire hard drive permanently',
                            'It automatically deletes duplicate rows on every query',
                            'It reduces the cost of electricity for the server'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Database Optimization & Querying',
                        'explanation': 'Indexes create efficient lookup trees (B-Trees) that reduce query time complexity from O(N) to O(log N).'
                    },
                    {
                        'id': 'q_shift_s3_3',
                        'question': 'What is Continuous Integration (CI) and why is it standard in modern engineering teams?',
                        'options': [
                            'An automated pipeline that builds, tests, and validates code changes before merging into the main branch',
                            'A manual process where a senior engineer prints code on paper to review',
                            'A system that prevents developers from writing new code on weekends',
                            'A replacement for software licenses'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'CI/CD & DevOps Automation',
                        'explanation': 'CI pipelines catch integration bugs early and ensure that every commit maintains high build quality.'
                    }
                ]
            },
            {
                'stage': 4,
                'title': f'Hybrid Functional Resume: Targeting {target_role}',
                'objective': f'Generate a modernized hybrid-functional resume framing your career pivot with STAR achievements.',
                'estimated_effort': '1 week (5-7 hours)',
                'skills_to_learn': ['Hybrid Resume Formatting', 'Career Pivot Storytelling', 'ATS Optimization'],
                'topics': ['Highlighting bridge competencies', 'Quantifying prior achievements', 'DOCX generation'],
                'practical_activity': {
                    'title': 'Hybrid Resume Generation & Download',
                    'type': 'Resume Hub Action',
                    'description': f'Use Resume Hub to analyze your background against {target_role}, review keyword alignment, and download your updated .docx resume.',
                    'deliverable': 'Downloadable updated .docx transition resume.'
                },
                'expected_outcome': 'Compelling, ATS-compliant transition resume emphasizing transferable strengths.',
                'tasks': [
                    ('shift_s4_t1', f'Upload resume in Resume Hub to analyze alignment with {target_role}', '/resume/hub'),
                    ('shift_s4_t2', f'Structure hybrid functional resume highlighting transferable skills for {target_role}', '/resume/hub'),
                    ('shift_s4_t3', 'Generate and download updated .docx transition resume', '/resume/hub')
                ],
                'test': [
                    {
                        'id': 'q_shift_s4_1',
                        'question': 'What is a Hybrid/Combination resume format, and why is it ideal for career pivoters?',
                        'options': [
                            'It leads with relevant functional skills and verified projects while maintaining a chronological career history',
                            'It hides all company names and dates so nobody knows your age',
                            'It is a 10-page document containing personal essays',
                            'It is designed only for academic tenure applications'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Hybrid Resume Structure',
                        'explanation': 'The hybrid format showcases relevant upskilling competencies first, followed by a credible professional history.'
                    },
                    {
                        'id': 'q_shift_s4_2',
                        'question': 'How should you describe achievements from your previous career field on a transition resume?',
                        'options': [
                            'Omit them entirely and pretend you had no previous jobs',
                            'Focus on transferable impact: leadership, process improvement, metrics delivered, and complex problem solving',
                            'Use hyper-specialized jargon that only people in your old industry understand',
                            'Copy and paste generic job descriptions from search engines'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Transferable Impact Framing',
                        'explanation': 'Emphasizing process improvements, quantifiable results, and stakeholder collaboration proves your universal professional caliber.'
                    },
                    {
                        'id': 'q_shift_s4_3',
                        'question': 'Why is downloading a genuine Microsoft Word (.docx) file important for enterprise job applications?',
                        'options': [
                            'Because enterprise ATS scanners reliably parse DOCX text layers without graphic rendering issues',
                            'Because DOCX files cannot be read by human recruiters',
                            'Because PDF files are illegal in software companies',
                            'Because DOCX files automatically grant you higher test scores'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'ATS Parsing & Document Integrity',
                        'explanation': 'Properly formatted .docx documents ensure reliable parsing across legacy and modern recruiting systems.'
                    }
                ]
            },
            {
                'stage': 5,
                'title': f'Bridge Capstone Project for {target_role}',
                'objective': f'Build a comprehensive, demonstrable capstone project addressing modern {target_role} challenges.',
                'estimated_effort': '2-3 weeks (15-25 hours)',
                'skills_to_learn': ['Full Lifecycle Development', 'System Architecture', 'Portfolio Publishing'],
                'topics': ['Project scope & design', 'Implementation & testing', 'Live deployment & documentation'],
                'practical_activity': {
                    'title': f'{target_role} Capstone Showcase',
                    'type': 'Demonstrable Capstone',
                    'description': f'Develop and deploy a complete capstone project demonstrating end-to-end capabilities in {target_role}. Publish repository and live demo link.',
                    'deliverable': 'Public portfolio repository with live demo.'
                },
                'expected_outcome': 'Indisputable tangible proof of competency in target domain.',
                'tasks': [
                    ('shift_s5_t1', f'Develop a demonstrable capstone project addressing modern {target_role} challenges', '/path/transition'),
                    ('shift_s5_t2', 'Publish project case study or GitHub portfolio demonstrating practical mastery', '/path/transition')
                ],
                'test': [
                    {
                        'id': 'q_shift_s5_1',
                        'question': 'What key element distinguishes an amateur project from a production-ready capstone project?',
                        'options': [
                            'Production readiness includes robust error handling, automated tests, clean architecture, and deployment instructions',
                            'Amateur projects have more lines of unformatted code',
                            'Production readiness means paying for expensive billboard advertisements',
                            'There is no difference between a toy script and production software'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Production Engineering Standards',
                        'explanation': 'Production-quality projects demonstrate attention to edge cases, data validation, automated testing, and maintainability.'
                    },
                    {
                        'id': 'q_shift_s5_2',
                        'question': 'Why is documenting architectural decisions (e.g. why tool A was chosen over tool B) valuable in a portfolio case study?',
                        'options': [
                            'It demonstrates senior engineering judgment, trade-off evaluation, and analytical maturity',
                            'It fills up empty whitespace on the page',
                            'It prevents other engineers from using the same tools',
                            'It is required by the open source police'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Architectural Decision Making',
                        'explanation': 'Engineering leaders hire professionals who can articulate the rationale, trade-offs, and constraints behind technical choices.'
                    },
                    {
                        'id': 'q_shift_s5_3',
                        'question': 'When deploying your capstone project, what security practice is essential?',
                        'options': [
                            'Hardcoding API secret keys and database passwords directly into public GitHub commits',
                            'Using environment variables and .env files to keep secrets and credentials secure',
                            'Disabling all authentication so anyone can delete the production database',
                            'Sharing admin credentials on public forums'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Security & Environment Configuration',
                        'explanation': 'Never commit API keys or credentials to version control; utilize environment variables and secret management.'
                    }
                ]
            },
            {
                'stage': 6,
                'title': f'Strategic Transition Search: {target_role}',
                'objective': f'Target verified bridge roles, returnships, and pivot-friendly employers hiring {target_role}.',
                'estimated_effort': '1-2 weeks (8-10 hours)',
                'skills_to_learn': ['Strategic Filtering', 'Company Research', 'Application Customization'],
                'topics': ['Bridge employer identification', 'Verified recruiter listings', 'Direct outreach strategy'],
                'practical_activity': {
                    'title': 'Target Transition Opportunity Pipeline',
                    'type': 'Opportunity Targeting',
                    'description': f'Identify and bookmark at least 3 transition-friendly job listings for {target_role} on the platform. Tailor cover notes focusing on your pivot narrative.',
                    'deliverable': 'Bookmarked high-alignment opportunities.'
                },
                'expected_outcome': 'Active pipeline of verified transition opportunities.',
                'tasks': [
                    ('shift_s6_t1', f'Explore verified transition returnships and bridge roles in {target_role}', '/explore'),
                    ('shift_s6_t2', 'Review applicable public sector initiatives and skill development programs', '/government/hub')
                ],
                'test': [
                    {
                        'id': 'q_shift_s6_1',
                        'question': 'What type of companies are typically most receptive to career shift candidates?',
                        'options': [
                            'Organizations and returnship programs that explicitly value multidisciplinary problem solvers and domain diversity',
                            'Companies that have a rigid policy of only hiring candidates with 10 identical years in the exact same role',
                            'Unverified anonymous job boards asking for payment',
                            'Companies that do not use computers or technology'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Target Employer Selection',
                        'explanation': 'Forward-thinking companies and structured returnship programs recognize the unique multi-disciplinary value career changers bring.'
                    },
                    {
                        'id': 'q_shift_s6_2',
                        'question': 'What should be the main focus of your application cover note when submitting for a pivot role?',
                        'options': [
                            'Summarize how your prior professional foundations combine with your verified new skills to solve their specific business challenges',
                            'Complain about how hard it is to change careers',
                            'Copy the entire text of the job description verbatim',
                            'Ask the hiring manager for a personal favor'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Application Cover Strategy',
                        'explanation': 'Connecting your prior business perspective to their current operational goals creates immediate alignment.'
                    },
                    {
                        'id': 'q_shift_s6_3',
                        'question': 'How can platform notifications help you maintain momentum in your job search?',
                        'options': [
                            'They provide real-time updates when new verified jobs match your target role or when your application status changes',
                            'They automatically delete your account if you do not check them daily',
                            'They send spam advertisements from third parties',
                            'They change your resume without your consent'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Platform Notification Management',
                        'explanation': 'In-app notifications keep you immediately informed of application reviews, interview updates, and new verified postings.'
                    }
                ]
            },
            {
                'stage': 7,
                'title': 'Transition Narrative & Interview Prep',
                'objective': f'Deliver a compelling interview elevator pitch articulating your pivot from {prev_title or "prior field"} to {target_role}.',
                'estimated_effort': '1-2 weeks (8-12 hours)',
                'skills_to_learn': ['Elevator Pitch Mastery', 'Technical Defense', 'Objection Handling'],
                'topics': ['Framing the pivot positively', 'Handling skepticism', 'Demonstrating capstone architecture'],
                'practical_activity': {
                    'title': 'Pivot Story & Technical Defense Session',
                    'type': 'Mock Interview Defense',
                    'description': f'Practice your response to "Why are you transitioning to {target_role}?" and prepare a 5-minute technical walkthrough of your capstone project.',
                    'deliverable': 'Recorded or written transition defense.'
                },
                'expected_outcome': 'Poised, persuasive interview performance with clear technical depth.',
                'tasks': [
                    ('shift_s7_t1', f'Craft compelling elevator pitch articulating the pivot from {prev_title or "prior field"} to {target_role}', '/learning?category=Interview+Preparation'),
                    ('shift_s7_t2', f'Submit tailored applications for verified {target_role} openings', '/explore')
                ],
                'test': [
                    {
                        'id': 'q_shift_s7_1',
                        'question': 'When asked: "Why are you switching careers into {target_role}?", what is the winning response structure?',
                        'options': [
                            'Share your genuine passion for the domain, highlight intentional reskilling, and demonstrate how past experience enriches your new role',
                            'Say that your previous job did not pay enough money and you heard this field was easy',
                            'State that someone in your family told you to apply',
                            'Ask the interviewer why they switched jobs 5 years ago'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Career Shift Interview Story',
                        'explanation': 'A purposeful explanation focused on intellectual alignment, deliberate skill investment, and additive experience wins candidate trust.'
                    },
                    {
                        'id': 'q_shift_s7_2',
                        'question': 'If an interviewer challenges your lack of years in the new stack, how should you respond?',
                        'options': [
                            'Acknowledge the career timeline confidently, then pivot to demonstrating your capstone architecture and rapid learning speed',
                            'Get defensive and argue that years of experience are completely meaningless',
                            'Pretend you did not hear the question and change the subject',
                            'Give up and walk out of the interview room'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Objection Handling & Poise',
                        'explanation': 'Acknowledging reality with composure while directing focus to tangible work samples demonstrates emotional intelligence.'
                    },
                    {
                        'id': 'q_shift_s7_3',
                        'question': 'What is the most effective way to walk through your technical capstone during a video interview?',
                        'options': [
                            'Screen-share the running application, explain the problem solved, trace the data flow, and discuss trade-offs in architecture',
                            'Read the code line by line starting from line 1 for 45 minutes',
                            'Show only a static logo image without showing how it works',
                            'Claim that you cannot show the code because it is classified'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Technical Demonstration Skill',
                        'explanation': 'A structured demo focusing on problem statement, data flow, architecture choices, and lessons learned showcases engineering maturity.'
                    }
                ]
            }
        ]

    else:
        # EXPERIENCED_GAP (Default career returnee pathway)
        return [
            {
                'stage': 1,
                'title': f'Direction Clarity: Return as {target_role}',
                'objective': f'Re-establish professional trajectory, validate career pause details ({gap_duration}), and align re-entry criteria for {target_role}.',
                'estimated_effort': '1 week (5-7 hours)',
                'skills_to_learn': ['Career Strategy', 'Gap Framing', 'Market Realignment'],
                'topics': ['Auditing career pause narrative', 'Confirming target role scope', f'{work_mode} work model preferences'],
                'practical_activity': {
                    'title': 'Career Re-Entry Roadmap Alignment',
                    'type': 'Diagnostic Audit',
                    'description': f'Review your candidate profile with {top_skills_str} and {gap_duration} break details ({gap_reason}). Define your target role criteria and salary/work mode preferences.',
                    'deliverable': 'Confirmed profile and career direction in ReTurn workspace.'
                },
                'expected_outcome': f'Strategic alignment and confidence in returning to the workforce as {target_role}.',
                'tasks': [
                    ('exp_s1_t1', f'Review candidate profile with {top_skills_str} and {gap_duration} break details', '/profile/complete'),
                    ('exp_s1_t2', f'Confirm target role specifications and {work_mode} preferences for {target_role}', '/profile/complete')
                ],
                'test': [
                    {
                        'id': 'q_exp_s1_1',
                        'question': f'What is the most effective way to present your {gap_duration} career pause ({gap_reason}) to potential employers?',
                        'options': [
                            'Attempt to conceal the gap by altering employment dates or inventing fake companies',
                            'Transparently communicate the reason with confidence, emphasizing professional maturity and proactive upskilling',
                            'Apologize repeatedly for having taken time off for family care or medical recovery',
                            'Leave large unexplained gaps on your resume with no context'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Career Gap Framing Strategy',
                        'explanation': 'Progressive employers respect transparent career pauses. Framing your pause constructively alongside upskilling builds strong credibility.'
                    },
                    {
                        'id': 'q_exp_s1_2',
                        'question': f'When restarting your career in {target_role}, why is defining clear work-mode preferences ({work_mode}) essential?',
                        'options': [
                            'It ensures you only apply to opportunities that realistically fit your lifestyle and scheduling needs',
                            'It guarantees that every company will immediately offer you a promotion',
                            'It is required so ATS software can filter out all remote candidates',
                            'It has no impact on job search success'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Work Mode & Life Integration',
                        'explanation': 'Clarity on remote, hybrid, or onsite preferences prevents burnout and ensures sustainable career longevity upon return.'
                    },
                    {
                        'id': 'q_exp_s1_3',
                        'question': 'How does our platform utilize your actual profile data across AI workflows?',
                        'options': [
                            'It ignores your data and returns generic templates to every user',
                            'It passes your actual skills, experience, and career gap directly into analysis models to generate custom recommendations',
                            'It sells your data to third-party telemarketers',
                            'It replaces your real name with a random celebrity name'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Platform Personalization Standard',
                        'explanation': 'ReTurn operates on strict data fidelity: every recommendation, analysis score, and resume rewrite stems directly from your authentic profile.'
                    }
                ]
            },
            {
                'stage': 2,
                'title': f'Skill Audit & Re-Entry Diagnostic for {target_role}',
                'objective': f'Audit established strengths ({top_skills_str}) against recent technological advancements that emerged during your {gap_duration} pause.',
                'estimated_effort': '1-2 weeks (8-12 hours)',
                'skills_to_learn': ['Delta Skill Analysis', 'Tooling Modernization', 'Industry Standards'],
                'topics': ['Recent library/framework updates', 'Modern design patterns', 'Cloud & collaboration tooling'],
                'practical_activity': {
                    'title': 'Modern Tooling Diagnostic Lab',
                    'type': 'Technical Diagnostic',
                    'description': f'Run an in-depth Career Gap Analysis to isolate high-priority skill deltas in {primary_skill} and related technologies.',
                    'deliverable': 'Personalized Skill Gap Readiness Report.'
                },
                'expected_outcome': f'Precise inventory of skills needing refresher vs modern tools to acquire for {target_role}.',
                'tasks': [
                    ('exp_s2_t1', f'Audit existing skills ({top_skills_str}) against modern {target_role} job requirements', '/career-analysis'),
                    ('exp_s2_t2', f'Identify tooling and framework updates emerged during your {gap_duration} pause', '/career-analysis')
                ],
                'test': [
                    {
                        'id': 'q_exp_s2_1',
                        'question': f'Why is conducting a structured skill audit essential before starting job applications for {target_role}?',
                        'options': [
                            'It identifies the exact modern tools and methodologies that evolved during your pause, allowing focused reskilling',
                            'It guarantees that you do not need to update your resume',
                            'It proves that older software versions are always better than modern frameworks',
                            'It is required by the government before taking an interview'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Skill Gap Diagnostics',
                        'explanation': 'A systematic diagnostic saves time by preventing you from relearning what you already know while zeroing in on high-demand modern deltas.'
                    },
                    {
                        'id': 'q_exp_s2_2',
                        'question': 'How should an experienced professional view their past technical foundation after a career break?',
                        'options': [
                            'As completely worthless because technology changed',
                            'As a solid foundational bedrock that makes learning modern framework iterations significantly faster and easier',
                            'As a secret that must never be mentioned to hiring managers',
                            'As an excuse to refuse to learn any modern tools'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Foundational Experience Leverage',
                        'explanation': 'Core computer science, system thinking, and problem-solving principles remain constant across technology cycles.'
                    },
                    {
                        'id': 'q_exp_s2_3',
                        'question': 'In modern distributed development environments, what collaborative tools are essential to refresh?',
                        'options': [
                            'Git workflow (branching, PRs), Slack/Teams async communication, Jira/Agile boards, and CI/CD pipelines',
                            'Floppy disks and paper memos',
                            'Only desktop text editors without internet connectivity',
                            'Standalone single-user spreadsheets with no sharing capabilities'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Modern Collaborative Tooling',
                        'explanation': 'Modern teams operate in distributed, agile environments where version control and asynchronous collaboration are standard.'
                    }
                ]
            },
            {
                'stage': 3,
                'title': f'Targeted Reskilling for {target_role}',
                'objective': f'Complete hands-on refresher modules on modern {primary_skill} and contemporary {target_role} industry practices.',
                'estimated_effort': '2-3 weeks (15-20 hours)',
                'skills_to_learn': [primary_skill, secondary_skill, 'Modern Best Practices'],
                'topics': ['Refresher exercises', 'Asynchronous workflows', 'Clean code & unit testing'],
                'practical_activity': {
                    'title': f'{primary_skill} Refresher Implementation',
                    'type': 'Hands-on Technical Task',
                    'description': f'Complete a practical exercise writing clean, testable code in {primary_skill} applying modern paradigms and automated test assertions.',
                    'deliverable': 'Working codebase or validated test suite.'
                },
                'expected_outcome': f'Up-to-date practical fluency in {primary_skill} matching current industry standards.',
                'tasks': [
                    ('exp_s3_t1', f'Complete recommended refresher course on modern {target_role} tools and methodologies', '/learning'),
                    ('exp_s3_t2', 'Review industry standard communication and team collaboration practices', '/learning?category=Soft+Skills')
                ],
                'test': [
                    {
                        'id': 'q_exp_s3_1',
                        'question': 'What is the primary advantage of asynchronous communication in modern remote/hybrid workplaces?',
                        'options': [
                            'It allows team members to review detailed documentation and respond thoughtfully without requiring constant live meetings',
                            'It ensures that no work gets done for several weeks at a time',
                            'It eliminates the need for written messages',
                            'It forces everyone to work 24 hours a day'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Asynchronous Workplace Collaboration',
                        'explanation': 'Asynchronous workflows prioritize clear written documentation, structured task boards, and uninterrupted focus time.'
                    },
                    {
                        'id': 'q_exp_s3_2',
                        'question': 'When refactoring legacy code into modern design patterns, what is the best practice?',
                        'options': [
                            'Rewrite everything in a weekend without running any tests',
                            'Establish comprehensive regression tests first, then refactor incrementally in small, validated PRs',
                            'Disable logging and error handling to make the code look cleaner',
                            'Never touch any code that was written more than two years ago'
                        ],
                        'correct_index': 1,
                        'topic_tag': 'Safe Code Refactoring',
                        'explanation': 'Test-driven refactoring ensures that existing business logic remains intact while modernizing internal architecture.'
                    },
                    {
                        'id': 'q_exp_s3_3',
                        'question': 'Why is understanding API rate limiting and pagination important for backend/full-stack developers?',
                        'options': [
                            'It prevents client requests from overwhelming server memory and database performance',
                            'It makes APIs run out of memory intentionally',
                            'It is used only to charge users credit card fees',
                            'It replaces the need for data security'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Scalable API Integration',
                        'explanation': 'Pagination and rate limiting protect backend infrastructure from denial-of-service spikes and ensure reliable latency.'
                    }
                ]
            },
            {
                'stage': 4,
                'title': f'Resume Modernization & Gap Framing ({gap_duration})',
                'objective': f'Modernize your resume format, integrate STAR bullet points, frame your {gap_duration} pause constructively, and download your .docx re-entry resume.',
                'estimated_effort': '1 week (5-7 hours)',
                'skills_to_learn': ['Resume Modernization', 'STAR Impact Formulation', 'ATS Keyword Alignment'],
                'topics': ['Career break section formatting', 'Action verb transformation', 'Keyword transparency'],
                'practical_activity': {
                    'title': 'Resume Hub Re-Entry Transformation',
                    'type': 'Resume Hub Optimization',
                    'description': f'Upload your resume in Resume Hub, review role keyword match for {target_role}, apply STAR rewrites, and download your updated .docx resume.',
                    'deliverable': 'Downloadable updated .docx re-entry resume.'
                },
                'expected_outcome': 'A polished, ATS-optimized re-entry resume with clear career break presentation.',
                'tasks': [
                    ('exp_s4_t1', f'Upload existing resume for structural analysis against {target_role}', '/resume/hub'),
                    ('exp_s4_t2', f'Frame {gap_duration} ({gap_reason}) constructively with STAR bullets and upskilling highlights', '/resume/hub'),
                    ('exp_s4_t3', 'Generate and download modernized .docx re-entry resume', '/resume/hub')
                ],
                'test': [
                    {
                        'id': 'q_exp_s4_1',
                        'question': 'How should a career break be represented in a modern chronological resume?',
                        'options': [
                            'As a distinct entry labeled "Career Break" or "Career Pause & Upskilling", highlighting reason and continuous learning milestones',
                            'Completely hidden with fake employment dates',
                            'As a 3-page apology letter at the end of the resume',
                            'By deleting all previous work experience prior to the break'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Career Break Architecture',
                        'explanation': 'An explicit, professional Career Break entry clarifies your timeline immediately, preventing recruiters from wondering if employment gaps are clerical errors.'
                    },
                    {
                        'id': 'q_exp_s4_2',
                        'question': 'Why does our Resume Hub show a detailed Keyword Transparency breakdown?',
                        'options': [
                            'To clearly show which target keywords were found, emphasized, or missing, and explain why each recommended keyword matters',
                            'To force users to add fake skills they do not have',
                            'To hide the real ATS matching logic from the candidate',
                            'To change the candidate’s target role without permission'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Keyword Transparency & Ethical ATS',
                        'explanation': 'Transparency empowers candidates to understand exact market expectations while strictly preventing the fabrication of unearned credentials.'
                    },
                    {
                        'id': 'q_exp_s4_3',
                        'question': 'What is the role of action verbs (e.g., "Spearheaded", "Architected", "Streamlined") in resume bullet points?',
                        'options': [
                            'They clearly convey your proactive ownership and direct contributions to business outcomes',
                            'They make sentences as confusing as possible for human readers',
                            'They are required only for executive CEO resumes',
                            'They replace the need to list technical skills'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Action Verbs & Executive Language',
                        'explanation': 'Active verbs demonstrate direct ownership, leadership, and operational agency rather than passive presence.'
                    }
                ]
            },
            {
                'stage': 5,
                'title': f'Practical Work Sample & Portfolio: {target_role}',
                'objective': f'Build or refresh a portfolio work sample / case study demonstrating {target_role} expertise.',
                'estimated_effort': '2 weeks (12-18 hours)',
                'skills_to_learn': ['Work Sample Construction', 'Technical Demonstration', 'Interview Readiness'],
                'topics': ['Case study structure', 'Quantifiable outcomes', 'Live walkthrough preparation'],
                'practical_activity': {
                    'title': f'{target_role} Re-Entry Portfolio Case Study',
                    'type': 'Portfolio Refresher',
                    'description': f'Develop a concrete work sample or case study demonstrating contemporary {target_role} problem solving using {primary_skill}.',
                    'deliverable': 'Published work sample / case study artifact.'
                },
                'expected_outcome': 'Fresh proof of execution demonstrating immediate readiness to contribute to team deliverables.',
                'tasks': [
                    ('exp_s5_t1', f'Build or refresh a portfolio work sample / case study demonstrating {target_role} expertise', '/learning'),
                    ('exp_s5_t2', 'Conduct a mock technical / behavioral interview practice session', '/learning?category=Interview+Preparation')
                ],
                'test': [
                    {
                        'id': 'q_exp_s5_1',
                        'question': 'Why is a recent work sample or portfolio artifact so powerful for career returnees?',
                        'options': [
                            'It provides immediate, incontrovertible proof of current technical fluency and active skills',
                            'It replaces the need to attend an interview',
                            'It allows you to skip background verification',
                            'It guarantees an immediate executive salary'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Work Sample Value & Proof',
                        'explanation': 'A fresh artifact eliminates recruiter doubt regarding skill staleness by proving hands-on modern mastery.'
                    },
                    {
                        'id': 'q_exp_s5_2',
                        'question': 'What should you highlight when explaining a technical case study during an interview?',
                        'options': [
                            'The business problem, architecture decisions, trade-offs evaluated, and measurable outcomes achieved',
                            'Only the color scheme used for the user interface',
                            'How easy the project was and that it required zero thought',
                            'That you copied the code from an online forum without understanding it'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Case Study Articulation',
                        'explanation': 'Articulating business rationale, architectural trade-offs, and outcomes showcases mature engineering capability.'
                    },
                    {
                        'id': 'q_exp_s5_3',
                        'question': 'How should you prepare for technical whiteboard or live coding assessments?',
                        'options': [
                            'Practice talking aloud while breaking down problems, clarifying constraints, and writing modular solutions',
                            'Remain completely silent and write random equations until time expires',
                            'Memorize code solutions without understanding the logic',
                            'Refuse to participate in live assessments'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Live Coding & Problem Solving',
                        'explanation': 'Interviewers evaluate your thought process, communication clarity, and adaptability when working through problems.'
                    }
                ]
            },
            {
                'stage': 6,
                'title': f'Target Opportunity Discovery: {target_role}',
                'objective': f'Explore verified recruiter returnships, flexible openings, and public initiatives tailored for {target_role}.',
                'estimated_effort': '1-2 weeks (8-10 hours)',
                'skills_to_learn': ['Returnship Targeting', 'Opportunity Curation', 'Application Submission'],
                'topics': ['Return-to-work program identification', 'Verified recruiter filters', 'Direct bookmarking'],
                'practical_activity': {
                    'title': 'Target Returnship & Job Pipeline',
                    'type': 'Opportunity Targeting',
                    'description': f'Filter and bookmark at least 3 verified recruiter returnship or flexible job opportunities matching {target_role}.',
                    'deliverable': 'Curated pipeline of bookmarked returnee opportunities.'
                },
                'expected_outcome': 'Active pipeline of returnee-friendly positions ready for direct application.',
                'tasks': [
                    ('exp_s6_t1', f'Explore verified recruiter returnships and openings for {target_role}', '/explore?source=VERIFIED_RECRUITER'),
                    ('exp_s6_t2', 'Check applicable government opportunities and returnee-friendly initiatives', '/government/hub')
                ],
                'test': [
                    {
                        'id': 'q_exp_s6_1',
                        'question': 'What is a structured corporate "Returnship" program?',
                        'options': [
                            'A paid, supportive bridge program specifically designed to reintegrate experienced professionals after a career break',
                            'An unpaid student internship with no path to full-time employment',
                            'A mandatory government military assignment',
                            'A penalty program for taking a career pause'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Corporate Returnship Programs',
                        'explanation': 'Returnships provide mentorship, upskilling, and a dedicated pathway back to full-time career roles for experienced returnees.'
                    },
                    {
                        'id': 'q_exp_s6_2',
                        'question': 'Why should candidates check both verified recruiter jobs and government/public sector hubs on ReTurn?',
                        'options': [
                            'To maximize access to verified corporate openings as well as public sector schemes with age/gap relaxations',
                            'Because private jobs are always fake and government jobs are always closed',
                            'Because the platform requires candidates to apply to 100 jobs daily',
                            'There is no benefit to checking both'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Multichannel Opportunity Strategy',
                        'explanation': 'Combining verified private sector listings with public sector re-entry schemes broadens high-quality opportunities.'
                    },
                    {
                        'id': 'q_exp_s6_3',
                        'question': 'When submitting an application through ReTurn, what happens on the recruiter side?',
                        'options': [
                            'The verified recruiter receives your application and can review your profile, resume, and application notes in their dashboard',
                            'Your application is automatically rejected by an AI bot',
                            'The application is posted on public social media',
                            'The recruiter is not notified'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Recruiter Application Workflow',
                        'explanation': 'Verified recruiters have dedicated portals where they review candidate qualifications, download resumes, and update application statuses.'
                    }
                ]
            },
            {
                'stage': 7,
                'title': 'Tailored Applications & Interview Readiness',
                'objective': f'Execute tailored job applications for {target_role} and deliver a confident 2-minute pitch explaining your {gap_duration} break and re-entry readiness.',
                'estimated_effort': '1-2 weeks (8-12 hours)',
                'skills_to_learn': ['Re-Entry Elevator Pitch', 'Executive Presence', 'Offer Evaluation'],
                'topics': ['Confident gap articulation', 'Behavioral interview mastery', 'Negotiation basics'],
                'practical_activity': {
                    'title': 'Re-Entry Pitch & Application Sprint',
                    'type': 'Career Launch',
                    'description': f'Submit tailored applications for your bookmarked {target_role} positions with your modernized .docx resume and practice your 2-minute re-entry introduction.',
                    'deliverable': 'Active submitted applications and recorded pitch.'
                },
                'expected_outcome': 'Successful completion of career re-entry launch with active recruiter engagement.',
                'tasks': [
                    ('exp_s7_t1', f'Submit tailored applications to verified {target_role} vacancies', '/explore'),
                    ('exp_s7_t2', f'Prepare confident 2-minute elevator pitch explaining {gap_duration} pause and readiness for {target_role}', '/learning?category=Interview+Preparation')
                ],
                'test': [
                    {
                        'id': 'q_exp_s7_1',
                        'question': 'How should you deliver your 2-minute re-entry elevator pitch in an interview?',
                        'options': [
                            'Lead with your foundational experience, state your career pause transparently, highlight your proactive upskilling, and express excitement for the role',
                            'Spend the entire 2 minutes listing every software version you used in 2005',
                            'Avoid mentioning your career break and hope they do not look at your resume dates',
                            'Read your entire resume verbatim in a monotone voice'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Re-Entry Elevator Pitch Mastery',
                        'explanation': 'A concise narrative connecting past success, purposeful pause, recent upskilling, and current value proposition establishes instant credibility.'
                    },
                    {
                        'id': 'q_exp_s7_2',
                        'question': 'What is the best mindset when receiving an invitation for an interview after a career break?',
                        'options': [
                            'Approach the conversation as an equal peer dialogue focused on mutual fit and collaborative problem solving',
                            'Assume that the company feels sorry for you and wants to test your weaknesses',
                            'Demand an immediate offer before answering any technical questions',
                            'Cancel the interview out of fear of being asked about the break'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Executive Presence & Confidence',
                        'explanation': 'You are an experienced professional offering valuable maturity, dedication, and problem-solving capability to their team.'
                    },
                    {
                        'id': 'q_exp_s7_3',
                        'question': 'How should you evaluate a job offer when returning to the workforce?',
                        'options': [
                            'Evaluate total compensation, role scope, mentorship, growth opportunities, and alignment with your work-mode preferences',
                            'Accept the very first offer regardless of terms or company culture without reading the contract',
                            'Reject all offers that do not match the highest salary in the country',
                            'Assume you cannot negotiate any terms because you took a break'
                        ],
                        'correct_index': 0,
                        'topic_tag': 'Offer Evaluation & Career Re-Entry',
                        'explanation': 'A comprehensive assessment of role scope, supportive culture, compensation, and work-life sustainability ensures long-term returnee success.'
                    }
                ]
            }
        ]

def get_or_create_user_roadmap(user_id: int, pathway: str = None, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Retrieves existing roadmap or dynamically creates/updates tasks and stages
    tailored to the user's current profile, skills, target role, and evaluation progress.
    Enforces test-based stage unlocking progression logic.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    profile_row = cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    profile_dict = dict(profile_row) if profile_row else {}

    if not pathway:
        cs = cursor.execute(
            "SELECT pathway FROM career_selections WHERE user_id = ?", (user_id,)
        ).fetchone()
        pathway = cs['pathway'] if cs else 'EXPERIENCED_GAP'

    roadmap = cursor.execute(
        "SELECT * FROM user_roadmaps WHERE user_id = ?", (user_id,)
    ).fetchone()

    dynamic_stages_data = generate_dynamic_stages(profile_dict, pathway)

    if not roadmap:
        cursor.execute(
            "INSERT INTO user_roadmaps (user_id, pathway, current_stage, total_stages, completion_percentage) VALUES (?, ?, 1, 7, 0)",
            (user_id, pathway)
        )
        roadmap_id = cursor.lastrowid
        conn.commit()

        # Seed dynamic tasks
        for stage_info in dynamic_stages_data:
            for task_key, desc, url in stage_info['tasks']:
                cursor.execute('''
                    INSERT INTO roadmap_tasks (roadmap_id, stage_number, stage_title, task_key, task_description, resource_url, is_completed)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (roadmap_id, stage_info['stage'], stage_info['title'], task_key, desc, url))
        conn.commit()
        roadmap = cursor.execute("SELECT * FROM user_roadmaps WHERE id = ?", (roadmap_id,)).fetchone()
    elif force_refresh or (roadmap['pathway'] != pathway):
        roadmap_id = roadmap['id']
        cursor.execute("UPDATE user_roadmaps SET pathway = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (pathway, roadmap_id))
        
        old_completed_keys = set()
        old_tasks = cursor.execute("SELECT task_key FROM roadmap_tasks WHERE roadmap_id = ? AND is_completed = 1", (roadmap_id,)).fetchall()
        for ot in old_tasks:
            old_completed_keys.add(ot['task_key'])

        cursor.execute("DELETE FROM roadmap_tasks WHERE roadmap_id = ?", (roadmap_id,))

        for stage_info in dynamic_stages_data:
            for task_key, desc, url in stage_info['tasks']:
                is_comp = 1 if task_key in old_completed_keys else 0
                cursor.execute('''
                    INSERT INTO roadmap_tasks (roadmap_id, stage_number, stage_title, task_key, task_description, resource_url, is_completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (roadmap_id, stage_info['stage'], stage_info['title'], task_key, desc, url, is_comp))
        conn.commit()
        roadmap = cursor.execute("SELECT * FROM user_roadmaps WHERE id = ?", (roadmap_id,)).fetchone()

    # Fetch user evaluation history from roadmap_stage_evaluations
    evaluations_raw = cursor.execute('''
        SELECT * FROM roadmap_stage_evaluations
        WHERE user_id = ?
        ORDER BY stage_number ASC, attempt_number DESC
    ''', (user_id,)).fetchall()

    # Organize evaluations by stage
    eval_by_stage: Dict[int, List[Dict[str, Any]]] = {}
    passed_stages = set()
    for ev in evaluations_raw:
        s_num = ev['stage_number']
        ev_dict = dict(ev)
        if s_num not in eval_by_stage:
            eval_by_stage[s_num] = []
        eval_by_stage[s_num].append(ev_dict)
        if ev_dict['passed'] == 1:
            passed_stages.add(s_num)

    # Fetch all tasks grouped by stage
    tasks = cursor.execute(
        "SELECT * FROM roadmap_tasks WHERE roadmap_id = ? ORDER BY stage_number ASC, id ASC",
        (roadmap['id'],)
    ).fetchall()

    task_dicts = [dict(t) for t in tasks]
    stages_dict = {}
    for t in task_dicts:
        s_num = t['stage_number']
        if s_num not in stages_dict:
            # Match with dynamic stage metadata
            meta = next((s for s in dynamic_stages_data if s['stage'] == s_num), {})
            stages_dict[s_num] = {
                'stage_number': s_num,
                'stage_title': t['stage_title'],
                'objective': meta.get('objective', ''),
                'estimated_effort': meta.get('estimated_effort', ''),
                'skills_to_learn': meta.get('skills_to_learn', []),
                'topics': meta.get('topics', []),
                'practical_activity': meta.get('practical_activity', {}),
                'expected_outcome': meta.get('expected_outcome', ''),
                'tasks': [],
                'completed_count': 0,
                'is_completed': False,
                'status': 'LOCKED',
                'is_unlocked': False,
                'has_passed': False,
                'latest_score': None,
                'attempts_count': 0,
                'weak_topics': [],
                'test': meta.get('test', []),
                'test_questions_count': len(meta.get('test', []))
            }
        stages_dict[s_num]['tasks'].append(t)
        if t['is_completed']:
            stages_dict[s_num]['completed_count'] += 1

    # Progression and locking logic
    # Stage 1 is ALWAYS unlocked.
    # Stage N (N > 1) is unlocked ONLY if Stage N-1 has been passed (evaluation passed = 1).
    for s_num in range(1, 8):
        if s_num not in stages_dict:
            continue
        stage_obj = stages_dict[s_num]
        
        # Determine unlock status
        if s_num == 1:
            is_unlocked = True
        else:
            is_unlocked = (s_num - 1) in passed_stages

        stage_obj['is_unlocked'] = is_unlocked

        # Check evaluations for this stage
        st_evals = eval_by_stage.get(s_num, [])
        stage_obj['attempts_count'] = len(st_evals)
        
        if st_evals:
            latest_eval = st_evals[0]  # ordered by attempt_number DESC
            stage_obj['latest_score'] = latest_eval['score']
            if latest_eval['weak_topics']:
                try:
                    stage_obj['weak_topics'] = json.loads(latest_eval['weak_topics'])
                except Exception:
                    stage_obj['weak_topics'] = []

        if s_num in passed_stages:
            stage_obj['has_passed'] = True
            stage_obj['is_completed'] = True
            stage_obj['status'] = 'COMPLETED'
        elif is_unlocked:
            if stage_obj['attempts_count'] > 0:
                stage_obj['status'] = 'REVISION_NEEDED'
            else:
                stage_obj['status'] = 'IN_PROGRESS'
        else:
            stage_obj['status'] = 'LOCKED'

    stages = list(stages_dict.values())

    # Overall completion percentage based on passed stages and tasks
    total_stages = 7
    completed_stages_count = len(passed_stages)
    pct = int((completed_stages_count / total_stages) * 100) if total_stages > 0 else 0

    # Determine next active task / stage
    next_active_stage = next((s for s in stages if s['is_unlocked'] and not s['has_passed']), None)
    next_task = next((t for t in tasks if t['is_completed'] == 0), None)

    # Update DB current_stage & completion_percentage
    curr_st_num = next_active_stage['stage_number'] if next_active_stage else 7
    if pct != roadmap['completion_percentage'] or curr_st_num != roadmap['current_stage']:
        cursor.execute('''
            UPDATE user_roadmaps 
            SET completion_percentage = ?, current_stage = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (pct, curr_st_num, roadmap['id']))
        conn.commit()

    conn.close()

    return {
        'roadmap': dict(roadmap) if roadmap else {},
        'tasks': task_dicts,
        'stages': stages,
        'total_tasks': len(tasks),
        'completed_tasks': sum(1 for t in tasks if t['is_completed'] == 1),
        'completed_stages_count': completed_stages_count,
        'percentage': pct,
        'next_task': dict(next_task) if next_task else None,
        'next_active_stage': next_active_stage,
        'passing_score': Config.ROADMAP_PASSING_SCORE
    }

def get_stage_test_data(user_id: int, stage_number: int) -> Dict[str, Any]:
    """
    Retrieves the dynamic test questions for a specific stage tailored to the candidate,
    stripping correct answers so the frontend user cannot inspect them beforehand.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    profile_row = cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    profile_dict = dict(profile_row) if profile_row else {}

    cs = cursor.execute("SELECT pathway FROM career_selections WHERE user_id = ?", (user_id,)).fetchone()
    pathway = cs['pathway'] if cs else 'EXPERIENCED_GAP'
    conn.close()

    dynamic_stages = generate_dynamic_stages(profile_dict, pathway)
    stage_data = next((s for s in dynamic_stages if s['stage'] == stage_number), None)

    if not stage_data or 'test' not in stage_data:
        return {'success': False, 'error': f'Test data not found for stage {stage_number}'}

    # Prepare client-safe question list (omit correct_index & explanation)
    client_questions = []
    for q in stage_data['test']:
        client_questions.append({
            'id': q['id'],
            'question': q['question'],
            'options': q['options'],
            'topic_tag': q.get('topic_tag', 'General Stage Topic')
        })

    return {
        'success': True,
        'stage_number': stage_number,
        'stage_title': stage_data['title'],
        'passing_score': Config.ROADMAP_PASSING_SCORE,
        'total_questions': len(client_questions),
        'questions': client_questions
    }

def evaluate_stage_test(user_id: int, stage_number: int, submitted_answers: Dict[str, int]) -> Dict[str, Any]:
    """
    Evaluates submitted answers against the stage test, calculates the score,
    identifies weak topics, determines pass/fail status (>= 70%),
    persists progress in roadmap_stage_evaluations, and unlocks the next stage upon passing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    profile_row = cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    profile_dict = dict(profile_row) if profile_row else {}

    cs = cursor.execute("SELECT pathway FROM career_selections WHERE user_id = ?", (user_id,)).fetchone()
    pathway = cs['pathway'] if cs else 'EXPERIENCED_GAP'

    roadmap = cursor.execute("SELECT * FROM user_roadmaps WHERE user_id = ?", (user_id,)).fetchone()
    if not roadmap:
        conn.close()
        rm_data = get_or_create_user_roadmap(user_id, pathway)
        conn = get_db_connection()
        cursor = conn.cursor()
        roadmap_id = rm_data['roadmap']['id']
    else:
        roadmap_id = roadmap['id']

    dynamic_stages = generate_dynamic_stages(profile_dict, pathway)
    stage_data = next((s for s in dynamic_stages if s['stage'] == stage_number), None)

    if not stage_data or 'test' not in stage_data:
        conn.close()
        return {'success': False, 'error': f'Invalid stage test for stage {stage_number}.'}

    test_questions = stage_data['test']
    total_questions = len(test_questions)
    if total_questions == 0:
        conn.close()
        return {'success': False, 'error': 'No questions available for this stage.'}

    correct_count = 0
    weak_topics = []
    explanation_summary = []

    for idx, q in enumerate(test_questions):
        q_id = q['id']
        correct_idx = q['correct_index']
        user_choice = submitted_answers.get(q_id)
        if user_choice is None:
            user_choice = submitted_answers.get(str(q_id))
        if user_choice is None:
            user_choice = submitted_answers.get(str(idx))
        if user_choice is None:
            user_choice = submitted_answers.get(idx)
        
        # Verify user choice
        is_correct = False
        try:
            if user_choice is not None and int(user_choice) == int(correct_idx):
                is_correct = True
        except (ValueError, TypeError):
            is_correct = False

        if is_correct:
            correct_count += 1
        else:
            topic = q.get('topic_tag', 'General Concept')
            if topic not in weak_topics:
                weak_topics.append(topic)

        user_choice_idx = None
        try:
            if user_choice is not None:
                user_choice_idx = int(user_choice)
        except (ValueError, TypeError):
            user_choice_idx = None

        user_choice_text = q['options'][user_choice_idx] if (user_choice_idx is not None and 0 <= user_choice_idx < len(q['options'])) else "No answer provided"
        correct_choice_text = q['options'][correct_idx]

        explanation_summary.append({
            'question_id': q_id,
            'question': q['question'],
            'user_choice': user_choice_text,
            'correct_choice': correct_choice_text,
            'is_correct': is_correct,
            'explanation': q.get('explanation', ''),
            'topic_tag': q.get('topic_tag', '')
        })

    # Calculate actual score
    score = round((correct_count / total_questions) * 100, 1)
    passing_score = Config.ROADMAP_PASSING_SCORE
    passed = 1 if score >= passing_score else 0

    # Get attempt number
    prev_attempt = cursor.execute('''
        SELECT MAX(attempt_number) as max_att 
        FROM roadmap_stage_evaluations 
        WHERE user_id = ? AND stage_number = ?
    ''', (user_id, stage_number)).fetchone()
    attempt_num = (prev_attempt['max_att'] or 0) + 1

    # Persist evaluation record
    cursor.execute('''
        INSERT INTO roadmap_stage_evaluations (
            roadmap_id, user_id, stage_number, score, passing_score, passed,
            total_questions, correct_answers, weak_topics, explanation_summary,
            attempt_number, submitted_answers
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        roadmap_id,
        user_id,
        stage_number,
        score,
        passing_score,
        passed,
        total_questions,
        correct_count,
        json.dumps(weak_topics),
        json.dumps(explanation_summary),
        attempt_num,
        json.dumps(submitted_answers)
    ))

    # If passed, mark tasks for this stage as completed and advance current_stage
    if passed == 1:
        cursor.execute('''
            UPDATE roadmap_tasks 
            SET is_completed = 1, completed_at = CURRENT_TIMESTAMP
            WHERE roadmap_id = ? AND stage_number = ?
        ''', (roadmap_id, stage_number))

        # Advance current stage if applicable
        next_stage_num = min(stage_number + 1, 7)
        cursor.execute('''
            UPDATE user_roadmaps
            SET current_stage = MAX(current_stage, ?), updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (next_stage_num, roadmap_id))

    conn.commit()
    conn.close()

    # Refresh full roadmap progress
    updated_roadmap = get_or_create_user_roadmap(user_id)

    recommendations = [
        f"Review core fundamentals on {topic} before retaking the stage evaluation." for topic in weak_topics
    ] if weak_topics else ["Outstanding performance! You have demonstrated role competency and unlocked the next stage."]

    return {
        'success': True,
        'stage_number': stage_number,
        'score': score,
        'passing_score': passing_score,
        'passed': bool(passed),
        'correct_answers': correct_count,
        'total_questions': total_questions,
        'attempt_number': attempt_num,
        'weak_topics': weak_topics,
        'recommendations': recommendations,
        'explanation_summary': explanation_summary,
        'next_stage': min(stage_number + 1, 7) if passed else stage_number,
        'next_stage_unlocked': bool(passed and stage_number < 7),
        'overall_progress_percentage': updated_roadmap['percentage']
    }

def regenerate_user_roadmap(user_id: int) -> Dict[str, Any]:
    """Explicitly regenerates roadmap tasks using latest user profile and pathway."""
    return get_or_create_user_roadmap(user_id, force_refresh=True)

def toggle_task_status(user_id: int, task_id: int) -> Dict[str, Any]:
    """Toggles task completed state and recalculates roadmap progress."""
    conn = get_db_connection()
    cursor = conn.cursor()

    task = cursor.execute('''
        SELECT t.*, r.user_id 
        FROM roadmap_tasks t
        JOIN user_roadmaps r ON t.roadmap_id = r.id
        WHERE t.id = ? AND r.user_id = ?
    ''', (task_id, user_id)).fetchone()

    if not task:
        conn.close()
        return {'success': False, 'error': 'Task not found or access denied'}

    new_status = 0 if task['is_completed'] == 1 else 1
    cursor.execute('''
        UPDATE roadmap_tasks 
        SET is_completed = ?, completed_at = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END
        WHERE id = ?
    ''', (new_status, new_status, task_id))
    conn.commit()

    # Recalculate
    tasks = cursor.execute("SELECT is_completed FROM roadmap_tasks WHERE roadmap_id = ?", (task['roadmap_id'],)).fetchall()
    total = len(tasks)
    completed = sum(1 for t in tasks if t['is_completed'] == 1)
    pct = int((completed / total * 100)) if total > 0 else 0

    cursor.execute("UPDATE user_roadmaps SET completion_percentage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (pct, task['roadmap_id']))
    conn.commit()
    conn.close()

    return {
        'success': True,
        'task_id': task_id,
        'is_completed': bool(new_status),
        'percentage': pct,
        'completed_tasks': completed,
        'total_tasks': total
    }

