import os
import re
import json
import urllib.request
import urllib.error
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from database import init_db, get_db_connection

# Load .env file locally if present
def load_dotenv_fallback(filepath='.env'):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass

load_dotenv_fallback()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mait-super-secret-key-2026-secure')

# Initialize DB and seed data
init_db()

UNANSWERED_DEFAULT_REPLY = "I'm not sure about this, I've forwarded it to college staff"

CATEGORY_KEYWORDS = {
    'Fees': ['fee', 'fees', 'tuition', 'fine', 'dues', 'payment', 'challan', 'cost', 'pay'],
    'Exams': ['exam', 'exams', 'examination', 'datesheet', 'date-sheet', 'mid-term', 'end-term', 'admit', 'result', 'paper', 'marks', 'ipu'],
    'Timetable': ['timetable', 'time-table', 'timing', 'timings', 'schedule', 'lecture', 'recess', 'period', 'class hours'],
    'Attendance': ['attendance', 'detain', 'detained', 'shortage', '75%', '75 percent', 'medical certificate', 'medical'],
    'Notices': ['notice', 'notices', 'circular', 'circulars', 'announcement', 'certificate', 'bonafide', 'character'],
    'Hostel': ['hostel', 'hostels', 'mess', 'curfew', 'room', 'warden', 'accommodation'],
    'Library': ['library', 'book', 'books', 'borrow', 'issue', 'reading room', 'return'],
    'Placements': ['placement', 'placements', 'company', 'companies', 'recruit', 'recruiter', 'package', 'ctc', 't&p', 'internship', 'tpo', 'jobs']
}

def detect_category(text, matched_faq_category=None):
    if matched_faq_category:
        return matched_faq_category
    lower_text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', lower_text):
                return category
    return 'Other'

def keyword_match_faq(user_query, faqs):
    query_clean = re.sub(r'[^\w\s]', ' ', user_query.lower())
    stopwords = {
        'what', 'is', 'the', 'of', 'in', 'at', 'for', 'to', 'a', 'an', 'and', 'how', 'can', 'i',
        'do', 'where', 'when', 'my', 'me', 'please', 'tell', 'about', 'mait', 'are', 'there',
        'does', 'any', 'college', 'delhi', 'who', 'with', 'on', 'campus', 'institute',
        'student', 'students', 'has', 'have', 'provide', 'provided', 'facility', 'facilities',
        'get', 'give', 'take', 'information', 'details', 'rule', 'rules'
    }
    query_tokens = [w for w in query_clean.split() if w not in stopwords and len(w) > 2]
    
    if not query_tokens:
        return None

    best_faq = None
    best_score = 0

    for faq in faqs:
        q_text = faq['question'].lower()
        a_text = faq['answer'].lower()
        score = 0
        
        # Exact question match or high phrase similarity
        if user_query.lower().strip() in q_text:
            score += 20

        matched_tokens = 0
        for token in query_tokens:
            if re.search(r'\b' + re.escape(token) + r'\b', q_text):
                score += 5
                matched_tokens += 1
            elif re.search(r'\b' + re.escape(token) + r'\b', a_text):
                score += 2
                matched_tokens += 1
                
        # Category bonus if category keyword is explicitly mentioned
        if faq['category'].lower() in query_clean:
            score += 4

        # Only count if at least one meaningful token matched specifically
        if score > best_score and matched_tokens > 0:
            best_score = score
            best_faq = faq

    # Minimum threshold of 5 for confidence (requires either question token match or multiple tokens)
    if best_faq and best_score >= 5:
        return best_faq
    return None

def query_gemini_api(user_query, faqs, api_key):
    faq_context_lines = []
    for f in faqs:
        faq_context_lines.append(f"[{f['category']}] Question: {f['question']}\nAnswer: {f['answer']}")
    faq_context = "\n\n".join(faq_context_lines)

    system_instruction = (
        "You are the official student helpdesk AI assistant for Maharaja Agrasen Institute of Technology (MAIT), Delhi. "
        "Answer the student's question accurately and politely based ONLY on the provided FAQ context below. "
        "Rules:\n"
        "1. If the answer is directly or reasonably covered in the FAQ context, provide a helpful and direct answer.\n"
        "2. If the answer is NOT found in the FAQ context, you MUST reply with EXACTLY:\n"
        "\"I'm not sure about this, I've forwarded it to college staff\"\n"
        "Do not invent facts, contact numbers, or dates not in the context."
    )

    prompt_content = f"FAQ CONTEXT:\n{faq_context}\n\nSTUDENT QUESTION:\n{user_query}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instruction}\n\n{prompt_content}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 300
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=7) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            candidates = data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return parts[0].get('text', '').strip()
    except Exception as e:
        # Fall back will be triggered
        return None
    return None

