import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_utils import build_export_bundle, filter_dataframe, summarize_counts

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Natural Sciences QA Dashboard",
    page_icon="🎓",
    layout="wide",
)

# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 100%);
    }
    .main {
        background-color: #f8fbff;
    }
    [data-testid="stMetric"] {
        background: #ffffff;
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 4px 18px rgba(37, 99, 235, 0.10);
        border-left: 6px solid #2563eb;
    }
    h1, h2, h3 {
        color: #0f3d7a;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

Path("data").mkdir(exist_ok=True)
Path("backups").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)

DB = "data/natural_sciences.db"

conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS performance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        programme TEXT,
        academic_year TEXT,
        year_level TEXT,
        category TEXT,
        students INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)

cur.execute(
    """
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
    """
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS exchange_programmes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year TEXT,
        programme TEXT,
        student TEXT,
        institution TEXT,
        country TEXT
    )
    """
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS internships(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year TEXT,
        programme TEXT,
        student TEXT,
        organization TEXT,
        location TEXT
    )
    """
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS guest_lectures(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lecture_date TEXT,
        speaker TEXT,
        institution TEXT,
        topic TEXT,
        programme TEXT
    )
    """
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS alumni(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        programme TEXT,
        graduation_year TEXT,
        organization TEXT,
        country TEXT,
        email TEXT
    )
    """
)

conn.commit()

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

PROGRAMMES = ["Life Science", "Chemistry", "Physics"]


def fetch(table):
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def insert_record(table, values, columns):
    placeholders = ", ".join(["?"] * len(values))
    column_sql = ", ".join(columns)
    cur.execute(f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})", values)
    conn.commit()


