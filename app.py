# =========================================
# SMART BIOLOGY EXAM SYSTEM — BACKEND
# PART 1 — CONFIG + DATABASE MODELS
# =========================================

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import pyexcel as p
import os

app = Flask(__name__)
app.secret_key = "BIOLOGY-SYSTEM-SECRET-KEY"

# -----------------------------
# DATABASE CONFIG (SQLite)
# -----------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///biology_exam.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================================
# DATABASE MODELS
# ================================

# USER MODEL
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    username = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(300))
    role = db.Column(db.String(50))  # Teacher, Admin, SuperAdmin, Viewer
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


# GRADE LEVELS
class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


# EXAM MODEL
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    grade_id = db.Column(db.Integer, db.ForeignKey("grade.id"))
    duration = db.Column(db.Integer)
    negative = db.Column(db.Float)
    version_count = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))


# QUESTION MODEL
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"))
    question_text = db.Column(db.Text)
    type = db.Column(db.String(50))  # MCQ, TF, Short, Fill, Match, Image

    # MCQ OPTIONS
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))

    # CORRECT ANSWER
    correct_answer = db.Column(db.String(500))
    points = db.Column(db.Integer, default=1)

    # Matching questions (stored as "A:B,A2:B2")
    match_pairs = db.Column(db.String(1000))

    # Fill answers (comma-separated)
    fill_answers = db.Column(db.String(500))

    # Image question path
    image_path = db.Column(db.String(500))


# STUDENT ATTEMPTS
class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(200))
    grade = db.Column(db.String(50))
    exam_id = db.Column(db.Integer)
    score = db.Column(db.Float)
    violations = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.now)
# =========================================
# PART 2 — LOGIN SYSTEM (STAFF + STUDENT)
# =========================================

# ----------------------------------
# HOME PAGE (LOGIN SELECTION)
# ----------------------------------
@app.route("/")
def home():
    return render_template("login.html")


# ----------------------------------
# STAFF LOGIN PAGE
# ----------------------------------
# -----------------------------
# SUPERADMIN LOGIN
# -----------------------------

SUPERADMIN_CODE = "Hcsbio25"   # Your superadmin code

@app.route('/superadmin_login', methods=['GET', 'POST'])
def superadmin_login():
    if request.method == 'POST':
        code = request.form.get('code')

        if code == SUPERADMIN_CODE:
            session['role'] = 'superadmin'
            return redirect('/superadmin_dashboard')
        else:
            return render_template('superadmin_login.html', error="Invalid Superadmin Code")

    return render_template('superadmin_login.html')



# -----------------------------
# SUPERADMIN DASHBOARD (Protected)
# -----------------------------
@app.route('/superadmin_dashboard')
def superadmin_dashboard():
    if session.get('role') != 'superadmin':
        return redirect('/superadmin_login')

    return render_template('superadmin_dashboard.html')



# ----------------------------------
# TEACHER REGISTRATION
# ----------------------------------
@app.route("/register_teacher", methods=["GET", "POST"])
def register_teacher():
    if request.method == "GET":
        return render_template("register_teacher.html")

    name = request.form["name"]
    username = request.form["username"]
    password = request.form["password"]

    if User.query.filter_by(username=username).first():
        return "❌ Username already exists"

    hashed = generate_password_hash(password)

    new_teacher = User(
        name=name,
        username=username,
        password=hashed,
        role="Teacher",
        approved=False
    )

    db.session.add(new_teacher)
    db.session.commit()

    return "✔ Registration successful! Wait for admin approval."


# ----------------------------------
# STUDENT LOGIN PAGE
# ----------------------------------
@app.route("/student_login_page")
def student_login_page():
    return render_template("student_login_page.html")


# ----------------------------------
# STUDENT LOGIN HANDLER
# ----------------------------------
@app.route("/student_login", methods=["POST"])
def student_login():
    session["student_name"] = request.form["student_name"]
    session["grade"] = request.form["grade"]
    session["class_code"] = request.form["class_code"]

    return redirect("/select_exam")


# ----------------------------------
# LOGOUT
# ----------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
# =========================================
# PART 3 — EXAM CREATION + QUESTIONS + EXCEL IMPORT
# =========================================

