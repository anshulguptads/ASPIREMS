# -*- coding: utf-8 -*-
"""teacher_dashboard

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1dpNnHh83SjyYtUAfi8E8J6MLOS89xdTf
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def show_teacher_dashboard(teacher_id, data):
    teachers = data['teachers']
    students = data['students']
    sections = data['sections']
    skills = data['skills']
    tasks = data['tasks']
    assessments = data['assessments']
    milestones = data['milestones']
    mentor_chats = data['mentor_chats']
    interventions = data['interventions']
    resources = data['resources']
    parent_teacher_msgs = data['parent_teacher_msgs']

    # --- Teacher Profile Card ---
    teacher = teachers[teachers['teacher_id'] == teacher_id].iloc[0]
    st.header(f"👩‍🏫 Welcome, {teacher['name']}")
    st.markdown(f"**Email:** {teacher['email']}")
    st.markdown(f"**Assigned Sections:** {', '.join(str(x) for x in eval(teacher['assigned_sections']))}")
    st.divider()

    # --- Class Overview ---
    st.subheader("📊 Class Overview & Heatmap")
    # Find students assigned to this teacher
    my_students = students[students['assigned_teacher_id'] == teacher_id]
    st.markdown(f"**Total Students:** {len(my_students)}")
    class_overview = my_students[['student_id', 'name', 'grade', 'section', 'aspiration', 'progress', 'risk_flag']]
    st.dataframe(class_overview, height=200)
    # Progress heatmap by section
    if not my_students.empty:
        section_progress = my_students.groupby('section')['progress'].mean().reset_index()
        fig = px.bar(section_progress, x='section', y='progress', title="Avg. Progress by Section")
        st.plotly_chart(fig, use_container_width=True)
    st.divider()

    # --- Student Drilldown ---
    st.subheader("👨‍🎓 Student Drilldown")
    student_id = st.selectbox("Select Student", my_students['student_id'])
    s = my_students[my_students['student_id'] == student_id].iloc[0]
    st.markdown(f"**Name:** {s['name']}, **Grade:** {s['grade']}, **Risk:** `{s['risk_flag']}`")
    st.markdown(f"**Aspirations:** {', '.join(eval(s['aspiration']))}")
    st.markdown(f"**Progress:** {s['progress']*100:.1f}%")

    # Student skill gap (first suggested career)
    career_suggestions = eval(s['career_suggestions'])
    skill_df = skills[(skills['student_id'] == student_id) & (skills['aspiration'] == career_suggestions[0])]
    if not skill_df.empty:
        fig = px.line_polar(skill_df, r='current_level', theta='skill', line_close=True,
                            title=f"Student Skill Gap: {career_suggestions[0]}")
        fig.add_scatterpolar(r=skill_df['required_level'], theta=skill_df['skill'],
                             fill='toself', name='Required')
        st.plotly_chart(fig, use_container_width=True)

    # Student tasks and assessment summary
    s_tasks = tasks[tasks['student_id'] == student_id]
    s_assess = assessments[assessments['student_id'] == student_id]
    st.markdown(f"**Pending Tasks:** {s_tasks[s_tasks['status'] != 'Completed'].shape[0]} | **Avg. Quiz Score:** {s_assess['score'].mean():.1f}")
    st.dataframe(s_tasks[['subject', 'status', 'due_date', 'completed_date']].sort_values('due_date'), height=100)
    st.dataframe(s_assess[['subject', 'score', 'date', 'feedback']].sort_values('date'), height=100)

    st.divider()

    # --- Progress Analytics ---
    st.subheader("📈 Progress Analytics")
    # Distribution of student progress
    fig = px.histogram(my_students, x='progress', nbins=20, title="Student Progress Distribution")
    st.plotly_chart(fig, use_container_width=True)
    # Risk distribution
    risk_counts = my_students['risk_flag'].value_counts()
    st.bar_chart(risk_counts)

    # Leaderboard by assessment score
    student_scores = assessments[assessments['student_id'].isin(my_students['student_id'])]
    avg_scores = student_scores.groupby('student_id')['score'].mean().reset_index()
    top_students = avg_scores.sort_values('score', ascending=False).merge(my_students[['student_id', 'name']], on='student_id').head(5)
    st.markdown("**Top 5 Students by Avg. Assessment Score:**")
    st.table(top_students[['name', 'score']])

    st.divider()

    # --- Assignments & Assessment Management ---
    st.subheader("📝 Assignments & Assessments")
    st.markdown("**Assignment Completion:**")
    assign_status = tasks[tasks['student_id'].isin(my_students['student_id'])]['status'].value_counts()
    st.bar_chart(assign_status)
    st.markdown("**Recent Quizzes/Tests:**")
    st.dataframe(student_scores.sort_values('date', ascending=False).head(10)[['student_id', 'subject', 'score', 'date', 'feedback']], height=140)

    st.divider()

    # --- Mentor Interaction Logs ---
    st.subheader("🤖 Mentor AI Chat Summary")
    chats = mentor_chats[mentor_chats['student_id'].isin(my_students['student_id'])]
    st.markdown(f"**Total Mentor Interactions:** {chats.shape[0]}")
    st.dataframe(chats[['student_id', 'date', 'topic', 'resolved']].sort_values('date', ascending=False).head(10), height=100)
    unresolved = chats[chats['resolved'] == False].shape[0]
    st.warning(f"{unresolved} unresolved AI mentor issues flagged for follow-up.")

    st.divider()

    # --- Teacher Interventions/Feedback ---
    st.subheader("✍️ Intervention & Feedback Log")
    my_interventions = interventions[(interventions['teacher_id'] == teacher_id)]
    st.dataframe(my_interventions[['student_id', 'date', 'note']].sort_values('date', ascending=False).head(12), height=100)

    st.divider()

    # --- Resource Sharing & Access ---
    st.subheader("📚 Resource Sharing & Usage")
    res = resources[resources['student_id'].isin(my_students['student_id'])]
    res_counts = res['resource_type'].value_counts()
    st.markdown("**Resource Type Distribution:**")
    st.bar_chart(res_counts)
    st.dataframe(res[['student_id', 'resource_type', 'subject', 'usage_time_minutes', 'access_date']].sort_values('access_date', ascending=False).head(10), height=100)

    st.divider()

    # --- Parent-Teacher Communication Center ---
    st.subheader("📬 Parent-Teacher Communication")
    msgs = parent_teacher_msgs[parent_teacher_msgs['teacher_id'] == teacher_id].sort_values('date', ascending=False).head(8)
    for idx, row in msgs.iterrows():
        st.markdown(f"**{row['date']} | {row['sender'].capitalize()}:** {row['message']}")

    st.divider()

    # --- Download Teacher's Student Data ---
    st.download_button("Download My Class Data",
        data=my_students.to_csv(index=False),
        file_name=f"{teacher_id}_students.csv")