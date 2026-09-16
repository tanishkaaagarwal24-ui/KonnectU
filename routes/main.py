import os
from google import genai
from google.genai import types
from flask import Blueprint, request, jsonify

from database.db import db

from database.models import (
    User,
    Center,
    Batch,
    BatchStudent,
    Content,
    Attendance,
    Test,
    Question,
    Submission,
    Homework,
    HomeworkSubmission,
    Doubt,
    Notification,
    Fee,
    ParentStudent
)

from .auth import token_required, role_required


main = Blueprint(
    "main",
    __name__,
    url_prefix="/api"
)


# =========================================================
# CENTER
# =========================================================

@main.route("/center")
@token_required
def get_center(user):

    center = Center.query.get(user.center_id)

    if not center:

        return jsonify({
            "error": "Center not found"
        }), 404

    return jsonify({
        "id": center.id,
        "name": center.name,
        "slug": center.slug,
        "logo": center.logo,
        "primary_color": center.primary_color,
        "secondary_color": center.secondary_color,
        "language": center.language
    })


@main.route("/center/branding", methods=["PUT"])
@role_required("admin")
def update_branding(user):

    data = request.get_json() or {}

    center = Center.query.get(user.center_id)

    if data.get("name"):
        center.name = data["name"]

    if data.get("logo"):
        center.logo = data["logo"]

    if data.get("primary_color"):
        center.primary_color = data["primary_color"]

    if data.get("secondary_color"):
        center.secondary_color = data["secondary_color"]

    if data.get("language"):
        center.language = data["language"]

    db.session.commit()

    return jsonify({
        "message": "Branding updated"
    })


# =========================================================
# USERS
# =========================================================

@main.route("/users", methods=["POST"])
@role_required("admin")
def create_user(user):

    data = request.get_json() or {}

    if data.get("role") not in [
        "teacher",
        "student",
        "parent"
    ]:

        return jsonify({
            "error": "Invalid role"
        }), 400

    if User.query.filter_by(
        email=data.get("email")
    ).first():

        return jsonify({
            "error": "Email already exists"
        }), 409

    new_user = User(
        name=data.get("name"),
        email=data.get("email"),
        role=data.get("role"),
        center_id=user.center_id
    )

    new_user.set_password(
        data.get("password", "welcome123")
    )

    db.session.add(new_user)

    db.session.commit()

    return jsonify({
        "message": "User created",
        "id": new_user.id
    }), 201


@main.route("/users")
@role_required("admin", "teacher")
def list_users(user):

    users = User.query.filter_by(
        center_id=user.center_id
    ).all()

    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ])


# =========================================================
# BATCHES
# =========================================================

@main.route("/batches", methods=["POST"])
@role_required("admin", "teacher")
def create_batch(user):

    data = request.get_json() or {}

    batch = Batch(
        name=data.get("name"),
        subject=data.get("subject"),
        teacher_id=data.get(
            "teacher_id",
            user.id
        ),
        center_id=user.center_id,
        schedule=data.get("schedule")
    )

    db.session.add(batch)

    db.session.commit()

    return jsonify({
        "message": "Batch created",
        "id": batch.id
    }), 201


@main.route("/batches")
@token_required
def list_batches(user):

    batches = Batch.query.filter_by(
        center_id=user.center_id
    ).all()

    return jsonify([
        {
            "id": b.id,
            "name": b.name,
            "subject": b.subject,
            "teacher_id": b.teacher_id,
            "schedule": b.schedule
        }
        for b in batches
    ])


@main.route("/batches/<int:batch_id>/students", methods=["POST"])
@role_required("admin", "teacher")
def add_student_to_batch(user, batch_id):

    data = request.get_json() or {}

    student = User.query.get(
        data.get("student_id")
    )

    batch = Batch.query.get(batch_id)

    if not student or not batch:

        return jsonify({
            "error": "Student or batch not found"
        }), 404

    if student.center_id != user.center_id:

        return jsonify({
            "error": "Unauthorized"
        }), 403

    connection = BatchStudent(
        batch_id=batch.id,
        student_id=student.id
    )

    db.session.add(connection)

    db.session.commit()

    return jsonify({
        "message": "Student added to batch"
    })


