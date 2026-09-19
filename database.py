import sqlite3
import os
from config import Config

def get_db_connection():
    """Returns a SQLite connection with row factory enabled, WAL journal mode, and 30s busy timeout."""
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

def init_db():
    """Initializes database schema and ensures upload directory exists."""
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    db_dir = os.path.dirname(Config.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('USER', 'RECRUITER', 'ADMIN')),
            full_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    ''')

    # Profiles Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            location TEXT,
            education TEXT,
            qualification TEXT,
            graduation_year INTEGER,
            skills TEXT,
            preferred_work_location TEXT,
            work_mode_preference TEXT,
            previous_job_title TEXT,
            years_of_experience REAL DEFAULT 0,
            career_gap_duration TEXT,
            gap_reason TEXT,
            previous_industry TEXT,
            current_skills TEXT,
            desired_career_direction TEXT,
            preferences_sector TEXT,
            profile_completed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Career Selections
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS career_selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            pathway TEXT NOT NULL CHECK(pathway IN ('EXPERIENCED_GAP', 'NO_EXPERIENCE', 'CAREER_SHIFT')),
            sub_direction TEXT,
            selected_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User Roadmaps
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            pathway TEXT NOT NULL,
            current_stage INTEGER DEFAULT 1,
            total_stages INTEGER DEFAULT 7,
            completion_percentage INTEGER DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Roadmap Tasks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roadmap_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL REFERENCES user_roadmaps(id) ON DELETE CASCADE,
            stage_number INTEGER NOT NULL,
            stage_title TEXT NOT NULL,
            task_key TEXT NOT NULL,
            task_description TEXT NOT NULL,
            resource_url TEXT,
            is_completed INTEGER DEFAULT 0,
            completed_at DATETIME
        )
    ''')

    # Resumes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            raw_text TEXT,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Resume Analyses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resume_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER UNIQUE NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_role TEXT,
            extracted_skills TEXT,
            missing_keywords TEXT,
            missing_sections TEXT,
            action_verbs_analysis TEXT,
            gap_presentation_advice TEXT,
            format_issues TEXT,
            role_alignment_feedback TEXT,
            suggested_bullet_points TEXT,
            enhanced_resume_text TEXT,
            analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Recruiters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recruiters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recruiter_name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            official_company_email TEXT NOT NULL,
            company_website TEXT,
            company_description TEXT,
            designation TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            verification_notes TEXT,
            verified_at DATETIME,
            verified_by INTEGER REFERENCES users(id)
        )
    ''')

    # Jobs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter_id INTEGER REFERENCES recruiters(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            company_name TEXT NOT NULL,
            location TEXT NOT NULL,
            work_mode TEXT NOT NULL CHECK(work_mode IN ('Remote', 'Hybrid', 'On-site')),
            experience_required TEXT NOT NULL,
            skills_required TEXT NOT NULL,
            qualification_required TEXT NOT NULL,
            salary_range TEXT,
            description TEXT NOT NULL,
            application_deadline DATE,
            application_method TEXT NOT NULL,
            source_type TEXT NOT NULL CHECK(source_type IN ('VERIFIED_RECRUITER', 'PLATFORM_REVIEWED', 'GOVERNMENT_SOURCE', 'EXTERNAL_SOURCE')),
            source_name TEXT NOT NULL,
            source_url TEXT,
            approval_status TEXT DEFAULT 'APPROVED' CHECK(approval_status IN ('PENDING', 'APPROVED', 'REJECTED')),
            rejection_notes TEXT,
            is_active INTEGER DEFAULT 1,
            posted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Government Opportunities
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS government_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            sector TEXT NOT NULL,
            state TEXT NOT NULL,
            location TEXT NOT NULL,
            qualification TEXT NOT NULL,
            age_criteria TEXT,
            category_criteria TEXT,
            job_type TEXT NOT NULL,
            application_status TEXT NOT NULL,
            deadline DATE,
            eligibility_details TEXT NOT NULL,
            selection_process TEXT NOT NULL,
            required_documents TEXT NOT NULL,
            official_portal_url TEXT NOT NULL,
            is_verified INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Learning Resources
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('Career Skills', 'Technical Skills', 'Soft Skills', 'Interview Preparation', 'Resume Preparation', 'Entrepreneurship', 'Government Exam Preparation')),
            provider TEXT NOT NULL,
            description TEXT NOT NULL,
            url TEXT NOT NULL,
            duration_estimate TEXT,
            cost_type TEXT DEFAULT 'Free',
            skill_level TEXT DEFAULT 'Beginner to Intermediate',
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Startup Ideas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS startup_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            business_name TEXT,
            problem_statement TEXT NOT NULL,
            solution_description TEXT NOT NULL,
            target_users TEXT NOT NULL,
            skills_available TEXT NOT NULL,
            budget_range TEXT NOT NULL,
            location TEXT NOT NULL,
            problem_clarity_score TEXT,
            suggested_business_model TEXT,
            mvp_steps TEXT,
            relevant_schemes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User Bookmarks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_type TEXT NOT NULL CHECK(item_type IN ('JOB', 'GOVERNMENT', 'LEARNING')),
            item_id INTEGER NOT NULL,
            notes TEXT,
            saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, item_type, item_id)
        )
    ''')

    # Job Applications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            resume_id INTEGER REFERENCES resumes(id),
            cover_note TEXT,
            status TEXT DEFAULT 'Submitted' CHECK(status IN ('Submitted', 'Under Review', 'Shortlisted', 'Closed')),
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Chat Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            session_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            context_category TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Admin Audit Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL REFERENCES users(id),
            action_type TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Career Gap Analyses (Persists AI Gap Analysis & Roadmaps)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS career_gap_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_role TEXT,
            readiness_level TEXT,
            career_analysis TEXT,
            skill_gaps TEXT,
            suggested_roles TEXT,
            roadmap_plan TEXT,
            learning_recommendations TEXT,
            resume_advice TEXT,
            interview_prep TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Notifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT,
            is_read INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Roadmap Stage Evaluations (Module 2: Stage Tests & Adaptive Progression)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roadmap_stage_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL REFERENCES user_roadmaps(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stage_number INTEGER NOT NULL,
            score REAL NOT NULL,
            passing_score REAL DEFAULT 70.0,
            passed INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL,
            weak_topics TEXT,
            explanation_summary TEXT,
            attempt_number INTEGER DEFAULT 1,
            submitted_answers TEXT,
            evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ensure schema migrations for existing jobs table
    cursor.execute("PRAGMA table_info(jobs)")
    job_columns = [row[1] for row in cursor.fetchall()]
    if 'approval_status' not in job_columns:
        cursor.execute("ALTER TABLE jobs ADD COLUMN approval_status TEXT DEFAULT 'APPROVED'")
    if 'rejection_notes' not in job_columns:
        cursor.execute("ALTER TABLE jobs ADD COLUMN rejection_notes TEXT")

    # Ensure schema migrations for profiles table (new personalization fields)
    cursor.execute("PRAGMA table_info(profiles)")
    profile_columns = [row[1] for row in cursor.fetchall()]
    if 'career_goal' not in profile_columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN career_goal TEXT")
    if 'learning_preference' not in profile_columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN learning_preference TEXT DEFAULT 'Self-paced'")
    if 'cost_preference' not in profile_columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN cost_preference TEXT DEFAULT 'Free Only'")
    if 'target_role' not in profile_columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN target_role TEXT")

    # Ensure schema migrations for career_gap_analyses table
    cursor.execute("PRAGMA table_info(career_gap_analyses)")
    gap_columns = [row[1] for row in cursor.fetchall()]
    if 'readiness_score' not in gap_columns:
        cursor.execute("ALTER TABLE career_gap_analyses ADD COLUMN readiness_score INTEGER DEFAULT 0")

    # Ensure schema migrations for resume_analyses table (updated resume generation & keyword transparency)
    cursor.execute("PRAGMA table_info(resume_analyses)")
    resume_analysis_cols = [row[1] for row in cursor.fetchall()]
    if 'updated_resume_docx_path' not in resume_analysis_cols:
        cursor.execute("ALTER TABLE resume_analyses ADD COLUMN updated_resume_docx_path TEXT")
    if 'updated_resume_text' not in resume_analysis_cols:
        cursor.execute("ALTER TABLE resume_analyses ADD COLUMN updated_resume_text TEXT")
    if 'updated_at' not in resume_analysis_cols:
        cursor.execute("ALTER TABLE resume_analyses ADD COLUMN updated_at DATETIME")
    if 'match_score' not in resume_analysis_cols:
        cursor.execute("ALTER TABLE resume_analyses ADD COLUMN match_score INTEGER DEFAULT 0")
    if 'score_explanation' not in resume_analysis_cols:
        cursor.execute("ALTER TABLE resume_analyses ADD COLUMN score_explanation TEXT")
    if 'emphasized_keywords' not in resume_analysis_cols:
        cursor.execute("ALTER TABLE resume_analyses ADD COLUMN emphasized_keywords TEXT")
    if 'missing_keywords_reasons' not in resume_analysis_cols:
        cursor.execute("ALTER TABLE resume_analyses ADD COLUMN missing_keywords_reasons TEXT")
    if 'unsupported_keywords' not in resume_analysis_cols:
        cursor.execute("ALTER TABLE resume_analyses ADD COLUMN unsupported_keywords TEXT")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
