import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g, send_file, Response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database import get_db_connection, init_db
from services.auth_service import (
    get_current_user, login_required, role_required, hash_password, verify_password
)
from services.resume_analyzer import (
    extract_text_from_file, analyze_resume_text, generate_updated_resume_docx, parse_resume_data
)
from services.roadmap_engine import get_or_create_user_roadmap, toggle_task_status
from services.startup_analyzer import analyze_startup_idea
from services.chatbot_service import process_chatbot_query
from services.ai_service import (
    generate_career_gap_analysis, get_complete_user_context, generate_updated_resume_ai
)
from services.job_matcher import match_jobs_for_candidate
from services.notification_service import (
    create_notification, get_user_notifications, get_unread_notification_count,
    mark_notification_as_read, mark_all_notifications_as_read
)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database tables if not existing
init_db()

@app.before_request
def load_user_context():
    g.current_user = get_current_user()

@app.context_processor
def inject_global_variables():
    unread_notifs = 0
    if g.current_user and g.current_user.get('user'):
        try:
            unread_notifs = get_unread_notification_count(g.current_user['user']['id'])
        except Exception:
            unread_notifs = 0

    return {
        'current_user': g.current_user,
        'current_year': datetime.now().year,
        'unread_notifications_count': unread_notifs
    }

# ==============================================================================
# 1. PUBLIC ROUTES & LANDING PAGE
# ==============================================================================

@app.route('/')
def landing():
    return render_template('index.html')

@app.route('/explore')
def explore_opportunities():
    conn = get_db_connection()
    work_mode = request.args.get('work_mode', '').strip()
    source_type = request.args.get('source', '').strip()
    query = request.args.get('q', '').strip()

    sql = "SELECT * FROM jobs WHERE is_active = 1 AND approval_status = 'APPROVED'"
    params = []

    if work_mode:
        sql += " AND work_mode = ?"
        params.append(work_mode)
    if source_type:
        sql += " AND source_type = ?"
        params.append(source_type)
    if query:
        sql += " AND (title LIKE ? OR skills_required LIKE ? OR description LIKE ?)"
        q_term = f"%{query}%"
        params.extend([q_term, q_term, q_term])

    sql += " ORDER BY posted_at DESC"
    jobs_raw = conn.execute(sql, params).fetchall()

    saved_job_ids = set()
    if g.current_user and g.current_user.get('user'):
        u_id = g.current_user['user']['id']
        s_rows = conn.execute("SELECT item_id FROM user_bookmarks WHERE user_id = ? AND item_type = 'JOB'", (u_id,)).fetchall()
        saved_job_ids = set(r['item_id'] for r in s_rows)
        jobs = match_jobs_for_candidate(jobs_raw, g.current_user.get('profile'))
    else:
        jobs = [dict(j) for j in jobs_raw]

    conn.close()
    return render_template('explore/index.html', jobs=jobs, saved_job_ids=saved_job_ids)

@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        flash("The requested opportunity is not available or has been removed.", "warning")
        return redirect(url_for('explore_opportunities'))

    is_saved = False
    has_applied = False
    if g.current_user and g.current_user.get('user'):
        u_id = g.current_user['user']['id']
        b_row = conn.execute("SELECT id FROM user_bookmarks WHERE user_id = ? AND item_type = 'JOB' AND item_id = ?", (u_id, job_id)).fetchone()
        is_saved = bool(b_row)
        app_row = conn.execute("SELECT id, status, applied_at FROM job_applications WHERE user_id = ? AND job_id = ?", (u_id, job_id)).fetchone()
        has_applied = dict(app_row) if app_row else None

    conn.close()
    return render_template('explore/job_detail.html', job=job, is_saved=is_saved, has_applied=has_applied)

@app.route('/learning')
def learning_catalog():
    conn = get_db_connection()
    category = request.args.get('category', '').strip()
    query = request.args.get('q', '').strip()
    
    categories = [
        'Career Skills', 'Technical Skills', 'Soft Skills', 
        'Interview Preparation', 'Resume Preparation', 
        'Entrepreneurship', 'Government Exam Preparation'
    ]

    sql = "SELECT * FROM learning_resources WHERE is_active = 1"
    params = []

    if category and category in categories:
        sql += " AND category = ?"
        params.append(category)

    if query:
        sql += " AND (title LIKE ? OR description LIKE ? OR provider LIKE ?)"
        q_term = f"%{query}%"
        params.extend([q_term, q_term, q_term])

    sql += " ORDER BY id ASC"
    resources = conn.execute(sql, params).fetchall()

    saved_learning_ids = set()
    if g.current_user and g.current_user.get('user'):
        u_id = g.current_user['user']['id']
        s_rows = conn.execute("SELECT item_id FROM user_bookmarks WHERE user_id = ? AND item_type = 'LEARNING'", (u_id,)).fetchall()
        saved_learning_ids = set(r['item_id'] for r in s_rows)

    conn.close()
    return render_template(
        'learning/index.html',
        resources=resources,
        categories=categories,
        current_category=category,
        search_query=query,
        saved_learning_ids=saved_learning_ids
    )

# ==============================================================================
# 2. AUTHENTICATION (USER, RECRUITER, ADMIN)
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
@app.route('/login/user', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and verify_password(user['password_hash'], password):
            if user['is_active'] != 1:
                conn.close()
                flash("This account is currently deactivated. Please contact support.", "danger")
                return render_template('auth/login.html')

            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_name'] = user['full_name']

            conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
            conn.commit()
            conn.close()

            flash(f"Welcome back, {user['full_name']}!", "success")
            
            # Role-based redirection
            if user['role'] == 'RECRUITER':
                return redirect(url_for('recruiter_dashboard'))
            elif user['role'] == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            conn.close()
            flash("Invalid email address or password.", "danger")

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def auth_register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name or not email or not password:
            flash("All fields are required.", "warning")
            return render_template('auth/register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "warning")
            return render_template('auth/register.html')

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "warning")
            return render_template('auth/register.html')

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email address already exists. Please sign in.", "warning")
            return redirect(url_for('auth_login'))

        # Create user with role 'USER'
        hashed = hash_password(password)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, full_name, is_active) VALUES (?, ?, 'USER', ?, 1)",
            (email, hashed, full_name)
        )
        user_id = cursor.lastrowid

        # Create initial empty profile
        cursor.execute(
            "INSERT INTO profiles (user_id, profile_completed) VALUES (?, 0)",
            (user_id,)
        )
        conn.commit()
        conn.close()

        # Establish session and redirect user to "Complete Your Profile"
        session['user_id'] = user_id
        session['user_role'] = 'USER'
        session['user_name'] = full_name

        flash("Account created! Please complete your re-entry profile.", "success")
        return redirect(url_for('complete_profile'))

    return render_template('auth/register.html')

@app.route('/recruiter/login', methods=['GET', 'POST'])
@app.route('/login/recruiter', methods=['GET', 'POST'])
def recruiter_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'RECRUITER'", (email,)).fetchone()

        if user and verify_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_role'] = 'RECRUITER'
            session['user_name'] = user['full_name']
            conn.close()
            flash(f"Welcome to the Recruiter Portal, {user['full_name']}.", "success")
            return redirect(url_for('recruiter_dashboard'))
        else:
            conn.close()
            flash("Invalid corporate email or password.", "danger")

    return render_template('auth/recruiter_login.html')