# =========================================================
# CONTENT
# =========================================================

@main.route("/content", methods=["POST"])
@role_required("admin", "teacher")
def create_content(user):

    data = request.get_json() or {}

    content = Content(
        title=data.get("title"),
        description=data.get("description"),
        subject=data.get("subject"),
        chapter=data.get("chapter"),
        file_url=data.get("file_url"),
        teacher_id=user.id,
        center_id=user.center_id
    )

    db.session.add(content)

    db.session.commit()

    return jsonify({
        "message": "Content uploaded",
        "id": content.id
    }), 201


@main.route("/content")
@token_required
def list_content(user):

    content = Content.query.filter_by(
        center_id=user.center_id
    ).all()

    return jsonify([
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "subject": c.subject,
            "chapter": c.chapter,
            "file_url": c.file_url
        }
        for c in content
    ])


# =========================================================
# ATTENDANCE
# =========================================================

@main.route("/attendance", methods=["POST"])
@role_required("admin", "teacher")
def mark_attendance(user):

    data = request.get_json() or {}

    student_id = data.get("student_id")
    batch_id = data.get("batch_id")
    attendance_date = data.get("date")
    status = data.get("status")

    if not student_id or not status:
        return jsonify({
            "error": "student_id and status are required"
        }), 400

    if status not in ["present", "absent"]:
        return jsonify({
            "error": "status must be present or absent"
        }), 400

    student = User.query.filter_by(
        id=student_id,
        center_id=user.center_id
    ).first()

    if not student:
        return jsonify({
            "error": "Student not found in this center"
        }), 404

    record = Attendance(
        student_id=student_id,
        batch_id=batch_id,
        date=attendance_date,
        status=status
    )

    db.session.add(record)
    db.session.commit()

    workflow_result = None

    if status == "absent":
        from workflows.attendance_workflow import run_absence_workflow

        workflow_result = run_absence_workflow(
            student_id=student_id,
            center_id=user.center_id
        )

    return jsonify({
        "message": "Attendance recorded",
        "status": status,
        "workflow": workflow_result
    })


@main.route("/attendance/student/<int:student_id>")
@token_required
def student_attendance(user, student_id):

    records = Attendance.query.filter_by(
        student_id=student_id
    ).all()

    total = len(records)

    present = len([
        r for r in records
        if r.status == "present"
    ])

    percentage = (
        round((present / total) * 100, 2)
        if total else 0
    )

    return jsonify({
        "student_id": student_id,
        "total_classes": total,
        "present": present,
        "attendance_percentage": percentage
    })


# =========================================================
# TESTS
# =========================================================

@main.route("/tests", methods=["POST"])
@role_required("admin", "teacher")
def create_test(user):

    data = request.get_json() or {}

    test = Test(
        title=data.get("title"),
        subject=data.get("subject"),
        batch_id=data.get("batch_id"),
        teacher_id=user.id,
        total_marks=data.get(
            "total_marks",
            100
        )
    )

    db.session.add(test)

    db.session.flush()

    questions = data.get("questions", [])

    for q in questions:

        question = Question(
            test_id=test.id,
            question=q.get("question"),
            option_a=q.get("option_a"),
            option_b=q.get("option_b"),
            option_c=q.get("option_c"),
            option_d=q.get("option_d"),
            correct_answer=q.get(
                "correct_answer"
            ),
            marks=q.get("marks", 1)
        )

        db.session.add(question)

    db.session.commit()

    return jsonify({
        "message": "Test created",
        "id": test.id
    }), 201


@main.route("/tests")
@token_required
def list_tests(user):

    tests = Test.query.all()

    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "subject": t.subject,
            "batch_id": t.batch_id,
            "total_marks": t.total_marks
        }
        for t in tests
    ])