def log_message(user_query, bot_response, category):
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO messages (query, response, category) VALUES (?, ?, ?)',
            (user_query, bot_response, category)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def save_unanswered(user_query, category):
    try:
        conn = get_db_connection()
        # Avoid duplicate pending entries for identical questions
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM unanswered_queries WHERE question = ? AND status = "Pending"',
            (user_query,)
        )
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO unanswered_queries (question, category, status) VALUES (?, ?, "Pending")',
                (user_query, category)
            )
            conn.commit()
        conn.close()
    except Exception:
        pass

# Admin login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== PUBLIC CHAT ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    user_query = data.get('message', '').strip()

    if not user_query:
        return jsonify({'reply': 'Please type a question.', 'category': 'Other'}), 400

    conn = get_db_connection()
    faqs = conn.execute('SELECT id, question, answer, category FROM faqs').fetchall()
    conn.close()

    api_key = os.environ.get('GEMINI_API_KEY')
    answer = None
    detected_cat = None

    # Try Gemini API if key is present
    if api_key and api_key != 'your_gemini_api_key_here':
        api_response = query_gemini_api(user_query, faqs, api_key)
        if api_response:
            answer = api_response

    # Fallback to keyword matching if Gemini absent or failed
    if not answer:
        matched_faq = keyword_match_faq(user_query, faqs)
        if matched_faq:
            answer = matched_faq['answer']
            detected_cat = matched_faq['category']

    # If still no answer or bot answered unsure
    if not answer or "not sure about this" in answer.lower() or "forwarded it to college staff" in answer.lower():
        reply = UNANSWERED_DEFAULT_REPLY
        category = detected_cat or detect_category(user_query)
        save_unanswered(user_query, category)
    else:
        reply = answer
        category = detected_cat or detect_category(user_query)

    # Save to chat history log
    log_message(user_query, reply, category)

    return jsonify({
        'reply': reply,
        'category': category
    })

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE email = ?', (email,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_email'] = admin['email']
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid email or password. Please try again.'

    return render_template('login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db_connection()
    faqs = conn.execute('SELECT * FROM faqs ORDER BY category, id DESC').fetchall()
    unanswered = conn.execute(
        'SELECT * FROM unanswered_queries WHERE status = "Pending" ORDER BY id DESC'
    ).fetchall()
    total_queries = conn.execute('SELECT COUNT(*) as count FROM messages').fetchone()['count']
    conn.close()

    categories = ['Fees', 'Exam Schedule', 'Timetable', 'Attendance', 'Notices', 'Hostel', 'Library', 'Placements', 'Other']

    return render_template(
        'admin.html',
        faqs=faqs,
        unanswered=unanswered,
        total_queries=total_queries,
        categories=categories
    )

@app.route('/admin/faq/add', methods=['POST'])
@login_required
def add_faq():
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    category = request.form.get('category', 'Other').strip()

    if question and answer:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)',
            (question, answer, category)
        )
        conn.commit()
        conn.close()
        flash('FAQ added successfully!', 'success')
    else:
        flash('Question and Answer are required.', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/faq/edit/<int:faq_id>', methods=['POST'])
@login_required
def edit_faq(faq_id):
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    category = request.form.get('category', 'Other').strip()

    if question and answer:
        conn = get_db_connection()
        conn.execute(
            'UPDATE faqs SET question = ?, answer = ?, category = ? WHERE id = ?',
            (question, answer, category, faq_id)
        )
        conn.commit()
        conn.close()
        flash('FAQ updated successfully!', 'success')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/faq/delete/<int:faq_id>', methods=['POST'])
@login_required
def delete_faq(faq_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM faqs WHERE id = ?', (faq_id,))
    conn.commit()
    conn.close()
    flash('FAQ deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unanswered/convert/<int:query_id>', methods=['POST'])
@login_required
def convert_unanswered(query_id):
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    category = request.form.get('category', 'Other').strip()

    if question and answer:
        conn = get_db_connection()
        # Add to FAQs
        conn.execute(
            'INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)',
            (question, answer, category)
        )
        # Mark unanswered query as resolved
        conn.execute(
            'UPDATE unanswered_queries SET status = "Resolved" WHERE id = ?',
            (query_id,)
        )
        conn.commit()
        conn.close()
        flash('Query converted into a live FAQ!', 'success')
    else:
        flash('Answer cannot be empty.', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unanswered/delete/<int:query_id>', methods=['POST'])
@login_required
def delete_unanswered(query_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM unanswered_queries WHERE id = ?', (query_id,))
    conn.commit()
    conn.close()
    flash('Unanswered query removed.', 'info')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
