# app/main.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import streamlit.components.v1 as components

from app.controller import run_task
# from utils.speech import record_and_transcribe


st.set_page_config(page_title="🧠 AI Multi-Agent Automator", layout="wide")
st.markdown("<h1 style='text-align:center;'> Multi-Agent Android Automation</h1>", unsafe_allow_html=True)
st.markdown("---")


if "chatroom" in st.session_state:
    with st.sidebar:
        st.markdown("## 💬 Chat Memory")
        for msg in st.session_state.chatroom.get_history():
            st.markdown(f"**[{msg['sender']}]** ({msg['type']}): {msg['content'][:200]}")


@st.dialog("User Input Required")
def get_user_input(up):
    st.write(up)
    updated_task = st.text_input("", key="updated_task_input")
    if st.button("Submit"):
        if updated_task.strip():
            driver, chatroom, task_status = run_task(
                updated_task.strip(),
                driver=st.session_state.get("driver"),
                chatroom=st.session_state.get("chatroom")
            )
            st.session_state["driver"] = driver
            st.session_state["chatroom"] = chatroom
            st.session_state["task_status"] = task_status
        else:
            st.warning("Please enter a valid task.")
        st.rerun()


col1, col2, col3 = st.columns([1.5, 2.5, 1.5])

# with col2:
st.subheader("📝 Enter Your Automation Task")


task_input = st.text_input("Type a task (e.g., 'Open camera and take a selfie')", key="task")

if st.button("🚀 Start Automation"):
    task = st.session_state.get("task_voice", "").strip() or st.session_state.get("task", "").strip()
    if not task:
        st.warning("Please enter or speak a task first.")
    else:
        with st.spinner("Running multi-agent task..."):
            driver, chatroom, task_status = run_task(task)
            st.session_state["chatroom"] = chatroom
            st.session_state["driver"] = driver
            st.session_state["task_status"] = task_status

# with col2:
task_status = st.session_state.get("task_status")
if task_status == "done":
    st.success("✅ Task completed successfully.")
elif task_status == "Paused":
    st.warning("🕓 Task paused, waiting for user input.")
    cht = st.session_state.get("chatroom","")
    up=cht.get_latest("user_prompt")
    get_user_input(up["content"]) 
elif task_status == "max_iterations_reached":
    st.error("⏹️ Max iterations reached. Task stopped.")


st.markdown("---")
st.markdown("### 📱 Agent Status & Feedback")

if "chatroom" in st.session_state:
    summary = st.session_state.chatroom.get_latest("summary")
    if summary:
        st.success(f"Task Summary:\n\n{summary['content']}")