@main.route("/tests/<int:test_id>")
@token_required
def get_test(user, test_id):

    test = Test.query.get(test_id)

    if not test:

        return jsonify({
            "error": "Test not found"
        }), 404

    questions = Question.query.filter_by(
        test_id=test.id
    ).all()

    return jsonify({
        "id": test.id,
        "title": test.title,
        "subject": test.subject,
        "total_marks": test.total_marks,
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d,
                "marks": q.marks
            }
            for q in questions
        ]
    })


@main.route("/tests/<int:test_id>/submit", methods=["POST"])
@role_required("student")
def submit_test(user, test_id):

    data = request.get_json() or {}

    test = Test.query.get(test_id)

    if not test:

        return jsonify({
            "error": "Test not found"
        }), 404

    answers = data.get("answers", {})

    questions = Question.query.filter_by(
        test_id=test.id
    ).all()

    score = 0
    total = 0

    for q in questions:

        total += q.marks

        answer = answers.get(
            str(q.id)
        )

        if answer == q.correct_answer:

            score += q.marks

    submission = Submission(
        test_id=test.id,
        student_id=user.id,
        score=score,
        total=total
    )

    db.session.add(submission)

    db.session.commit()

    return jsonify({
        "message": "Test submitted",
        "score": score,
        "total": total,
        "percentage": round(
            score / total * 100,
            2
        ) if total else 0
    })


# =========================================================
# HOMEWORK
# =========================================================

@main.route("/homework", methods=["POST"])
@role_required("admin", "teacher")
def create_homework(user):

    data = request.get_json() or {}

    homework = Homework(
        title=data.get("title"),
        description=data.get("description"),
        subject=data.get("subject"),
        batch_id=data.get("batch_id"),
        deadline=data.get("deadline"),
        teacher_id=user.id
    )

    db.session.add(homework)

    db.session.commit()

    return jsonify({
        "message": "Homework created",
        "id": homework.id
    }), 201


@main.route("/homework")
@token_required
def list_homework(user):

    homework = Homework.query.all()

    return jsonify([
        {
            "id": h.id,
            "title": h.title,
            "description": h.description,
            "subject": h.subject,
            "batch_id": h.batch_id,
            "deadline": h.deadline
        }
        for h in homework
    ])


@main.route("/homework/<int:homework_id>/submit", methods=["POST"])
@role_required("student")
def submit_homework(user, homework_id):

    data = request.get_json() or {}

    submission = HomeworkSubmission(
        homework_id=homework_id,
        student_id=user.id,
        answer=data.get("answer")
    )

    db.session.add(submission)

    db.session.commit()

    return jsonify({
        "message": "Homework submitted"
    })

# =========================================================
# VOICE TRANSCRIPTION
# =========================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


@main.route("/transcribe", methods=["POST"])
@role_required("student")
def transcribe_audio(user):

    try:
        if "audio" not in request.files:
            return jsonify({
                "error": "No audio file received"
            }), 400

        audio_file = request.files["audio"]

        audio_data = audio_file.read()

        if not audio_data:
            return jsonify({
                "error": "Audio file is empty"
            }), 400

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                "Transcribe this audio exactly. "
                "Return only the spoken words. "
                "Do not add explanations.",
                types.Part.from_bytes(
                    data=audio_data,
                    mime_type=audio_file.mimetype or "audio/webm"
                )
            ]
        )

        return jsonify({
            "transcription": response.text
        }), 200

    except Exception as e:
        print("Transcription error:", e)

        return jsonify({
            "error": str(e)
        }), 500

# =========================================================
# VOICE DOUBTS
# =========================================================

@main.route("/doubts", methods=["POST"])
@role_required("student")
def create_doubt(user):

    data = request.get_json() or {}

    doubt = Doubt(
        student_id=user.id,
        center_id=user.center_id,
        subject=data.get("subject"),
        language=data.get(
            "language",
            "English"
        ),
        transcription=data.get(
            "transcription"
        )
    )

    db.session.add(doubt)

    db.session.commit()

    return jsonify({
        "message": "Doubt submitted",
        "id": doubt.id
    }), 201


