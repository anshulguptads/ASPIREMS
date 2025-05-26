import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
import ast
from datetime import datetime

def safe_list(val):
    if isinstance(val, list):
        return val
    try:
        return ast.literal_eval(val)
    except Exception:
        return [str(val)]

def show_student_dashboard(student_id, data):
    # Load main datasets
    students = data['students']
    skills = data['skills']
    tasks = data['tasks']
    assessments = data['assessments']
    resources = data['resources']
    milestones = data['milestones']
    mentor_chats = data['mentor_chats']
    interventions = data['interventions']
    notifications = data['notifications']
    journals = data['journals']
    parents = data['parents']
    teachers = data['teachers']

    # Load additional datasets
    flashcards = pd.read_csv('flashcards.csv')
    content_catalog = pd.read_csv('content_catalog.csv')

    student = students[students['student_id'] == student_id].iloc[0]
    # Parse aspirations and career_suggestions robustly
    aspirations = safe_list(student['aspiration'])
    career_paths = safe_list(student['career_suggestions'])

    # --- Top Achievement Bar ---
    my_milestones = milestones[milestones['student_id'] == student_id]
    badge_list = my_milestones['badge'].unique().tolist()
    streak = my_milestones['date_awarded'].nunique()
    grade_section = (student['grade'], student['section'])
    peers = students[(students['grade'] == student['grade']) & (students['section'] == student['section'])]
    peer_progress = peers['progress']
    student_percentile = (peer_progress < student['progress']).mean() * 100
    motivational_quotes = [
        "You're doing great! Keep pushing forward.",
        "Every day is a new chance to improve.",
        "Believe in yourself and all that you are.",
        "Stay curious, stay motivated!"
    ]
    mot_quote = random.choice(motivational_quotes)
    col1, col2, col3, col4 = st.columns([2,1,1,3])
    col1.markdown("🏅 **Badges:** " + (", ".join(badge_list[:3]) if badge_list else "None"))
    col2.metric("Streak", f"{streak} days")
    col3.metric("Percentile", f"{int(student_percentile)}%")
    col4.success(mot_quote)
    st.divider()

    # --- Profile Card ---
    st.markdown(f"### {student['name']} | Grade {student['grade']}, Section {student['section']}")
    st.markdown(f"**Aspirations:** {', '.join(aspirations)}")
    st.progress(student['progress'])
    st.markdown(f"**Psychometric Score:** {student['psychometric_score']}")
    st.markdown(f"**Risk Level:** `{student['risk_flag']}`")
    st.divider()

    # --- Quick Actions ---
    if "qa_clicked" not in st.session_state:
        st.session_state['qa_clicked'] = None
    ca1, ca2, ca3, ca4 = st.columns(4)
    if ca1.button("🤖 Ask AI Mentor"):
        st.session_state['qa_clicked'] = "ai_mentor"
    if ca2.button("⚡ Start Revision"):
        st.session_state['qa_clicked'] = "flashcards"
    if ca3.button("📝 Take a Quiz"):
        st.session_state['qa_clicked'] = "assessments"
    if ca4.button("📓 Update Journal"):
        st.session_state['qa_clicked'] = "journal"
    st.divider()

    # ----------- Main Content Tabs -------------
    tabs = st.tabs([
        "Career Pathways & Skill Gap", "Flashcards", "Assessments",
        "Learning Path", "Recommended Content", "Journal",
        "AI Mentor Chat", "Class Standing", "Feedback/Events"
    ])

    # Tab index map for quick action routing
    tab_map = {
        "ai_mentor": 6,
        "flashcards": 1,
        "assessments": 2,
        "journal": 5
    }
    auto_tab = tab_map.get(st.session_state['qa_clicked'], 0)

    # --- Career Pathways & Skill Gap (5 radars) ---
    with tabs[0]:
        st.subheader("🎯 Career Pathways & Skill Gap")
        for cp in career_paths[:5]:
            st.markdown(f"#### {cp}")
            skill_df = skills[(skills['student_id'] == student_id) & (skills['aspiration'] == cp)]
            if not skill_df.empty:
                radar_fig = px.line_polar(skill_df, r='current_level', theta='skill', line_close=True,
                                         title=f"{cp} - Skill Gap")
                radar_fig.add_scatterpolar(r=skill_df['required_level'], theta=skill_df['skill'],
                                           fill='toself', name='Required')
                st.plotly_chart(radar_fig, use_container_width=True)
                ready = (skill_df['current_level'] >= skill_df['required_level']).mean() * 100
                st.progress(int(ready), f"{int(ready)}% Ready")
            else:
                st.info(f"No skill data for {cp}.")
        st.markdown("**Milestones Timeline (Simulated):**")
        for cp in career_paths[:5]:
            st.info(f"{cp}: Complete next milestones to reach readiness!")

    # --- Flashcards ---
    with tabs[1]:
        st.subheader("🃏 Flashcards for Quick Revision")
        subjects_with_cards = flashcards[flashcards['student_id'].isin([student_id, 'ALL'])]['subject'].unique().tolist()
        subject = st.selectbox("Choose Subject", subjects_with_cards)
        student_cards = flashcards[((flashcards['student_id'] == student_id) | (flashcards['student_id'] == 'ALL')) & (flashcards['subject'] == subject)]
        topics_for_subject = student_cards['topic'].unique().tolist()
        topic = st.selectbox("Choose Topic", topics_for_subject)
        filtered_cards = student_cards[student_cards['topic'] == topic].reset_index(drop=True)
        if not filtered_cards.empty:
            card_idx = st.number_input("Card #", min_value=1, max_value=len(filtered_cards), value=1)
            card = filtered_cards.iloc[int(card_idx)-1]
            st.write(f"**Q:** {card['question']}")
            with st.expander("Show Answer"):
                st.write(f"**A:** {card['answer']}")
            st.write(f"**Known:** {card['is_known']}")
        else:
            st.info("No flashcards for this selection.")

    # --- Assessments & Peer Comparison ---
    with tabs[2]:
        st.subheader("📝 Assessments & Peer Comparison")
        my_assessments = assessments[assessments['student_id'] == student_id].sort_values('date')
        st.dataframe(my_assessments[['subject', 'score', 'date', 'feedback']], height=180)
        peer_assessments = assessments[assessments['student_id'].isin(peers['student_id']) & (assessments['subject'].isin(my_assessments['subject'].unique()))]
        # Plot both "You" and "Class Avg"
        if not my_assessments.empty and not peer_assessments.empty:
            # Align dates
            my_scores = my_assessments[['date', 'score']].set_index('date')
            class_avg = peer_assessments.groupby('date')['score'].mean().reindex(my_scores.index)
            plot_df = pd.DataFrame({'You': my_scores['score'], 'Class Avg': class_avg})
            fig = px.line(plot_df, y=['You', 'Class Avg'], title="Your Scores vs Class Average")
            st.plotly_chart(fig, use_container_width=True)

    # --- Learning Path / Tasks ---
    with tabs[3]:
        st.subheader("📚 Learning Path & Tasks")
        my_tasks = tasks[tasks['student_id'] == student_id]
        st.dataframe(my_tasks[['subject', 'status', 'assigned_date', 'due_date', 'completed_date']].sort_values('due_date'), height=120)
        st.bar_chart(my_tasks['status'].value_counts())

    # --- Recommended Content ---
    with tabs[4]:
        st.subheader("📂 Recommended Articles & Resources")
        weak_skills = skills[(skills['student_id'] == student_id) & (skills['current_level'] < skills['required_level'])]
        weak_topics = weak_skills['skill'].unique().tolist()
        if weak_topics:
            recs = content_catalog[content_catalog['topic'].isin(weak_topics)].drop_duplicates(subset=['title']).head(5)
            st.markdown("**AI-recommended for your skill gaps:**")
        else:
            recs = content_catalog.sample(5)
            st.markdown("**Recommended for exploration:**")
        if not recs.empty:
            for idx, row in recs.iterrows():
                st.markdown(f"- [{row['title']}]({row['url']}) — *{row['description']}*")
        st.dataframe(recs[['title', 'subject', 'topic', 'content_type', 'url', 'description']])

    # --- Reflection & Journal ---
    with tabs[5]:
        st.subheader("📓 Reflection & Journal")
        my_journals = journals[journals['student_id'] == student_id].sort_values('date', ascending=False)
        st.dataframe(my_journals[['date', 'entry']], height=80)
        new_entry = st.text_area("Add your reflection/journal for today")
        if st.button("Save Reflection", key="save_journal_btn"):
            st.success("Reflection saved! (In production, this will write to DB or file)")

    # --- AI Mentor Chat ---
    with tabs[6]:
        st.subheader("🤖 Ask the AI Mentor")
        query = st.text_input("Type your question for the AI Mentor:")
        if st.button("Ask AI Mentor"):
            ai_reply = f"(AI Mentor simulated response to: '{query}')"
            st.success(ai_reply)
        chat_hist = mentor_chats[mentor_chats['student_id'] == student_id].sort_values('date', ascending=False)
        st.dataframe(chat_hist[['date', 'topic', 'summary', 'resolved']], height=90)

    # --- Class Standing ---
    with tabs[7]:
        st.subheader("📊 Class Standing")
        rank = (peer_progress > student['progress']).sum() + 1
        st.markdown(f"**Your rank in section:** {rank} / {len(peer_progress)}")
        st.bar_chart({'You': [student['progress']], 'Class Avg': [peer_progress.mean()]})
        leaderboard = peers[['name', 'progress']].sort_values('progress', ascending=False).reset_index(drop=True)
        leaderboard['Rank'] = leaderboard.index + 1
        st.table(leaderboard[['Rank', 'name', 'progress']].head(5))

    # --- Feedback / Events / Notifications ---
    with tabs[8]:
        st.subheader("📣 Feedback, Notifications & Events")
        my_teacher_notes = interventions[interventions['student_id'] == student_id].sort_values('date', ascending=False).head(2)
        st.markdown("**Recent Teacher Notes:**")
        for idx, row in my_teacher_notes.iterrows():
            st.write(f"- *{row['date']}:* {row['note']}")
        my_student_notifications = notifications[(notifications['student_id'] == student_id) & (notifications['audience'] == 'student')].sort_values('date', ascending=False)
        st.dataframe(my_student_notifications[['date', 'notif_type', 'content']], height=80)
        st.markdown("**Upcoming Deadlines/Events:**")
        my_tasks = tasks[tasks['student_id'] == student_id]
        events = my_tasks[(my_tasks['status'] != 'Completed') & (pd.to_datetime(my_tasks['due_date']) >= datetime.now())]
        st.table(events[['subject', 'due_date']].sort_values('due_date').head(3))

    # --- Handle Quick Action Navigation ---
    # --- Handle Quick Action Navigation ---
    if st.session_state['qa_clicked'] and auto_tab != 0:
        st.query_params["tab"] = auto_tab
        st.session_state['qa_clicked'] = None