def create_dashboard_chart(df):
    if df.empty:
        return None

    chart_df = df.groupby(["programme", "category"], as_index=False)["students"].sum()
    fig = px.bar(
        chart_df,
        x="programme",
        y="students",
        color="category",
        title="Performance by Programme and Category",
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_status_chart(df):
    if df.empty:
        return None

    chart_df = df.groupby("status", as_index=False).size()
    fig = px.pie(
        chart_df,
        names="status",
        values="size",
        title="Graduate Employment Status",
        hole=0.45,
    )
    fig.update_layout(template="plotly_white")
    return fig


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    # 🎓 Department of Natural Sciences

    ### Academic Monitoring, Graduate Tracking & Quality Assurance System

    **Sherubtse College • Royal University of Bhutan**

    Life Science • Chemistry • Physics
    """
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.image("https://img.icons8.com/color/96/university.png", width=70)
st.sidebar.markdown("### Navigation")
menu = st.sidebar.selectbox(
    "Choose a module",
    [
        "Dashboard",
        "Student Performance",
        "Graduate Outcomes",
        "Exchange Programme",
        "Internships",
        "Guest Lectures",
        "Alumni",
        "Reports",
    ],
)

selected_programme = st.sidebar.selectbox("Programme Filter", ["All"] + PROGRAMMES)
selected_year = st.sidebar.text_input("Academic Year Filter", "")

# --------------------------------------------------
# COMMON DATA
# --------------------------------------------------

perf = fetch("performance")
grad = fetch("graduate_outcomes")

exch = fetch("exchange_programmes")
intr = fetch("internships")
guest = fetch("guest_lectures")
alumni = fetch("alumni")

perf_filtered = filter_dataframe(perf, selected_programme, selected_year)
grad_filtered = filter_dataframe(grad, selected_programme, selected_year, "programme", "graduation_year")
exch_filtered = filter_dataframe(exch, selected_programme, selected_year, "programme", "year")
intr_filtered = filter_dataframe(intr, selected_programme, selected_year, "programme", "year")
guest_filtered = filter_dataframe(guest, selected_programme, selected_year, "programme", "lecture_date")
alumni_filtered = filter_dataframe(alumni, selected_programme, selected_year, "programme", "graduation_year")

summary = summarize_counts(
    perf_filtered,
    grad_filtered,
    exch_filtered,
    intr_filtered,
    guest_filtered,
    alumni_filtered,
)

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if menu == "Dashboard":
    st.subheader("📊 Live Dashboard Overview")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Performance Records", summary["performance_records"])
    col2.metric("Graduate Records", summary["graduate_records"])
    col3.metric("Exchange Students", summary["exchange_students"])
    col4.metric("Internships", summary["internships"])
    col5.metric("Guest Lectures", summary["guest_lectures"])
    col6.metric("Alumni Records", summary["alumni_records"])

    st.divider()

    left_col, right_col = st.columns([2, 1])
    with left_col:
        fig = create_dashboard_chart(perf_filtered)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.markdown("### Quick Insights")
        st.info("Use the sidebar filters to focus on a programme or academic year.")
        if not grad_filtered.empty:
            status_fig = create_status_chart(grad_filtered)
            if status_fig:
                st.plotly_chart(status_fig, use_container_width=True)
        else:
            st.caption("No graduate outcomes available yet.")

# --------------------------------------------------
# STUDENT PERFORMANCE
# --------------------------------------------------

elif menu == "Student Performance":
    st.subheader("📊 Student Performance")

    with st.form("performance_form", clear_on_submit=True):
        programme = st.selectbox("Programme", PROGRAMMES)
        academic_year = st.text_input("Academic Year", str(datetime.now().year))
        year_level = st.selectbox("Year Level", ["Year 1", "Year 2", "Year 3"])
        category = st.selectbox(
            "Category",
            ["Outstanding", "Very Good", "Good", "Satisfactory", "Failed", "Re-Assessment"],
        )
        students = st.number_input("Students", min_value=0, step=1)
        submitted = st.form_submit_button("Save Record")

        if submitted:
            insert_record(
                "performance",
                (programme, academic_year, year_level, category, students),
                ["programme", "academic_year", "year_level", "category", "students"],
            )
            st.success("Performance record saved successfully.")

    st.dataframe(perf_filtered, use_container_width=True)

# --------------------------------------------------
# GRADUATE OUTCOMES
# --------------------------------------------------

elif menu == "Graduate Outcomes":
    st.subheader("💼 Graduate Outcomes")

    with st.form("graduate_form", clear_on_submit=True):
        student_id = st.text_input("Student ID")
        name = st.text_input("Student Name")
        programme = st.selectbox("Programme", PROGRAMMES)
        gender = st.selectbox("Gender", ["Male", "Female"])
        grad_year = st.text_input("Graduation Year", str(datetime.now().year))
        status = st.selectbox("Status", ["Employed", "Higher Studies", "Self Employed", "Internship", "Unemployed"])
        org = st.text_input("Organization")
        country = st.text_input("Country")
        remarks = st.text_area("Remarks")
        submitted = st.form_submit_button("Save")

        if submitted:
            insert_record(
                "graduate_outcomes",
                (student_id, name, programme, gender, grad_year, status, org, country, remarks),
                ["student_id", "name", "programme", "gender", "graduation_year", "status", "organization", "country", "remarks"],
            )
            st.success("Graduate outcome saved successfully.")

    st.dataframe(grad_filtered, use_container_width=True)

# --------------------------------------------------
# EXCHANGE
# --------------------------------------------------

elif menu == "Exchange Programme":
    st.subheader("🌍 Exchange Programmes")

    with st.form("exchange_form", clear_on_submit=True):
        year = st.text_input("Year", str(datetime.now().year))
        programme = st.selectbox("Programme", PROGRAMMES)
        student = st.text_input("Student Name")
        institution = st.text_input("Institution")
        country = st.text_input("Country")
        submitted = st.form_submit_button("Save")

        if submitted:
            insert_record(
                "exchange_programmes",
                (year, programme, student, institution, country),
                ["year", "programme", "student", "institution", "country"],
            )
            st.success("Exchange record saved successfully.")

    st.dataframe(exch_filtered, use_container_width=True)

# --------------------------------------------------
# INTERNSHIPS
# --------------------------------------------------

elif menu == "Internships":
    st.subheader("🏢 Internships")

    with st.form("internship_form", clear_on_submit=True):
        year = st.text_input("Year", str(datetime.now().year))
        programme = st.selectbox("Programme", PROGRAMMES)
        student = st.text_input("Student Name")
        organization = st.text_input("Organization")
        location = st.text_input("Location")
        submitted = st.form_submit_button("Save")

        if submitted:
            insert_record(
                "internships",
                (year, programme, student, organization, location),
                ["year", "programme", "student", "organization", "location"],
            )
            st.success("Internship record saved successfully.")

    st.dataframe(intr_filtered, use_container_width=True)

# --------------------------------------------------
# GUEST LECTURES
# --------------------------------------------------

elif menu == "Guest Lectures":
    st.subheader("🎤 Guest Lectures")

    with st.form("guest_form", clear_on_submit=True):
        lecture_date = st.text_input("Lecture Date")
        speaker = st.text_input("Speaker")
        institution = st.text_input("Institution")
        topic = st.text_input("Topic")
        programme = st.selectbox("Programme", PROGRAMMES)
        submitted = st.form_submit_button("Save")

        if submitted:
            insert_record(
                "guest_lectures",
                (lecture_date, speaker, institution, topic, programme),
                ["lecture_date", "speaker", "institution", "topic", "programme"],
            )
            st.success("Guest lecture saved successfully.")

    st.dataframe(guest_filtered, use_container_width=True)

# --------------------------------------------------
# ALUMNI
# --------------------------------------------------

elif menu == "Alumni":
    st.subheader("👩‍🎓 Alumni")

    with st.form("alumni_form", clear_on_submit=True):
        name = st.text_input("Name")
        programme = st.selectbox("Programme", PROGRAMMES)
        graduation_year = st.text_input("Graduation Year", str(datetime.now().year))
        organization = st.text_input("Organization")
        country = st.text_input("Country")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Save")

        if submitted:
            insert_record(
                "alumni",
                (name, programme, graduation_year, organization, country, email),
                ["name", "programme", "graduation_year", "organization", "country", "email"],
            )
            st.success("Alumni record saved successfully.")

    st.dataframe(alumni_filtered, use_container_width=True)

# --------------------------------------------------
# REPORTS
# --------------------------------------------------

elif menu == "Reports":
    st.subheader("📄 Reports & Exports")

    st.markdown("Export the full database into a polished Excel workbook with all modules included.")

    if st.button("Backup Database"):
        backup_name = datetime.now().strftime("backups/backup_%Y%m%d_%H%M.db")
        shutil.copy(DB, backup_name)
        st.success(f"Backup created: {backup_name}")

    export_data = {
        "Performance": perf,
        "Graduate_Outcomes": grad,
        "Exchange_Programmes": exch,
        "Internships": intr,
        "Guest_Lectures": guest,
        "Alumni": alumni,
    }

    excel_bytes = build_export_bundle(export_data)
    st.download_button(
        "Download Excel Report",
        data=excel_bytes,
        file_name="Natural_Sciences_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
