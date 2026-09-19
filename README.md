<p align="center">
  <h1 align="center">🚀 ReTurn Platform</h1>
  <p align="center">
    <strong>AI-Powered Career Re-Entry & Opportunity Platform for Women</strong>
  </p>
  <p align="center">
    <a href="#-features">Features</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-getting-started">Getting Started</a> •
    <a href="#-deployment">Deployment</a> •
    <a href="#-demo-credentials">Demo</a> •
    <a href="#-contributing">Contributing</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/flask-3.x-green?style=flat-square&logo=flask&logoColor=white" alt="Flask 3.x">
    <img src="https://img.shields.io/badge/AI-Gemini%20Powered-orange?style=flat-square&logo=google&logoColor=white" alt="Gemini AI">
    <img src="https://img.shields.io/badge/deploy-Render-purple?style=flat-square&logo=render&logoColor=white" alt="Render Deploy">
    <img src="https://img.shields.io/badge/license-MIT-brightgreen?style=flat-square" alt="MIT License">
  </p>
</p>

---

## 📖 About

**ReTurn** is a production-grade, AI-powered web platform designed to empower women re-entering the workforce after a career break — whether they're returning to employment, starting a business, pursuing education, or shifting careers entirely.

The platform provides **personalized career roadmaps**, **AI-driven resume analysis**, **verified job matching**, **government scheme discovery**, and a **startup feasibility evaluator** — all within a role-based ecosystem connecting candidates, recruiters, and platform administrators.

> **🎯 Core Promise** — *No fake data. No fabricated statistics. No artificial testimonials. Every opportunity is either recruiter-verified, government-sourced, or clearly flagged for independent verification.*

---

## ✨ Features

### 🧑‍💼 For Candidates (Users)

| Feature | Description |
|---------|-------------|
| **3 Career Pathways** | Personalized tracks for experienced professionals, first-time workers, and career switchers |
| **7-Stage Interactive Roadmap** | AI-generated, step-by-step career progression with task tracking |
| **Resume Analyzer & Improver** | Upload PDF/DOCX/TXT — get structural audit, keyword analysis, STAR rewrites, and an auto-improved draft |
| **AI Career Gap Analysis** | Contextual analysis powered by Google Gemini with actionable recommendations |
| **Job Matching Engine** | Intelligent opportunity matching based on skills, experience, and preferences |
| **Government Schemes Hub** | Verified public programs with direct links to official `.gov.in` portals |
| **Startup Feasibility Evaluator** | Idea submission, market analysis, 4-phase MVP roadmap, and funding scheme mapping |
| **AI Chatbot Assistant** | Context-aware embedded chatbot for real-time career guidance |
| **Bookmarks & Notifications** | Save opportunities and track application updates |

### 👔 For Recruiters

| Feature | Description |
|---------|-------------|
| **Verified Employer Profiles** | Domain-verified company accounts with trust badges |
| **Structured Job Posting** | Post vacancies with skill requirements, work modes, and compensation details |
| **Applicant Management** | Review candidate profiles and manage the hiring pipeline |
| **Verification Lifecycle** | Transparent pending → verified → active status workflow |

### 🛡️ For Administrators

| Feature | Description |
|---------|-------------|
| **Live Operational Dashboard** | Real-time platform metrics and analytics |
| **Recruiter Verification Queue** | Domain verification and approval workflow |
| **Content Moderation** | Job listing review and management |
| **User Management** | User registry with role-based access control |
| **Resource Management** | Curate verified government schemes and learning resources |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+ · Flask 3.x · Gunicorn |
| **Database** | SQLite 3 (WAL mode, foreign keys, indexes) |
| **AI Engine** | Google Gemini API (configurable provider) |
| **File Parsing** | `pypdf` · `python-docx` for resume analysis |
| **Frontend** | Tailwind CSS · Semantic HTML5 · Vanilla JavaScript |
| **Security** | Werkzeug password hashing · HttpOnly cookies · RBAC · CSRF protection |
| **Deployment** | Render · Gunicorn WSGI |

---

## 📁 Project Structure

