from datetime import datetime
from .db import db


class Center(db.Model):
    __tablename__ = "centers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    logo = db.Column(db.String(500))
    primary_color = db.Column(db.String(20), default="#2563EB")
    secondary_color = db.Column(db.String(20), default="#FFFFFF")
    language = db.Column(db.String(50), default="English")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)
    center_id = db.Column(db.Integer, db.ForeignKey("centers.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class Batch(db.Model):
    __tablename__ = "batches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    center_id = db.Column(db.Integer, db.ForeignKey("centers.id"))
    schedule = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BatchStudent(db.Model):
    __tablename__ = "batch_students"

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"))


class Content(db.Model):
    __tablename__ = "content"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    subject = db.Column(db.String(100))
    chapter = db.Column(db.String(100))

    file_url = db.Column(db.String(500))

    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    center_id = db.Column(db.Integer, db.ForeignKey("centers.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"))

    date = db.Column(db.String(20))
    status = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Test(db.Model):
    __tablename__ = "tests"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100))

    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"))
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    total_marks = db.Column(db.Integer, default=100)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)

    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"))

    question = db.Column(db.Text, nullable=False)

    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))

    correct_answer = db.Column(db.String(1))

    marks = db.Column(db.Integer, default=1)


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)

    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    score = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class Homework(db.Model):
    __tablename__ = "homework"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    subject = db.Column(db.String(100))
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"))

    deadline = db.Column(db.String(50))

    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HomeworkSubmission(db.Model):
    __tablename__ = "homework_submissions"

    id = db.Column(db.Integer, primary_key=True)

    homework_id = db.Column(
        db.Integer,
        db.ForeignKey("homework.id")
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    answer = db.Column(db.Text)

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Doubt(db.Model):
    __tablename__ = "doubts"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    center_id = db.Column(db.Integer, db.ForeignKey("centers.id"))

    subject = db.Column(db.String(100))

    language = db.Column(db.String(50))

    transcription = db.Column(db.Text, nullable=False)

    answer = db.Column(db.Text)

    status = db.Column(
        db.String(30),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    title = db.Column(db.String(200))

    message = db.Column(db.Text)

    read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Fee(db.Model):
    __tablename__ = "fees"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    center_id = db.Column(
        db.Integer,
        db.ForeignKey("centers.id")
    )

    amount = db.Column(db.Float)

    due_date = db.Column(db.String(50))

    status = db.Column(
        db.String(30),
        default="PENDING"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class ParentStudent(db.Model):
    __tablename__ = "parent_students"

    id = db.Column(db.Integer, primary_key=True)

    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )