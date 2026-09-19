import os
import unittest
import json
import time
from app import app
from database import get_db_connection, init_db
from seed_data import seed_platform_data
from services.resume_analyzer import analyze_resume_text
from services.startup_analyzer import analyze_startup_idea
from services.chatbot_service import process_chatbot_query
from services.auth_service import hash_password

class ReTurnPlatformTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        seed_platform_data()

    def setUp(self):
        self.client = app.test_client()

    def test_01_landing_page_accessible(self):
        """Landing page must load with clean headline, workflow steps, and trust section."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CAREER RE-ENTRY", response.data.upper())
        self.assertIn(b"Practical Career Re-Entry Workflow", response.data)
        self.assertIn(b"Job Authenticity & Trust System", response.data)
        self.assertIn(b"Experienced + Career Gap", response.data)

    def test_02_user_registration_and_profile_flow(self):
        """User registers and is redirected to Complete Profile, then Choose Path."""
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email = 'anita.test@example.com'")
        conn.commit()
        conn.close()

        # 1. Register new candidate
        reg_resp = self.client.post('/register', data={
            'full_name': 'Anita Test',
            'email': 'anita.test@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)
        self.assertEqual(reg_resp.status_code, 200)
        self.assertIn(b"Complete Your Re-Entry Profile", reg_resp.data)

        # 2. Complete Profile
        prof_resp = self.client.post('/profile/complete', data={
            'location': 'Bengaluru, Karnataka',
            'preferred_work_location': 'Bengaluru or Remote',
            'education': "Bachelor's Degree",
            'qualification': 'B.Tech Computer Science',
            'graduation_year': '2017',
            'work_mode_preference': 'Hybrid',
            'previous_job_title': 'Software QA Engineer',
            'years_of_experience': '4.0',
            'career_gap_duration': '3 - 5 years',
            'gap_reason': 'Maternity & Childcare',
            'previous_industry': 'IT Services',
            'skills': 'Manual Testing, SQL, Jira, Python, Selenium',
            'desired_career_direction': 'Python Quality Engineer',
            'preferences_sector': 'Private'
        }, follow_redirects=True)
        self.assertEqual(prof_resp.status_code, 200)
        self.assertIn(b"Choose Your Career Situation", prof_resp.data)

        # 3. Select Pathway: Experienced + Career Gap
        path_resp = self.client.post('/select-path', data={
            'pathway': 'EXPERIENCED_GAP'
        }, follow_redirects=True)
        self.assertEqual(path_resp.status_code, 200)
        self.assertIn(b"Career Re-Entry for Experienced Professionals", path_resp.data)

    def test_03_roadmap_generation_and_task_toggle(self):
        """Roadmap must generate 7 stages and allow interactive task toggling."""
        # Create user for this test
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email = 'roadmap.user@example.com'")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, full_name, is_active) VALUES (?, ?, 'USER', ?, 1)",
            ('roadmap.user@example.com', hash_password('Password123!'), 'Roadmap Candidate')
        )
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO profiles (user_id, profile_completed) VALUES (?, 1)", (user_id,))
        cursor.execute("INSERT INTO career_selections (user_id, pathway) VALUES (?, 'EXPERIENCED_GAP')", (user_id,))
        conn.commit()
        conn.close()

        # Login
        self.client.post('/login', data={
            'email': 'roadmap.user@example.com',
            'password': 'Password123!'
        })

        roadmap_resp = self.client.get('/roadmap')
        self.assertEqual(roadmap_resp.status_code, 200)
        self.assertIn(b"Career Re-Entry Roadmap", roadmap_resp.data)

        # Query first task from DB
        conn = get_db_connection()
        task = conn.execute('''
            SELECT t.id, t.is_completed FROM roadmap_tasks t
            JOIN user_roadmaps r ON t.roadmap_id = r.id
            WHERE r.user_id = ? LIMIT 1
        ''', (user_id,)).fetchone()
        conn.close()

        self.assertIsNotNone(task)
        task_id = task['id']

        # Toggle task status via API
        toggle_resp = self.client.post('/api/roadmap/task/toggle', 
            data=json.dumps({'task_id': task_id}),
            content_type='application/json'
        )
        self.assertEqual(toggle_resp.status_code, 200)
        data = json.loads(toggle_resp.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['is_completed'])
        self.assertGreater(data['percentage'], 0)

    def test_04_substantive_resume_analyzer(self):
        """Resume analyzer extracts criteria, highlights missing sections, and generates STAR rewrites."""
        sample_resume = """
        Ananya Rao
        Email: ananya.rao@example.com | Phone: 9876543210
        
        EXPERIENCE
        Worked on customer support tickets and helped with team escalations.
        Handled monthly reports in Excel.
        
        EDUCATION
        B.Com - University of Pune, 2019
        """
        analysis = analyze_resume_text(sample_resume, target_role="Software Engineer")

        # Must flag missing sections
        self.assertIn("Skills & Core Competencies", analysis['sections_missing'])
        self.assertIn("Professional Summary / Objective", analysis['sections_missing'])
        
        # Must detect passive verbs and recommend action verbs
        self.assertTrue(len(analysis['action_verb_feedback']) > 0)

        # Must provide missing keywords for the target role
        missing_kw_lower = [k.lower() for k in analysis['missing_keywords']]
        self.assertIn("python", missing_kw_lower)
        self.assertIn("git", missing_kw_lower)

        # Must include STAR rewrites and an enhanced draft
        self.assertTrue(len(analysis['suggested_bullets']) > 0)
        self.assertIn("PROFESSIONAL SUMMARY", analysis['enhanced_resume_text'])
        self.assertIn("ANANYA RAO", analysis['enhanced_resume_text'])

    def test_05_recruiter_and_admin_verification_workflow(self):
        """Pending recruiter must NOT have Verified badge until Admin approves."""
        # Ensure InnovateSoft starts unverified
        conn = get_db_connection()
        conn.execute("UPDATE recruiters SET is_verified = 0 WHERE company_name = 'InnovateSoft Systems'")
        conn.commit()
        conn.close()

        # 1. Login as Admin
        admin_login = self.client.post('/admin/login', data={
            'email': 'admin@return.internal',
            'password': 'AdminPassword123!'
        }, follow_redirects=True)
        self.assertEqual(admin_login.status_code, 200)

        # 2. Check pending recruiter queue
        queue_resp = self.client.get('/admin/verify-recruiters')
        self.assertEqual(queue_resp.status_code, 200)
        self.assertIn(b"InnovateSoft Systems", queue_resp.data)

        # 3. Approve the pending recruiter
        conn = get_db_connection()
        pending_recruiter = conn.execute("SELECT id FROM recruiters WHERE company_name = 'InnovateSoft Systems'").fetchone()
        conn.close()

        approve_resp = self.client.post(f'/admin/recruiters/{pending_recruiter["id"]}/action', data={
            'action': 'approve'
        }, follow_redirects=True)
        self.assertEqual(approve_resp.status_code, 200)
        self.assertIn(b"Recruiter approved", approve_resp.data)

        # 4. Verify in DB that is_verified is now 1
        conn = get_db_connection()
        rec_status = conn.execute("SELECT is_verified FROM recruiters WHERE id = ?", (pending_recruiter['id'],)).fetchone()
        conn.close()
        self.assertEqual(rec_status['is_verified'], 1)

    def test_06_government_opportunity_filtering(self):
        """Government opportunities directory filters correctly by state and sector."""
        resp = self.client.get('/government/hub?state=Central+%2F+All+India')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Stand-Up India Scheme", resp.data)
        self.assertIn(b"Women Scientist Scheme", resp.data)
        self.assertIn(b"Official Application Portal", resp.data)

    def test_07_startup_analyzer_and_disclaimer(self):
        """Startup idea evaluation provides 4-phase MVP and explicit funding disclaimer."""
        idea_data = {
            'business_name': 'HerCraft Home Studio',
            'problem_statement': 'Local women artisans struggle to sell hand-woven crafts online due to complex digital marketing requirements.',
            'solution_description': 'Curated collective catalogue offering photo styling, logistics handling, and bulk shipping.',
            'target_users': 'Rural women artisans and conscious metropolitan urban buyers.',
            'skills_available': 'Craft curation, basic accounting, local community organizing.',
            'budget_range': 'INR 50,000 - 5 Lakhs (Mudra Shishu/Kishore)',
            'location': 'Jaipur, Rajasthan'
        }
        result = analyze_startup_idea(idea_data)

        self.assertEqual(result['business_name'], 'HerCraft Home Studio')
        self.assertIn('Funding eligibility depends on the specific scheme', result['funding_disclaimer'])
        self.assertEqual(len(result['mvp_steps']), 4)
        self.assertTrue(len(result['verified_schemes']) >= 3)

    def test_08_chatbot_widget_and_api(self):
        """Chatbot widget, cross/wrong close button, and /api/chat endpoint must function correctly."""
        # 1. Check UI markup for chatbox container, toggle button, window, and close button
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'id="chatbot-container"', resp.data)
        self.assertIn(b'id="chatbot-toggle-btn"', resp.data)
        self.assertIn(b'id="chatbot-window"', resp.data)
        self.assertIn(b'id="chatbot-close-btn"', resp.data)
        self.assertIn(b'chatbot.js', resp.data)

        # 2. Test /api/chat with career gap query
        api_resp = self.client.post('/api/chat', json={'message': 'How to explain a career gap?'})
        self.assertEqual(api_resp.status_code, 200)
        data = api_resp.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('How to Frame a Career Gap', data['reply'])
        self.assertIn('Notice: I am an automated platform assistant', data['disclaimer'])

        # 3. Test /api/chat with government schemes query
        gov_resp = self.client.post('/api/chat', json={'message': 'What government schemes are available?'})
        self.assertEqual(gov_resp.status_code, 200)
        gov_data = gov_resp.get_json()
        self.assertEqual(gov_data['status'], 'success')
        self.assertIn('Stand-Up India', gov_data['reply'])

    def test_09_login_dropdown_and_routes(self):
        """Login dropdown must display User, Recruiter, and Admin links and route properly."""
        # 1. Check landing page has login dropdown with all 3 options
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'id="login-dropdown-btn"', resp.data)
        self.assertIn(b'id="login-dropdown-menu"', resp.data)
        self.assertIn(b'/login/user', resp.data)
        self.assertIn(b'/login/recruiter', resp.data)
        self.assertIn(b'/login/admin', resp.data)

        # 2. Test /login/user route renders User Sign In
        user_resp = self.client.get('/login/user')
        self.assertEqual(user_resp.status_code, 200)
        self.assertIn(b"User Sign In", user_resp.data)

        # 3. Test /login/recruiter route renders Recruiter Portal
        rec_resp = self.client.get('/login/recruiter')
        self.assertEqual(rec_resp.status_code, 200)
        self.assertIn(b"Recruiter Portal", rec_resp.data)

        # 4. Test /login/admin route renders Admin Console Sign In
        admin_resp = self.client.get('/login/admin')
        self.assertEqual(admin_resp.status_code, 200)
        self.assertIn(b"Admin Console Sign In", admin_resp.data)

    def test_10_rbac_protection(self):
        """Users cannot access recruiter or admin portals."""
        # Unauthenticated user access to admin redirects to login
        admin_resp = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(admin_resp.status_code, 302)

        # Create normal user
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email = 'candidate.rbac@example.com'")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, full_name, is_active) VALUES (?, ?, 'USER', ?, 1)",
            ('candidate.rbac@example.com', hash_password('Password123!'), 'Candidate RBAC')
        )
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO profiles (user_id, profile_completed) VALUES (?, 1)", (user_id,))
        conn.commit()
        conn.close()

        # Login as normal user
        self.client.post('/login', data={
            'email': 'candidate.rbac@example.com',
            'password': 'Password123!'
        })

        # Attempt to access admin console as normal user
        forbidden_admin = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b"You do not have permission", forbidden_admin.data)

    def test_11_ai_career_gap_analysis_and_persistence(self):
        """AI Career-Gap Analysis endpoint generates diagnostic and persists to career_gap_analyses."""
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email = 'gap.candidate@example.com'")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, full_name, is_active) VALUES (?, ?, 'USER', ?, 1)",
            ('gap.candidate@example.com', hash_password('Password123!'), 'Gap Candidate')
        )
        user_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO profiles (
                user_id, profile_completed, previous_job_title, years_of_experience,
                career_gap_duration, skills, desired_career_direction, work_mode_preference
            ) VALUES (?, 1, 'Associate Java Developer', '3.5', '4 years', 'Java, Spring, MySQL, Git', 'Cloud Backend Engineer', 'Remote')
        ''', (user_id,))
        cursor.execute("INSERT INTO career_selections (user_id, pathway) VALUES (?, 'EXPERIENCED_GAP')", (user_id,))
        conn.commit()
        conn.close()

        # Login
        self.client.post('/login', data={'email': 'gap.candidate@example.com', 'password': 'Password123!'})

        # Trigger AI analysis
        resp = self.client.post('/api/ai/analyze-gap')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIn('analysis', data)
        self.assertTrue(any(level in data['analysis']['readiness_level'] for level in ['High', 'Moderate', 'Foundational']))
        self.assertTrue(len(data['analysis']['skill_gaps']) > 0)
        self.assertTrue(any(k in data['analysis']['roadmap_90_days'] for k in ['phase1_weeks_1_2', 'month_1']))

        # Verify DB persistence
        conn = get_db_connection()
        saved = conn.execute("SELECT * FROM career_gap_analyses WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        self.assertIsNotNone(saved)
        self.assertEqual(saved['target_role'], 'Cloud Backend Engineer')

        # Verify UI page renders
        page_resp = self.client.get('/career-analysis')
        self.assertEqual(page_resp.status_code, 200)
        self.assertIn(b"Career-Gap Analysis & Re-Entry Strategy", page_resp.data)
        self.assertIn(b"Cloud Backend Engineer", page_resp.data)

    def test_12_dynamic_job_matching_and_scores(self):
        """Dynamic job matching ranks approved jobs and outputs match scores & reasons."""
        conn = get_db_connection()
        user_id = conn.execute("SELECT id FROM users WHERE email = 'gap.candidate@example.com'").fetchone()['id']
        profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        raw_jobs = conn.execute("SELECT * FROM jobs WHERE is_active = 1 AND approval_status = 'APPROVED'").fetchall()
        conn.close()

        from services.job_matcher import match_jobs_for_candidate
        ranked = match_jobs_for_candidate(raw_jobs, profile)
        self.assertTrue(len(ranked) > 0)
        self.assertIn('match_score', ranked[0])
        self.assertIn('match_reasons', ranked[0])
        self.assertGreaterEqual(ranked[0]['match_score'], ranked[-1]['match_score'])

    def test_13_recruiter_job_posting_starts_as_pending(self):
        """Recruiter-submitted job starts as PENDING and is not in public candidate feed."""
        # 0. Clean up any existing job with that title for idempotency
        conn = get_db_connection()
        conn.execute("DELETE FROM job_applications WHERE job_id IN (SELECT id FROM jobs WHERE title = 'Senior Automation Test Engineer')")
        conn.execute("DELETE FROM jobs WHERE title = 'Senior Automation Test Engineer'")
        conn.commit()
        conn.close()

        # 1. Login as Verified Recruiter
        self.client.post('/login', data={
            'email': 'recruiter@techworks.com',
            'password': 'Recruiter123!'
        })

        # 2. Post a new job
        post_resp = self.client.post('/recruiter/post-job', data={
            'title': 'Senior Automation Test Engineer',
            'location': 'Bengaluru',
            'work_mode': 'Hybrid',
            'experience_level': 'Mid-Level (3-6 yrs)',
            'salary_range': '₹12-16 LPA',
            'career_gap_tolerated_min': '1',
            'career_gap_tolerated_max': '8',
            'description': 'Leading our QA returnee cohort with automated testing infrastructure in Playwright & Python.',
            'requirements': 'Python, PyTest, Selenium, CI/CD',
            'benefits': 'Flexible hours, returning mother mentorship cohort'
        }, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)
        self.assertIn(b"submitted for platform moderation", post_resp.data)

        # 3. Check DB for PENDING status
        conn = get_db_connection()
        job = conn.execute("SELECT * FROM jobs WHERE title = 'Senior Automation Test Engineer'").fetchone()
        conn.close()
        self.assertIsNotNone(job)
        self.assertEqual(job['approval_status'], 'PENDING')

        # 4. Check candidate explore page: Job must NOT be visible yet
        explore_resp = self.client.get('/explore')
        self.assertNotIn(b"Senior Automation Test Engineer", explore_resp.data)

    def test_14_admin_job_moderation_lifecycle(self):
        """Admin reviews pending job, approves it, and job becomes visible in candidate feed."""
        conn = get_db_connection()
        job = conn.execute("SELECT id FROM jobs WHERE title = 'Senior Automation Test Engineer'").fetchone()
        conn.close()
        job_id = job['id']

        # 1. Login as Admin
        self.client.post('/admin/login', data={
            'email': 'admin@return.internal',
            'password': 'AdminPassword123!'
        })

        # 2. View moderation queue
        mod_resp = self.client.get('/admin/manage-jobs')
        self.assertIn(b"Senior Automation Test Engineer", mod_resp.data)
        self.assertIn(b"Pending Moderation Queue", mod_resp.data)

        # 3. Approve job
        approve_resp = self.client.post(f'/admin/jobs/{job_id}/review', data={
            'decision': 'APPROVE'
        }, follow_redirects=True)
        self.assertEqual(approve_resp.status_code, 200)
        self.assertIn(b"approved and published", approve_resp.data)

        # 4. Verify in DB
        conn = get_db_connection()
        updated_job = conn.execute("SELECT approval_status, is_active FROM jobs WHERE id = ?", (job_id,)).fetchone()
        conn.close()
        self.assertEqual(updated_job['approval_status'], 'APPROVED')
        self.assertEqual(updated_job['is_active'], 1)

        # 5. Now it MUST appear in candidate explore feed
        explore_resp = self.client.get('/explore')
        self.assertIn(b"Senior Automation Test Engineer", explore_resp.data)

    def test_15_recruiter_application_workflow_and_candidate_profile(self):
        """Candidate applies, recruiter inspects profile/resume, updates status, and notifications dispatch."""
        conn = get_db_connection()
        job = conn.execute("SELECT id FROM jobs WHERE title = 'Senior Automation Test Engineer'").fetchone()
        user = conn.execute("SELECT id FROM users WHERE email = 'gap.candidate@example.com'").fetchone()
        conn.execute("DELETE FROM job_applications WHERE user_id = ? AND job_id = ?", (user['id'], job['id']))
        conn.commit()
        conn.close()

        # 1. Login as Candidate and apply
        self.client.post('/login', data={'email': 'gap.candidate@example.com', 'password': 'Password123!'})
        apply_resp = self.client.post(f'/jobs/{job["id"]}/apply', data={
            'cover_note': 'I have 3.5 years of QA testing background and recently upskilled in automated Python pipelines.'
        }, follow_redirects=True)
        self.assertEqual(apply_resp.status_code, 200)
        self.assertIn(b"directly submitted to the recruiter", apply_resp.data)

        # 2. Get the application ID
        conn = get_db_connection()
        application = conn.execute("SELECT id FROM job_applications WHERE job_id = ? AND user_id = ?", (job['id'], user['id'])).fetchone()
        conn.close()
        app_id = application['id']

        # 3. Login as Recruiter
        self.client.post('/login', data={'email': 'recruiter@techworks.com', 'password': 'Recruiter123!'})

        # 4. Recruiter inspects candidate credentials via JSON API
        cand_resp = self.client.get(f'/recruiter/applications/{app_id}/candidate')
        self.assertEqual(cand_resp.status_code, 200)
        cand_data = cand_resp.get_json()
        self.assertTrue(cand_data['success'])
        self.assertEqual(cand_data['candidate']['name'], 'Gap Candidate')
        self.assertEqual(cand_data['profile']['career_gap_duration'], '4 years')

        # 5. Recruiter updates application status to Shortlisted
        status_resp = self.client.post(f'/recruiter/applications/{app_id}/status', data={
            'status': 'Shortlisted'
        }, follow_redirects=True)
        self.assertEqual(status_resp.status_code, 200)
        self.assertTrue(b"updated to" in status_resp.data and b"Shortlisted" in status_resp.data)

        # 6. Verify notification was sent to candidate
        conn = get_db_connection()
        notif = conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user['id'],)
        ).fetchone()
        conn.close()
        self.assertIsNotNone(notif)
        self.assertIn("Shortlisted", notif['message'])

    def test_16_admin_user_activation_and_gov_scheme_crud(self):
        """Admin toggles user activation and adds/edits government schemes."""
        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE email = 'gap.candidate@example.com'").fetchone()
        conn.close()
        target_user_id = user['id']

        # 1. Login as Admin
        self.client.post('/admin/login', data={'email': 'admin@return.internal', 'password': 'AdminPassword123!'})

        # 2. Toggle user status to deactivated
        toggle_resp = self.client.post(f'/admin/users/{target_user_id}/toggle', follow_redirects=True)
        self.assertEqual(toggle_resp.status_code, 200)
        conn = get_db_connection()
        u_status = conn.execute("SELECT is_active FROM users WHERE id = ?", (target_user_id,)).fetchone()
        self.assertEqual(u_status['is_active'], 0)

        # Re-activate user
        self.client.post(f'/admin/users/{target_user_id}/toggle', follow_redirects=True)
        u_status2 = conn.execute("SELECT is_active FROM users WHERE id = ?", (target_user_id,)).fetchone()
        self.assertEqual(u_status2['is_active'], 1)

        # 3. Add government scheme
        add_gov_resp = self.client.post('/admin/government/add', data={
            'title': 'National Returnee Tech Grant',
            'department': 'Ministry of Electronics & IT',
            'state': 'All India',
            'sector': 'Technology & Upskilling',
            'job_type': 'Fellowship Grant',
            'eligibility_criteria': 'Women STEM degree holders with >= 2 years gap.',
            'age_limit': 'Up to 50 years',
            'reservation_relaxations': '5 years age relaxation for career breaks',
            'official_notification_url': 'https://meity.gov.in/returnee-fellowship',
            'apply_url': 'https://meity.gov.in/apply'
        }, follow_redirects=True)
        self.assertEqual(add_gov_resp.status_code, 200)
        self.assertIn(b"published successfully", add_gov_resp.data)

        # 4. Verify in government hub
        hub_resp = self.client.get('/government/hub')
        self.assertIn(b"National Returnee Tech Grant", hub_resp.data)
        conn.close()

    def test_17_unified_user_context_builder(self):
        """Unified get_complete_user_context must aggregate profile, resume, and pathway accurately."""
        from services.ai_service import get_complete_user_context
        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE email = 'gap.candidate@example.com'").fetchone()
        conn.close()
        self.assertIsNotNone(user)

        ctx = get_complete_user_context(user['id'])
        self.assertEqual(ctx['user_id'], user['id'])
        self.assertEqual(ctx['email'], 'gap.candidate@example.com')
        self.assertTrue(ctx['profile_completed'])
        self.assertEqual(ctx['pathway'], 'EXPERIENCED_GAP')
        self.assertTrue(len(ctx['skills']) > 0)

    def test_18_personalized_career_gap_scenarios(self):
        """AI Career Gap recommendations must differ and reason specifically from candidate profiles (Scenarios A, B, C)."""
        from services.ai_service import generate_career_gap_analysis

        # Scenario A: Corporate HR -> HR Analyst (4 years gap)
        profile_a = {
            'name': 'Pooja HR',
            'qualification': 'MBA Human Resources',
            'previous_job_title': 'HR Executive',
            'years_of_experience': 3.0,
            'career_gap_duration': '3 - 5 years',
            'gap_reason': 'Maternity & Childcare',
            'previous_industry': 'Corporate IT Services',
            'skills': 'Recruitment, Employee Onboarding, Excel, HRIS',
            'target_role': 'HR Analyst',
            'work_mode_preference': 'Hybrid'
        }
        res_a = generate_career_gap_analysis(profile_a, 'EXPERIENCED_GAP')
        self.assertIn('HR', res_a['current_position_analysis'])
        self.assertTrue(any('HR' in str(r) or 'Analyst' in str(r) for r in res_a['suggested_roles']))
        self.assertIn('Maternity', res_a['resume_advice'])

        # Scenario B: Fresher / Limited Experience -> Accounting
        profile_b = {
            'name': 'Sneha Fresher',
            'qualification': 'B.Com General',
            'previous_job_title': 'None',
            'years_of_experience': 0.0,
            'career_gap_duration': 'No Prior Employment (Fresh)',
            'gap_reason': 'Education / Voluntary Sabbatical',
            'previous_industry': 'None',
            'skills': 'Basic Accounting, Spreadsheets',
            'target_role': 'Junior Accountant',
            'work_mode_preference': 'On-site'
        }
        res_b = generate_career_gap_analysis(profile_b, 'NO_EXPERIENCE')
        self.assertIn('Junior Accountant', res_b['current_position_analysis'])
        self.assertTrue(any('Accountant' in str(r) for r in res_b['suggested_roles']))

        # Scenario C: Tech QA -> Python Backend Transition (3 years gap)
        profile_c = {
            'name': 'Ritu Tech',
            'qualification': 'B.Tech Computer Science',
            'previous_job_title': 'Manual QA Tester',
            'years_of_experience': 4.0,
            'career_gap_duration': '3 - 5 years',
            'gap_reason': 'Personal Health & Medical Recovery',
            'previous_industry': 'Software Testing',
            'skills': 'Manual Testing, SQL, Jira, Regression',
            'target_role': 'Python Backend Engineer',
            'work_mode_preference': 'Remote'
        }
        res_c = generate_career_gap_analysis(profile_c, 'CAREER_SHIFT')
        self.assertIn('Python', res_c['current_position_analysis'])
        self.assertTrue(any('Python' in str(r) or 'Engineer' in str(r) for r in res_c['suggested_roles']))

        # Verify scenarios produce distinct targeted outputs
        self.assertNotEqual(res_a['suggested_roles'], res_b['suggested_roles'])
        self.assertNotEqual(res_b['suggested_roles'], res_c['suggested_roles'])

    def test_19_resume_upload_analysis_and_docx_generation(self):
        """Resume upload parses text, runs qualitative analysis, generates real .docx, and supports download."""
        import io
        import docx

        # 1. Login user
        self.client.post('/login', data={'email': 'gap.candidate@example.com', 'password': 'Password123!'})

        # 2. Upload text resume
        sample_resume_content = b"""
