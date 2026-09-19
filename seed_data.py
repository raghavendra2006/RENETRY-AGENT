import sqlite3
from werkzeug.security import generate_password_hash
from database import get_db_connection, init_db

def seed_platform_data():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Seed Admin User
    admin_email = "admin@return.internal"
    cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, full_name, is_active)
            VALUES (?, ?, 'ADMIN', ?, 1)
        ''', (admin_email, generate_password_hash("AdminPassword123!"), "Platform Administrator"))
        admin_id = cursor.lastrowid
        print("Admin account created.")
    else:
        admin_id = admin_row['id']

    # 2. Seed Demo Verified Recruiter
    recruiter1_email = "recruiter@techworks.com"
    cursor.execute("SELECT id FROM users WHERE email = ?", (recruiter1_email,))
    r1_user = cursor.fetchone()
    if not r1_user:
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, full_name, is_active)
            VALUES (?, ?, 'RECRUITER', ?, 1)
        ''', (recruiter1_email, generate_password_hash("Recruiter123!"), "Ayesha Khan"))
        r1_user_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO recruiters (user_id, recruiter_name, company_name, official_company_email, company_website, company_description, designation, is_verified, verification_notes, verified_at, verified_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'Corporate domain and business registration verified.', CURRENT_TIMESTAMP, ?)
        ''', (r1_user_id, "Ayesha Khan", "TechWorks Global Solutions", "careers@techworks.com", "https://techworks-global.example.com", "Enterprise cloud solutions and technology consulting firm committed to inclusive hiring returnships.", "Talent Acquisition Lead", admin_id))
        r1_recruiter_id = cursor.lastrowid
        print("Verified Recruiter created.")
    else:
        r1_user_id = r1_user['id']
        cursor.execute("SELECT id FROM recruiters WHERE user_id = ?", (r1_user_id,))
        r1_recruiter_id = cursor.fetchone()['id']

    # 3. Seed Demo Pending Recruiter (To demonstrate Admin verification workflow)
    recruiter2_email = "recruiter@innovatesoft.com"
    cursor.execute("SELECT id FROM users WHERE email = ?", (recruiter2_email,))
    r2_user = cursor.fetchone()
    if not r2_user:
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, full_name, is_active)
            VALUES (?, ?, 'RECRUITER', ?, 1)
        ''', (recruiter2_email, generate_password_hash("Recruiter123!"), "Priya Sharma"))
        r2_user_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO recruiters (user_id, recruiter_name, company_name, official_company_email, company_website, company_description, designation, is_verified, verification_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'Pending domain verification document check.')
        ''', (r2_user_id, "Priya Sharma", "InnovateSoft Systems", "hiring@innovatesoft.com", "https://innovatesoft-systems.example.com", "B2B SaaS product development company focusing on supply chain intelligence.", "HR Director"))
        print("Pending Recruiter created.")

    # 4. Seed Verified Job Vacancies (Transparently tied to verified recruiter)
    cursor.execute("SELECT COUNT(*) as count FROM jobs")
    if cursor.fetchone()['count'] == 0:
        jobs_data = [
            (
                r1_recruiter_id,
                "Software Engineer (Backend Python/Flask/Django) - Returnship Program",
                "TechWorks Global Solutions",
                "Bengaluru / Hybrid",
                "Hybrid",
                "2+ years prior experience before career gap",
                "Python, SQL, REST APIs, Git, Problem Solving",
                "B.E / B.Tech / B.Sc / BCA in Computer Science or related quantitative field",
                "INR 9,00,000 - 14,00,000 / year (commensurate with skills)",
                "We are actively seeking experienced engineers returning after a career break (1 to 6+ years). This position features structured re-onboarding, dedicated mentorship from senior engineering staff, flexible hybrid hours, and a 6-month ramp-up roadmap focusing on enterprise Python backend microservices.",
                "2026-11-30",
                "Internal",
                "VERIFIED_RECRUITER",
                "TechWorks Talent Portal (Direct)",
                "https://techworks-global.example.com/careers"
            ),
            (
                r1_recruiter_id,
                "Technical Documentation & Product Specialist",
                "TechWorks Global Solutions",
                "Remote / Anywhere in India",
                "Remote",
                "1-3 years experience in technical writing, QA, or customer support",
                "Technical Writing, Markdown, API Documentation, Cross-functional Communication",
                "Any Graduate / Post Graduate with strong written communication skills",
                "INR 5,50,000 - 8,00,000 / year",
                "Ideal for professionals returning after a career gap who possess strong attention to detail and clear written communication. You will collaborate with product managers and engineers to document cloud APIs, user guides, and internal release changelogs.",
                "2026-12-15",
                "Internal",
                "VERIFIED_RECRUITER",
                "TechWorks Talent Portal (Direct)",
                "https://techworks-global.example.com/careers"
            ),
            (
                r1_recruiter_id,
                "Data Operations & QA Analyst",
                "TechWorks Global Solutions",
                "Pune / Hybrid",
                "Hybrid",
                "1+ years experience or strong academic portfolio with SQL & Excel",
                "SQL, Advanced Excel, Data Cleaning, Analytical Thinking",
                "Bachelor's degree in any discipline",
                "INR 4,80,000 - 7,00,000 / year",
                "Role centered on data integrity, verification, and automated reporting. We offer refresher workshops on current data toolsets for returning candidates.",
                "2026-11-20",
                "Internal",
                "VERIFIED_RECRUITER",
                "TechWorks Talent Portal (Direct)",
                "https://techworks-global.example.com/careers"
            ),
            (
                None,
                "Open Source Python Contributor & Community Fellow (External Opportunity)",
                "Python Software Foundation / Outreachy",
                "Remote",
                "Remote",
                "No prior employment required; commitment to learning open source",
                "Python or Git basics, Willingness to Learn",
                "Open to all qualifications",
                "USD $7,000 total stipend for 3-month internship",
                "Outreachy provides paid, remote internships to people subject to systemic bias and impacted by career interruption. This is an external verified public opportunity.",
                "2026-10-31",
                "External",
                "EXTERNAL_SOURCE",
                "Outreachy Official Portal",
                "https://www.outreachy.org"
            )
        ]

        cursor.executemany('''
            INSERT INTO jobs (
                recruiter_id, title, company_name, location, work_mode,
                experience_required, skills_required, qualification_required,
                salary_range, description, application_deadline, application_method,
                source_type, source_name, source_url, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', jobs_data)
        print("Seeded authentic job opportunities.")

    # 5. Seed Authentic Government Opportunities (Verifiable public schemes & portals)
    cursor.execute("SELECT COUNT(*) as count FROM government_opportunities")
    if cursor.fetchone()['count'] == 0:
        gov_data = [
            (
                "Stand-Up India Scheme for Women Entrepreneurs",
                "Department of Financial Services, Ministry of Finance",
                "Entrepreneurship & Credit",
                "Central / All India",
                "All Scheduled Commercial Banks Nationwide",
                "Open to all women entrepreneurs (minimum 18 years of age)",
                "Age 18+; Enterprise must be a Greenfield project in manufacturing, services, or trading",
                "Women Entrepreneurs (100% women-owned or 51% controlling stake)",
                "Scheme / Fellowship",
                "Open",
                "2027-03-31",
                "Facilitates bank loans between INR 10 Lakhs and INR 1 Crore to at least one woman borrower per bank branch for setting up greenfield enterprises.",
                "Online application through Stand-Up Mitra portal -> Bank branch verification -> Project report appraisal -> Loan sanction.",
                "Proof of identity, Proof of residence, PAN Card, Project report, Bank statements, Proof of business premises.",
                "https://www.standupmitra.in",
                1
            ),
            (
                "Pradhan Mantri Mudra Yojana (PMMY) - Mahila Udyami Initiative",
                "Ministry of Micro, Small and Medium Enterprises (MSME)",
                "Micro Finance & Small Business",
                "Central / All India",
                "Public, Private, and Regional Rural Banks Nationwide",
                "No formal degree required; vocational or trade knowledge beneficial",
                "Age 18 years and above",
                "Special interest rate concessions for women entrepreneurs through selected banks",
                "Scheme / Fellowship",
                "Open",
                "2026-12-31",
                "Provides collateral-free loans up to INR 10 Lakhs across Shishu (up to 50k), Kishore (50k to 5 Lakhs), and Tarun (5 to 10 Lakhs) categories for non-corporate small business enterprises.",
                "Direct application at participating commercial banks or through Udyamimitra portal.",
                "Self-attested identity proof, Proof of address, Quotation of machinery/items to be purchased, Business registration (if available).",
                "https://www.mudra.org.in",
                1
            ),
            (
                "Women Scientist Scheme (WOS-A / DISHA Program)",
                "Department of Science & Technology (DST)",
                "Science, Technology & Research Re-entry",
                "Central / All India",
                "Recognized Universities and R&D Institutes across India",
                "M.Sc. / Ph.D. / B.Tech / M.Tech in Basic or Applied Sciences",
                "Age between 27 and 57 years; minimum 2-year career gap mandatory",
                "Exclusively formulated for women scientists and technologists facing career break",
                "Scheme / Fellowship",
                "Open",
                "2026-12-15",
                "Aimed at providing opportunities to women scientists and technologists who have taken a break in their career to re-enter mainstream science by pursuing research in frontier areas.",
                "Online proposal submission via online-wosa.gov.in -> Peer review by subject expert committee -> Presentation and sanction.",
                "Degree certificates, Proof of career gap, Project proposal, Host institution endorsement letter.",
                "https://online-wosa.gov.in",
                1
            ),
            (
                "Trade Related Entrepreneurship Assistance and Development (TREAD) Scheme for Women",
                "Ministry of Micro, Small and Medium Enterprises (MSME)",
                "Micro Enterprise & Self-Help Support",
                "Central / All India",
                "Through Non-Governmental Organizations (NGOs) and Microfinance Institutions",
                "Literate / Semi-literate / Educated women seeking self-employment",
                "No upper age limit for adult women",
                "Focused on marginalized, rural, and urban women micro-entrepreneurs",
                "Scheme / Fellowship",
                "Open",
                "2027-01-31",
                "Provides Government of India grants up to 30% of total project cost through non-profit partner agencies, with the remaining 70% financed as bank credit for group economic activities.",
                "Submission of composite proposal through participating registered non-profit/lending agency to MSME development offices.",
                "NGO registration, SHG member list, activity proposal, training plan.",
                "https://msme.gov.in",
                1
            ),
            (
                "Public Service Commission - Age Relaxation for Women & Gap Returnees",
                "State & Central Administrative Commissions",
                "Civil & Administrative Services",
                "Central / State Cadres",
                "Respective State Capital Centers",
                "Bachelor's degree in any discipline from a recognized University",
                "General age limits extended by 5 to 10 years for widows, divorced women, and women candidates under state service rules",
                "Women-specific age relaxations per gazette notifications",
                "Permanent",
                "Open",
                "2026-10-30",
                "Permanent public service recruitment for administrative, educational, and clerical cadre roles with statutory age concession provisions allowing career returnees to sit for competitive examinations.",
                "Preliminary Exam -> Mains Written Examination -> Interview / Document Verification.",
                "Graduation marksheet, domicile certificate, age verification document, caste/category certificate if claiming reservation.",
                "https://upsc.gov.in",
                1
            )
        ]

        cursor.executemany('''
            INSERT INTO government_opportunities (
                title, department, sector, state, location, qualification,
                age_criteria, category_criteria, job_type, application_status,
                deadline, eligibility_details, selection_process, required_documents,
                official_portal_url, is_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', gov_data)
        print("Seeded verifiable government opportunities.")

    # 6. Seed Authentic Free Learning Resources
    cursor.execute("SELECT COUNT(*) as count FROM learning_resources")
    if cursor.fetchone()['count'] == 0:
        learning_data = [
            (
                "Office Automation, Cloud Productivity & Professional Computing",
                "Technical Skills",
                "SWAYAM / UGC (Govt. of India)",
                "Free, university-accredited modular course covering digital spreadsheets, data collation, modern document collaboration, and cloud storage systems.",
                "https://swayam.gov.in",
                "6 Weeks (Self-paced)",
                "Free",
                "Beginner"
            ),
            (
                "Introduction to Python Programming & Modern Data Analysis",
                "Technical Skills",
                "NPTEL / IIT Madras",
                "Rigorous fundamentals course teaching core programming, structured problem solving, working with tabular data, and automation scripts.",
                "https://nptel.ac.in",
                "8 Weeks (Audit Free)",
                "Free",
                "Beginner to Intermediate"
            ),
            (
                "Workplace Communication, Assertiveness & Professional Confidence",
                "Soft Skills",
                "Skill India Digital / NSDC",
                "Practical modules designed specifically for workforce re-entrants to practice confident communication, executive presence, and business writing.",
                "https://www.skillindiadigital.gov.in",
                "4 Weeks",
                "Free",
                "All Levels"
            ),
            (
                "CS50's Introduction to Computer Science",
                "Technical Skills",
                "Harvard University / edX",
                "Worldwide benchmark course covering computational thinking, algorithms, Python, SQL, and web application architecture. Free audit tracks available.",
                "https://cs50.harvard.edu/x",
                "10-12 Weeks (Self-paced)",
                "Free",
                "Beginner to Intermediate"
            ),
            (
                "Responsive Web Design & Modern Frontend Standards",
                "Technical Skills",
                "FreeCodeCamp",
                "Interactive hands-on curriculum teaching HTML5, CSS3, modern responsive layouts, accessibility (WCAG), and responsive flexbox/grid.",
                "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
                "Self-paced (Approx 40 hours)",
                "Free",
                "Beginner"
            ),
            (
                "Framing Career Breaks & Modern Competency-Based Resumes",
                "Resume Preparation",
                "National Career Service (NCS) / ReTurn Resource Hub",
                "Step-by-step masterclass on transforming gap years into strategic value: functional vs hybrid resume formats, quantifiable achievements, and handling gap questions.",
                "/learning?category=Resume+Preparation",
                "2 Hours",
                "Free",
                "All Levels"
            ),
            (
                "Structured Behavioral & Technical Interview Mastery for Returnees",
                "Interview Preparation",
                "National Career Service / MoLE",
                "Techniques for answering the 'Tell me about your career break' question using the STAR framework, technical refreshers, and mock interview checklists.",
                "/learning?category=Interview+Preparation",
                "3 Hours",
                "Free",
                "All Levels"
            ),
            (
                "Entrepreneurship: From Problem Identification to Lean Business Plan",
                "Entrepreneurship",
                "SWAYAM / IIM Bangalore",
                "Comprehensive curriculum on validating customer needs, cost structuring, pricing strategies, and assembling proof-of-concept prototypes.",
                "https://swayam.gov.in",
                "6 Weeks",
                "Free",
                "Beginner to Intermediate"
            ),
            (
                "Government Examination Strategy: Syllabi, Timelines & Aptitude Refresher",
                "Government Exam Preparation",
                "National Career Service & Public Knowledge Portal",
                "Clear syllabus breakdowns, age relaxation guidelines, previous year question banks, and analytical reasoning preparation for SSC, Banking, and State PSCs.",
                "/learning?category=Government+Exam+Preparation",
                "Self-paced",
                "Free",
                "All Levels"
            )
        ]

        cursor.executemany('''
            INSERT INTO learning_resources (
                title, category, provider, description, url, duration_estimate, cost_type, skill_level, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', learning_data)
        print("Seeded authentic learning resources.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed_platform_data()
    print("Seed process completed.")