@main.route("/doubts")
@role_required("admin", "teacher")
def list_doubts(user):

    doubts = Doubt.query.filter_by(
        center_id=user.center_id
    ).order_by(
        Doubt.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": d.id,
            "student_id": d.student_id,
            "subject": d.subject,
            "language": d.language,
            "transcription": d.transcription,
            "answer": d.answer,
            "status": d.status
        }
        for d in doubts
    ])


@main.route("/doubts/<int:doubt_id>/resolve", methods=["PUT"])
@role_required("admin", "teacher")
def resolve_doubt(user, doubt_id):

    doubt = Doubt.query.get(doubt_id)

    if not doubt:

        return jsonify({
            "error": "Doubt not found"
        }), 404

    data = request.get_json() or {}

    doubt.answer = data.get("answer")
    doubt.status = "resolved"

    db.session.add(
        Notification(
            user_id=doubt.student_id,
            title="Doubt Resolved",
            message="Your teacher answered your doubt."
        )
    )

    db.session.commit()

    return jsonify({
        "message": "Doubt resolved"
    })


# =========================================================
# NOTIFICATIONS
# =========================================================

@main.route("/notifications")
@token_required
def notifications(user):

    notifications = Notification.query.filter_by(
        user_id=user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "read": n.read
        }
        for n in notifications
    ])


# =========================================================
# FEES
# =========================================================

@main.route("/fees", methods=["POST"])
@role_required("admin")
def create_fee(user):

    data = request.get_json() or {}

    fee = Fee(
        student_id=data.get("student_id"),
        center_id=user.center_id,
        amount=data.get("amount"),
        due_date=data.get("due_date"),
        status=data.get(
            "status",
            "PENDING"
        )
    )

    db.session.add(fee)

    db.session.commit()

    return jsonify({
        "message": "Fee record created",
        "id": fee.id
    }), 201


@main.route("/fees")
@token_required
def list_fees(user):

    if user.role == "student":

        fees = Fee.query.filter_by(
            student_id=user.id
        ).all()

    else:

        fees = Fee.query.filter_by(
            center_id=user.center_id
        ).all()

    return jsonify([
        {
            "id": f.id,
            "student_id": f.student_id,
            "amount": f.amount,
            "due_date": f.due_date,
            "status": f.status
        }
        for f in fees
    ])


# =========================================================
# STUDENT PROGRESS
# =========================================================

@main.route("/progress")
@role_required("student")
def progress(user):

    submissions = Submission.query.filter_by(
        student_id=user.id
    ).all()

    attendance = Attendance.query.filter_by(
        student_id=user.id
    ).all()

    total_tests = len(submissions)

    average_score = 0

    if total_tests:

        average_score = round(
            sum(
                (
                    s.score / s.total * 100
                )
                for s in submissions
                if s.total
            ) / total_tests,
            2
        )

    present = len([
        a for a in attendance
        if a.status == "present"
    ])

    attendance_percentage = (
        round(
            present / len(attendance) * 100,
            2
        )
        if attendance
        else 0
    )

    return jsonify({
        "tests_completed": total_tests,
        "average_score": average_score,
        "attendance": attendance_percentage
    })


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@main.route("/dashboard")
@role_required("admin")
def dashboard(user):

    students = User.query.filter_by(
        center_id=user.center_id,
        role="student"
    ).count()

    teachers = User.query.filter_by(
        center_id=user.center_id,
        role="teacher"
    ).count()

    batches = Batch.query.filter_by(
        center_id=user.center_id
    ).count()

    doubts = Doubt.query.filter_by(
        center_id=user.center_id,
        status="pending"
    ).count()

    return jsonify({
        "students": students,
        "teachers": teachers,
        "batches": batches,
        "pending_doubts": doubts
    })


# =========================================================
# PARENT → STUDENT
# =========================================================

@main.route("/parent/children")
@role_required("parent")
def parent_children(user):

    relationships = ParentStudent.query.filter_by(
        parent_id=user.id
    ).all()

    children = []

    for relationship in relationships:

        student = User.query.get(
            relationship.student_id
        )

        if student:

            children.append({
                "id": student.id,
                "name": student.name,
                "email": student.email
            })

    return jsonify(children)