# ----------------------------------
# TEACHER DASHBOARD
# ----------------------------------
@app.route("/teacher_dashboard")
def teacher_dashboard():
    if "role" not in session or session["role"] != "Teacher":
        return redirect("/")

    exams = Exam.query.filter_by(created_by=session["user_id"]).all()

    return render_template("teacher_dashboard.html", exams=exams)


# ----------------------------------
# CREATE EXAM
# ----------------------------------
@app.route("/create_exam", methods=["GET", "POST"])
def create_exam():
    if "role" not in session or session["role"] not in ["Teacher", "Admin", "SuperAdmin"]:
        return redirect("/")

    grades = Grade.query.all()

    if request.method == "GET":
        return render_template("create_exam.html", grades=grades)

    title = request.form["title"]
    grade = request.form["grade"]
    duration = int(request.form["duration"])
    negative = float(request.form["negative"])
    versions = int(request.form["versions"])

    new_exam = Exam(
        title=title,
        grade_id=grade,
        duration=duration,
        negative=negative,
        version_count=versions,
        created_by=session["user_id"]
    )

    db.session.add(new_exam)
    db.session.commit()

    return redirect("/teacher_dashboard")


# ----------------------------------
# SELECT EXAM FOR ADDING QUESTIONS
# ----------------------------------
@app.route("/select_exam")
def select_exam():
    exams = Exam.query.all()
    return render_template("select_exam.html", exams=exams)


# ----------------------------------
# ADD QUESTION PAGE
# ----------------------------------
@app.route("/add_question/<int:exam_id>", methods=["GET", "POST"])
def add_question(exam_id):
    exam = Exam.query.get(exam_id)

    if request.method == "GET":
        return render_template("add_question.html", exam=exam)

    q_text = request.form["question"]
    q_type = request.form["type"]
    points = int(request.form["points"])

    new_q = Question(
        exam_id=exam_id,
        question_text=q_text,
        type=q_type,
        points=points
    )

    # MCQ
    if q_type == "MCQ":
        new_q.option_a = request.form["a"]
        new_q.option_b = request.form["b"]
        new_q.option_c = request.form.get("c")
        new_q.option_d = request.form.get("d")
        new_q.correct_answer = request.form["correct_mcq"]

    # TRUE/FALSE
    elif q_type == "TF":
        new_q.correct_answer = request.form["correct_tf"]

    # SHORT ANSWER
    elif q_type == "Short":
        new_q.correct_answer = request.form["short_answer"]

    # FILL-IN-THE-BLANK
    elif q_type == "Fill":
        new_q.fill_answers = request.form["fill_answers"]

    # MATCHING
    elif q_type == "Match":
        pair1 = request.form["pair1_left"] + ":" + request.form["pair1_right"]
        pair2 = request.form["pair2_left"] + ":" + request.form["pair2_right"]
        new_q.match_pairs = pair1 + "," + pair2

    # IMAGE QUESTION
    elif q_type == "Image":
        img = request.files["image_file"]
        if img.filename != "":
            if not os.path.exists("static/uploads"):
                os.makedirs("static/uploads")

            path = f"static/uploads/{img.filename}"
            img.save(path)
            new_q.image_path = path

        new_q.correct_answer = request.form["image_answer"]

    db.session.add(new_q)
    db.session.commit()

    return redirect(f"/add_question/{exam_id}")