Priya Sharma
Bengaluru, Karnataka | priya.sharma@example.com | +91 9876543210 | linkedin.com/in/priyasharma

PROFESSIONAL SUMMARY
Experienced Software QA Analyst with 4 years testing web and mobile platforms. Returning to work following a career break.

EXPERIENCE
Infosys Technologies | Bengaluru
QA Analyst | 2017 - 2021
- Worked on regression testing and executed test cases daily.
- Handled defect reporting in Jira and coordinated with developers.
- Managed sprint QA deliverables and test matrices.

Career Break & Upskilling | 2021 - 2024
- Managed family responsibilities while completing certified Python and Selenium coursework.

EDUCATION
B.Tech in Computer Science | VTU Bengaluru | 2017

SKILLS
Manual Testing, SQL, Jira, Python, Selenium, Postman, Git
"""
        upload_resp = self.client.post('/resume/upload', data={
            'target_role': 'Quality Engineer',
            'resume_file': (io.BytesIO(sample_resume_content), 'Priya_Sharma_Resume.txt')
        }, follow_redirects=True)
        self.assertEqual(upload_resp.status_code, 200)
        self.assertIn(b"Resume analyzed successfully", upload_resp.data)

        # 3. Generate updated resume via API
        gen_resp = self.client.post('/api/resume/generate-updated', json={
            'target_role': 'Quality Engineer'
        })
        self.assertEqual(gen_resp.status_code, 200)
        gen_data = gen_resp.get_json()
        self.assertTrue(gen_data['success'])
        self.assertIn('download_docx_url', gen_data)

        # 4. Download original resume
        orig_download = self.client.get('/resume/download-original')
        self.assertEqual(orig_download.status_code, 200)

        # 5. Download updated .docx file and verify it is a valid Word document
        docx_download = self.client.get('/resume/download-updated?format=docx')
        self.assertEqual(docx_download.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.wordprocessingml.document', docx_download.content_type)
        
        doc_stream = io.BytesIO(docx_download.data)
        loaded_doc = docx.Document(doc_stream)
        doc_text = "\n".join(p.text for p in loaded_doc.paragraphs)
        self.assertIn("PROFESSIONAL SUMMARY", doc_text.upper())
        self.assertIn("PRIYA SHARMA", doc_text.upper())
        self.assertIn("QUALITY ENGINEER", doc_text.upper())

        # 6. Download updated text version
        txt_download = self.client.get('/resume/download-updated?format=txt')
        self.assertEqual(txt_download.status_code, 200)
        self.assertIn(b"PROFESSIONAL SUMMARY", txt_download.data)
        self.assertIn(b"PRIYA SHARMA", txt_download.data)

    def test_20_chatbot_context_awareness_and_memory(self):
        """Chatbot uses candidate profile context and multi-turn session memory."""
        # 1. Login user
        self.client.post('/login', data={'email': 'gap.candidate@example.com', 'password': 'Password123!'})

        # 2. Query for role-specific learning recommendations
        learn_resp = self.client.post('/api/chat', json={'message': 'What should I learn?'})
        self.assertEqual(learn_resp.status_code, 200)
        learn_data = learn_resp.get_json()
        self.assertEqual(learn_data['status'], 'success')
        # Candidate is targeting Python QA / Software QA
        self.assertTrue('Python' in learn_data['reply'] or 'Quality' in learn_data['reply'] or 'Test' in learn_data['reply'] or 'Learning' in learn_data['category'])

        # 3. Query for specific career gap explanation
        gap_resp = self.client.post('/api/chat', json={'message': 'How should I explain my career gap in an interview?'})
        self.assertEqual(gap_resp.status_code, 200)
        gap_data = gap_resp.get_json()
        self.assertEqual(gap_data['status'], 'success')
        self.assertIn('Career Gap', gap_data['reply'])

        # 4. Follow-up query checking session memory
        role_resp = self.client.post('/api/chat', json={'message': 'What roles can I target?'})
        self.assertEqual(role_resp.status_code, 200)
        role_data = role_resp.get_json()
        self.assertEqual(role_data['status'], 'success')
        self.assertIn('Target Roles', role_data['reply'])

    def test_21_dynamic_roadmap_generation_and_updates(self):
        """Roadmap dynamically tailors 7 stages to user target role and updates on profile change."""
        # 1. Register new user for HR profile
        u_email = f"hr.returnee.{int(time.time())}@example.com"
        self.client.post('/register', data={
            'email': u_email,
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'full_name': 'Anita Rao',
            'role': 'USER'
        })
        self.client.post('/login', data={'email': u_email, 'password': 'Password123!'})

        # 2. Complete profile as HR Specialist
        self.client.post('/profile/complete', data={
            'location': 'Hyderabad',
            'education': "Master's Degree",
            'qualification': 'MBA in Human Resources',
            'skills': 'Talent Acquisition, HRIS, Employee Onboarding',
            'previous_job_title': 'Senior HR Specialist',
            'years_of_experience': '5',
            'career_gap_duration': '4 years',
            'gap_reason': 'Maternity and Child Care',
            'target_role': 'HR Talent Acquisition Lead',
            'desired_career_direction': 'HR Talent Acquisition Lead',
            'work_mode_preference': 'Hybrid',
            'preferences_sector': 'Private'
        })
        self.client.post('/select-path', data={'pathway': 'EXPERIENCED_GAP'})

        # 3. Fetch roadmap and verify dynamic HR tasks
        rm_resp = self.client.get('/roadmap')
        self.assertEqual(rm_resp.status_code, 200)
        self.assertIn(b"HR Talent Acquisition Lead", rm_resp.data)

        # 4. Change profile to "Data Analyst"
        self.client.post('/profile/complete', data={
            'location': 'Hyderabad',
            'education': "Master's Degree",
            'qualification': 'MBA in Human Resources',
            'skills': 'SQL, Python, Power BI, Data Cleaning',
            'previous_job_title': 'Senior HR Specialist',
            'years_of_experience': '5',
            'career_gap_duration': '4 years',
            'gap_reason': 'Maternity and Child Care',
            'target_role': 'Data Analyst',
            'desired_career_direction': 'Data Analyst',
            'work_mode_preference': 'Remote',
            'preferences_sector': 'Private'
        })

        # 5. Fetch updated roadmap and verify dynamic update to Data Analyst
        rm_updated_resp = self.client.get('/roadmap')
        self.assertEqual(rm_updated_resp.status_code, 200)
        self.assertIn(b"Data Analyst", rm_updated_resp.data)

    def test_22_dynamic_job_matching_and_profile_updates(self):
        """Job match scores and reasons dynamically compute against user skills and target role."""
        from services.job_matcher import match_jobs_for_candidate

        sample_jobs = [
            {
                'id': 1,
                'title': 'Software Engineer (Backend Python)',
                'company_name': 'TechWorks Global Solutions',
                'location': 'Bengaluru',
                'work_mode': 'Remote',
                'skills_required': 'Python, SQL, REST APIs, Git',
                'source_type': 'VERIFIED_RECRUITER'
            },
            {
                'id': 2,
                'title': 'HR Operations & Talent Specialist',
                'company_name': 'Global People Partners',
                'location': 'Hyderabad',
                'work_mode': 'Hybrid',
                'skills_required': 'Talent Acquisition, HRIS, Employee Relations',
                'source_type': 'VERIFIED_RECRUITER'
            }
        ]

        # Profile A: Python Dev
        profile_dev = {
            'skills': 'Python, SQL, Django, Git',
            'desired_career_direction': 'Software Engineer',
            'work_mode_preference': 'Remote',
            'location': 'Bengaluru',
            'preferences_sector': 'Private'
        }

        # Profile B: HR Specialist
        profile_hr = {
            'skills': 'Talent Acquisition, HRIS, Onboarding',
            'desired_career_direction': 'HR Operations',
            'work_mode_preference': 'Hybrid',
            'location': 'Hyderabad',
            'preferences_sector': 'Private'
        }

        matched_dev = match_jobs_for_candidate(sample_jobs, profile_dev)
        # Job 1 should be ranked #1 for dev
        self.assertEqual(matched_dev[0]['id'], 1)
        self.assertGreater(matched_dev[0]['match_score'], matched_dev[1]['match_score'])

        matched_hr = match_jobs_for_candidate(sample_jobs, profile_hr)
        # Job 2 should be ranked #1 for HR
        self.assertEqual(matched_hr[0]['id'], 2)
        self.assertGreater(matched_hr[0]['match_score'], matched_hr[1]['match_score'])

    def test_23_distinct_resumes_for_different_user_profiles(self):
        """Verify that 3 different candidate profiles produce completely unique, factual resumes without boilerplate."""
        from services.resume_analyzer import generate_improved_resume_draft, parse_resume_data

        # Profile 1: HR Specialist
        resume_hr = """