```
RETURN-AGENT/
├── app.py                    # Main Flask application (routes, views, API endpoints)
├── config.py                 # Application configuration & environment variables
├── database.py               # Database schema, connection management, migrations
├── seed_data.py              # Authentic seed data for demo & testing
├── test_platform.py          # Comprehensive test suite
├── requirements.txt          # Python dependencies
├── build.sh                  # Render deployment build script
├── .env.example              # Environment variables template
├── .gitignore
│
├── services/
│   ├── ai_service.py         # Gemini AI integration, career analysis, resume AI
│   ├── auth_service.py       # Authentication, session management, RBAC
│   ├── chatbot_service.py    # Context-aware AI chatbot engine
│   ├── job_matcher.py        # Intelligent job-candidate matching algorithm
│   ├── notification_service.py  # In-app notification system
│   ├── resume_analyzer.py    # PDF/DOCX parsing, structural audit, STAR rewrites
│   ├── roadmap_engine.py     # 7-stage career roadmap generation & tracking
│   └── startup_analyzer.py   # Startup idea feasibility & MVP planning
│
├── templates/
│   ├── base.html             # Master layout template
│   ├── index.html            # Landing page
│   ├── auth/                 # Login, register, password recovery
│   ├── user/                 # Candidate dashboard, pathways, roadmap, resume hub
│   ├── recruiter/            # Recruiter dashboard, job management, profile
│   ├── admin/                # Admin dashboard, verification, moderation
│   ├── explore/              # Public job browsing & detail views
│   └── learning/             # Learning resources hub
│
└── static/
    ├── css/main.css          # Stylesheet
    ├── js/                   # Client-side scripts (app, chatbot, resume, roadmap)
    └── uploads/              # User-uploaded files (resumes, documents)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **pip** (Python package manager)
- A **Google Gemini API key** ([Get one free](https://aistudio.google.com/apikey))

### 1. Clone the Repository

```bash
git clone https://github.com/raghavendra2006/RENETRY-AGENT.git
cd RENETRY-AGENT
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```env
SECRET_KEY=your_secure_secret_key
AI_API_KEY=your_gemini_api_key_here
AI_PROVIDER=gemini
AI_MODEL=gemini-flash-latest
DATABASE_PATH=return_platform.db
PORT=5000
FLASK_ENV=development
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database & Seed Data

```bash
python seed_data.py
```

### 5. Run the Application

```bash
python app.py
```

🌐 Open your browser at **http://localhost:5000**

### 6. Run Tests (Optional)

```bash
python test_platform.py
```

---

## ☁️ Deployment

### Deploy to Render (Free Tier)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your GitHub repository
4. Configure the service:

| Setting | Value |
|---------|-------|
| **Runtime** | Python 3 |
| **Build Command** | `bash build.sh` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

5. Add your environment variables in the Render dashboard
6. Click **Deploy** 🚀

> **Note:** The free tier uses an ephemeral filesystem — the SQLite database resets on each deploy. For production persistence, upgrade to a paid plan or switch to PostgreSQL.

---

## 🔐 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@return.internal` | `AdminPassword123!` |
| **Verified Recruiter** | `recruiter@techworks.com` | `Recruiter123!` |
| **Pending Recruiter** | `recruiter@innovatesoft.com` | `Recruiter123!` |
| **Candidate** | Register at `/register` | *(your password)* |

---

## 🔧 Configuration

### AI Provider Setup

The platform supports configurable AI providers through environment variables:

```env
# Google Gemini (Default)
AI_PROVIDER=gemini
AI_MODEL=gemini-flash-latest
AI_API_KEY=your_key_here
```

If no API key is configured, the platform gracefully falls back to intelligent heuristic-based analysis — all core features remain functional without AI.

### Database

The platform uses SQLite with the following optimizations:
- **WAL journal mode** for concurrent read performance
- **Foreign key constraints** for data integrity
- **30-second busy timeout** for handling concurrent writes
- **Indexed columns** for optimized query performance

**Tables:** `users`, `profiles`, `career_selections`, `user_roadmaps`, `roadmap_tasks`, `resumes`, `resume_analyses`, `jobs`, `recruiters`, `government_opportunities`, `learning_resources`, `startup_ideas`, `user_bookmarks`, `job_applications`, `chat_logs`, `notifications`, `admin_audit_logs`

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Flask](https://flask.palletsprojects.com/) — Lightweight Python web framework
- [Google Gemini](https://ai.google.dev/) — AI-powered career analysis
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS framework
- [Render](https://render.com/) — Cloud deployment platform

---

<p align="center">
  Built with ❤️ to empower women returning to the workforce
</p>