# ----------------------------------
# IMPORT EXCEL REDIRECT
# ----------------------------------
@app.route('/import_excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return "No file uploaded"

    file = request.files['file']

    if file.filename == "":
        return "No file selected"

    # Read Excel using pyexcel
    records = p.get_records(file_type="xlsx", file_stream=file.stream)

    # Each row becomes a dictionary
    for row in records:
        question_text = row.get("question")
        option_a = row.get("option_a")
        option_b = row.get("option_b")
        option_c = row.get("option_c")
        option_d = row.get("option_d")
        correct_answer = row.get("correct")
        marks = row.get("marks", 1)

        new_question = Question(
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            marks=marks
        )
        db.session.add(new_question)

    db.session.commit()

    return "Excel import successful"

    # Create questions
    for _, row in df.iterrows():

        q = Question(
            exam_id=exam_id,
            question_text=row["Question"],
            type="MCQ",
            option_a=row["Option A"],
            option_b=row["Option B"],
            option_c=row["Option C"],
            option_d=row["Option D"],
            correct_answer=row["Correct"],
            points=row["Points"]
        )

        db.session.add(q)

    db.session.commit()

    return "✔ Excel imported successfully!"
# =========================================
# PART 4 — STUDENT EXAM SYSTEM + ADMIN/SUPERADMIN + ANALYTICS + RUN
# =========================================

# ----------------------------------
# SELECT EXAM (Student)
# ----------------------------------
@app.route("/select_exam")
def select_exam_student():
    if "student_name" not in session:
        return redirect("/student_login_page")

    grade = session["grade"]
    exams = Exam.query.filter_by(grade_id=grade).all()

    return render_template("select_exam.html", exams=exams)


# ----------------------------------
# START EXAM
# ----------------------------------
@app.route("/start_exam/<int:exam_id>")
def start_exam(exam_id):
    if "student_name" not in session:
        return redirect("/student_login_page")

    exam = Exam.query.get(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).all()

    # Shuffle question order
    random.shuffle(questions)

    # Randomize exam version
    version = random.randint(1, exam.version_count)
    session["version"] = version
    session["current_exam"] = exam_id

    return render_template("exam.html", exam=exam, questions=questions)


# ----------------------------------
# SUBMIT EXAM + SCORING
# ----------------------------------
@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    if "student_name" not in session:
        return redirect("/student_login_page")

    exam_id = session["current_exam"]
    exam = Exam.query.get(exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).all()

    score = 0
    violations = int(request.form.get("violations", 0))

    for q in questions:
        key = f"q_{q.id}"
        answer = request.form.get(key)

        if not answer:
            continue

        # MCQ, TF, IMAGE
        if q.type in ["MCQ", "TF", "Image"]:
            if answer.strip().lower() == q.correct_answer.strip().lower():
                score += q.points
            else:
                score -= exam.negative

        # SHORT ANSWER
        elif q.type == "Short":
            if answer.strip().lower() == q.correct_answer.strip().lower():
                score += q.points

        # FILL-IN-BLANK
        elif q.type == "Fill":
            correct_list = [x.strip().lower() for x in q.fill_answers.split(",")]
            if answer.strip().lower() in correct_list:
                score += q.points

        # MATCHING
        elif q.type == "Match":
            is_correct = True
            pairs = q.match_pairs.split(",")

            for i, pair in enumerate(pairs, start=1):
                left, right = pair.split(":")
                user_right = request.form.get(f"q_{q.id}_{i}", "").lower().strip()
                if user_right != right.lower().strip():
                    is_correct = False

            if is_correct:
                score += q.points

    if score < 0:
        score = 0

    # Save attempt
    attempt = Attempt(
        student_name=session["student_name"],
        grade=session["grade"],
        exam_id=exam_id,
        score=score,
        violations=violations
    )

    db.session.add(attempt)
    db.session.commit()

    session.pop("current_exam", None)

    return render_template("exam_submitted.html", score=score)


# ======================================================
# TEACHER FEATURES — VIEW ATTEMPTS + ANALYTICS
# ======================================================
@app.route("/teacher_dashboard_attempts")
def teacher_dashboard_attempts():
    if session.get("role") != "Teacher":
        return redirect("/")

    teacher_id = session["user_id"]
    exams = Exam.query.filter_by(created_by=teacher_id).all()

    exam_ids = [e.id for e in exams]

    attempts = Attempt.query.filter(Attempt.exam_id.in_(exam_ids)) \
                            .order_by(Attempt.date.desc()).all()

    return render_template("teacher_attempts.html", attempts=attempts, exams=exams)


@app.route("/teacher_attempts_by_exam", methods=["POST"])
def teacher_attempts_by_exam():
    exam_id = request.form["exam_id"]
    attempts = Attempt.query.filter_by(exam_id=exam_id).all()

    exams = Exam.query.filter_by(created_by=session["user_id"]).all()

    return render_template("teacher_attempts.html", attempts=attempts, exams=exams)


# ----------------------------------
# ANALYTICS (All roles)
# ----------------------------------
@app.route("/analytics")
def analytics():
    if "role" not in session:
        return redirect("/")

    attempts = Attempt.query.order_by(Attempt.date.desc()).all()
    exams = Exam.query.all()

    total = len(attempts)
    avg = sum([a.score for a in attempts]) / total if total > 0 else 0
    highest = max([a.score for a in attempts], default=0)
    lowest = min([a.score for a in attempts], default=0)

    return render_template("analytics.html",
                           attempts=attempts,
                           exams=exams,
                           total_attempts=total,
                           avg_score=round(avg, 2),
                           highest=highest,
                           lowest=lowest)


# ======================================================
# ADMIN + SUPERADMIN FEATURES
# ======================================================

@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "Admin":
        return redirect("/")
    return render_template("admin_dashboard.html")


# ----------------------------------
# APPROVE TEACHERS
# ----------------------------------
@app.route("/pending_teachers")
def pending_teachers():
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    pending = User.query.filter_by(role="Teacher", approved=False).all()
    return render_template("approve_teachers.html", pending=pending)


@app.route("/approve_teacher/<int:user_id>", methods=["POST"])
def approve_teacher(user_id):
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    user = User.query.get(user_id)
    user.approved = True
    db.session.commit()
    return redirect("/pending_teachers")


@app.route("/reject_teacher/<int:user_id>", methods=["POST"])
def reject_teacher(user_id):
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect("/pending_teachers")


# ----------------------------------
# GRADE MANAGEMENT
# ----------------------------------
@app.route("/manage_grades")
def manage_grades():
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    grades = Grade.query.all()
    return render_template("manage_grades.html", grades=grades)


@app.route("/add_grade", methods=["POST"])
def add_grade():
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    grade_name = request.form["grade_name"]
    db.session.add(Grade(name=grade_name))
    db.session.commit()
    return redirect("/manage_grades")


@app.route("/rename_grade/<int:grade_id>", methods=["POST"])
def rename_grade(grade_id):
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    new_name = request.form["new_name"]
    grade = Grade.query.get(grade_id)
    grade.name = new_name
    db.session.commit()
    return redirect("/manage_grades")


@app.route("/delete_grade/<int:grade_id>", methods=["POST"])
def delete_grade(grade_id):
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    grade = Grade.query.get(grade_id)
    db.session.delete(grade)
    db.session.commit()
    return redirect("/manage_grades")


# ----------------------------------
# USER MANAGEMENT
# ----------------------------------
@app.route("/manage_users")
def manage_users():
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    users = User.query.all()
    return render_template("manage_users.html", users=users)


@app.route("/change_role/<int:user_id>", methods=["POST"])
def change_role(user_id):
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    user = User.query.get(user_id)
    new_role = request.form["role"]

    # Admin cannot promote to SuperAdmin
    if session["role"] == "Admin" and new_role == "SuperAdmin":
        return "❌ Only SuperAdmin can assign this role."

    user.role = new_role
    db.session.commit()
    return redirect("/manage_users")


@app.route("/reset_password/<int:user_id>", methods=["POST"])
def reset_password(user_id):
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    user = User.query.get(user_id)
    user.password = generate_password_hash("123456")
    db.session.commit()
    return redirect("/manage_users")


@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if session.get("role") not in ["Admin", "SuperAdmin"]:
        return redirect("/")

    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect("/manage_users")


# ======================================================
# DATABASE INITIALIZATION
# ======================================================
with app.app_context():
    db.create_all()


    # Default grades
    if Grade.query.count() == 0:
        defaults = ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
        for g in defaults:
            db.session.add(Grade(name=g))
        db.session.commit()

    # Default SuperAdmin
    if not User.query.filter_by(role="SuperAdmin").first():
        superadmin = User(
            name="System SuperAdmin",
            username="Hcsbio25",
            password=generate_password_hash("123456"),
            role="SuperAdmin",
            approved=True
        )
        db.session.add(superadmin)
        db.session.commit()


# ======================================================
# RUN APPLICATION (RENDER READY)
# ======================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
