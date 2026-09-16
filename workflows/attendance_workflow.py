from datetime import datetime, timedelta

from database.db import db
from database.models import (
    User,
    BatchStudent,
    Content,
    Attendance,
    Test,
    Homework,
    Notification,
    ParentStudent,
)


def create_notification(user_id, title, message, notification_type="workflow"):
    """Create a notification for a user."""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        read=False,
        created_at=datetime.utcnow(),
    )

    db.session.add(notification)
    return notification


def notification_exists(user_id, title, message):
    """Prevent duplicate workflow notifications."""
    existing = Notification.query.filter_by(
        user_id=user_id,
        title=title,
        message=message,
    ).first()

    return existing is not None


def get_student_batch(student_id):
    """Return the student's batch relationship."""
    return BatchStudent.query.filter_by(student_id=student_id).first()


def get_student_parents(student_id):
    """Return parent users linked to this student."""
    links = ParentStudent.query.filter_by(student_id=student_id).all()

    parents = []

    for link in links:
        parent = User.query.get(link.parent_id)

        if parent:
            parents.append(parent)

    return parents


def find_missed_content(center_id):
    """
    Find content created today for the student's coaching center.

    The current Content model does not contain batch_id, so we use
    center_id to find today's uploaded learning material.
    """

    now = datetime.utcnow()

    start_of_day = datetime(
        now.year,
        now.month,
        now.day,
    )

    end_of_day = start_of_day + timedelta(days=1)

    content = (
        Content.query
        .filter(Content.center_id == center_id)
        .filter(Content.created_at >= start_of_day)
        .filter(Content.created_at < end_of_day)
        .order_by(Content.created_at.desc())
        .all()
    )

    return content


def find_upcoming_tests(center_id):
    """Find tests scheduled within the next 7 days."""

    now = datetime.utcnow()
    next_week = now + timedelta(days=7)

    results = []

    tests = Test.query.all()

    for test in tests:
        if hasattr(test, "center_id"):
            if test.center_id != center_id:
                continue

        test_date = None

        for field in [
            "date",
            "test_date",
            "scheduled_date",
            "exam_date",
        ]:
            if hasattr(test, field):
                value = getattr(test, field)

                if value:
                    test_date = value
                    break

        if not test_date:
            continue

        if isinstance(test_date, str):
            try:
                test_date = datetime.fromisoformat(
                    test_date.replace("Z", "")
                )
            except ValueError:
                continue

        if now <= test_date <= next_week:
            results.append(test)

    return results


def find_upcoming_homework(center_id):
    """Find homework due within the next 7 days."""

    now = datetime.utcnow()
    next_week = now + timedelta(days=7)

    results = []

    homework_items = Homework.query.all()

    for homework in homework_items:

        if hasattr(homework, "center_id"):
            if homework.center_id != center_id:
                continue

        due_date = None

        for field in [
            "due_date",
            "deadline",
            "submission_date",
        ]:
            if hasattr(homework, field):
                value = getattr(homework, field)

                if value:
                    due_date = value
                    break

        if not due_date:
            continue

        if isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(
                    due_date.replace("Z", "")
                )
            except ValueError:
                continue

        if now <= due_date <= next_week:
            results.append(homework)

    return results


