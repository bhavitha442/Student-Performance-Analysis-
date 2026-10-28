"""
app.py
====================================================================
Student Performance Analysis System - Streamlit Web Application
Clean, modular, beginner-friendly interface for students and teachers.
====================================================================
"""

import streamlit as st
import pandas as pd
import io
import os

from database import (
    test_db_connection,
    init_db,
    load_sample_data,
    get_db_config
)
from student_operations import (
    add_student,
    get_all_students,
    search_students,
    update_student,
    delete_student
)
from subject_operations import (
    add_subject,
    get_all_subjects,
    update_subject,
    delete_subject
)
from marks_operations import (
    add_mark,
    get_all_marks,
    get_marks_for_student,
    update_mark,
    delete_mark,
    get_distinct_assessments
)
from analysis import (
    generate_all_students_summary,
    get_top_performing_students,
    get_students_needing_support,
    get_students_with_missing_marks,
    get_subject_wise_summary,
    get_section_wise_summary,
    get_class_summary
)
from visualizations import (
    plot_subject_averages,
    plot_subject_pass_percentage,
    plot_student_marks_comparison,
    plot_marks_distribution,
    plot_section_performance
)

# Page Configuration
st.set_page_config(
    page_title="Student Performance Analysis System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3d59;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #1e3d59;
    }