@app.route('/recruiter/register', methods=['GET', 'POST'])
def recruiter_register():
    if request.method == 'POST':
        recruiter_name = request.form.get('recruiter_name', '').strip()
        company_name = request.form.get('company_name', '').strip()
        official_company_email = request.form.get('official_company_email', '').strip().lower()
        company_website = request.form.get('company_website', '').strip()
        designation = request.form.get('designation', '').strip()
        company_description = request.form.get('company_description', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not recruiter_name or not company_name or not official_company_email or not password:
            flash("Please fill in all required company and recruiter details.", "warning")
            return render_template('auth/recruiter_register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "warning")
            return render_template('auth/recruiter_register.html')

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (official_company_email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this corporate email is already registered.", "warning")
            return redirect(url_for('recruiter_login'))

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, role, full_name, is_active) VALUES (?, ?, 'RECRUITER', ?, 1)",
            (official_company_email, hash_password(password), recruiter_name)
        )
        user_id = cursor.lastrowid

        # Recruiter record with is_verified = 0 (Pending Admin Verification)
        cursor.execute('''
            INSERT INTO recruiters (
                user_id, recruiter_name, company_name, official_company_email,
                company_website, company_description, designation, is_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        ''', (user_id, recruiter_name, company_name, official_company_email, company_website, company_description, designation))
        conn.commit()
        conn.close()

        session['user_id'] = user_id
        session['user_role'] = 'RECRUITER'
        session['user_name'] = recruiter_name

        flash("Recruiter registration submitted. Your account is pending domain verification.", "info")
        return redirect(url_for('recruiter_dashboard'))

    return render_template('auth/recruiter_register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
@app.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'ADMIN'", (email,)).fetchone()

        if user and verify_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_role'] = 'ADMIN'
            session['user_name'] = user['full_name']
            conn.close()
            flash("Administrator session established.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            conn.close()
            flash("Unauthorized administrator credentials.", "danger")

    return render_template('auth/admin_login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def auth_forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        flash(f"If an account is associated with {email}, reset instructions have been logged.", "info")
        return redirect(url_for('auth_login'))
    return render_template('auth/forgot_password.html')

@app.route('/logout')
def auth_logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('landing'))

# ==============================================================================
# 3. USER PROFILE & CAREER SITUATION SELECTION
# ==============================================================================

@app.route('/profile/complete', methods=['GET', 'POST'])
@login_required
@role_required(['USER'])
def complete_profile():
    user_id = session['user_id']
    conn = get_db_connection()

    if request.method == 'POST':
        location = request.form.get('location', '').strip()
        education = request.form.get('education', '').strip()
        qualification = request.form.get('qualification', '').strip()
        graduation_year = request.form.get('graduation_year') or None
        skills = request.form.get('skills', '').strip()
        preferred_work_location = request.form.get('preferred_work_location', '').strip()
        work_mode_preference = request.form.get('work_mode_preference', 'Flexible / Any')

        previous_job_title = request.form.get('previous_job_title', '').strip()
        years_of_experience = float(request.form.get('years_of_experience', 0) or 0)
        career_gap_duration = request.form.get('career_gap_duration', '')
        gap_reason = request.form.get('gap_reason', '')
        previous_industry = request.form.get('previous_industry', '').strip()
        desired_career_direction = request.form.get('desired_career_direction', '').strip()
        preferences_sector = request.form.get('preferences_sector', 'Private')

        # New fields for better AI personalization
        career_goal = request.form.get('career_goal', '').strip()
        learning_preference = request.form.get('learning_preference', 'Self-paced')
        cost_preference = request.form.get('cost_preference', 'Free Only')
        target_role = request.form.get('target_role', '').strip()

        cursor = conn.cursor()
        cursor.execute('''
            UPDATE profiles SET
                location = ?, education = ?, qualification = ?, graduation_year = ?,
                skills = ?, preferred_work_location = ?, work_mode_preference = ?,
                previous_job_title = ?, years_of_experience = ?, career_gap_duration = ?,
                gap_reason = ?, previous_industry = ?, desired_career_direction = ?,
                preferences_sector = ?, career_goal = ?, learning_preference = ?,
                cost_preference = ?, target_role = ?,
                profile_completed = 1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            location, education, qualification, graduation_year, skills,
            preferred_work_location, work_mode_preference, previous_job_title,
            years_of_experience, career_gap_duration, gap_reason, previous_industry,
            desired_career_direction, preferences_sector, career_goal,
            learning_preference, cost_preference, target_role, user_id
        ))
        conn.commit()
        conn.close()

        # Dynamically regenerate user roadmap milestones with latest profile inputs
        try:
            from services.roadmap_engine import regenerate_user_roadmap
            regenerate_user_roadmap(user_id)
        except Exception as e:
            print(f"[Profile Update] Error refreshing roadmap: {e}")

        # Invalidate / re-generate career gap analysis with new profile data
        try:
            from services.ai_service import get_complete_user_context, generate_career_gap_analysis
            u_ctx = get_complete_user_context(user_id)
            pway = u_ctx.get('pathway', 'EXPERIENCED_GAP')
            fresh_analysis = generate_career_gap_analysis(u_ctx, pway)

            c_conn = get_db_connection()
            c_cursor = c_conn.cursor()
            c_cursor.execute('''
                INSERT INTO career_gap_analyses (
                    user_id, target_role, readiness_level, readiness_score, career_analysis,
                    skill_gaps, suggested_roles, roadmap_plan,
                    learning_recommendations, resume_advice, interview_prep
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                u_ctx.get('target_role') or 'Professional Returnee',
                fresh_analysis.get('readiness_level', 'Moderate'),
                fresh_analysis.get('readiness_score', 65),
                fresh_analysis.get('current_position_analysis', ''),
                json.dumps(fresh_analysis.get('skill_gaps', [])),
                json.dumps(fresh_analysis.get('suggested_roles', [])),
                json.dumps(fresh_analysis.get('roadmap_90_days', {})),
                json.dumps(fresh_analysis.get('learning_recommendations', [])),
                fresh_analysis.get('resume_advice', ''),
                json.dumps(fresh_analysis.get('interview_focus_areas', []))
            ))
            c_conn.commit()
            c_conn.close()
        except Exception as e:
            print(f"[Profile Update] Error refreshing career analysis: {e}")

        flash("Profile updated! Now select your career path.", "success")
        return redirect(url_for('choose_career_path'))

    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return render_template('user/complete_profile.html', profile=profile)

@app.route('/choose-path')
@login_required
@role_required(['USER'])
def choose_career_path():
    user_id = session['user_id']
    conn = get_db_connection()
    cs = conn.execute("SELECT pathway FROM career_selections WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    current_pathway = cs['pathway'] if cs else None
    return render_template('user/choose_path.html', current_pathway=current_pathway)

@app.route('/select-path', methods=['POST'])
@login_required
@role_required(['USER'])
def select_career_path():
    user_id = session['user_id']
    pathway = request.form.get('pathway')

    if pathway not in ['EXPERIENCED_GAP', 'NO_EXPERIENCE', 'CAREER_SHIFT']:
        flash("Invalid pathway selected.", "danger")
        return redirect(url_for('choose_career_path'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO career_selections (user_id, pathway)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET pathway = excluded.pathway, selected_at = CURRENT_TIMESTAMP
    ''', (user_id, pathway))
    conn.commit()
    conn.close()

    # Re-initialize roadmap for this pathway
    get_or_create_user_roadmap(user_id, pathway)

    flash("Career situation confirmed. Your personalized workspace is ready.", "success")
    if pathway == 'EXPERIENCED_GAP':
        return redirect(url_for('path_experienced'))
    elif pathway == 'NO_EXPERIENCE':
        return redirect(url_for('path_beginner'))
    else:
        return redirect(url_for('path_transition'))

# ==============================================================================
# 4. USER DASHBOARD & ROADMAP
# ==============================================================================

@app.route('/dashboard')
@login_required
@role_required(['USER'])
def user_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()

    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    cs = conn.execute("SELECT pathway FROM career_selections WHERE user_id = ?", (user_id,)).fetchone()
    pathway = cs['pathway'] if cs else 'EXPERIENCED_GAP'

    # Fetch roadmap details and next action
    roadmap_info = get_or_create_user_roadmap(user_id, pathway)

    # Fetch latest resume analysis if available
    latest_resume = conn.execute(
        "SELECT * FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()

    # Fetch or auto-generate AI Career-Gap analysis with latest profile context
    user_context = get_complete_user_context(user_id)
    current_target = user_context.get('target_role') or 'Professional Returnee'

    gap_row = conn.execute(
        "SELECT * FROM career_gap_analyses WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()

    gap_analysis = None
    if gap_row and gap_row['target_role'] == current_target:
        r_score = gap_row['readiness_score'] if 'readiness_score' in gap_row.keys() and gap_row['readiness_score'] else 0
        if not r_score:
            lvl = (gap_row['readiness_level'] or '').lower()
            if 'high' in lvl:
                r_score = 85
            elif 'moderate' in lvl:
                r_score = 65
            elif 'foundational' in lvl or 'needs' in lvl:
                r_score = 45
            else:
                r_score = 65
        gap_analysis = {
            'readiness_level': gap_row['readiness_level'],
            'readiness_score': r_score,
            'target_role': gap_row['target_role'],
            'career_analysis': gap_row['career_analysis'],
            'skill_gaps': json.loads(gap_row['skill_gaps']) if gap_row['skill_gaps'] else [],
            'suggested_roles': json.loads(gap_row['suggested_roles']) if gap_row['suggested_roles'] else [],
            'roadmap_plan': json.loads(gap_row['roadmap_plan']) if gap_row['roadmap_plan'] else {},
            'learning_recommendations': json.loads(gap_row['learning_recommendations']) if gap_row['learning_recommendations'] else [],
            'resume_advice': gap_row['resume_advice'],
            'interview_prep': json.loads(gap_row['interview_prep']) if gap_row['interview_prep'] else [],
            'updated_at': gap_row['updated_at']
        }
    elif profile and profile['profile_completed']:
        # Auto-compute fresh analysis with current user context
        try:
            computed = generate_career_gap_analysis(user_context, pathway)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO career_gap_analyses (
                    user_id, target_role, readiness_level, readiness_score, career_analysis,
                    skill_gaps, suggested_roles, roadmap_plan,
                    learning_recommendations, resume_advice, interview_prep
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                current_target,
                computed.get('readiness_level', 'Moderate'),
                computed.get('readiness_score', 65),
                computed.get('current_position_analysis', ''),
                json.dumps(computed.get('skill_gaps', [])),
                json.dumps(computed.get('suggested_roles', [])),
                json.dumps(computed.get('roadmap_90_days', {})),
                json.dumps(computed.get('learning_recommendations', [])),
                computed.get('resume_advice', ''),
                json.dumps(computed.get('interview_focus_areas', []))
            ))
            conn.commit()
            gap_analysis = computed
        except Exception as e:
            print(f"Error auto-generating gap analysis: {e}")

    # Fetch matching jobs dynamically using job_matcher
    raw_jobs = conn.execute(
        "SELECT * FROM jobs WHERE is_active = 1 AND approval_status = 'APPROVED' ORDER BY posted_at DESC"
    ).fetchall()
    ranked_jobs = match_jobs_for_candidate(raw_jobs, profile)
    matching_jobs = ranked_jobs[:4]

    # Fetch user saved bookmarks
    saved_raw = conn.execute(
        "SELECT * FROM user_bookmarks WHERE user_id = ? ORDER BY saved_at DESC", (user_id,)
    ).fetchall()
    
    saved_items = []
    saved_job_ids = set()
    for b in saved_raw:
        title = "Saved Item"
        if b['item_type'] == 'JOB':
            saved_job_ids.add(b['item_id'])
            j = conn.execute("SELECT title, company_name FROM jobs WHERE id = ?", (b['item_id'],)).fetchone()
            if j: title = f"{j['title']} ({j['company_name']})"
        elif b['item_type'] == 'GOVERNMENT':
            g_item = conn.execute("SELECT title FROM government_opportunities WHERE id = ?", (b['item_id'],)).fetchone()
            if g_item: title = g_item['title']
        elif b['item_type'] == 'LEARNING':
            l_item = conn.execute("SELECT title FROM learning_resources WHERE id = ?", (b['item_id'],)).fetchone()
            if l_item: title = l_item['title']

        saved_items.append({
            'id': b['id'],
            'item_id': b['item_id'],
            'item_type': b['item_type'],
            'title': title,
            'type_label': b['item_type'].title(),
            'saved_at': b['saved_at']
        })

    conn.close()
    return render_template(
        'user/dashboard.html',
        user=user,
        profile=profile,
        pathway=pathway,
        roadmap_info=roadmap_info,
        next_task=roadmap_info['next_task'],
        latest_resume=latest_resume,
        gap_analysis=gap_analysis,
        matching_jobs=matching_jobs,
        saved_items=saved_items,
        saved_job_ids=saved_job_ids
    )

@app.route('/career-analysis')
@login_required
@role_required(['USER'])
def career_analysis_view():
    user_id = session['user_id']
    user_context = get_complete_user_context(user_id)
    user = user_context.get('user')
    profile = user_context.get('profile')
    pathway = user_context.get('pathway', 'EXPERIENCED_GAP')
    current_target = user_context.get('target_role') or 'Professional Returnee'

    conn = get_db_connection()
    gap_row = conn.execute(
        "SELECT * FROM career_gap_analyses WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()

    analysis = None
    if gap_row and gap_row['target_role'] == current_target:
        r_score = gap_row['readiness_score'] if 'readiness_score' in gap_row.keys() and gap_row['readiness_score'] else 0
        if not r_score:
            lvl = (gap_row['readiness_level'] or '').lower()
            if 'high' in lvl:
                r_score = 85
            elif 'moderate' in lvl:
                r_score = 65
            elif 'foundational' in lvl or 'needs' in lvl:
                r_score = 45
            else:
                r_score = 65
        analysis = {
            'readiness_level': gap_row['readiness_level'],
            'readiness_score': r_score,
            'target_role': gap_row['target_role'],
            'career_analysis': gap_row['career_analysis'],
            'skill_gaps': json.loads(gap_row['skill_gaps']) if gap_row['skill_gaps'] else [],
            'suggested_roles': json.loads(gap_row['suggested_roles']) if gap_row['suggested_roles'] else [],
            'roadmap_plan': json.loads(gap_row['roadmap_plan']) if gap_row['roadmap_plan'] else {},
            'learning_recommendations': json.loads(gap_row['learning_recommendations']) if gap_row['learning_recommendations'] else [],
            'resume_advice': gap_row['resume_advice'],
            'interview_prep': json.loads(gap_row['interview_prep']) if gap_row['interview_prep'] else [],
            'updated_at': gap_row['updated_at']
        }
    elif profile and profile.get('profile_completed'):
        # Auto-compute fresh analysis with current user context
        analysis = generate_career_gap_analysis(user_context, pathway)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO career_gap_analyses (
                user_id, target_role, readiness_level, readiness_score, career_analysis,
                skill_gaps, suggested_roles, roadmap_plan,
                learning_recommendations, resume_advice, interview_prep
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            current_target,
            analysis.get('readiness_level', 'Moderate'),
            analysis.get('readiness_score', 65),
            analysis.get('current_position_analysis', ''),
            json.dumps(analysis.get('skill_gaps', [])),
            json.dumps(analysis.get('suggested_roles', [])),
            json.dumps(analysis.get('roadmap_90_days', {})),
            json.dumps(analysis.get('learning_recommendations', [])),
            analysis.get('resume_advice', ''),
            json.dumps(analysis.get('interview_focus_areas', []))
        ))
        conn.commit()

    conn.close()
    return render_template('user/career_analysis.html', user=user, profile=profile, pathway=pathway, analysis=analysis)

def _handle_analyze_gap():
    user_id = session['user_id']
    user_context = get_complete_user_context(user_id)

    if not user_context or not user_context.get('profile_completed'):
        return jsonify({'success': False, 'error': 'Please complete your profile before running Career Gap Analysis.'}), 400

    pathway = user_context.get('pathway', 'EXPERIENCED_GAP')
    analysis = generate_career_gap_analysis(user_context, pathway)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO career_gap_analyses (
            user_id, target_role, readiness_level, readiness_score, career_analysis,
            skill_gaps, suggested_roles, roadmap_plan,
            learning_recommendations, resume_advice, interview_prep
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        user_context.get('target_role') or 'Professional Returnee',
        analysis.get('readiness_level', 'Moderate'),
        analysis.get('readiness_score', 65),
        analysis.get('current_position_analysis', ''),
        json.dumps(analysis.get('skill_gaps', [])),
        json.dumps(analysis.get('suggested_roles', [])),
        json.dumps(analysis.get('roadmap_90_days', {})),
        json.dumps(analysis.get('learning_recommendations', [])),
        analysis.get('resume_advice', ''),
        json.dumps(analysis.get('interview_focus_areas', []))
    ))
    conn.commit()
    conn.close()

    create_notification(
        user_id,
        "AI Career-Gap Analysis Complete",
        "Your personalized re-entry readiness report, skill gap roadmap, and role fit recommendations have been generated.",
        url_for('career_analysis_view')
    )

    return jsonify({'success': True, 'analysis': analysis})

@app.route('/api/ai/analyze-gap', methods=['POST'], endpoint='api_ai_analyze_gap')
@login_required
@role_required(['USER'])
def api_ai_analyze_gap():
    return _handle_analyze_gap()

@app.route('/api/analyze-gap', methods=['POST'], endpoint='api_analyze_gap')
@login_required
@role_required(['USER'])
def api_analyze_gap():
    return _handle_analyze_gap()

@app.route('/notifications')
@login_required
def user_notifications():
    user_id = session['user_id']
    notifs = get_user_notifications(user_id)
    unread = get_unread_notification_count(user_id)
    return render_template('user/notifications.html', notifications=notifs, unread_count=unread)

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def api_mark_notification_read():
    user_id = session['user_id']
    notif_id = (request.get_json() or {}).get('notification_id') or request.form.get('notification_id')
    if not notif_id:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Missing notification_id'}), 400
        return redirect(url_for('user_notifications'))
    res = mark_notification_as_read(int(notif_id), user_id)
    if request.is_json:
        return jsonify({'success': res})
    return redirect(url_for('user_notifications'))

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_notifications_read():
    user_id = session['user_id']
    count = mark_all_notifications_as_read(user_id)
    if request.is_json:
        return jsonify({'success': True, 'count': count})
    return redirect(url_for('user_notifications'))

@app.route('/roadmap')
@login_required
@role_required(['USER'])
def user_roadmap():
    user_id = session['user_id']
    roadmap_info = get_or_create_user_roadmap(user_id)
    return render_template('user/roadmap.html', roadmap_info=roadmap_info)

# ==============================================================================
# 5. SPECIALIZED PATHWAYS (PATH 1, PATH 2, PATH 3)
# ==============================================================================

@app.route('/path/experienced')
@login_required
@role_required(['USER'])
def path_experienced():
    user_id = session['user_id']
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    private_jobs = conn.execute(
        "SELECT * FROM jobs WHERE is_active = 1 AND source_type = 'VERIFIED_RECRUITER' LIMIT 4"
    ).fetchall()
    conn.close()
    return render_template('user/path_experienced.html', profile=profile, private_jobs=private_jobs)

@app.route('/path/beginner')
@login_required
@role_required(['USER'])
def path_beginner():
    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return render_template('user/path_beginner.html', user=user, profile=profile)

@app.route('/path/transition')
@login_required
@role_required(['USER'])
def path_transition():
    user_id = session['user_id']
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return render_template('user/path_transition.html', profile=profile)

# ==============================================================================
# 6. RESUME HUB & ANALYSIS ENGINE
# ==============================================================================

@app.route('/resume/hub')
@login_required
@role_required(['USER'])
def resume_hub():
    user_id = session['user_id']
    user_context = get_complete_user_context(user_id)
    profile = user_context.get('profile')
    latest_resume = user_context.get('latest_resume')

    latest_analysis = None
    if latest_resume:
        conn = get_db_connection()
        analysis_row = conn.execute(
            "SELECT * FROM resume_analyses WHERE resume_id = ?", (latest_resume['id'],)
        ).fetchone()
        conn.close()
        if analysis_row:
            analysis_dict = dict(analysis_row)
            latest_analysis = {
                'target_role': analysis_dict.get('target_role'),
                'match_score': analysis_dict.get('match_score') or 75,
                'score_explanation': analysis_dict.get('score_explanation') or '',
                'sections_found': json.loads(analysis_dict['missing_sections']) if analysis_dict.get('missing_sections') else [],
                'sections_missing': json.loads(analysis_dict['missing_keywords']) if analysis_dict.get('missing_keywords') else [],
                'action_verb_feedback': json.loads(analysis_dict['action_verbs_analysis']) if analysis_dict.get('action_verbs_analysis') else [],
                'gap_advice': json.loads(analysis_dict['gap_presentation_advice']) if analysis_dict.get('gap_presentation_advice') else [],
                'suggested_bullets': json.loads(analysis_dict['suggested_bullet_points']) if analysis_dict.get('suggested_bullet_points') else [],
                'found_keywords': json.loads(analysis_dict['extracted_skills']) if analysis_dict.get('extracted_skills') else [],
                'missing_keywords': json.loads(analysis_dict['role_alignment_feedback']) if analysis_dict.get('role_alignment_feedback') else [],
                'missing_keywords_reasons': json.loads(analysis_dict['missing_keywords_reasons']) if analysis_dict.get('missing_keywords_reasons') else {},
                'emphasized_keywords': json.loads(analysis_dict['emphasized_keywords']) if analysis_dict.get('emphasized_keywords') else [],
                'unsupported_keywords': json.loads(analysis_dict['unsupported_keywords']) if analysis_dict.get('unsupported_keywords') else [],
                'enhanced_resume_text': analysis_dict.get('enhanced_resume_text'),
                'updated_resume_docx_path': analysis_dict.get('updated_resume_docx_path'),
                'updated_resume_text': analysis_dict.get('updated_resume_text'),
                'updated_at': analysis_dict.get('updated_at')
            }
    return render_template(
        'user/resume_hub.html',
        profile=profile,
        user_context=user_context,
        latest_resume=latest_resume,
        latest_analysis=latest_analysis
    )

@app.route('/resume/upload', methods=['POST'])
@login_required
@role_required(['USER'])
def upload_resume():
    user_id = session['user_id']
    user_context = get_complete_user_context(user_id)
    target_role = request.form.get('target_role', '').strip() or user_context.get('target_role', '')
    
    if 'resume_file' not in request.files:
        flash("No file selected for upload.", "warning")
        return redirect(url_for('resume_hub'))

    file = request.files['resume_file']
    if file.filename == '':
        flash("Please choose a valid resume file.", "warning")
        return redirect(url_for('resume_hub'))

    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if file_ext not in Config.ALLOWED_RESUME_EXTENSIONS:
        flash("Invalid file format. Please upload PDF, DOCX, or TXT format.", "danger")
        return redirect(url_for('resume_hub'))

    unique_filename = f"user_{user_id}_{int(datetime.now().timestamp())}_{filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    file.save(filepath)

    # Substantive text extraction
    extracted_text = extract_text_from_file(filepath, file_ext)
    if not extracted_text:
        flash("File uploaded, but could not extract readable text. Ensure document is not an image-only scan.", "warning")
        extracted_text = "Candidate Resume"

    # Run dynamic qualitative analysis using user context
    analysis = analyze_resume_text(extracted_text, target_role, user_context)

    # Pre-generate updated docx file
    updated_folder = os.path.join(Config.UPLOAD_FOLDER, 'updated_resumes')
    os.makedirs(updated_folder, exist_ok=True)
    docx_filename = f"updated_resume_user_{user_id}_{int(datetime.now().timestamp())}.docx"
    docx_filepath = os.path.join(updated_folder, docx_filename)
    try:
        generate_updated_resume_docx(
            extracted_text, user_context, target_role, docx_filepath, analysis['enhanced_resume_text']
        )
    except Exception as e:
        print(f"Error pre-generating docx: {e}")
        docx_filename = None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resumes (user_id, filename, original_filename, file_type, raw_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, unique_filename, filename, file_ext, extracted_text))
    resume_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO resume_analyses (
            resume_id, user_id, target_role, match_score, score_explanation,
            extracted_skills, missing_keywords, missing_sections, action_verbs_analysis,
            gap_presentation_advice, role_alignment_feedback, missing_keywords_reasons,
            emphasized_keywords, unsupported_keywords, suggested_bullet_points,
            enhanced_resume_text, updated_resume_docx_path, updated_resume_text, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        resume_id, user_id, target_role,
        analysis['match_score'],
        analysis['score_explanation'],
        json.dumps(analysis['found_keywords']),
        json.dumps(analysis['sections_missing']),
        json.dumps(analysis['sections_found']),
        json.dumps(analysis['action_verb_feedback']),
        json.dumps(analysis['gap_advice']),
        json.dumps(analysis['missing_keywords']),
        json.dumps(analysis['missing_keywords_reasons']),
        json.dumps(analysis['emphasized_keywords']),
        json.dumps(analysis['unsupported_keywords']),
        json.dumps(analysis['suggested_bullets']),
        analysis['enhanced_resume_text'],
        docx_filename,
        analysis['enhanced_resume_text']
    ))
    conn.commit()
    conn.close()

    flash("Resume analyzed successfully. Review structural feedback, STAR rewrites, and generated updated draft.", "success")
    return redirect(url_for('resume_hub'))

@app.route('/resume/generate-updated', methods=['POST'])
@app.route('/api/resume/generate-updated', methods=['POST'])
@login_required
@role_required(['USER'])
def generate_updated_resume_endpoint():
    """
    Generates a personalized, modernized .docx resume from original uploaded resume
    and candidate profile data, preserving all authentic facts.
    """
    user_id = session['user_id']
    user_context = get_complete_user_context(user_id)
    target_role = request.form.get('target_role') or (request.get_json() or {}).get('target_role') or user_context.get('target_role') or 'Professional Returnee'

    conn = get_db_connection()
    latest_resume = conn.execute(
        "SELECT * FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()

    if not latest_resume:
        conn.close()
        if request.is_json:
            return jsonify({'success': False, 'error': 'No resume uploaded yet. Please upload a resume first.'}), 400
        flash("No resume uploaded yet. Please upload your resume first.", "warning")
        return redirect(url_for('resume_hub'))

    raw_text = latest_resume['raw_text'] or ""
    custom_draft = request.form.get('draft_text') or (request.get_json() or {}).get('draft_text')

    if custom_draft and len(custom_draft.strip()) > 100:
        updated_text = custom_draft.strip()
    else:
        updated_text = generate_updated_resume_ai(raw_text, target_role, user_context)

    updated_folder = os.path.join(Config.UPLOAD_FOLDER, 'updated_resumes')
    os.makedirs(updated_folder, exist_ok=True)
    docx_filename = f"updated_resume_user_{user_id}_{int(datetime.now().timestamp())}.docx"
    docx_filepath = os.path.join(updated_folder, docx_filename)

    generate_updated_resume_docx(
        raw_text, user_context, target_role, docx_filepath, updated_text
    )

    # Re-run analysis with target role to keep keyword transparency updated
    analysis = analyze_resume_text(raw_text, target_role, user_context)

    # Update resume_analyses
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE resume_analyses
        SET target_role = ?,
            match_score = ?,
            score_explanation = ?,
            extracted_skills = ?,
            missing_keywords = ?,
            missing_sections = ?,
            action_verbs_analysis = ?,
            gap_presentation_advice = ?,
            role_alignment_feedback = ?,
            missing_keywords_reasons = ?,
            emphasized_keywords = ?,
            unsupported_keywords = ?,
            suggested_bullet_points = ?,
            updated_resume_docx_path = ?,
            updated_resume_text = ?,
            enhanced_resume_text = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE resume_id = ?
    ''', (
        target_role,
        analysis['match_score'],
        analysis['score_explanation'],
        json.dumps(analysis['found_keywords']),
        json.dumps(analysis['sections_missing']),
        json.dumps(analysis['sections_found']),
        json.dumps(analysis['action_verb_feedback']),
        json.dumps(analysis['gap_advice']),
        json.dumps(analysis['missing_keywords']),
        json.dumps(analysis['missing_keywords_reasons']),
        json.dumps(analysis['emphasized_keywords']),
        json.dumps(analysis['unsupported_keywords']),
        json.dumps(analysis['suggested_bullets']),
        docx_filename,
        updated_text,
        updated_text,
        latest_resume['id']
    ))
    conn.commit()
    conn.close()

    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Updated resume generated successfully!',
            'target_role': target_role,
            'match_score': analysis['match_score'],
            'score_explanation': analysis['score_explanation'],
            'found_keywords': analysis['found_keywords'],
            'emphasized_keywords': analysis['emphasized_keywords'],
            'missing_keywords': analysis['missing_keywords'],
            'missing_keywords_reasons': analysis['missing_keywords_reasons'],
            'unsupported_keywords': analysis['unsupported_keywords'],
            'updated_text': updated_text,
            'download_docx_url': url_for('download_updated_resume', format='docx'),
            'download_txt_url': url_for('download_updated_resume', format='txt')
        })

    flash("Updated resume generated successfully. You can now review and download your .docx file.", "success")
    return redirect(url_for('resume_hub'))

@app.route('/api/roadmap/stage-test/<int:stage_number>', methods=['GET'])
@login_required
@role_required(['USER'])
def api_roadmap_stage_test(stage_number):
    """Returns dynamic evaluation test questions for the specified roadmap stage."""
    user_id = session['user_id']
    from services.roadmap_engine import get_stage_test_data
    result = get_stage_test_data(user_id, stage_number)
    if not result.get('success'):
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/roadmap/evaluate-stage', methods=['POST'])
@login_required
@role_required(['USER'])
def api_roadmap_evaluate_stage():
    """Evaluates candidate submitted answers for a roadmap stage test."""
    user_id = session['user_id']
    data = request.get_json() or {}
    stage_number = data.get('stage_number')
    answers = data.get('answers') or {}

    if not stage_number:
        return jsonify({'success': False, 'error': 'Missing stage_number'}), 400

    from services.roadmap_engine import evaluate_stage_test
    result = evaluate_stage_test(user_id, int(stage_number), answers)
    if not result.get('success'):
        return jsonify(result), 400
    return jsonify(result)

# ==============================================================================
# 7. GOVERNMENT OPPORTUNITIES & STARTUP / FREELANCE HUBS
# ==============================================================================

@app.route('/government/hub')
def government_hub():
    state = request.args.get('state', '').strip()
    sector = request.args.get('sector', '').strip()
    job_type = request.args.get('job_type', '').strip()
    search = request.args.get('q', '').strip()

    conn = get_db_connection()
    sql = "SELECT * FROM government_opportunities WHERE is_verified = 1"
    params = []

    if state:
        sql += " AND state = ?"
        params.append(state)
    if sector:
        sql += " AND sector = ?"
        params.append(sector)
    if job_type:
        sql += " AND job_type = ?"
        params.append(job_type)
    if search:
        like = f"%{search}%"
        sql += """ AND (
            title LIKE ? OR department LIKE ? OR sector LIKE ? OR
            qualification LIKE ? OR eligibility_details LIKE ?
        )"""
        params.extend([like, like, like, like, like])

    sql += " ORDER BY CASE WHEN deadline IS NULL THEN 1 ELSE 0 END, deadline ASC, id ASC"
    opportunities = conn.execute(sql, params).fetchall()

    saved_gov_ids = set()
    user_id = session.get('user_id')
    if user_id:
        bms = conn.execute("SELECT item_id FROM user_bookmarks WHERE user_id = ? AND item_type = 'GOVERNMENT'", (user_id,)).fetchall()
        saved_gov_ids = {b['item_id'] for b in bms}

    conn.close()
    return render_template(
        'user/government_hub.html',
        opportunities=opportunities,
        saved_gov_ids=saved_gov_ids,
        search=search
    )

@app.route('/startup/hub')
@login_required
@role_required(['USER'])
def startup_hub():
    user_id = session['user_id']
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    last_idea = conn.execute(
        "SELECT * FROM startup_ideas WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()

    analysis_result = None
    if last_idea:
        analysis_result = analyze_startup_idea(dict(last_idea))

    return render_template(
        'user/startup_hub.html',
        profile=profile,
        last_idea=last_idea,
        analysis_result=analysis_result
    )

@app.route('/startup/analyze', methods=['POST'])
@login_required
@role_required(['USER'])
def analyze_startup_submission():
    user_id = session['user_id']
    data = {
        'business_name': request.form.get('business_name', ''),
        'problem_statement': request.form.get('problem_statement', ''),
        'solution_description': request.form.get('solution_description', ''),
        'target_users': request.form.get('target_users', ''),
        'skills_available': request.form.get('skills_available', ''),
        'budget_range': request.form.get('budget_range', ''),
        'location': request.form.get('location', '')
    }

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO startup_ideas (
            user_id, business_name, problem_statement, solution_description,
            target_users, skills_available, budget_range, location
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, data['business_name'], data['problem_statement'],
        data['solution_description'], data['target_users'],
        data['skills_available'], data['budget_range'], data['location']
    ))
    conn.commit()
    conn.close()

    flash("Concept evaluated. Feasibility report and verified scheme matches updated.", "success")
    return redirect(url_for('startup_hub'))

# ==============================================================================
# 8. BOOKMARKS & APPLICATIONS
# ==============================================================================

@app.route('/saved')
@login_required
@role_required(['USER'])
def saved_items():
    user_id = session['user_id']
    conn = get_db_connection()
    raw = conn.execute(
        "SELECT * FROM user_bookmarks WHERE user_id = ? ORDER BY saved_at DESC", (user_id,)
    ).fetchall()

    bookmarks = []
    for b in raw:
        title = "Opportunity"
        subtitle = ""
        url = "#"
        if b['item_type'] == 'JOB':
            j = conn.execute("SELECT * FROM jobs WHERE id = ?", (b['item_id'],)).fetchone()
            if j:
                title = j['title']
                subtitle = f"{j['company_name']} • {j['location']}"
                url = url_for('job_detail', job_id=j['id'])
        elif b['item_type'] == 'GOVERNMENT':
            g_item = conn.execute("SELECT * FROM government_opportunities WHERE id = ?", (b['item_id'],)).fetchone()
            if g_item:
                title = g_item['title']
                subtitle = f"{g_item['department']} • {g_item['state']}"
                url = url_for('government_hub')
        elif b['item_type'] == 'LEARNING':
            l_item = conn.execute("SELECT * FROM learning_resources WHERE id = ?", (b['item_id'],)).fetchone()
            if l_item:
                title = l_item['title']
                subtitle = f"{l_item['provider']} • {l_item['category']}"
                url = l_item['url']

        bookmarks.append({
            'id': b['id'],
            'title': title,
            'subtitle': subtitle,
            'item_type': b['item_type'].title(),
            'url': url,
            'saved_at': b['saved_at']
        })

    conn.close()
    return render_template('user/saved_items.html', bookmarks=bookmarks)

@app.route('/bookmarks/remove/<int:bookmark_id>', methods=['POST'])
@login_required
@role_required(['USER'])
def remove_bookmark(bookmark_id):
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM user_bookmarks WHERE id = ? AND user_id = ?", (bookmark_id, user_id))
    conn.commit()
    conn.close()
    flash("Bookmark removed.", "info")
    return redirect(url_for('saved_items'))

@app.route('/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
@role_required(['USER'])
def apply_job(job_id):
    user_id = session['user_id']
    cover_note = request.form.get('cover_note', '').strip()

    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ? AND is_active = 1 AND approval_status = 'APPROVED'", (job_id,)).fetchone()
    if not job:
        conn.close()
        flash("This vacancy is no longer accepting applications or is awaiting verification.", "warning")
        return redirect(url_for('explore_opportunities'))

    existing = conn.execute("SELECT id FROM job_applications WHERE user_id = ? AND job_id = ?", (user_id, job_id)).fetchone()
    if existing:
        conn.close()
        flash("You have already submitted an application for this vacancy.", "info")
        return redirect(url_for('job_detail', job_id=job_id))

    latest_resume = conn.execute("SELECT id FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    resume_id = latest_resume['id'] if latest_resume else None

    conn.execute('''
        INSERT INTO job_applications (user_id, job_id, resume_id, cover_note, status)
        VALUES (?, ?, ?, ?, 'Submitted')
    ''', (user_id, job_id, resume_id, cover_note))
    conn.commit()

    # In-app notifications
    candidate = conn.execute("SELECT full_name FROM users WHERE id = ?", (user_id,)).fetchone()
    cand_name = candidate['full_name'] if candidate else "A candidate"

    rec_user_id = None
    if job['recruiter_id']:
        rec = conn.execute("SELECT user_id FROM recruiters WHERE id = ?", (job['recruiter_id'],)).fetchone()
        if rec and rec['user_id']:
            rec_user_id = rec['user_id']
    conn.close()

    create_notification(
        user_id,
        "Application Submitted",
        f"Your application for '{job['title']}' at {job['company_name']} has been submitted.",
        url_for('job_detail', job_id=job_id)
    )

    if rec_user_id:
        create_notification(
            rec_user_id,
            "New Candidate Application",
            f"{cand_name} applied for your listing: '{job['title']}'.",
            url_for('manage_recruiter_jobs')
        )

    flash("Your application has been directly submitted to the recruiter.", "success")
    return redirect(url_for('job_detail', job_id=job_id))

# ==============================================================================
# 9. RECRUITER MODULE
# ==============================================================================

@app.route('/recruiter/profile', methods=['GET', 'POST'])
@login_required
@role_required(['RECRUITER'])
def recruiter_profile():
    user_id = session['user_id']
    conn = get_db_connection()
    recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()

    if request.method == 'POST':
        recruiter_name = request.form.get('recruiter_name', '').strip()
        company_name = request.form.get('company_name', '').strip()
        company_website = request.form.get('company_website', '').strip()
        company_description = request.form.get('company_description', '').strip()
        designation = request.form.get('designation', '').strip()

        if not recruiter_name or not company_name:
            flash("Recruiter name and company name are required.", "warning")
            return render_template('recruiter/profile.html', recruiter=recruiter)

        cursor = conn.cursor()
        cursor.execute('''
            UPDATE recruiters SET
                recruiter_name = ?, company_name = ?, company_website = ?,
                company_description = ?, designation = ?
            WHERE user_id = ?
        ''', (recruiter_name, company_name, company_website, company_description, designation, user_id))
        cursor.execute("UPDATE users SET full_name = ? WHERE id = ?", (recruiter_name, user_id))
        session['user_name'] = recruiter_name
        conn.commit()

        recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        flash("Company profile updated successfully.", "success")
        return redirect(url_for('recruiter_profile'))

    conn.close()
    return render_template('recruiter/profile.html', recruiter=recruiter)

@app.route('/recruiter/dashboard')
@login_required
@role_required(['RECRUITER'])
def recruiter_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()

    recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()
    if not recruiter:
        conn.close()
        flash("Recruiter profile not found.", "danger")
        return redirect(url_for('landing'))

    jobs_raw = conn.execute(
        "SELECT * FROM jobs WHERE recruiter_id = ? ORDER BY posted_at DESC", (recruiter['id'],)
    ).fetchall()

    jobs = []
    active_count = 0
    total_applicants = 0
    pending_count = 0

    for j in jobs_raw:
        j_dict = dict(j)
        app_count = conn.execute(
            "SELECT COUNT(*) as c FROM job_applications WHERE job_id = ?", (j['id'],)
        ).fetchone()['c']
        total_applicants += app_count
        if j['is_active'] and j_dict.get('approval_status') == 'APPROVED':
            active_count += 1
        if j_dict.get('approval_status') == 'PENDING':
            pending_count += 1
        jobs.append({
            'id': j['id'],
            'title': j['title'],
            'location': j['location'],
            'work_mode': j['work_mode'],
            'is_active': j['is_active'],
            'approval_status': j_dict.get('approval_status', 'APPROVED'),
            'rejection_notes': j_dict.get('rejection_notes'),
            'application_deadline': j['application_deadline'],
            'applicant_count': app_count
        })

    conn.close()
    return render_template(
        'recruiter/dashboard.html',
        recruiter=recruiter,
        jobs=jobs,
        active_jobs_count=active_count,
        pending_jobs_count=pending_count,
        total_applicants_count=total_applicants
    )

@app.route('/recruiter/post-job', methods=['GET', 'POST'])
@login_required
@role_required(['RECRUITER'])
def post_job():
    user_id = session['user_id']
    conn = get_db_connection()
    recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        location = request.form.get('location', '').strip()
        work_mode = request.form.get('work_mode', 'Hybrid')
        salary_range = request.form.get('salary_range', '').strip()
        experience_required = request.form.get('experience_required', '').strip() or request.form.get('experience_level', '').strip()
        qualification_required = request.form.get('qualification_required', '').strip()
        skills_required = request.form.get('skills_required', '').strip() or request.form.get('requirements', '').strip()
        description = request.form.get('description', '').strip()
        application_deadline = request.form.get('application_deadline') or None
        application_method = request.form.get('application_method', 'Internal')
        source_url = request.form.get('source_url', '').strip()

        if not title or not location or not description or not skills_required:
            flash("Please provide all required job listing fields.", "warning")
            conn.close()
            return render_template('recruiter/post_job.html', recruiter=recruiter)

        source_type = 'VERIFIED_RECRUITER' if recruiter['is_verified'] == 1 else 'EXTERNAL_SOURCE'
        source_name = f"{recruiter['company_name']} Career Portal"
        approval_status = 'PENDING'

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO jobs (
                recruiter_id, title, company_name, location, work_mode,
                experience_required, skills_required, qualification_required,
                salary_range, description, application_deadline, application_method,
                source_type, source_name, source_url, approval_status, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            recruiter['id'], title, recruiter['company_name'], location, work_mode,
            experience_required, skills_required, qualification_required,
            salary_range, description, application_deadline, application_method,
            source_type, source_name, source_url, approval_status
        ))
        new_job_id = cursor.lastrowid
        conn.commit()

        # Notify admins of pending job
        admins = conn.execute("SELECT id FROM users WHERE role = 'ADMIN'").fetchall()
        admin_ids = [a['id'] for a in admins]
        conn.close()

        for a_id in admin_ids:
            create_notification(
                a_id,
                "New Vacancy Awaiting Review",
                f"Recruiter {recruiter['company_name']} submitted '{title}' for moderation.",
                url_for('admin_manage_jobs')
            )

        flash("Job vacancy submitted for platform moderation. It will appear on the platform once reviewed by administrators.", "success")
        return redirect(url_for('manage_recruiter_jobs'))

    conn.close()
    return render_template('recruiter/post_job.html', recruiter=recruiter)

@app.route('/recruiter/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['RECRUITER'])
def edit_recruiter_job(job_id):
    user_id = session['user_id']
    conn = get_db_connection()
    recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()
    job = conn.execute("SELECT * FROM jobs WHERE id = ? AND recruiter_id = ?", (job_id, recruiter['id'])).fetchone()

    if not job:
        conn.close()
        flash("Vacancy not found or access denied.", "warning")
        return redirect(url_for('manage_recruiter_jobs'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        location = request.form.get('location', '').strip()
        work_mode = request.form.get('work_mode', 'Hybrid')
        salary_range = request.form.get('salary_range', '').strip()
        experience_required = request.form.get('experience_required', '').strip()
        qualification_required = request.form.get('qualification_required', '').strip()
        skills_required = request.form.get('skills_required', '').strip()
        description = request.form.get('description', '').strip()
        application_deadline = request.form.get('application_deadline') or None
        application_method = request.form.get('application_method', 'Internal')
        source_url = request.form.get('source_url', '').strip()

        cursor = conn.cursor()
        cursor.execute('''
            UPDATE jobs SET
                title = ?, location = ?, work_mode = ?, salary_range = ?,
                experience_required = ?, qualification_required = ?,
                skills_required = ?, description = ?, application_deadline = ?,
                application_method = ?, source_url = ?
            WHERE id = ? AND recruiter_id = ?
        ''', (
            title, location, work_mode, salary_range,
            experience_required, qualification_required,
            skills_required, description, application_deadline,
            application_method, source_url, job_id, recruiter['id']
        ))
        conn.commit()
        conn.close()
        flash(f"Vacancy '{title}' updated successfully.", "success")
        return redirect(url_for('manage_recruiter_jobs'))

    conn.close()
    return render_template('recruiter/edit_job.html', recruiter=recruiter, job=job)

@app.route('/recruiter/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required(['RECRUITER'])
def delete_recruiter_job(job_id):
    user_id = session['user_id']
    conn = get_db_connection()
    recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()
    job = conn.execute("SELECT * FROM jobs WHERE id = ? AND recruiter_id = ?", (job_id, recruiter['id'])).fetchone()

    if job:
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        flash(f"Vacancy '{job['title']}' permanently removed.", "info")

    conn.close()
    return redirect(url_for('manage_recruiter_jobs'))

@app.route('/recruiter/applications/<int:app_id>/status', methods=['POST'])
@login_required
@role_required(['RECRUITER'])
def update_application_status(app_id):
    user_id = session['user_id']
    new_status = request.form.get('status', '').strip()
    if new_status not in ['Submitted', 'Under Review', 'Shortlisted', 'Closed']:
        flash("Invalid status selected.", "warning")
        return redirect(url_for('manage_recruiter_jobs'))

    conn = get_db_connection()
    recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()
    
    app_data = conn.execute('''
        SELECT a.*, j.title as job_title, j.company_name
        FROM job_applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id = ? AND j.recruiter_id = ?
    ''', (app_id, recruiter['id'])).fetchone()

    if not app_data:
        conn.close()
        flash("Application record not found.", "warning")
        return redirect(url_for('manage_recruiter_jobs'))

    conn.execute("UPDATE job_applications SET status = ? WHERE id = ?", (new_status, app_id))
    conn.commit()

    applicant_user_id = app_data['user_id']
    job_title = app_data['job_title']
    company_name = app_data['company_name']
    job_id = app_data['job_id']
    conn.close()

    # Notify applicant
    create_notification(
        applicant_user_id,
        "Application Status Updated",
        f"Your application for '{job_title}' at {company_name} is now: {new_status}.",
        url_for('job_detail', job_id=job_id)
    )

    flash(f"Candidate application status updated to '{new_status}'.", "success")
    return redirect(url_for('manage_recruiter_jobs'))

@app.route('/recruiter/applications/<int:app_id>/candidate')
@login_required
@role_required(['RECRUITER'])
def view_candidate_details(app_id):
    user_id = session['user_id']
    conn = get_db_connection()
    recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()

    row = conn.execute('''
        SELECT a.*, u.full_name as candidate_name, u.email as candidate_email,
               p.location, p.education, p.qualification, p.graduation_year,
               p.skills, p.work_mode_preference, p.previous_job_title,
               p.years_of_experience, p.career_gap_duration, p.gap_reason,
               p.previous_industry, p.desired_career_direction,
               r.filename as resume_file, r.raw_text as resume_text
        FROM job_applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN users u ON a.user_id = u.id
        LEFT JOIN profiles p ON u.id = p.user_id
        LEFT JOIN resumes r ON a.resume_id = r.id
        WHERE a.id = ? AND j.recruiter_id = ?
    ''', (app_id, recruiter['id'])).fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Candidate details not found'}), 404

    d = dict(row)
    return jsonify({
        'success': True,
        'candidate': {
            'name': d['candidate_name'],
            'email': d['candidate_email']
        },
        'profile': {
            'previous_job_title': d['previous_job_title'],
            'career_gap_duration': d['career_gap_duration'],
            'years_of_experience': d['years_of_experience'],
            'preferred_work_mode': d['work_mode_preference'],
            'skills': d['skills'],
            'qualification': d['qualification']
        },
        'resume': {
            'filename': d['resume_file'],
            'raw_text': d['resume_text']
        },
        **d
    })

@app.route('/recruiter/manage-jobs')
@login_required
@role_required(['RECRUITER'])
def manage_recruiter_jobs():
    user_id = session['user_id']
    conn = get_db_connection()
    recruiter = conn.execute("SELECT * FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()

    jobs_raw = conn.execute(
        "SELECT * FROM jobs WHERE recruiter_id = ? ORDER BY posted_at DESC", (recruiter['id'],)
    ).fetchall()

    jobs = []
    for j in jobs_raw:
        apps = conn.execute('''
            SELECT a.*, u.full_name as candidate_name, u.email as candidate_email,
                   p.qualification, p.career_gap_duration as gap_duration,
                   p.skills as candidate_skills
            FROM job_applications a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN profiles p ON u.id = p.user_id
            WHERE a.job_id = ?
            ORDER BY a.applied_at DESC
        ''', (j['id'],)).fetchall()

        j_dict = dict(j)
        jobs.append({
            'id': j['id'],
            'title': j['title'],
            'location': j['location'],
            'work_mode': j['work_mode'],
            'is_active': j['is_active'],
            'approval_status': j_dict.get('approval_status', 'APPROVED'),
            'rejection_notes': j_dict.get('rejection_notes'),
            'application_deadline': j['application_deadline'],
            'posted_at': j['posted_at'],
            'applicants': [dict(a) for a in apps]
        })

    conn.close()
    return render_template('recruiter/manage_jobs.html', recruiter=recruiter, jobs=jobs)

@app.route('/recruiter/jobs/<int:job_id>/toggle', methods=['POST'])
@login_required
@role_required(['RECRUITER'])
def toggle_job_status(job_id):
    user_id = session['user_id']
    conn = get_db_connection()
    recruiter = conn.execute("SELECT id FROM recruiters WHERE user_id = ?", (user_id,)).fetchone()
    job = conn.execute("SELECT * FROM jobs WHERE id = ? AND recruiter_id = ?", (job_id, recruiter['id'])).fetchone()

    if job:
        new_status = 0 if job['is_active'] == 1 else 1
        conn.execute("UPDATE jobs SET is_active = ? WHERE id = ?", (new_status, job_id))
        conn.commit()
        flash(f"Vacancy '{job['title']}' updated to {'Active' if new_status else 'Closed'}.", "info")

    conn.close()
    return redirect(url_for('manage_recruiter_jobs'))

# ==============================================================================
# 10. ADMIN MODULE
# ==============================================================================

@app.route('/admin/dashboard')
@login_required
@role_required(['ADMIN'])
def admin_dashboard():
    conn = get_db_connection()

    total_users = conn.execute("SELECT COUNT(*) as c FROM users WHERE role = 'USER'").fetchone()['c']
    total_recruiters = conn.execute("SELECT COUNT(*) as c FROM recruiters").fetchone()['c']
    pending_recruiters_count = conn.execute("SELECT COUNT(*) as c FROM recruiters WHERE is_verified = 0").fetchone()['c']
    pending_jobs_count = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE approval_status = 'PENDING'").fetchone()['c']
    total_jobs = conn.execute("SELECT COUNT(*) as c FROM jobs").fetchone()['c']
    active_jobs = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE is_active = 1").fetchone()['c']
    total_gov = conn.execute("SELECT COUNT(*) as c FROM government_opportunities").fetchone()['c']
    total_learning = conn.execute("SELECT COUNT(*) as c FROM learning_resources").fetchone()['c']

    # Pathway distribution from actual database
    pathway_rows = conn.execute("SELECT pathway, COUNT(*) as count FROM career_selections GROUP BY pathway").fetchall()
    pathway_counts = {'EXPERIENCED_GAP': 0, 'NO_EXPERIENCE': 0, 'CAREER_SHIFT': 0}
    for row in pathway_rows:
        if row['pathway'] in pathway_counts:
            pathway_counts[row['pathway']] = row['count']

    # Audit logs
    audit_logs = conn.execute("SELECT * FROM admin_audit_logs ORDER BY created_at DESC LIMIT 6").fetchall()

    conn.close()
    return render_template(
        'admin/dashboard.html',
        metrics={
            'total_users': total_users,
            'total_recruiters': total_recruiters,
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_gov_opps': total_gov,
            'total_learning': total_learning,
            'pending_jobs_count': pending_jobs_count
        },
        pending_recruiters_count=pending_recruiters_count,
        pending_jobs_count=pending_jobs_count,
        pathway_counts=pathway_counts,
        audit_logs=audit_logs
    )

@app.route('/admin/verify-recruiters')
@login_required
@role_required(['ADMIN'])
def admin_verify_recruiters():
    conn = get_db_connection()
    recruiters = conn.execute("SELECT * FROM recruiters ORDER BY is_verified ASC, id DESC").fetchall()
    conn.close()
    return render_template('admin/verify_recruiters.html', recruiters=recruiters)

@app.route('/admin/recruiters/<int:recruiter_id>/action', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_action_verify_recruiter(recruiter_id):
    action = request.form.get('action')
    admin_id = session['user_id']
    conn = get_db_connection()

    if action == 'approve':
        conn.execute('''
            UPDATE recruiters 
            SET is_verified = 1, verified_at = CURRENT_TIMESTAMP, verified_by = ?,
                verification_notes = 'Corporate domain manually verified by admin.'
            WHERE id = ?
        ''', (admin_id, recruiter_id))
        # Upgrade existing jobs for this recruiter to verified recruiter badge
        conn.execute("UPDATE jobs SET source_type = 'VERIFIED_RECRUITER' WHERE recruiter_id = ?", (recruiter_id,))

        conn.execute('''
            INSERT INTO admin_audit_logs (admin_id, action_type, target_type, target_id, details)
            VALUES (?, 'APPROVE_RECRUITER', 'RECRUITER', ?, 'Approved recruiter domain verification.')
        ''', (admin_id, recruiter_id))
        flash("Recruiter approved. Their job postings now display the Verified Recruiter badge.", "success")
    elif action == 'reject':
        conn.execute('''
            UPDATE recruiters 
            SET is_verified = 2, verification_notes = 'Corporate domain verification rejected.'
            WHERE id = ?
        ''', (recruiter_id,))
        conn.execute('''
            INSERT INTO admin_audit_logs (admin_id, action_type, target_type, target_id, details)
            VALUES (?, 'REJECT_RECRUITER', 'RECRUITER', ?, 'Declined recruiter verification.')
        ''', (admin_id, recruiter_id))
        flash("Recruiter verification declined.", "warning")

    conn.commit()
    conn.close()
    return redirect(url_for('admin_verify_recruiters'))

@app.route('/admin/manage-jobs')
@login_required
@role_required(['ADMIN'])
def admin_manage_jobs():
    conn = get_db_connection()
    pending_jobs = conn.execute(
        "SELECT * FROM jobs WHERE approval_status = 'PENDING' ORDER BY posted_at DESC"
    ).fetchall()
    reviewed_jobs = conn.execute(
        "SELECT * FROM jobs WHERE approval_status != 'PENDING' OR approval_status IS NULL ORDER BY posted_at DESC"
    ).fetchall()
    jobs = conn.execute("SELECT * FROM jobs ORDER BY posted_at DESC").fetchall()
    conn.close()
    return render_template(
        'admin/manage_jobs.html',
        jobs=jobs,
        pending_jobs=pending_jobs,
        reviewed_jobs=reviewed_jobs
    )

@app.route('/admin/jobs/<int:job_id>/review', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_review_job(job_id):
    admin_id = session['user_id']
    decision = request.form.get('decision', '').strip().upper()
    rejection_notes = request.form.get('rejection_notes', '').strip()

    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        flash("Job listing not found.", "warning")
        return redirect(url_for('admin_manage_jobs'))

    if decision == 'APPROVE':
        conn.execute('''
            UPDATE jobs 
            SET approval_status = 'APPROVED', is_active = 1, rejection_notes = NULL
            WHERE id = ?
        ''', (job_id,))
        conn.execute('''
            INSERT INTO admin_audit_logs (admin_id, action_type, target_type, target_id, details)
            VALUES (?, 'APPROVE_JOB', 'JOB', ?, ?)
        ''', (admin_id, job_id, f"Approved job listing '{job['title']}' for {job['company_name']}."))
        
        rec_user_id = None
        if job['recruiter_id']:
            rec = conn.execute("SELECT user_id FROM recruiters WHERE id = ?", (job['recruiter_id'],)).fetchone()
            if rec: rec_user_id = rec['user_id']

        conn.commit()
        conn.close()

        if rec_user_id:
            create_notification(
                rec_user_id,
                "Job Posting Approved",
                f"Your job posting '{job['title']}' has been reviewed, approved, and is now active for candidates.",
                url_for('manage_recruiter_jobs')
            )
        flash(f"Job '{job['title']}' approved and published to candidate feed.", "success")

    elif decision == 'REJECT':
        notes = rejection_notes or "Listing does not meet platform standards or returnee criteria."
        conn.execute('''
            UPDATE jobs 
            SET approval_status = 'REJECTED', is_active = 0, rejection_notes = ?
            WHERE id = ?
        ''', (notes, job_id))
        conn.execute('''
            INSERT INTO admin_audit_logs (admin_id, action_type, target_type, target_id, details)
            VALUES (?, 'REJECT_JOB', 'JOB', ?, ?)
        ''', (admin_id, job_id, f"Rejected job listing '{job['title']}'. Reason: {notes}"))

        rec_user_id = None
        if job['recruiter_id']:
            rec = conn.execute("SELECT user_id FROM recruiters WHERE id = ?", (job['recruiter_id'],)).fetchone()
            if rec: rec_user_id = rec['user_id']

        conn.commit()
        conn.close()

        if rec_user_id:
            create_notification(
                rec_user_id,
                "Job Posting Needs Revision",
                f"Your job posting '{job['title']}' was not approved. Feedback: {notes}",
                url_for('manage_recruiter_jobs')
            )
        flash(f"Job '{job['title']}' rejected.", "warning")

    return redirect(url_for('admin_manage_jobs'))

@app.route('/admin/jobs/<int:job_id>/toggle', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_toggle_job(job_id):
    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job:
        new_status = 0 if job['is_active'] == 1 else 1
        conn.execute("UPDATE jobs SET is_active = ? WHERE id = ?", (new_status, job_id))
        conn.commit()
        flash(f"Listing '{job['title']}' status toggled.", "info")
    conn.close()
    return redirect(url_for('admin_manage_jobs'))

@app.route('/admin/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_delete_job(job_id):
    admin_id = session['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.execute('''
        INSERT INTO admin_audit_logs (admin_id, action_type, target_type, target_id, details)
        VALUES (?, 'DELETE_JOB', 'JOB', ?, 'Deleted inappropriate or outdated listing.')
    ''', (admin_id, job_id))
    conn.commit()
    conn.close()
    flash("Job listing deleted from platform.", "info")
    return redirect(url_for('admin_manage_jobs'))

@app.route('/admin/manage-users')
@login_required
@role_required(['ADMIN'])
def admin_manage_users():
    conn = get_db_connection()
    users = conn.execute('''
        SELECT u.*, p.profile_completed, cs.pathway
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        LEFT JOIN career_selections cs ON u.id = cs.user_id
        ORDER BY u.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_toggle_user(user_id):
    admin_id = session['user_id']
    if user_id == admin_id:
        flash("You cannot deactivate your own admin account.", "danger")
        return redirect(url_for('admin_manage_users'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        new_active = 0 if user['is_active'] == 1 else 1
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_active, user_id))
        status_word = "Activated" if new_active == 1 else "Deactivated"
        conn.execute('''
            INSERT INTO admin_audit_logs (admin_id, action_type, target_type, target_id, details)
            VALUES (?, 'TOGGLE_USER_STATUS', 'USER', ?, ?)
        ''', (admin_id, user_id, f"{status_word} user {user['email']}"))
        conn.commit()
        flash(f"User {user['full_name']} ({user['email']}) is now {status_word.lower()}.", "info")
    conn.close()
    return redirect(url_for('admin_manage_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_delete_user(user_id):
    admin_id = session['user_id']
    if user_id == admin_id:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for('admin_manage_users'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.execute('''
            INSERT INTO admin_audit_logs (admin_id, action_type, target_type, target_id, details)
            VALUES (?, 'DELETE_USER', 'USER', ?, ?)
        ''', (admin_id, user_id, f"Deleted user {user['email']}"))
        conn.commit()
        flash(f"User {user['full_name']} has been removed.", "info")
    conn.close()
    return redirect(url_for('admin_manage_users'))

@app.route('/admin/manage-learning')
@login_required
@role_required(['ADMIN'])
def admin_manage_learning():
    conn = get_db_connection()
    resources = conn.execute("SELECT * FROM learning_resources ORDER BY id ASC").fetchall()
    conn.close()
    return render_template('admin/manage_learning.html', resources=resources)

@app.route('/admin/learning/add', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_add_learning():
    title = request.form.get('title', '').strip()
    category = request.form.get('category', '').strip()
    provider = request.form.get('provider', '').strip()
    description = request.form.get('description', '').strip()
    url = request.form.get('url', '').strip()
    duration = request.form.get('duration_estimate', '').strip()

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO learning_resources (title, category, provider, description, url, duration_estimate, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (title, category, provider, description, url, duration))
    conn.commit()
    conn.close()
    flash("New verified learning resource published.", "success")
    return redirect(url_for('admin_manage_learning'))

@app.route('/admin/learning/<int:resource_id>/delete', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_delete_learning(resource_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM learning_resources WHERE id = ?", (resource_id,))
    conn.commit()
    conn.close()
    flash("Resource deleted.", "info")
    return redirect(url_for('admin_manage_learning'))

@app.route('/admin/manage-government')
@login_required
@role_required(['ADMIN'])
def admin_manage_government():
    conn = get_db_connection()
    opportunities = conn.execute("SELECT * FROM government_opportunities ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin/manage_government.html', opportunities=opportunities)

@app.route('/admin/government/add', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_add_government():
    title = request.form.get('title', '').strip()
    department = request.form.get('department', '').strip()
    state = request.form.get('state', '').strip()
    sector = request.form.get('sector', '').strip()
    job_type = request.form.get('job_type', '').strip()
    eligibility_criteria = request.form.get('eligibility_criteria', '').strip()
    age_limit = request.form.get('age_limit', '').strip()
    reservation_relaxations = request.form.get('reservation_relaxations', '').strip()
    exam_process = request.form.get('exam_process', '').strip()
    syllabus_outline = request.form.get('syllabus_outline', '').strip()
    official_notification_url = request.form.get('official_notification_url', '').strip()
    apply_url = request.form.get('apply_url', '').strip()
    last_date_to_apply = request.form.get('last_date_to_apply', '').strip()

    if not title or not department:
        flash("Opportunity title and department are required.", "warning")
        return redirect(url_for('admin_manage_government'))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO government_opportunities (
            title, department, sector, state, location, qualification,
            age_criteria, category_criteria, job_type, application_status,
            deadline, eligibility_details, selection_process, required_documents,
            official_portal_url, is_verified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        title, department, sector or 'General Administration', state or 'All India',
        state or 'All India', 'Graduate / Any Degree', age_limit or '18-45 years',
        reservation_relaxations or 'Standard returnee relaxations', job_type or 'Full-Time',
        'Open', last_date_to_apply or 'Rolling', eligibility_criteria or 'Open to eligible citizens',
        exam_process or 'Merit / Written Exam', syllabus_outline or 'Standard qualifications check',
        official_notification_url or apply_url or 'https://india.gov.in'
    ))
    conn.commit()
    conn.close()
    flash("New verified government scheme published successfully.", "success")
    return redirect(url_for('admin_manage_government'))

@app.route('/admin/government/<int:opp_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def admin_edit_government(opp_id):
    conn = get_db_connection()
    opp = conn.execute("SELECT * FROM government_opportunities WHERE id = ?", (opp_id,)).fetchone()
    if not opp:
        conn.close()
        flash("Government opportunity not found.", "warning")
        return redirect(url_for('admin_manage_government'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        department = request.form.get('department', '').strip()
        state = request.form.get('state', '').strip()
        sector = request.form.get('sector', '').strip()
        job_type = request.form.get('job_type', '').strip()
        eligibility_criteria = request.form.get('eligibility_criteria', '').strip()
        age_limit = request.form.get('age_limit', '').strip()
        reservation_relaxations = request.form.get('reservation_relaxations', '').strip()
        exam_process = request.form.get('exam_process', '').strip()
        syllabus_outline = request.form.get('syllabus_outline', '').strip()
        official_notification_url = request.form.get('official_notification_url', '').strip()
        apply_url = request.form.get('apply_url', '').strip()
        last_date_to_apply = request.form.get('last_date_to_apply', '').strip()

        conn.execute('''
            UPDATE government_opportunities SET
                title = ?, department = ?, state = ?, sector = ?, job_type = ?,
                eligibility_details = ?, age_criteria = ?, category_criteria = ?,
                selection_process = ?, required_documents = ?, official_portal_url = ?,
                deadline = ?
            WHERE id = ?
        ''', (
            title, department, state, sector, job_type,
            eligibility_criteria, age_limit, reservation_relaxations,
            exam_process, syllabus_outline, official_notification_url or apply_url,
            last_date_to_apply, opp_id
        ))
        conn.commit()
        conn.close()
        flash(f"Government opportunity '{title}' updated.", "success")
        return redirect(url_for('admin_manage_government'))

    conn.close()
    return render_template('admin/edit_government.html', opp=opp)

@app.route('/admin/government/<int:opp_id>/delete', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_delete_government(opp_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM government_opportunities WHERE id = ?", (opp_id,))
    conn.commit()
    conn.close()
    flash("Government opportunity deleted.", "info")
    return redirect(url_for('admin_manage_government'))

# ==============================================================================
# 11. REST API ENDPOINTS (CHATBOT, ROADMAP, BOOKMARKS)
# ==============================================================================

@app.route('/api/chatbot/query', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Processes queries to the automated career assistant with candidate context and session memory."""
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    page_context = data.get('page_context', '').strip()
    if not message:
        return jsonify({'status': 'error', 'error': 'Message cannot be empty', 'reply': 'Please provide a message.'}), 400

    user_id = session.get('user_id')
    user_context = {}
    chat_history = []
    
    if user_id:
        user_context = get_complete_user_context(user_id)
        conn = get_db_connection()
        try:
            logs = conn.execute(
                "SELECT user_message, bot_response FROM chat_logs WHERE user_id = ? ORDER BY id DESC LIMIT 6",
                (user_id,)
            ).fetchall()
            for log in reversed(logs):
                chat_history.append({'role': 'user', 'content': log['user_message']})
                chat_history.append({'role': 'assistant', 'content': log['bot_response']})
        except Exception as e:
            print(f"Error fetching chat history: {e}")
        finally:
            conn.close()

    response_data = process_chatbot_query(message, user_context, page_context=page_context, chat_history=chat_history)

    # Persist interaction into chat_logs
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO chat_logs (user_id, session_id, user_message, bot_response, context_category)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                user_id,
                session.get('_id', 'guest-session'),
                message,
                response_data['reply'],
                response_data['category']
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Chat log persistence error: {e}")

    return jsonify({
        'status': 'success',
        'reply': response_data['reply'],
        'category': response_data['category'],
        'disclaimer': response_data.get('disclaimer', '')
    })

@app.route('/api/roadmap/task/toggle', methods=['POST'])
@login_required
def api_roadmap_task_toggle():
    user_id = session['user_id']
    data = request.get_json() or {}
    task_id = data.get('task_id')
    if not task_id:
        return jsonify({'success': False, 'error': 'Missing task_id'}), 400

    result = toggle_task_status(user_id, int(task_id))
    return jsonify(result)

@app.route('/api/roadmap/regenerate', methods=['POST'])
@login_required
@role_required(['USER'])
def api_roadmap_regenerate():
    """Regenerates user roadmap tasks dynamically using current profile."""
    user_id = session['user_id']
    from services.roadmap_engine import regenerate_user_roadmap
    result = regenerate_user_roadmap(user_id)
    return jsonify({'success': True, 'roadmap_info': result})

@app.route('/api/bookmarks/toggle', methods=['POST'])
@login_required
def api_bookmark_toggle():
    user_id = session['user_id']
    data = request.get_json() or {}
    item_type = data.get('item_type')
    item_id = data.get('item_id')

    if not item_type or not item_id:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute(
        "SELECT id FROM user_bookmarks WHERE user_id = ? AND item_type = ? AND item_id = ?",
        (user_id, item_type, item_id)
    ).fetchone()

    if existing:
        cursor.execute("DELETE FROM user_bookmarks WHERE id = ?", (existing['id'],))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'is_bookmarked': False})
    else:
        cursor.execute(
            "INSERT INTO user_bookmarks (user_id, item_type, item_id) VALUES (?, ?, ?)",
            (user_id, item_type, item_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'is_bookmarked': True})

# ==============================================================================
# 12. LEGAL PAGES & RESUME DOWNLOAD
# ==============================================================================

@app.route('/terms')
def terms_page():
    return render_template('terms.html')

@app.route('/privacy')
def privacy_page():
    return render_template('privacy.html')

@app.route('/resume/download-original')
@login_required
@role_required(['USER'])
def download_original_resume():
    """Downloads the candidate's originally uploaded resume file."""
    user_id = session['user_id']
    conn = get_db_connection()
    latest_resume = conn.execute(
        "SELECT * FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()

    if not latest_resume:
        flash("No uploaded resume found.", "warning")
        return redirect(url_for('resume_hub'))

    filepath = os.path.join(Config.UPLOAD_FOLDER, latest_resume['filename'])
    if not os.path.exists(filepath):
        if latest_resume['raw_text']:
            return Response(
                latest_resume['raw_text'],
                mimetype='text/plain',
                headers={'Content-Disposition': f'attachment; filename="{latest_resume["original_filename"]}"'}
            )
        flash("Original resume file not found on server.", "danger")
        return redirect(url_for('resume_hub'))

    return send_file(
        filepath,
        as_attachment=True,
        download_name=latest_resume['original_filename']
    )

@app.route('/resume/download-updated')
@app.route('/resume/download-improved')
@login_required
@role_required(['USER'])
def download_updated_resume():
    """
    Downloads the AI-updated re-entry resume as a genuine .docx file
    (or as .txt if format=txt requested).
    """
    user_id = session['user_id']
    download_format = request.args.get('format', 'docx').lower()
    user_context = get_complete_user_context(user_id)
    candidate_name = (user_context.get('name') or 'Candidate').replace(' ', '_')

    conn = get_db_connection()
    latest_resume = conn.execute(
        "SELECT * FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone()

    if not latest_resume:
        conn.close()
        flash("No resume found. Please upload a resume first.", "warning")
        return redirect(url_for('resume_hub'))

    analysis_row = conn.execute(
        "SELECT * FROM resume_analyses WHERE resume_id = ?", (latest_resume['id'],)
    ).fetchone()
    conn.close()

    if not analysis_row:
        flash("Please analyze your resume first.", "warning")
        return redirect(url_for('resume_hub'))

    analysis_dict = dict(analysis_row)
    enhanced_text = analysis_dict.get('updated_resume_text') or analysis_dict.get('enhanced_resume_text')
    docx_file = analysis_dict.get('updated_resume_docx_path')

    if download_format == 'txt' or not docx_file:
        if not enhanced_text:
            enhanced_text = "ReTurn Professional Re-Entry Resume"
        filename = f"ReTurn_Updated_Resume_{candidate_name}.txt"
        return Response(
            enhanced_text,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    # DOCX format download
    updated_folder = os.path.join(Config.UPLOAD_FOLDER, 'updated_resumes')
    docx_path = os.path.join(updated_folder, docx_file)

    if not os.path.exists(docx_path):
        os.makedirs(updated_folder, exist_ok=True)
        generate_updated_resume_docx(
            latest_resume['raw_text'] or '',
            user_context,
            analysis_dict.get('target_role') or 'Professional Returnee',
            docx_path,
            enhanced_text
        )

    return send_file(
        docx_path,
        as_attachment=True,
        download_name=f"ReTurn_Updated_Resume_{candidate_name}.docx",
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

# ==============================================================================
# 13. AI ROADMAP GENERATION API
# ==============================================================================

@app.route('/api/ai/generate-roadmap', methods=['POST'])
@login_required
@role_required(['USER'])
def api_generate_ai_roadmap():
    """Generates a personalized AI-driven learning roadmap."""
    user_id = session['user_id']
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    cs = conn.execute("SELECT pathway FROM career_selections WHERE user_id = ?", (user_id,)).fetchone()
    pathway = cs['pathway'] if cs else 'EXPERIENCED_GAP'

    if not profile or not profile['profile_completed']:
        conn.close()
        return jsonify({'success': False, 'error': 'Please complete your profile first.'}), 400

    from services.ai_service import generate_personalized_roadmap
    p_dict = dict(profile)
    roadmap = generate_personalized_roadmap(p_dict, pathway)
    conn.close()

    return jsonify({'success': True, 'roadmap': roadmap})

# ==============================================================================
# 14. ERROR HANDLERS
# ==============================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        'error.html',
        error_code='404',
        error_title='Page Not Found',
        error_message='The requested URL does not exist on the ReTurn platform.'
    ), 404

@app.errorhandler(500)
def server_error(e):
    return render_template(
        'error.html',
        error_code='500',
        error_title='Service Temporarily Unavailable',
        error_message='An unexpected error occurred while processing your request. Please try again shortly.'
    ), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
