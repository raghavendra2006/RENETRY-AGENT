# ReTurn: Women Career Gap — Re-Entry & Opportunity Platform

A complete, production-grade, human-centered web application built to empower women returning to employment, education, entrepreneurship, freelancing, or career transition after a career break.

---

## 🌟 Core Product Principles

- **No Fake Data Guarantee**: Zero fabricated statistics, fake testimonials, fake company logos, fake user reviews, or artificial job counts.
- **Job Authenticity & Trust System**: Transparent 3-tier categorization with explicit source indicators:
  1. **Verified Recruiter**: Direct corporate employer reviewed and verified by platform administrators.
  2. **Official Government Source**: Verifiable public schemes and gazette links (`.gov.in` / `.nic.in`).
  3. **External Job Source**: Clearly flagged public opportunities with an explicit reminder to verify on the employer's official careers portal.
- **Action-Oriented UX**: Every major screen explicitly answers: *"What should I do next?"*
- **Strict 3-Module Architecture**:
  1. **USER Module** (Profile, 3 distinct career pathways, 7-stage roadmap, resume analyzer & improver, opportunity matching, government hub, startup hub, bookmarks).
  2. **RECRUITER Module** (Separate recruiter registration, verification status lifecycle, structured vacancy posting, applicant management).
  3. **ADMIN Module** (Operational live-database metrics, recruiter domain verification queue, job content moderation, user registry, verified scheme and learning resource management).

---

## 🧭 The Three Career Pathways

1. **Pathway 1: Experienced + Career Gap**
   - Built for women with prior professional experience returning after caregiving, health recovery, relocation, or personal breaks.
   - **Private Sector**: Career readiness assessment, skill gap audit, real PDF/DOCX resume analysis, and verified corporate returnships.
   - **Government Opportunities**: Statutory age concessions (5–10 years), public research fellowships (*Women Scientist Scheme WOS-A / DISHA*), and civil services exams.
   - **Startup / Freelance Hub**: Idea submission, feasibility evaluation, 4-phase MVP roadmap, and verified public credit (*Stand-Up India*, *Mudra Yojana*).
2. **Pathway 2: No Previous Experience**
   - Constructive, non-stigmatizing entry path for graduates or home-makers entering the formal workforce for the first time.
   - Focuses on core interest mapping, verified free learning (SWAYAM, Skill India), and an **Authentic First-Time Resume Builder** that highlights education, academic projects, coursework, and organizational strengths without inventing employment history.
3. **Pathway 3: Career Shift & Transition**
   - For professionals pivoting from one sector (e.g. teaching, administration, retail, banking) into modern digital, operations, or technical tracks.
   - Features **Transferable Skill Mapping**, technical gap prioritization, bridge portfolio projects, and **Hybrid Functional Resume Restructuring**.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10 with **Flask 3.1.1**
- **Database**: **SQLite 3** with foreign key constraints, indexes, and full relational tables (`users`, `profiles`, `career_selections`, `user_roadmaps`, `roadmap_tasks`, `resumes`, `resume_analyses`, `jobs`, `recruiters`, `government_opportunities`, `learning_resources`, `startup_ideas`, `user_bookmarks`, `job_applications`, `chat_logs`, `admin_audit_logs`).
- **File Parsing & Analysis**: `pypdf` and `python-docx` for substantive qualitative and structural text analysis (missing sections, action verbs, role keywords, STAR rewrites, auto-improved draft generation).
- **Frontend**: Clean, modern, responsive UI built with **Tailwind CSS**, accessible semantic HTML5, and vanilla JavaScript (no heavy node build steps required).
- **Security**: Password hashing via `werkzeug.security`, HttpOnly session cookies, input validation, secure file naming, and strict role-based access control (RBAC).

---

## 🚀 Getting Started

### 1. Installation
```bash
cd re_turn
pip install -r requirements.txt
```

### 2. Initialize & Seed Authentic Data
```bash
python seed_data.py
```

### 3. Run Automated Tests
```bash
python test_platform.py
```

### 4. Start the Application Server
```bash
python app.py
```
Open your browser at: **`http://localhost:5000`**

---

## 🔐 Demonstration & Test Credentials

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@return.internal` | `AdminPassword123!` | Full operational control, recruiter verification queue, content moderation, live metrics. |
| **Verified Recruiter** | `recruiter@techworks.com` | `Recruiter123!` | Verified corporate domain (`TechWorks Global Solutions`). Posts carry "Verified Recruiter" badge. |
| **Pending Recruiter** | `recruiter@innovatesoft.com` | `Recruiter123!` | Pending verification (`InnovateSoft Systems`). Used to demonstrate the admin approval workflow. |
| **Candidate / User** | Any new registration | (Your password) | Direct registration at `/register` leads immediately to the Profile Builder and Pathway Selector. |

---

## 📋 Verification Checklist

- [x] Landing page with clean navigation, workflow diagram, sections A-F, trust explanation, and responsive footer.
- [x] Secure authentication with RBAC (`USER`, `RECRUITER`, `ADMIN`).
- [x] Complete profile builder with respectful, optional career pause handling.
- [x] Choice of 3 dedicated pathways with dynamic 7-stage interactive roadmaps.
- [x] Real resume analyzer supporting PDF/DOCX/TXT file uploads with structural audit, keyword mapping, STAR rewrites, and auto-improved draft.
- [x] Government opportunities hub with multi-criteria filters and direct links to official `.gov.in` portals.
- [x] Startup & freelance feasibility evaluator with 4-phase MVP plan and statutory funding disclaimers.
- [x] Verified recruiter dashboard and job posting with "Verified Recruiter" trust badges.
- [x] Administrative moderation console with live operational metrics and verification queue.
- [x] Non-intrusive embedded assistant chatbot with contextual answers and zero exposed API keys.
- [x] 100% test coverage passing via `test_platform.py`.