def run_absence_workflow(student_id, center_id):
    """
    Autonomous absence workflow.

    Flow:

    Student absent
        ↓
    Notify student
        ↓
    Notify parents
        ↓
    Find today's learning content
        ↓
    Notify student about missed notes
        ↓
    Check upcoming tests
        ↓
    Check upcoming homework
    """

    student = User.query.get(student_id)

    if not student:
        return {
            "success": False,
            "error": "Student not found",
        }

    result = {
        "success": True,
        "student_id": student_id,
        "student_notification": False,
        "parent_notifications": 0,
        "missed_content_notifications": 0,
        "test_notifications": 0,
        "homework_notifications": 0,
        "errors": [],
    }

    # ---------------------------------------------------------
    # 1. Notify student about absence
    # ---------------------------------------------------------

    title = "Attendance Alert"
    message = (
        "You were marked absent today. "
        "We will help you catch up on what you missed."
    )

    try:
        if not notification_exists(
            student_id,
            title,
            message,
        ):
            create_notification(
                student_id,
                title,
                message,
                "attendance",
            )

        result["student_notification"] = True

    except Exception as e:
        result["errors"].append(
            f"Student notification error: {str(e)}"
        )

    # ---------------------------------------------------------
    # 2. Notify parents
    # ---------------------------------------------------------

    try:
        parents = get_student_parents(student_id)

        for parent in parents:

            title = "Student Absence Alert"

            message = (
                f"{student.name} was marked absent today. "
                "Please help them catch up on the missed learning material."
            )

            if not notification_exists(
                parent.id,
                title,
                message,
            ):
                create_notification(
                    parent.id,
                    title,
                    message,
                    "attendance",
                )

                result["parent_notifications"] += 1

    except Exception as e:
        result["errors"].append(
            f"Parent notification error: {str(e)}"
        )

    # ---------------------------------------------------------
    # 3. Find today's missed learning content
    # ---------------------------------------------------------

    try:
        missed_content = find_missed_content(center_id)

        for content in missed_content:

            title = f"Missed Notes: {content.title}"

            message_parts = [
                "You were absent today.",
                f"Here is the learning material you missed: {content.title}.",
            ]

            if content.subject:
                message_parts.append(
                    f"Subject: {content.subject}."
                )

            if content.chapter:
                message_parts.append(
                    f"Chapter: {content.chapter}."
                )

            if content.description:
                message_parts.append(
                    f"Details: {content.description}"
                )

            if content.file_url:
                message_parts.append(
                    f"Notes: {content.file_url}"
                )

            message = " ".join(message_parts)

            if not notification_exists(
                student_id,
                title,
                message,
            ):
                create_notification(
                    student_id,
                    title,
                    message,
                    "missed_content",
                )

                result["missed_content_notifications"] += 1

    except Exception as e:
        result["errors"].append(
            f"Missed content error: {str(e)}"
        )

    # ---------------------------------------------------------
    # 4. Upcoming test reminders
    # ---------------------------------------------------------

    try:
        upcoming_tests = find_upcoming_tests(center_id)

        for test in upcoming_tests:

            test_name = getattr(
                test,
                "title",
                "Upcoming Test",
            )

            title = f"Upcoming Test: {test_name}"

            message = (
                f"You have an upcoming test: {test_name}. "
                "Please make sure you prepare for it."
            )

            if not notification_exists(
                student_id,
                title,
                message,
            ):
                create_notification(
                    student_id,
                    title,
                    message,
                    "test_reminder",
                )

                result["test_notifications"] += 1

    except Exception as e:
        result["errors"].append(
            f"Test reminder error: {str(e)}"
        )

    # ---------------------------------------------------------
    # 5. Upcoming homework reminders
    # ---------------------------------------------------------

    try:
        upcoming_homework = find_upcoming_homework(
            center_id
        )

        for homework in upcoming_homework:

            homework_name = getattr(
                homework,
                "title",
                "Homework",
            )

            title = f"Homework Reminder: {homework_name}"

            message = (
                f"You have homework coming up: {homework_name}. "
                "Please complete it before the deadline."
            )

            if not notification_exists(
                student_id,
                title,
                message,
            ):
                create_notification(
                    student_id,
                    title,
                    message,
                    "homework_reminder",
                )

                result["homework_notifications"] += 1

    except Exception as e:
        result["errors"].append(
            f"Homework reminder error: {str(e)}"
        )

    # ---------------------------------------------------------
    # 6. Save everything
    # ---------------------------------------------------------

    try:
        db.session.commit()

    except Exception as e:
        db.session.rollback()

        result["success"] = False
        result["errors"].append(
            f"Database commit error: {str(e)}"
        )

    return result