</style>
""", unsafe_allow_html=True)


def check_connection_state():
    """Returns True if MySQL is reachable, False otherwise with error."""
    is_connected, msg = test_db_connection()
    return is_connected, msg


def render_sidebar():
    """Sidebar navigation, connection diagnostics, and database setup tools."""
    st.sidebar.title("🎓 Student Analytics")
    st.sidebar.markdown("**Navigation Menu**")

    menu_options = [
        "1. 📊 Dashboard",
        "2. 👨‍🎓 Manage Students",
        "3. 📚 Manage Subjects",
        "4. 📝 Enter & Manage Marks",
        "5. 📋 Student Performance Reports",
        "6. 📈 Class & Subject Analysis",
        "7. 📉 Charts & Data Export"
    ]
    selected_page = st.sidebar.radio("Select Section:", menu_options)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔌 Database Status")

    is_connected, msg = check_connection_state()
    if is_connected:
        st.sidebar.success("✅ MySQL Connected")
    else:
        st.sidebar.error("❌ MySQL Disconnected")
        with st.sidebar.expander("Diagnostic Info"):
            st.caption(msg)
            st.info("Check if MySQL Service is running and your .env credentials match.")

    st.sidebar.markdown("### ⚙️ Quick Actions")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🛠️ Init DB", help="Create tables if they don't exist"):
            with st.spinner("Initializing schema..."):
                ok, res_msg = init_db()
                if ok:
                    st.sidebar.success(res_msg)
                    st.rerun()
                else:
                    st.sidebar.error(res_msg)

    with col2:
        if st.button("📥 Sample Data", help="Load fictional test students & marks"):
            with st.spinner("Loading sample dataset..."):
                ok, res_msg = load_sample_data()
                if ok:
                    st.sidebar.success(res_msg)
                    st.rerun()
                else:
                    st.sidebar.error(res_msg)

    # Global Assessment filter selector
    distinct_assessments = get_distinct_assessments() if is_connected else []
    assessment_choices = ["All / Primary"] + distinct_assessments
    selected_assessment = st.sidebar.selectbox(
        "Current Assessment Filter:",
        assessment_choices,
        index=0,
        help="Evaluates performance metrics for a specific test assessment."
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("First-Year B.Tech Academic Project | Built with Python, Streamlit & MySQL")

    return selected_page, is_connected, selected_assessment


# ====================================================================
# PAGE 1: DASHBOARD
# ====================================================================
def render_dashboard(is_connected: bool, assessment: str):
    st.markdown('<div class="main-header">📊 Academic Performance Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Overview of class performance, academic metrics, and top achievers</div>', unsafe_allow_html=True)

    if not is_connected:
        st.warning("⚠️ **MySQL is currently not reachable.** Please verify your database service is started and .env is configured.")
        st.info("Tip: Use the 'Init DB' button in the sidebar after starting MySQL Server.")
        return

    students = get_all_students()
    subjects = get_all_subjects()
    all_marks = get_all_marks(assessment_filter=None if assessment == "All / Primary" else assessment)

    summary_df = generate_all_students_summary(students, all_marks, subjects, assessment=assessment)
    metrics = get_class_summary(summary_df)

    # Key Metrics Row
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Students", metrics["total_students"])
    m2.metric("Total Subjects", len(subjects))
    m3.metric("Marks Records", len(all_marks))
    m4.metric("Passed", f"{metrics['passed']} ({metrics['pass_percentage']}%)")
    m5.metric("Failed", f"{metrics['failed']} ({metrics['fail_percentage']}%)")
    m6.metric("Incomplete", metrics["incomplete"])

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🏆 Top Performing Students")
        top_df = get_top_performing_students(summary_df, n=5)
        if not top_df.empty:
            cols = ["Rank", "Roll No", "Name", "Section", "Percentage", "Grade", "Status"]
            st.dataframe(top_df[cols], use_container_width=True, hide_index=True)
        else:
            st.info("No graded students available yet. Load sample data or enter marks to view toppers.")

    with col_right:
        st.subheader("⚠️ Academic Support Needed")
        support_df = get_students_needing_support(summary_df, threshold=50.0)
        if not support_df.empty:
            st.dataframe(
                support_df[["Roll No", "Name", "Section", "Percentage", "Grade", "Status"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("All evaluated students are currently performing above the 50% threshold! 🎉")


# ====================================================================
# PAGE 2: MANAGE STUDENTS
# ====================================================================
def render_manage_students(is_connected: bool):
    st.markdown('<div class="main-header">👨‍🎓 Student Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Add, search, view, update, and manage student enrollments</div>', unsafe_allow_html=True)

    if not is_connected:
        st.error("Database connection required to manage students.")
        return

    tab_view, tab_add, tab_edit, tab_delete = st.tabs(["📋 View & Search", "➕ Add Student", "✏️ Edit Student", "🗑️ Delete Student"])

    with tab_view:
        search_kw = st.text_input("🔍 Search by Student Name or Roll Number:", "")
        students = search_students(search_kw)
        if students:
            df = pd.DataFrame(students)
            df = df.rename(columns={
                "student_id": "ID",
                "roll_no": "Roll Number",
                "name": "Full Name",
                "section": "Section",
                "created_at": "Enrollment Date"
            })
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(students)} student record(s).")
        else:
            st.info("No matching students found.")

    with tab_add:
        st.subheader("Enroll New Student")
        with st.form("add_student_form", clear_on_submit=True):
            f_roll = st.text_input("Roll Number (Unique)*", placeholder="e.g. 106")
            f_name = st.text_input("Full Name*", placeholder="e.g. Aarav Patel")
            f_section = st.text_input("Section*", placeholder="e.g. A or B")
            submitted = st.form_submit_button("Add Student Record")

            if submitted:
                ok, msg, new_id = add_student(f_roll, f_name, f_section)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with tab_edit:
        st.subheader("Update Student Information")
        all_s = get_all_students()
        if not all_s:
            st.info("No students enrolled to edit.")
        else:
            s_options = {f"{s['roll_no']} - {s['name']} (Sec {s['section']})": s for s in all_s}
            selected_label = st.selectbox("Select Student to Edit:", list(s_options.keys()))
            student_to_edit = s_options[selected_label]

            with st.form("edit_student_form"):
                e_roll = st.text_input("Roll Number*", value=student_to_edit["roll_no"])
                e_name = st.text_input("Full Name*", value=student_to_edit["name"])
                e_section = st.text_input("Section*", value=student_to_edit["section"])
                edit_btn = st.form_submit_button("Save Changes")

                if edit_btn:
                    ok, msg = update_student(student_to_edit["student_id"], e_roll, e_name, e_section)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    with tab_delete:
        st.subheader("Remove Student Record")
        st.warning("⚠️ Deleting a student will also remove all associated marks records (CASCADE).")
        all_s = get_all_students()
        if not all_s:
            st.info("No students enrolled.")
        else:
            s_options = {f"{s['roll_no']} - {s['name']} (ID: {s['student_id']})": s for s in all_s}
            selected_del = st.selectbox("Select Student to Delete:", list(s_options.keys()))
            target_student = s_options[selected_del]

            confirm_del = st.checkbox(f"Yes, I confirm deleting student {target_student['name']} ({target_student['roll_no']})")
            if st.button("Delete Student", type="primary", disabled=not confirm_del):
                ok, msg = delete_student(target_student["student_id"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ====================================================================
# PAGE 3: MANAGE SUBJECTS
# ====================================================================
def render_manage_subjects(is_connected: bool):
    st.markdown('<div class="main-header">📚 Subject Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Configure curriculum subjects, maximum marks, and pass marks</div>', unsafe_allow_html=True)

    if not is_connected:
        st.error("Database connection required to manage subjects.")
        return

    tab_view, tab_add, tab_edit, tab_delete = st.tabs(["📋 View Subjects", "➕ Add Subject", "✏️ Edit Subject", "🗑️ Delete Subject"])

    with tab_view:
        subjects = get_all_subjects()
        if subjects:
            df = pd.DataFrame(subjects)
            df = df.rename(columns={
                "subject_id": "ID",
                "subject_name": "Subject Name",
                "max_marks": "Maximum Marks",
                "pass_marks": "Pass Marks",
                "created_at": "Created Date"
            })
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No subjects defined yet.")

    with tab_add:
        st.subheader("Add New Subject")
        with st.form("add_subject_form", clear_on_submit=True):
            sub_name = st.text_input("Subject Name (Unique)*", placeholder="e.g. Data Structures")
            sub_max = st.number_input("Maximum Marks*", min_value=1.0, max_value=500.0, value=100.0, step=1.0)
            sub_pass = st.number_input("Pass Marks*", min_value=1.0, max_value=500.0, value=40.0, step=1.0)
            submitted = st.form_submit_button("Add Subject")

            if submitted:
                ok, msg, _ = add_subject(sub_name, sub_max, sub_pass)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with tab_edit:
        st.subheader("Update Subject Configuration")
        subjects = get_all_subjects()
        if not subjects:
            st.info("No subjects available to edit.")
        else:
            sub_map = {f"{s['subject_name']} (Max: {s['max_marks']}, Pass: {s['pass_marks']})": s for s in subjects}
            selected_key = st.selectbox("Choose Subject to Edit:", list(sub_map.keys()))
            target = sub_map[selected_key]

            with st.form("edit_subject_form"):
                e_name = st.text_input("Subject Name*", value=target["subject_name"])
                e_max = st.number_input("Maximum Marks*", min_value=1.0, max_value=500.0, value=float(target["max_marks"]), step=1.0)
                e_pass = st.number_input("Pass Marks*", min_value=1.0, max_value=500.0, value=float(target["pass_marks"]), step=1.0)
                update_btn = st.form_submit_button("Update Subject")

                if update_btn:
                    ok, msg = update_subject(target["subject_id"], e_name, e_max, e_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    with tab_delete:
        st.subheader("Delete Subject")
        st.info("Note: A subject with existing marks cannot be deleted to maintain academic records integrity.")
        subjects = get_all_subjects()
        if not subjects:
            st.info("No subjects available.")
        else:
            sub_map = {f"{s['subject_name']} (ID: {s['subject_id']})": s for s in subjects}
            del_key = st.selectbox("Select Subject to Delete:", list(sub_map.keys()))
            target = sub_map[del_key]

            confirm_sub_del = st.checkbox(f"I confirm deletion of subject: {target['subject_name']}")
            if st.button("Delete Subject", type="primary", disabled=not confirm_sub_del):
                ok, msg = delete_subject(target["subject_id"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ====================================================================
# PAGE 4: ENTER & MANAGE MARKS
# ====================================================================
def render_manage_marks(is_connected: bool):
    st.markdown('<div class="main-header">📝 Marks Entry & Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Record, view, modify, and delete assessment marks</div>', unsafe_allow_html=True)

    if not is_connected:
        st.error("Database connection required to manage marks.")
        return

    students = get_all_students()
    subjects = get_all_subjects()

    if not students:
        st.warning("⚠️ No students found. Please add students first.")
        return
    if not subjects:
        st.warning("⚠️ No subjects found. Please add subjects first.")
        return

    tab_record, tab_view_all, tab_edit, tab_delete = st.tabs(["➕ Record Marks", "📋 View Marks Records", "✏️ Edit Mark", "🗑️ Delete Mark"])

    student_options = {f"{s['roll_no']} - {s['name']} (Sec {s['section']})": s["student_id"] for s in students}
    subject_options = {f"{s['subject_name']} (Max: {s['max_marks']}, Pass: {s['pass_marks']})": s for s in subjects}

    with tab_record:
        st.subheader("Enter Assessment Marks")
        with st.form("add_marks_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                sel_student_label = st.selectbox("Select Student*", list(student_options.keys()))
            with c2:
                sel_subject_label = st.selectbox("Select Subject*", list(subject_options.keys()))

            c3, c4 = st.columns(2)
            with c3:
                assessment_name = st.text_input("Assessment Name*", value="Final Exam", placeholder="e.g. Midterm 1, Final Exam, Quiz 1")
            with c4:
                selected_sub_obj = subject_options[sel_subject_label]
                marks_val = st.number_input(
                    f"Marks Obtained (Max: {selected_sub_obj['max_marks']})*",
                    min_value=0.0,
                    max_value=float(selected_sub_obj["max_marks"]),
                    value=0.0,
                    step=0.5
                )

            submit_mark = st.form_submit_button("Save Marks Entry")
            if submit_mark:
                s_id = student_options[sel_student_label]
                sub_id = selected_sub_obj["subject_id"]
                ok, msg, _ = add_mark(s_id, sub_id, assessment_name, marks_val)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with tab_view_all:
        st.subheader("All Recorded Marks")
        all_marks = get_all_marks()
        if all_marks:
            df = pd.DataFrame(all_marks)
            cols_map = {
                "roll_no": "Roll No",
                "student_name": "Student Name",
                "section": "Section",
                "subject_name": "Subject",
                "assessment": "Assessment",
                "marks_obtained": "Marks Obtained",
                "max_marks": "Max Marks",
                "pass_marks": "Pass Marks",
                "mark_id": "Entry ID"
            }
            display_df = df[list(cols_map.keys())].rename(columns=cols_map)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.caption(f"Total entries: {len(display_df)}")
        else:
            st.info("No marks entries recorded yet.")

    with tab_edit:
        st.subheader("Modify Existing Marks Entry")
        all_marks = get_all_marks()
        if not all_marks:
            st.info("No marks available to edit.")
        else:
            mark_choice_map = {
                f"ID {m['mark_id']}: {m['student_name']} ({m['roll_no']}) - {m['subject_name']} [{m['assessment']}]: {m['marks_obtained']}/{m['max_marks']}": m
                for m in all_marks
            }
            sel_m_label = st.selectbox("Choose Marks Record to Edit:", list(mark_choice_map.keys()))
            m_target = mark_choice_map[sel_m_label]

            with st.form("edit_mark_entry_form"):
                new_assessment = st.text_input("Assessment Name*", value=m_target["assessment"])
                new_marks = st.number_input(
                    f"Marks Obtained (Max: {m_target['max_marks']})*",
                    min_value=0.0,
                    max_value=float(m_target["max_marks"]),
                    value=float(m_target["marks_obtained"]),
                    step=0.5
                )
                save_edit = st.form_submit_button("Update Marks")
                if save_edit:
                    ok, msg = update_mark(m_target["mark_id"], new_assessment, new_marks)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    with tab_delete:
        st.subheader("Delete Marks Record")
        all_marks = get_all_marks()
        if not all_marks:
            st.info("No marks entries to delete.")
        else:
            mark_choice_map = {
                f"ID {m['mark_id']}: {m['student_name']} ({m['roll_no']}) - {m['subject_name']} [{m['assessment']}]: {m['marks_obtained']}": m
                for m in all_marks
            }
            del_m_label = st.selectbox("Select Marks Entry to Remove:", list(mark_choice_map.keys()))
            target_entry = mark_choice_map[del_m_label]

            confirm_del_m = st.checkbox("Confirm deletion of this marks entry")
            if st.button("Delete Entry", type="primary", disabled=not confirm_del_m):
                ok, msg = delete_mark(target_entry["mark_id"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ====================================================================
# PAGE 5: STUDENT PERFORMANCE REPORTS
# ====================================================================
def render_student_reports(is_connected: bool, assessment: str):
    st.markdown('<div class="main-header">📋 Student Performance Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Individual student scorecards, subject breakdowns, and missing test trackers</div>', unsafe_allow_html=True)

    if not is_connected:
        st.error("Database connection required.")
        return

    students = get_all_students()
    subjects = get_all_subjects()

    if not students:
        st.info("No student records found.")
        return

    student_sel_map = {f"{s['roll_no']} - {s['name']} (Section {s['section']})": s for s in students}
    selected_s_key = st.selectbox("Select a Student to View Detailed Report:", list(student_sel_map.keys()))
    s_obj = student_sel_map[selected_s_key]

    student_marks = get_marks_for_student(s_obj["student_id"])
    if assessment != "All / Primary":
        student_marks = [m for m in student_marks if m.get("assessment") == assessment]

    # Individual Student Performance Summary Card
    from analysis import compute_student_summary
    s_summary = compute_student_summary(s_obj, student_marks, subjects, assessment=assessment)

    st.markdown("### 🎓 Student Profile & Performance Card")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Roll Number", s_obj["roll_no"])
    c2.metric("Total Marks", f"{s_summary['total_marks_obtained']} / {s_summary['total_max_marks']}")
    c3.metric("Percentage", f"{s_summary['percentage']}%" if s_summary["percentage"] is not None else "N/A")
    c4.metric("Grade", s_summary["grade"])
    
    # Status styling
    status_label = s_summary["status"]
    if status_label == "Pass":
        c5.success("Status: PASS ✅")
    elif status_label == "Fail":
        c5.error("Status: FAIL ❌")
    elif status_label == "Incomplete":
        c5.warning("Status: INCOMPLETE ⏳")
    else:
        c5.info(f"Status: {status_label}")

    st.markdown("---")
    st.subheader("📚 Subject-wise Breakdown")

    if student_marks:
        m_df = pd.DataFrame(student_marks)
        m_df["Status"] = m_df.apply(lambda r: "Pass" if r["marks_obtained"] >= r["pass_marks"] else "Fail", axis=1)
        m_df["Percentage"] = ((m_df["marks_obtained"] / m_df["max_marks"]) * 100).round(2)

        view_cols = {
            "subject_name": "Subject",
            "assessment": "Assessment",
            "marks_obtained": "Marks Obtained",
            "max_marks": "Max Marks",
            "pass_marks": "Pass Marks",
            "Percentage": "Score %",
            "Status": "Subject Status"
        }
        st.dataframe(m_df[list(view_cols.keys())].rename(columns=view_cols), use_container_width=True, hide_index=True)

        # Plot individual comparison chart
        st.pyplot(plot_student_marks_comparison(student_marks, s_obj["name"]))
    else:
        st.info("No marks entries recorded for this student under the selected filter.")

    # Missing marks tracker
    st.markdown("---")
    st.subheader("🔍 Students with Missing Marks")
    all_marks = get_all_marks(assessment_filter=None if assessment == "All / Primary" else assessment)
    missing_students = get_students_with_missing_marks(students, subjects, all_marks, assessment=assessment)

    if missing_students:
        missing_df = pd.DataFrame(missing_students).rename(columns={
            "roll_no": "Roll No",
            "name": "Student Name",
            "section": "Section",
            "missing_count": "Unattempted Subjects Count",
            "missing_subjects": "Subjects Not Completed"
        })
        st.dataframe(missing_df[["Roll No", "Student Name", "Section", "Unattempted Subjects Count", "Subjects Not Completed"]], use_container_width=True, hide_index=True)
    else:
        st.success("All students have complete marks records for all subjects! 🎉")


# ====================================================================
# PAGE 6: CLASS & SUBJECT ANALYSIS
# ====================================================================
def render_class_subject_analysis(is_connected: bool, assessment: str):
    st.markdown('<div class="main-header">📈 Class & Subject Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive academic statistics, section benchmarking, and pass rates</div>', unsafe_allow_html=True)

    if not is_connected:
        st.error("Database connection required.")
        return

    students = get_all_students()
    subjects = get_all_subjects()
    all_marks = get_all_marks(assessment_filter=None if assessment == "All / Primary" else assessment)

    summary_df = generate_all_students_summary(students, all_marks, subjects, assessment=assessment)

    st.subheader("📖 Subject-wise Performance Analysis")
    sub_df = get_subject_wise_summary(all_marks, subjects, assessment=assessment)

    if not sub_df.empty:
        display_sub = sub_df.drop(columns=["subject_id"], errors="ignore")
        st.dataframe(display_sub, use_container_width=True, hide_index=True)
    else:
        st.info("No subject marks available to analyze.")

    st.markdown("---")
    st.subheader("🏛️ Section-wise Performance Comparison")
    sec_df = get_section_wise_summary(summary_df)

    if not sec_df.empty:
        st.dataframe(sec_df, use_container_width=True, hide_index=True)
    else:
        st.info("No section data available.")

    st.markdown("---")
    st.subheader("🆘 Academic Support Analysis")
    support_threshold = st.slider("Select Academic Support Benchmark (%)", min_value=35.0, max_value=75.0, value=50.0, step=5.0)
    support_df = get_students_needing_support(summary_df, threshold=support_threshold)

    if not support_df.empty:
        st.warning(f"Found {len(support_df)} student(s) below {support_threshold}% or with subject failures.")
        show_cols = ["Rank", "Roll No", "Name", "Section", "Total Obtained", "Percentage", "Grade", "Status", "Failed Subjects"]
        st.dataframe(support_df[[c for c in show_cols if c in support_df.columns]], use_container_width=True, hide_index=True)
    else:
        st.success(f"No students need academic support at the {support_threshold}% benchmark.")


# ====================================================================
# PAGE 7: CHARTS & DATA EXPORT
# ====================================================================
def render_charts_and_export(is_connected: bool, assessment: str):
    st.markdown('<div class="main-header">📉 Performance Visualizations & Data Export</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive Matplotlib charts and downloadable CSV performance reports</div>', unsafe_allow_html=True)

    if not is_connected:
        st.error("Database connection required.")
        return

    students = get_all_students()
    subjects = get_all_subjects()
    all_marks = get_all_marks(assessment_filter=None if assessment == "All / Primary" else assessment)

    summary_df = generate_all_students_summary(students, all_marks, subjects, assessment=assessment)
    sub_df = get_subject_wise_summary(all_marks, subjects, assessment=assessment)
    sec_df = get_section_wise_summary(summary_df)

    tab_charts, tab_export = st.tabs(["📊 Charts & Visualizations", "📥 CSV Data Export"])

    with tab_charts:
        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(plot_subject_averages(sub_df))
        with c2:
            st.pyplot(plot_subject_pass_percentage(sub_df))

        c3, c4 = st.columns(2)
        with c3:
            st.pyplot(plot_marks_distribution(summary_df))
        with c4:
            st.pyplot(plot_section_performance(sec_df))

    with tab_export:
        st.subheader("📥 Download Academic CSV Reports")
        st.write("Export verified data files directly generated from the MySQL database:")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 1. Student Master List")
            if students:
                s_df = pd.DataFrame(students).rename(columns={
                    "roll_no": "Roll_No",
                    "name": "Student_Name",
                    "section": "Section"
                })
                csv_bytes = s_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Students CSV",
                    data=csv_bytes,
                    file_name="students_master_list.csv",
                    mime="text/csv"
                )
            else:
                st.caption("No students to export.")

        with col2:
            st.markdown("#### 2. Marks Master List")
            if all_marks:
                m_df = pd.DataFrame(all_marks)
                csv_bytes = m_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Marks CSV",
                    data=csv_bytes,
                    file_name="marks_records.csv",
                    mime="text/csv"
                )
            else:
                st.caption("No marks to export.")

        with col3:
            st.markdown("#### 3. Overall Performance Summary")
            if not summary_df.empty:
                export_cols = [c for c in summary_df.columns if c != "student_id"]
                csv_bytes = summary_df[export_cols].to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Class Summary CSV",
                    data=csv_bytes,
                    file_name="student_performance_summary.csv",
                    mime="text/csv"
                )
            else:
                st.caption("No summary data to export.")


# ====================================================================
# MAIN APPLICATION CONTROLLER
# ====================================================================
def main():
    selected_page, is_connected, selected_assessment = render_sidebar()

    if "1." in selected_page:
        render_dashboard(is_connected, selected_assessment)
    elif "2." in selected_page:
        render_manage_students(is_connected)
    elif "3." in selected_page:
        render_manage_subjects(is_connected)
    elif "4." in selected_page:
        render_manage_marks(is_connected)
    elif "5." in selected_page:
        render_student_reports(is_connected, selected_assessment)
    elif "6." in selected_page:
        render_class_subject_analysis(is_connected, selected_assessment)
    elif "7." in selected_page:
        render_charts_and_export(is_connected, selected_assessment)


if __name__ == "__main__":
    main()
