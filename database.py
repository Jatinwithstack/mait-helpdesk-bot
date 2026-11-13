import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mait_helpdesk.db')

SEED_FAQS = [
    {
        "category": "Fees",
        "question": "How can I pay my annual academic fees at MAIT?",
        "answer": "Academic fees can be paid online via the official MAIT Student Portal using Net Banking, Debit/Credit Card, or UPI. You can also generate an offline challan from the portal and deposit fees at the designated campus bank branch."
    },
    {
        "category": "Fees",
        "question": "What is the fee payment deadline and late fine policy?",
        "answer": "Academic fees for odd semesters must be paid by August 15th, and even semesters by January 15th. A late fee of Rs. 100 per day is charged for delays up to 15 days, after which special permission from the Accounts Office is mandatory."
    },
    {
        "category": "Exam Schedule",
        "question": "When are the IPU end-term semester examinations conducted?",
        "answer": "End-term theory examinations are typically conducted in December-January for odd semesters and in May-June for even semesters by Guru Gobind Singh Indraprastha University (GGSIPU). Practical exams precede theory papers."
    },
    {
        "category": "Exam Schedule",
        "question": "Where can I download the mid-term datesheet?",
        "answer": "Internal mid-term (minor) exam datesheets are published on the official MAIT website (mait.ac.in) under the 'Notice Board' section and displayed on respective departmental notice boards 2 weeks before exams."
    },
    {
        "category": "Timetable",
        "question": "Where can I find my semester class timetable?",
        "answer": "Semester class timetables are uploaded on the MAIT portal and pinned on respective department notice boards (CSE, IT, ECE, MAE, etc.) before the start of each semester. You can also get it from your class coordinator."
    },
    {
        "category": "Timetable",
        "question": "What are the official college hours and class timings at MAIT?",
        "answer": "College working hours are from 8:30 AM to 4:30 PM, Monday through Friday. Each lecture period lasts 50 minutes, with a scheduled lunch recess from 12:40 PM to 1:20 PM."
    },
    {
        "category": "Attendance",
        "question": "What is the minimum attendance requirement to appear for exams?",
        "answer": "As per GGSIPU norms, a minimum of 75% aggregate attendance across all theory and practical subjects is mandatory to be eligible for end-term semester examinations."
    },
    {
        "category": "Attendance",
        "question": "How can I submit medical certificates for attendance shortage?",
        "answer": "Medical certificates along with a parent-signed application must be submitted to the respective Head of Department (HOD) within 7 days of returning to college. A maximum relaxation of 5% to 10% may be granted per university guidelines."
    },
    {
        "category": "Notices",
        "question": "Where can I check official circulars and notices?",
        "answer": "Official announcements, holiday lists, and university circulars are available on the official MAIT website at www.mait.ac.in under 'Notices & Circulars', as well as the GGSIPU portal (ipu.ac.in)."
    },
    {
        "category": "Notices",
        "question": "How do I apply for a Bonafide or Character Certificate?",
        "answer": "Submit a prescribed application form at the Academic Administration Cell (Room 102, Block 1) along with your student ID card copy and fee clearance slip. Certificates are issued within 2-3 working days."
    },
    {
        "category": "Hostel",
        "question": "Does MAIT provide on-campus hostel accommodation?",
        "answer": "Yes, MAIT has on-campus hostel facilities for boys with air-cooled rooms, Wi-Fi, 24/7 security, gym, and mess facilities. Seats are allotted on a first-come, first-served basis and distance criteria during admission."
    },
    {
        "category": "Hostel",
        "question": "What are the hostel mess timings and rules?",
        "answer": "Hostel mess timings: Breakfast (7:30 AM - 9:00 AM), Lunch (12:30 PM - 2:00 PM), Evening Snacks (5:00 PM - 6:00 PM), and Dinner (8:00 PM - 9:30 PM). Night curfew for hostelers is 9:30 PM."
    },
    {
        "category": "Library",
        "question": "What are the MAIT Central Library operating hours and book borrowing limits?",
        "answer": "The Central Library is open Monday to Friday from 8:30 AM to 7:00 PM and on Saturdays from 9:00 AM to 5:00 PM. B.Tech students can borrow up to 4 books for 14 days, with options for online renewal."
    },
    {
        "category": "Placements",
        "question": "Which top recruiters visit MAIT for campus placements?",
        "answer": "Top recruiters include Google, Microsoft, Amazon, Atlassian, Infosys, TCS, Wipro, ZS Associates, Cognizant, and Accenture. The Training and Placement Cell (T&P) coordinates all on-campus and virtual drives."
    },
    {
        "category": "Placements",
        "question": "What is the eligibility criterion for campus placements?",
        "answer": "Students typically require a minimum CGPA of 6.5 or above (some companies require 7.0+) with no active backlogs. Registration with the Training and Placement Cell in the 6th semester is mandatory."
    }
]

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Admins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # FAQs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Unanswered queries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unanswered_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            category TEXT DEFAULT 'Other',
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Chat history / message log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            category TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed admin if not present
    cursor.execute('SELECT id FROM admins WHERE email = ?', ('admin@mait.edu',))
    if cursor.fetchone() is None:
        admin_pass_hash = generate_password_hash('Admin@123')
        cursor.execute('INSERT INTO admins (email, password_hash) VALUES (?, ?)',
                       ('admin@mait.edu', admin_pass_hash))

    # Seed FAQs if empty
    cursor.execute('SELECT COUNT(*) as count FROM faqs')
    row = cursor.fetchone()
    if row['count'] == 0:
        for faq in SEED_FAQS:
            cursor.execute(
                'INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)',
                (faq['question'], faq['answer'], faq['category'])
            )

    conn.commit()
    conn.close()
