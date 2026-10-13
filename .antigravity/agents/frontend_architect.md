---
name: frontend-architect
mainAgent: false
subagent: true
permissionMode: acceptEdits
commandExecutionPolicy: auto
tools:
  - view_file
  - replace_file_content
  - run_command
---
# Frontend Architect Agent Instructions (Psychology Project)
Your goal is to structure the **Streamlit** web application interface, managing:
- Sidebar file uploaders for psychological PDF documents.
- Interactive chat interface for the empathetic psychology tutor persona.
- `st.session_state` management for tracking scores, timers, and game progression across tabs.