Rashmi Kulkarni | Bangalore | rashmi.hr@example.com
EXPERIENCE
Wipro Limited | HR Executive | 2017 - 2022
- Managed end-to-end recruitment lifecycle and candidate sourcing.
- Coordinated onboarding process for 150+ new employees annually.
- Maintained employee records in Workday HRIS.

EDUCATION
MBA in Human Resources | Symbiosis University | 2017

SKILLS
Talent Acquisition, Workday HRIS, Employee Onboarding, Compliance
"""
        profile_hr = {
            'name': 'Rashmi Kulkarni',
            'location': 'Bangalore',
            'previous_job_title': 'HR Executive',
            'previous_industry': 'IT Services',
            'years_of_experience': 5,
            'career_gap_duration': '3 years',
            'gap_reason': 'Maternity and Child Care',
            'qualification': 'MBA in Human Resources',
            'skills': 'Talent Acquisition, Workday HRIS, Employee Onboarding',
            'target_role': 'HR Talent Acquisition Lead'
        }

        # Profile 2: Junior Accountant / B.Com Graduate
        resume_acc = """
Meera Patel | Ahmedabad | meera.p@example.com
EDUCATION
Bachelor of Commerce (B.Com) | Gujarat University | 2023
- Major in Accounting and Financial Management.

