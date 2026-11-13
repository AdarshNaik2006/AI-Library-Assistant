import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "resources.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
DATA_PATH = BASE_DIR / "data" / "resources.json"


def get_connection():
    """Returns a SQLite connection configured with sqlite3.Row for dict-like access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Initializes the database schema and performs non-destructive schema migrations."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        # 1. Ensure base table exists
        connection.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                publisher TEXT,
                subject TEXT NOT NULL,
                level TEXT,
                description TEXT,
                resource_type TEXT,
                url TEXT
            );
        """)

        # 2. Check for missing columns in existing database and add them safely
        cursor = connection.execute("PRAGMA table_info(resources)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        column_defs = {
            "education_level": "TEXT",
            "class_grade": "TEXT",
            "department": "TEXT",
            "language": "TEXT DEFAULT 'English'",
            "publisher": "TEXT",
        }
        for col, col_type in column_defs.items():
            if col not in existing_cols:
                connection.execute(f"ALTER TABLE resources ADD COLUMN {col} {col_type}")

        # 3. Create indices safely once columns are guaranteed to exist
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_subject ON resources(subject);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_level ON resources(level);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_edu_level ON resources(education_level);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_class_grade ON resources(class_grade);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_department ON resources(department);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_language ON resources(language);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_resources_publisher ON resources(publisher);")

        # 4. Remove leftover test records from previous test runs and ensure no NULLs
        connection.execute("DELETE FROM resources WHERE title = 'Test CS Book'")
        connection.execute("UPDATE resources SET publisher = 'Academic Press' WHERE publisher IS NULL")
        connection.execute("UPDATE resources SET education_level = 'Undergraduate' WHERE education_level IS NULL")
        connection.execute("UPDATE resources SET class_grade = 'All Classes' WHERE class_grade IS NULL")
        connection.execute("UPDATE resources SET department = 'General' WHERE department IS NULL")
        connection.commit()


def seed_database():
    """
    Seeds initial sample resources from data/resources.json.
    Ensures existing resources are preserved and updated, and new resources
    are inserted idempotently without creating duplicates.
    """
    initialize_database()

    if not DATA_PATH.exists():
        return

    try:
        resources = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not read resources.json: {e}")
        return

    if not isinstance(resources, list):
        return

    with get_connection() as connection:
        # Collect existing records by normalized title and author
        cursor = connection.execute("SELECT id, title, author FROM resources")
        existing_records = {
            (
                (row["title"] or "").strip().lower(),
                (row["author"] or "").strip().lower(),
            ): row["id"]
            for row in cursor.fetchall()
        }

        to_insert = []
        for r in resources:
            title = (r.get("title") or "").strip()
            author = (r.get("author") or "").strip()
            if not title:
                continue

            record_key = (title.lower(), author.lower())
            publisher = (r.get("publisher") or "").strip()
            subject = (r.get("subject") or "General").strip()
            level = (r.get("level") or "Beginner").strip()
            edu_level = (r.get("education_level") or "Undergraduate").strip()
            class_grade = (r.get("class_grade") or "All Classes").strip()
            dept = (r.get("department") or "General").strip()
            lang = (r.get("language") or "English").strip()
            description = (r.get("description") or "").strip()
            resource_type = (r.get("resource_type") or "Book").strip()
            url = (r.get("url") or "").strip()

            if record_key in existing_records:
                # Update existing record with enhanced universal metadata
                rec_id = existing_records[record_key]
                connection.execute(
                    """
                    UPDATE resources 
                    SET publisher = ?, subject = ?, level = ?, education_level = ?, class_grade = ?, 
                        department = ?, language = ?, description = ?, resource_type = ?, url = ?
                    WHERE id = ?
                    """,
                    (publisher, subject, level, edu_level, class_grade, dept, lang, description, resource_type, url, rec_id),
                )
            else:
                to_insert.append((
                    title,
                    author,
                    publisher,
                    subject,
                    level,
                    edu_level,
                    class_grade,
                    dept,
                    lang,
                    description,
                    resource_type,
                    url,
                ))
                existing_records[record_key] = True

        if to_insert:
            connection.executemany(
                """
                INSERT INTO resources (
                    title, author, publisher, subject, level, education_level, class_grade, 
                    department, language, description, resource_type, url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                to_insert,
            )
        connection.commit()


def search_resources(query=None, subject=None, level=None, education_level=None, class_grade=None, language=None):
    """
    Searches resources using parameterized SQL queries to prevent SQL injection.
    Supports keyword search across title, author, publisher, description, subject, department,
    and class_grade, as well as specific field filters.
    """
    sql = """
        SELECT id, title, author, publisher, subject, level, education_level, 
               class_grade, department, language, description, resource_type, url 
        FROM resources 
        WHERE 1=1
    """
    params = []

    if query and str(query).strip():
        q_term = f"%{str(query).strip()}%"
        sql += """ AND (
            title LIKE ? OR author LIKE ? OR publisher LIKE ? OR description LIKE ? 
            OR subject LIKE ? OR department LIKE ? OR class_grade LIKE ?
        )"""
        params.extend([q_term, q_term, q_term, q_term, q_term, q_term, q_term])

    if subject and str(subject).strip() and str(subject).strip().lower() != "all":
        sql += " AND LOWER(subject) = LOWER(?)"
        params.append(str(subject).strip())

    if level and str(level).strip() and str(level).strip().lower() != "all":
        sql += " AND LOWER(level) = LOWER(?)"
        params.append(str(level).strip())

    if education_level and str(education_level).strip() and str(education_level).strip().lower() != "all":
        sql += " AND LOWER(education_level) = LOWER(?)"
        params.append(str(education_level).strip())

    if class_grade and str(class_grade).strip() and str(class_grade).strip().lower() != "all":
        sql += " AND LOWER(class_grade) = LOWER(?)"
        params.append(str(class_grade).strip())

    if language and str(language).strip() and str(language).strip().lower() != "all":
        sql += " AND (LOWER(language) = LOWER(?) OR LOWER(language) = 'bilingual')"
        params.append(str(language).strip())

    sql += " ORDER BY education_level ASC, subject ASC, level ASC, title ASC"

    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def get_all_subjects():
    """Retrieves all distinct subjects currently stored in the database."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT DISTINCT subject FROM resources WHERE subject IS NOT NULL AND TRIM(subject) != '' ORDER BY subject ASC"
        ).fetchall()
        return [row["subject"] for row in rows]


