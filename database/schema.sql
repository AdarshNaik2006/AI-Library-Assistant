CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    subject TEXT NOT NULL,
    level TEXT,
    education_level TEXT,
    class_grade TEXT,
    department TEXT,
    language TEXT DEFAULT 'English',
    description TEXT,
    resource_type TEXT,
    url TEXT
);

CREATE INDEX IF NOT EXISTS idx_resources_subject ON resources(subject);
CREATE INDEX IF NOT EXISTS idx_resources_level ON resources(level);
CREATE INDEX IF NOT EXISTS idx_resources_edu_level ON resources(education_level);
CREATE INDEX IF NOT EXISTS idx_resources_class_grade ON resources(class_grade);
CREATE INDEX IF NOT EXISTS idx_resources_department ON resources(department);
CREATE INDEX IF NOT EXISTS idx_resources_language ON resources(language);
CREATE INDEX IF NOT EXISTS idx_resources_publisher ON resources(publisher);
