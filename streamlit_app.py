import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Natural Sciences QA Dashboard",
    page_icon="🎓",
    layout="wide"
)

# ==================================================
# STYLING
# ==================================================

st.markdown("""
<style>

.stApp{
    background-color:#f7fafc;
}

[data-testid="stMetric"]{
    background:white;
    padding:15px;
    border-radius:12px;
    border-left:6px solid #2563eb;
    box-shadow:0px 3px 10px rgba(0,0,0,0.08);
}

h1,h2,h3{
    color:#0f3d7a;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# FOLDERS
# ==================================================

Path("data").mkdir(parents=True, exist_ok=True)
Path("backups").mkdir(parents=True, exist_ok=True)
Path("exports").mkdir(parents=True, exist_ok=True)

# ==================================================
# DATABASE
# ==================================================

DB = "data/natural_sciences.db"

conn = sqlite3.connect(
    DB,
    check_same_thread=False
)

cur = conn.cursor()

# ==================================================
# TABLES
# ==================================================

cur.execute("""
CREATE TABLE IF NOT EXISTS performance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    programme TEXT,
    academic_year TEXT,
    year_level TEXT,
    category TEXT,
    students INTEGER
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

# ==================================================
# HELPERS
# ==================================================

PROGRAMMES = [
    "Life Science",
    "Chemistry",
    "Physics"
]


def fetch(table):
    return pd.read_sql_query(
        f"SELECT * FROM {table}",
        conn
    )


def insert_record(table, values, columns):
    placeholders = ",".join(["?"] * len(values))
    sql = f"""
    INSERT INTO {table}
    ({','.join(columns)})
    VALUES ({placeholders})
    """
    cur.execute(sql, values)
    conn.commit()


def filter_dataframe(
        df,
        programme="All",
        year="",
        programme_col="programme",
        year_col="academic_year"):

    if df.empty:
        return df

    if programme != "All" and programme_col in df.columns:
        df = df[df[programme_col] == programme]

    if year and year_col in df.columns:
        df = df[
            df[year_col].astype(str).str.contains(
                str(year),
                na=False
            )
        ]

    return df


def export_excel(dataframes):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        for name, df in dataframes.items():

            df.to_excel(
                writer,
                sheet_name=name[:31],
                index=False
            )

    return output.getvalue()


# ==================================================
# HEADER
# ==================================================

st.title("🎓 Department of Natural Sciences")
st.caption(
    "Academic Monitoring, Graduate Tracking and Quality Assurance System"
)

# ==================================================
# SIDEBAR
# ==================================================

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

selected_year = st.sidebar.text_input(
    "Year Filter"
)

# ==================================================
# LOAD DATA
# ==================================================

perf = fetch("performance")
grad = fetch("graduate_outcomes")
exch = fetch("exchange_programmes")
intr = fetch("internships")
guest = fetch("guest_lectures")
alumni = fetch("alumni")

# ==================================================
# DASHBOARD
# ==================================================

if menu == "Dashboard":

    c1,c2,c3,c4,c5,c6 = st.columns(6)

    c1.metric("Performance", len(perf))
    c2.metric("Graduates", len(grad))
    c3.metric("Exchange", len(exch))
    c4.metric("Internships", len(intr))
    c5.metric("Guest Lectures", len(guest))
    c6.metric("Alumni", len(alumni))

    st.divider()

    if not perf.empty:

        chart = (
            perf
            .groupby(
                ["programme", "category"],
                as_index=False
            )["students"]
            .sum()
        )

        fig = px.bar(
            chart,
            x="programme",
            y="students",
            color="category",
            barmode="group",
            title="Student Performance"
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

# ==================================================
# PERFORMANCE
# ==================================================

elif menu == "Student Performance":

    with st.form("performance"):

        programme = st.selectbox(
            "Programme",
            PROGRAMMES
        )

        academic_year = st.text_input(
            "Academic Year",
            str(datetime.now().year)
        )

        year_level = st.selectbox(
            "Year Level",
            [
                "Year 1",
                "Year 2",
                "Year 3"
            ]
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
            min_value=0,
            step=1
        )

        if st.form_submit_button("Save"):

            insert_record(
                "performance",
                (
                    programme,
                    academic_year,
                    year_level,
                    category,
                    students
                ),
                [
                    "programme",
                    "academic_year",
                    "year_level",
                    "category",
                    "students"
                ]
            )

            st.success("Saved")

    st.data_editor(
        perf,
        width="stretch"
    )

# ==================================================
# GRADUATE OUTCOMES
# ==================================================

elif menu == "Graduate Outcomes":

    st.data_editor(
        grad,
        width="stretch"
    )

# ==================================================
# EXCHANGE
# ==================================================

elif menu == "Exchange Programme":

    st.data_editor(
        exch,
        width="stretch"
    )

# ==================================================
# INTERNSHIPS
# ==================================================

elif menu == "Internships":

    st.data_editor(
        intr,
        width="stretch"
    )

# ==================================================
# GUEST LECTURES
# ==================================================

elif menu == "Guest Lectures":

    st.data_editor(
        guest,
        width="stretch"
    )

# ==================================================
# ALUMNI
# ==================================================

elif menu == "Alumni":

    st.data_editor(
        alumni,
        width="stretch"
    )

# ==================================================
# REPORTS
# ==================================================

elif menu == "Reports":

    if st.button("Backup Database"):

        backup_file = datetime.now().strftime(
            "backups/backup_%Y%m%d_%H%M.db"
        )

        shutil.copy(DB, backup_file)

        st.success(
            f"Backup created: {backup_file}"
        )

    excel_file = export_excel({
        "Performance": perf,
        "GraduateOutcomes": grad,
        "Exchange": exch,
        "Internships": intr,
        "GuestLectures": guest,
        "Alumni": alumni
    })

    st.download_button(
        "📥 Download Excel Report",
        data=excel_file,
        file_name="Natural_Sciences_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
