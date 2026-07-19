import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from io import BytesIO
import shutil

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Natural Sciences QA Dashboard",
    page_icon="🎓",
    layout="wide"
)

# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown("""
<style>

.main {
    background-color:#F8FAFC;
}

[data-testid="stMetric"]{
    background:#FFFFFF;
    padding:15px;
    border-radius:12px;
    box-shadow:0px 2px 8px rgba(0,0,0,0.08);
    border-left:5px solid #2563EB;
}

h1,h2,h3{
    color:#003366;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

Path("data").mkdir(exist_ok=True)
Path("backups").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)

DB = "data/natural_sciences.db"

conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

# --------------------------------------------------
# TABLES
# --------------------------------------------------

cur.execute("""
CREATE TABLE IF NOT EXISTS performance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
programme TEXT,
academic_year TEXT,
year_level TEXT,
category TEXT,
students INTEGER,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS graduate_outcomes(
id INTEGER PRIMARY KEY AUTOINCREMENT,
student_id TEXT,
name TEXT,
programme TEXT,
gender TEXT,
graduation_year TEXT,
status TEXT,
organization TEXT,
country TEXT,
remarks TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS exchange_programmes(
id INTEGER PRIMARY KEY AUTOINCREMENT,
year TEXT,
programme TEXT,
student TEXT,
institution TEXT,
country TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS internships(
id INTEGER PRIMARY KEY AUTOINCREMENT,
year TEXT,
programme TEXT,
student TEXT,
organization TEXT,
location TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS guest_lectures(
id INTEGER PRIMARY KEY AUTOINCREMENT,
lecture_date TEXT,
speaker TEXT,
institution TEXT,
topic TEXT,
programme TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS alumni(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
programme TEXT,
graduation_year TEXT,
organization TEXT,
country TEXT,
email TEXT
)
""")

conn.commit()

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

PROGRAMMES = [
    "Life Science",
    "Chemistry",
    "Physics"
]

def fetch(table):
    return pd.read_sql_query(
        f"SELECT * FROM {table}", conn
    )

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("""
# 🎓 Department of Natural Sciences

### Academic Monitoring & Quality Assurance System

**Sherubtse College • Royal University of Bhutan**

Life Science • Chemistry • Physics
""")

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.image(
    "https://img.icons8.com/color/96/university.png",
    width=70
)

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Student Performance",
        "Graduate Outcomes",
        "Exchange Programme",
        "Internships",
        "Guest Lectures",
        "Alumni",
        "Reports"
    ]
)

selected_programme = st.sidebar.selectbox(
    "Programme",
    ["All"] + PROGRAMMES
)

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if menu=="Dashboard":

    perf = fetch("performance")
    grad = fetch("graduate_outcomes")
    exch = fetch("exchange_programmes")
    intr = fetch("internships")
    guest = fetch("guest_lectures")

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric(
        "Performance Records",
        len(perf)
    )

    c2.metric(
        "Graduate Records",
        len(grad)
    )

    c3.metric(
        "Exchange Students",
        len(exch)
    )

    c4.metric(
        "Internships",
        len(intr)
    )

    c5.metric(
        "Guest Lectures",
        len(guest)
    )

    st.divider()

    if not perf.empty:

        fig = px.bar(
            perf,
            x="programme",
            y="students",
            color="category",
            title="Student Performance Distribution",
            barmode="group"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# --------------------------------------------------
# STUDENT PERFORMANCE
# --------------------------------------------------

elif menu=="Student Performance":

    st.subheader("📊 Student Performance")

    with st.form("performance_form"):

        programme = st.selectbox(
            "Programme",
            PROGRAMMES
        )

        academic_year = st.text_input(
            "Academic Year",
            "2026"
        )

        year_level = st.selectbox(
            "Year Level",
            ["Year 1","Year 2","Year 3"]
        )

        category = st.selectbox(
            "Category",
            [
                "Outstanding",
                "Very Good",
                "Good",
                "Satisfactory",
                "Failed",
                "Re-Assessment"
            ]
        )

        students = st.number_input(
            "Students",
            min_value=0
        )

        submit = st.form_submit_button(
            "Save Record"
        )

        if submit:

            cur.execute("""
            INSERT INTO performance
            (
              programme,
              academic_year,
              year_level,
              category,
              students
            )
            VALUES (?,?,?,?,?)
            """,
            (
                programme,
                academic_year,
                year_level,
                category,
                students
            ))

            conn.commit()

            st.success("Record Saved")

    st.data_editor(
        fetch("performance"),
        use_container_width=True
    )

# --------------------------------------------------
# GRADUATE OUTCOMES
# --------------------------------------------------

elif menu=="Graduate Outcomes":

    st.subheader("💼 Graduate Outcomes")

    statuses = [
        "Employed",
        "Higher Studies",
        "Self Employed",
        "Internship",
        "Unemployed"
    ]

    with st.form("graduate_form"):

        student_id = st.text_input(
            "Student ID"
        )

        name = st.text_input(
            "Student Name"
        )

        programme = st.selectbox(
            "Programme",
            PROGRAMMES
        )

        gender = st.selectbox(
            "Gender",
            ["Male","Female"]
        )

        grad_year = st.text_input(
            "Graduation Year"
        )

        status = st.selectbox(
            "Status",
            statuses
        )

        org = st.text_input(
            "Organization"
        )

        country = st.text_input(
            "Country"
        )

        remarks = st.text_area(
            "Remarks"
        )

        submitted = st.form_submit_button(
            "Save"
        )

        if submitted:

            cur.execute("""
            INSERT INTO graduate_outcomes
            (
                student_id,
                name,
                programme,
                gender,
                graduation_year,
                status,
                organization,
                country,
                remarks
            )
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                student_id,
                name,
                programme,
                gender,
                grad_year,
                status,
                org,
                country,
                remarks
            ))

            conn.commit()

            st.success("Record saved")

    st.data_editor(
        fetch("graduate_outcomes"),
        use_container_width=True
    )

# --------------------------------------------------
# REPORTS
# --------------------------------------------------

elif menu=="Reports":

    st.subheader("📄 Reports & Exports")

    if st.button("Backup Database"):

        backup_name = datetime.now().strftime(
            "backups/backup_%Y%m%d_%H%M.db"
        )

        shutil.copy(DB, backup_name)

        st.success(
            f"Backup created: {backup_name}"
        )

    if st.button("Generate Excel Report"):

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            fetch("performance").to_excel(
                writer,
                sheet_name="Performance",
                index=False
            )

            fetch("graduate_outcomes").to_excel(
                writer,
                sheet_name="GraduateOutcomes",
                index=False
            )

        st.download_button(
            "Download Excel",
            data=output.getvalue(),
            file_name="Natural_Sciences_Report.xlsx"
        )
