# MAIT Helpdesk AI Chatbot

A dedicated full-stack college helpdesk chatbot for students of Maharaja Agrasen Institute of Technology (MAIT), Delhi. Students ask about fees, exam schedules, class timetables, attendance rules, notices, hostels, library, and placements and get instant answers.

## Tech Stack
- **Backend:** Python Flask
- **Database:** SQLite with auto-initialization and 15 seeded FAQs
- **Frontend:** Responsive Plain HTML5 / CSS3 / Vanilla JavaScript (zero build step)
- **AI Integration:** Google Gemini API with fallback keyword/similarity matcher
- **Production Server:** Gunicorn

## Quick Start (Local Run)
1. Ensure Python 3.9+ is installed.
2. Navigate to project root:
   ```bash
   cd C:\Users\jatin\.gemini\antigravity\scratch\mait-helpdesk-bot
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure `.env`:
   ```bash
   copy .env.example .env
   # Add your GEMINI_API_KEY in .env (optional: fallback matching works automatically)
   ```
5. Run the app:
   ```bash
   python app.py
   ```
6. Open your browser:
   - **Student Chat:** http://localhost:5000/
   - **Admin Portal:** http://localhost:5000/admin/login

## Default Admin Credentials
- **Email:** `admin@mait.edu`
- **Password:** `Admin@123`

## Deploy to Render
The repository includes `Procfile`, `render.yaml`, `requirements.txt`, and `.gitignore`.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Environment Variables: `GEMINI_API_KEY`, `SECRET_KEY`
