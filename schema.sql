-- Student intake responses from class_dataset.csv.
-- One student row. Name is not unique, so student_id is generated.
-- tools and availability hold several values per cell, so each is a
-- lookup table plus a bridge table. Skill ratings stay on students.

CREATE TABLE students (
    student_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    netid TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    school_year TEXT NOT NULL CHECK (
        school_year IN ('First-year', 'Sophomore', 'Junior', 'Senior')
    ),
    intro_programming TEXT NOT NULL CHECK (
        intro_programming IN ('took_it', 'equivalent', 'neither')
    ),
    skill_programming INTEGER NOT NULL CHECK (skill_programming BETWEEN 1 AND 5),
    skill_data_stats INTEGER NOT NULL CHECK (skill_data_stats BETWEEN 1 AND 5),
    skill_frontend_design INTEGER NOT NULL CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch INTEGER NOT NULL CHECK (skill_business_pitch BETWEEN 1 AND 5),
    working_style TEXT,
    interests TEXT,
    semester_goal TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE tools (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE student_tools (
    student_id INTEGER NOT NULL REFERENCES students (student_id),
    tool_id INTEGER NOT NULL REFERENCES tools (id),
    PRIMARY KEY (student_id, tool_id)
);

CREATE TABLE availability (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE student_availability (
    student_id INTEGER NOT NULL REFERENCES students (student_id),
    availability_id INTEGER NOT NULL REFERENCES availability (id),
    PRIMARY KEY (student_id, availability_id)
);