SKILLS
Tally Prime, GST Filing, Excel Financial Modeling, Ledger Reconciliation
"""
        profile_acc = {
            'name': 'Meera Patel',
            'location': 'Ahmedabad',
            'previous_job_title': '',
            'previous_industry': '',
            'years_of_experience': 0,
            'career_gap_duration': '',
            'gap_reason': '',
            'qualification': 'Bachelor of Commerce (B.Com)',
            'skills': 'Tally Prime, GST Filing, Excel Financial Modeling, Ledger Reconciliation',
            'target_role': 'Junior Accountant'
        }

        # Profile 3: Python Backend Engineer
        resume_dev = """
Ananya Sen | Kolkata | ananya.dev@example.com
EXPERIENCE
Cognizant Technology Solutions | Python Developer | 2019 - 2022
- Developed scalable REST APIs using Python, Flask, and PostgreSQL.
- Implemented asynchronous Celery workers for report generation.
- Automated unit test suites using PyTest.

EDUCATION
B.Tech in Computer Science | Jadavpur University | 2019

SKILLS
Python, Flask, Django, PostgreSQL, Docker, Git, PyTest
"""
        profile_dev = {
            'name': 'Ananya Sen',
            'location': 'Kolkata',
            'previous_job_title': 'Python Developer',
            'previous_industry': 'Software Engineering',
            'years_of_experience': 3,
            'career_gap_duration': '2 years',
            'gap_reason': 'Family Healthcare Support',
            'qualification': 'B.Tech in Computer Science',
            'skills': 'Python, Flask, Django, PostgreSQL, Docker, Git',
            'target_role': 'Python Backend Engineer'
        }

        draft_hr = generate_improved_resume_draft(resume_hr, 'HR Talent Acquisition Lead', profile_hr)
        draft_acc = generate_improved_resume_draft(resume_acc, 'Junior Accountant', profile_acc)
        draft_dev = generate_improved_resume_draft(resume_dev, 'Python Backend Engineer', profile_dev)

        # 1. Verify Profile 1 (HR) specificity
        self.assertIn("RASHMI KULKARNI", draft_hr)
        self.assertIn("MBA IN HUMAN RESOURCES", draft_hr.upper())
        self.assertIn("Wipro Limited", draft_hr)
        self.assertIn("Talent Acquisition", draft_hr)
        self.assertIn("maternity", draft_hr.lower())
        self.assertNotIn("Python", draft_hr)
        self.assertNotIn("Tally Prime", draft_hr)

        # 2. Verify Profile 2 (Accountant) specificity
        self.assertIn("MEERA PATEL", draft_acc)
        self.assertIn("B.COM", draft_acc.upper())
        self.assertIn("Tally Prime", draft_acc)
        self.assertIn("Junior Accountant", draft_acc)
        self.assertNotIn("Wipro", draft_acc)
        self.assertNotIn("Celery", draft_acc)

        # 3. Verify Profile 3 (Python Dev) specificity
        self.assertIn("ANANYA SEN", draft_dev)
        self.assertIn("B.TECH IN COMPUTER SCIENCE", draft_dev.upper())
        self.assertIn("Cognizant", draft_dev)
        self.assertIn("PostgreSQL", draft_dev)
        self.assertIn("healthcare", draft_dev.lower())
        self.assertNotIn("MBA", draft_dev)
        self.assertNotIn("Tally", draft_dev)

        # 4. Verify ZERO generic boilerplate or placeholder text
        for draft in [draft_hr, draft_acc, draft_dev]:
            self.assertNotIn("[Company]", draft)
            self.assertNotIn("[Full Name]", draft)
            self.assertNotIn("[Degree]", draft)
            self.assertNotIn("[University / College Name]", draft)
            self.assertNotIn("Dedicated and adaptable", draft)
            self.assertNotIn("Spearheaded key workflow initiatives", draft)
            self.assertNotIn("Collaborated with cross-functional stakeholders", draft)
            self.assertNotIn("Analyzed operational bottlenecks", draft)

        # 5. Verify the 3 resumes are substantially distinct
        self.assertNotEqual(draft_hr, draft_acc)
        self.assertNotEqual(draft_hr, draft_dev)
        self.assertNotEqual(draft_acc, draft_dev)

    def test_24_three_distinct_profiles_end_to_end_verification(self):
        """
        Verify end-to-end dynamic workflow across 3 distinct candidate profiles:
        Profile A (Accountant -> Financial Analyst)
        Profile B (Teacher -> HR Executive)
        Profile C (Software Tester -> Data Analyst)
        """
        from services.ai_service import generate_career_gap_analysis
        from services.roadmap_engine import generate_dynamic_stages
        from services.job_matcher import match_jobs_for_candidate
        from services.chatbot_service import process_chatbot_query
        from services.resume_analyzer import generate_improved_resume_draft

        profile_a = {
            'name': 'Kavita Iyer',
            'full_name': 'Kavita Iyer',
            'location': 'Mumbai',
            'previous_job_title': 'Senior Accountant',
            'previous_industry': 'Corporate Finance',
            'years_of_experience': 4.0,
            'career_gap_duration': '3 years',
            'gap_reason': 'Maternity and Childcare',
            'skills': 'Tally Prime, GST, Balance Sheet Reconciliation, Financial Statements',
            'qualification': 'Master of Commerce (M.Com)',
            'target_role': 'Financial Analyst',
            'desired_career_direction': 'Financial Analyst',
            'work_mode_preference': 'Hybrid',
            'profile_completed': 1
        }

        profile_b = {
            'name': 'Sunita Menon',
            'full_name': 'Sunita Menon',
            'location': 'Delhi NCR',
            'previous_job_title': 'Senior Secondary Teacher',
            'previous_industry': 'Education',
            'years_of_experience': 6.0,
            'career_gap_duration': '4 years',
            'gap_reason': 'Family Relocation',
            'skills': 'Curriculum Design, Student Mentorship, Public Speaking, Administration',
            'qualification': 'Master of Arts (M.A.) in English',
            'target_role': 'HR Executive',
            'desired_career_direction': 'HR Executive',
            'work_mode_preference': 'On-site',
            'profile_completed': 1
        }

        profile_c = {
            'name': 'Divya Reddy',
            'full_name': 'Divya Reddy',
            'location': 'Hyderabad',
            'previous_job_title': 'Software QA Engineer',
            'previous_industry': 'Information Technology',
            'years_of_experience': 3.0,
            'career_gap_duration': '2 years',
            'gap_reason': 'Personal Health Recovery',
            'skills': 'Manual Testing, SQL, Jira, Defect Lifecycle, Python Basics',
            'qualification': 'B.Tech in Information Technology',
            'target_role': 'Data Analyst',
            'desired_career_direction': 'Data Analyst',
            'work_mode_preference': 'Remote',
            'profile_completed': 1
        }

        # 1. Verify Career Analysis is completely different
        analysis_a = generate_career_gap_analysis(profile_a, 'EXPERIENCED_GAP')
        analysis_b = generate_career_gap_analysis(profile_b, 'CAREER_SHIFT')
        analysis_c = generate_career_gap_analysis(profile_c, 'CAREER_SHIFT')

        self.assertIn("Financial Analyst", analysis_a['current_position_analysis'])
        self.assertIn("Corporate Finance", analysis_a['current_position_analysis'])
        self.assertIn("HR Executive", analysis_b['current_position_analysis'])
        self.assertIn("Education", analysis_b['current_position_analysis'])
        self.assertIn("Data Analyst", analysis_c['current_position_analysis'])
        self.assertIn("Information Technology", analysis_c['current_position_analysis'])

        # 2. Verify Skill Gaps are distinct
        self.assertNotEqual(analysis_a['skill_gaps'], analysis_b['skill_gaps'])
        self.assertNotEqual(analysis_b['skill_gaps'], analysis_c['skill_gaps'])

        # 3. Verify Dynamic Roadmap Stages are distinct
        stages_a = generate_dynamic_stages(profile_a, 'EXPERIENCED_GAP')
        stages_b = generate_dynamic_stages(profile_b, 'CAREER_SHIFT')
        stages_c = generate_dynamic_stages(profile_c, 'CAREER_SHIFT')

        self.assertIn("Financial Analyst", stages_a[0]['title'])
        self.assertIn("Teacher", stages_b[0]['title'])
        self.assertIn("Software QA Engineer", stages_c[0]['title'])

        # 4. Verify Chatbot responses for "What should I learn?" are distinct
        chat_a = process_chatbot_query('What should I learn?', profile_a)
        chat_b = process_chatbot_query('What should I learn?', profile_b)
        chat_c = process_chatbot_query('What should I learn?', profile_c)

        self.assertIn("Financial Analyst", chat_a['reply'])
        self.assertIn("HR Executive", chat_b['reply'])
        self.assertIn("Data Analyst", chat_c['reply'])
        self.assertNotEqual(chat_a['reply'], chat_b['reply'])
        self.assertNotEqual(chat_b['reply'], chat_c['reply'])

        # 5. Verify Chatbot responses for "How to explain career gap?" are distinct
        gap_a = process_chatbot_query('How should I explain my career gap?', profile_a)
        gap_b = process_chatbot_query('How should I explain my career gap?', profile_b)
        gap_c = process_chatbot_query('How should I explain my career gap?', profile_c)

        self.assertIn("3 years", gap_a['reply'])
        self.assertIn("4 years", gap_b['reply'])
        self.assertIn("2 years", gap_c['reply'])

    def test_25_chatbot_intent_classification_and_routing(self):
        """Chatbot must classify user intent and route away from Resume Analysis for non-resume queries."""
        sample_profile = {
            'full_name': 'Ananya Sen',
            'education': 'B.Tech Computer Science',
            'qualification': 'B.Tech',
            'previous_job_title': 'Software Engineer',
            'years_of_experience': 3.0,
            'career_gap_duration': '2 - 3 years',
            'gap_reason': 'Maternity & Childcare',
            'skills': 'Python, SQL, HTML, CSS',
            'target_role': 'Full Stack Engineer',
            'desired_career_direction': 'Full Stack Engineer',
            'work_mode_preference': 'Hybrid',
            'profile_completed': 1,
            'latest_resume': {'original_filename': 'Ananya_Sen_Resume.pdf'},
            'latest_analysis': {
                'match_score': 82,
                'strengths': ['Python', 'SQL', 'Database design'],
                'missing_skills': ['React', 'Node.js', 'Docker'],
                'suggestions': ['Add a modern React project to demonstrate full-stack integration.']
            }
        }

        # 1. "Please suggest me to choose startup or job" -> Career decision support
        q1 = process_chatbot_query("Please suggest me to choose startup or job", sample_profile)
        self.assertEqual(q1['category'], 'Career Decision Support')
        self.assertNotIn("Resume Analysis Summary", q1['reply'])
        self.assertNotIn("Target Role Match", q1['reply'])
        self.assertIn("Startup vs. Corporate", q1['reply'])

        # 2. "Analyze my resume" -> Resume analysis
        q2 = process_chatbot_query("Analyze my resume", sample_profile)
        self.assertEqual(q2['category'], 'Resume Feedback')
        self.assertIn("Resume Analysis Summary", q2['reply'])
        self.assertIn("82%", q2['reply'])

        # 3. "What skills should I learn for my target role?" -> Skill-gap / learning guidance
        q3 = process_chatbot_query("What skills should I learn for my target role?", sample_profile)
        self.assertEqual(q3['category'], 'Personalized Learning')
        self.assertNotIn("Resume Analysis Summary", q3['reply'])
        self.assertIn("Recommended Learning Priorities", q3['reply'])

        # 4. "Create a roadmap for me" -> Dynamic roadmap
        q4 = process_chatbot_query("Create a roadmap for me", sample_profile)
        self.assertEqual(q4['category'], 'Roadmap Guidance')
        self.assertNotIn("Resume Analysis Summary", q4['reply'])
        self.assertIn("Roadmap Progress", q4['reply'])

        # 5. "What jobs are suitable for me?" -> Dynamic job matching/search
        q5 = process_chatbot_query("What jobs are suitable for me?", sample_profile)
        self.assertEqual(q5['category'], 'Role Matching')
        self.assertNotIn("Resume Analysis Summary", q5['reply'])
        self.assertIn("Recommended Target Roles", q5['reply'])

        # 6. "How should I explain my career gap?" -> Career-gap guidance
        q6 = process_chatbot_query("How should I explain my career gap?", sample_profile)
        self.assertEqual(q6['category'], 'Career Gap Strategy')
        self.assertNotIn("Resume Analysis Summary", q6['reply'])
        self.assertIn("How to Frame a Career Gap", q6['reply'])

        # 7. "Generate my updated resume" -> Resume generation
        q7 = process_chatbot_query("Generate my updated resume", sample_profile)
        self.assertEqual(q7['category'], 'Resume Generation')
        self.assertNotIn("Resume Analysis Summary", q7['reply'])
        self.assertIn(".docx", q7['reply'])

        # 8. "How should I prepare for an interview?" -> Interview guidance
        q8 = process_chatbot_query("How should I prepare for an interview?", sample_profile)
        self.assertEqual(q8['category'], 'Interview Prep')
        self.assertNotIn("Resume Analysis Summary", q8['reply'])
        self.assertIn("Interview Preparation Strategy", q8['reply'])

        # 9. "Hello" -> Normal conversational greeting
        q9 = process_chatbot_query("Hello", sample_profile)
        self.assertEqual(q9['category'], 'Greeting')
        self.assertNotIn("Resume Analysis Summary", q9['reply'])
        self.assertIn("Hello Ananya Sen!", q9['reply'])

        # 10. "What should I do next in my career?" -> Personalized career guidance
        q10 = process_chatbot_query("What should I do next in my career?", sample_profile)
        self.assertEqual(q10['category'], 'Career Guidance')
        self.assertNotIn("Resume Analysis Summary", q10['reply'])
        self.assertIn("Personalized Career Direction", q10['reply'])

    def test_26_module1_keyword_transparency_and_docx_generation(self):
        """Module 1: Verify role keyword transparency, genuine docx generation, and zero skill fabrication."""
        from services.resume_analyzer import generate_updated_resume_docx

        sample_resume = """
        Pooja Nambiar
        Bangalore | pooja.ai@example.com | 9876543210
        
        SUMMARY
        Machine learning practitioner with 3 years experience building NLP models.
        
        EXPERIENCE
        Infosys | ML Engineer | 2019 - 2022
        - Trained transformer-based classification models using PyTorch and Hugging Face.
        - Built automated data preprocessing pipelines using Python and Pandas.
        - Deployed inference endpoints using Docker.
        
        EDUCATION
        B.Tech in Information Technology | 2019
        
        SKILLS
        Python, PyTorch, Hugging Face, Transformers, NLP, Pandas, Docker
        """

        profile_data = {
            'full_name': 'Pooja Nambiar',
            'location': 'Bangalore',
            'previous_job_title': 'ML Engineer',
            'previous_industry': 'IT Services',
            'years_of_experience': 3.0,
            'career_gap_duration': '2 years',
            'gap_reason': 'Maternity & Child Care',
            'qualification': 'B.Tech in Information Technology',
            'skills': 'Python, PyTorch, Hugging Face, Transformers, NLP, Pandas, Docker',
            'target_role': 'AI Developer'
        }

        analysis = analyze_resume_text(sample_resume, target_role="AI Developer", profile_data=profile_data)

        # 1. Verify Keyword Transparency outputs
        self.assertIn('found_keywords', analysis)
        self.assertIn('emphasized_keywords', analysis)
        self.assertIn('missing_keywords', analysis)
        self.assertIn('missing_keywords_reasons', analysis)
        self.assertIn('unsupported_keywords', analysis)

        # Pytorch / NLP / Python should be found
        found_lower = [k.lower() for k in analysis['found_keywords']]
        self.assertTrue(any("python" in k or "pytorch" in k or "nlp" in k for k in found_lower))

        # Missing keywords must have explanations
        self.assertGreater(len(analysis['missing_keywords']), 0)
        for kw in analysis['missing_keywords']:
            self.assertIn(kw, analysis['missing_keywords_reasons'])
            self.assertGreater(len(analysis['missing_keywords_reasons'][kw]), 10)

        # Unsupported keywords must NOT be added to enhanced draft (Zero Fabrication)
        for unsupp in analysis['unsupported_keywords']:
            # unsupp should not appear in candidate skills or experience if not in original profile
            if unsupp.lower() not in sample_resume.lower():
                self.assertNotIn(f"• {unsupp}", analysis['enhanced_resume_text'])

        # 2. Verify ATS Match Score breakdown
        self.assertGreaterEqual(analysis['match_score'], 50)
        self.assertLessEqual(analysis['match_score'], 100)
        self.assertIn("Score Breakdown", analysis['score_explanation'])
        self.assertIn("Role Keyword Alignment", analysis['score_explanation'])

        # 3. Verify .docx generation programmatically
        docx_path = os.path.join(app.config['UPLOAD_FOLDER'], 'updated_resumes', 'test_pooja_resume.docx')
        generate_updated_resume_docx(
            sample_resume, profile_data, 'AI Developer', docx_path, analysis['enhanced_resume_text']
        )
        self.assertTrue(os.path.exists(docx_path))
        self.assertTrue(docx_path.endswith('.docx'))
        self.assertGreater(os.path.getsize(docx_path), 5000)

        # Verify docx content matches user data
        import docx
        doc = docx.Document(docx_path)
        full_doc_text = " ".join([p.text for p in doc.paragraphs])
        self.assertIn("POOJA NAMBIAR", full_doc_text.upper())
        self.assertIn("ML ENGINEER", full_doc_text.upper())
        self.assertIn("PYTORCH", full_doc_text.upper())
        self.assertIn("CAREER BREAK", full_doc_text.upper())

    def test_27_module2_dynamic_roadmap_evaluation_and_progression(self):
        """Module 2: Verify dynamic roadmap stage tests, passing threshold unlocking, and attempt persistence."""
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email = 'eval.candidate@example.com'")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, full_name, is_active) VALUES (?, ?, 'USER', ?, 1)",
            ('eval.candidate@example.com', hash_password('Password123!'), 'Kavita Iyer')
        )
        user_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO profiles (
                user_id, location, previous_job_title, years_of_experience,
                career_gap_duration, gap_reason, qualification, skills, desired_career_direction,
                profile_completed
            ) VALUES (?, 'Chennai', 'Data Analyst', 3.0, '3 years', 'Childcare', 'B.Sc Statistics', 'SQL, Excel, Tableau, Python', 'Data Scientist', 1)
        """, (user_id,))
        cursor.execute("INSERT INTO career_selections (user_id, pathway) VALUES (?, 'EXPERIENCED_GAP')", (user_id,))
        conn.commit()
        conn.close()

        # Login
        self.client.post('/login', data={
            'email': 'eval.candidate@example.com',
            'password': 'Password123!'
        })

        # 1. Fetch Stage 1 Test via API
        test_resp = self.client.get('/api/roadmap/stage-test/1')
        self.assertEqual(test_resp.status_code, 200)
        test_data = json.loads(test_resp.data)
        self.assertTrue(test_data['success'])
        self.assertEqual(test_data['stage_number'], 1)
        self.assertGreaterEqual(len(test_data['questions']), 3)
        self.assertEqual(test_data['passing_score'], 70.0)

        # 2. Submit FAILING answers (all wrong indices or empty)
        fail_sub = {
            'stage_number': 1,
            'answers': {0: 99, 1: 99, 2: 99}
        }
        fail_resp = self.client.post('/api/roadmap/evaluate-stage',
            data=json.dumps(fail_sub),
            content_type='application/json'
        )
        self.assertEqual(fail_resp.status_code, 200)
        fail_data = json.loads(fail_resp.data)
        self.assertFalse(fail_data['passed'])
        self.assertLess(fail_data['score'], 70.0)
        self.assertGreater(len(fail_data['weak_topics']), 0)
        self.assertGreater(len(fail_data['recommendations']), 0)

        # Verify Stage 2 remains locked in roadmap view
        roadmap_resp = self.client.get('/roadmap')
        self.assertEqual(roadmap_resp.status_code, 200)
        self.assertIn(b"Locked", roadmap_resp.data)

        # 3. Submit PASSING answers by answering correctly
        # Fetch question keys and evaluate dynamically
        from services.roadmap_engine import get_or_create_user_roadmap, evaluate_stage_test
        rm = get_or_create_user_roadmap(user_id)
        stage1 = rm['stages'][0]
        correct_answers = {}
        for idx, q in enumerate(stage1.get('test', [])):
            correct_answers[q['id']] = q['correct_index']

        pass_resp = self.client.post('/api/roadmap/evaluate-stage',
            data=json.dumps({'stage_number': 1, 'answers': correct_answers}),
            content_type='application/json'
        )
        self.assertEqual(pass_resp.status_code, 200)
        pass_data = json.loads(pass_resp.data)
        self.assertTrue(pass_data['passed'])
        self.assertGreaterEqual(pass_data['score'], 70.0)
        self.assertEqual(pass_data['next_stage'], 2)

        # 4. Verify evaluation attempt history persisted in DB
        conn = get_db_connection()
        evals = conn.execute("SELECT * FROM roadmap_stage_evaluations WHERE user_id = ? ORDER BY id ASC", (user_id,)).fetchall()
        conn.close()
        self.assertEqual(len(evals), 2)  # Attempt 1 (failed) and Attempt 2 (passed)
        self.assertEqual(evals[0]['passed'], 0)
        self.assertEqual(evals[1]['passed'], 1)

        # 5. Verify Stage 2 is now unlocked
        roadmap_resp2 = self.client.get('/roadmap')
        self.assertEqual(roadmap_resp2.status_code, 200)
        self.assertIn(b"In Progress", roadmap_resp2.data)

    def test_28_chatbot_robust_relevance_and_government_job_intent(self):
        """Verify that 'suggest me governjob' and common returnee queries receive deeply relevant responses."""
        profile = {
            'name': 'subbu',
            'full_name': 'subbu',
            'target_role': 'developer',
            'previous_job_title': 'software developer',
            'years_of_experience': 2.0,
            'career_gap_duration': '2 years',
            'gap_reason': 'Family Care',
            'qualification': 'B.Tech Computer Science',
            'skills': 'Python, SQL, HTML'
        }

        # 1. "suggest me governjob" -> Government Schemes & Jobs
        r1 = process_chatbot_query("suggest me governjob", profile)
        self.assertEqual(r1['category'], 'Government Schemes')
        self.assertIn("Government Jobs", r1['reply'])
        self.assertIn("Banking Sector", r1['reply'])
        self.assertIn("/government/hub", r1['reply'])
        self.assertNotIn("How can I support your career journey today?", r1['reply'])

        # 2. "suggest me govt jobs" -> Government Schemes & Jobs
        r2 = process_chatbot_query("suggest me govt jobs", profile)
        self.assertEqual(r2['category'], 'Government Schemes')

        # 3. "suggest me job" -> Role Matching
        r3 = process_chatbot_query("suggest me job", profile)
        self.assertEqual(r3['category'], 'Role Matching')
        self.assertIn("/explore", r3['reply'])

        # 4. "How are recruiters verified?" (Built-in chip) -> Platform Trust & Verification
        r4 = process_chatbot_query("How are recruiters verified?", profile)
        self.assertEqual(r4['category'], 'Platform Trust & Verification')
        self.assertIn("Verification", r4['reply'])

        # 5. "remote work options" -> Flexible & Remote Work
        r5 = process_chatbot_query("remote work options", profile)
        self.assertEqual(r5['category'], 'Flexible & Remote Work')
        self.assertIn("Remote", r5['reply'])

        # 6. Fallback never uses irrelevant canned greeting
        r6 = process_chatbot_query("tell me something unique about my transition", profile)
        self.assertEqual(r6['category'], 'Career Guidance')
        self.assertIn("developer", r6['reply'].lower())
        self.assertNotIn("How can I support your career journey today?", r6['reply'])

if __name__ == '__main__':
    unittest.main()