def get_all_education_levels():
    """Retrieves all distinct education levels currently stored in the database."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT DISTINCT education_level FROM resources WHERE education_level IS NOT NULL AND TRIM(education_level) != '' ORDER BY education_level ASC"
        ).fetchall()
        return [row["education_level"] for row in rows]


def get_all_departments():
    """Retrieves all distinct academic departments currently stored in the database."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT DISTINCT department FROM resources WHERE department IS NOT NULL AND TRIM(department) != '' ORDER BY department ASC"
        ).fetchall()
        return [row["department"] for row in rows]


def get_resource_by_id(resource_id):
    """Retrieves a single resource by its primary key ID."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, title, author, publisher, subject, level, education_level, 
                   class_grade, department, language, description, resource_type, url 
            FROM resources WHERE id = ?
            """,
            (resource_id,),
        ).fetchone()
        return dict(row) if row else None


def add_resource(title, author, subject, level="Beginner", description="", resource_type="Book", url="",
                 education_level="Undergraduate", class_grade="All Classes", department="General", language="English",
                 publisher="Academic Press"):
    """Adds a new resource using parameterized SQL queries."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO resources (
                title, author, publisher, subject, level, education_level, 
                class_grade, department, language, description, resource_type, url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (title or "").strip(),
                (author or "").strip(),
                (publisher or "").strip(),
                (subject or "General").strip(),
                (level or "Beginner").strip(),
                (education_level or "Undergraduate").strip(),
                (class_grade or "All Classes").strip(),
                (department or "General").strip(),
                (language or "English").strip(),
                (description or "").strip(),
                (resource_type or "Book").strip(),
                (url or "").strip(),
            ),
        )
        connection.commit()
        return cursor.lastrowid


if __name__ == "__main__":
    seed_database()
    print("Database initialized and seeded successfully.")
    print(f"Subjects available: {len(get_all_subjects())} subjects -> {get_all_subjects()}")
    print(f"Education levels available: {get_all_education_levels()}")
    print(f"Total resources count: {len(search_resources())}")
