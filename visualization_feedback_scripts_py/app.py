"""Streamlit entry point for the TeachCL lesson-plan co-design assistant."""

import base64
import json
import uuid
from datetime import datetime, timezone

import streamlit as st

from conversation_export import (
    build_analysis_record, build_conversation_record, build_session_record,
    format_session_text, utc_now,
)
from feedback_generator import generate_feedback
from google_drive_store import allocate_participant_id, load_drive_config, upload_record
from interaction_tracker import code_interaction
from llm_client import MODEL_NAME, conversation_input, stream_openai
from pattern_detector import detect_interaction_pattern
from prompts import CHATBOT_PROMPT
from scaffold_selector import select_scaffold
from visualization.radar_chart import render_interaction_radar_chart


def _archive(kind, record, session_id):
    """Try Drive immediately; retain only in Streamlit session state on failure."""
    key = f"{kind}:{session_id}"
    st.session_state.archive_outbox[key] = record
    try:
        config = load_drive_config()
        if config is None:
            if st.session_state.archive_errors.get(key) != "not_configured":
                print(f"Drive archive skipped ({kind}): [google_drive] secrets are not configured")
            st.session_state.archive_errors[key] = "not_configured"
            return False
        upload_record(config, kind, record, session_id)
        st.session_state.archive_outbox.pop(key, None)
        st.session_state.archive_errors.pop(key, None)
        return True
    except Exception as error:
        # Do not log request bodies, secrets, or participant-facing archive details.
        st.session_state.archive_errors[key] = type(error).__name__
        print(f"Drive archive failed ({kind}): {type(error).__name__}")
        return False


def _flush_archive_outbox():
    for key, record in list(st.session_state.archive_outbox.items()):
        kind, session_id = key.split(":", 1)
        _archive(kind, record, session_id)


def _show_archive_status():
    pending = st.session_state.archive_outbox
    errors = st.session_state.archive_errors
    if not pending:
        return
    if "not_configured" in errors.values():
        st.sidebar.warning(
            "Google Drive archiving is not configured. Records are pending only in this browser session."
        )
        return
    pending_kinds = sorted({key.split(":", 1)[0] for key in pending})
    st.sidebar.warning(
        "Google Drive upload is pending for: " + ", ".join(pending_kinds)
        + ". Check the Apps Script deployment and Drive permissions."
    )


def _conversation_record(status="in_progress"):
    return build_conversation_record(
        st.session_state.conversation_history,
        st.session_state.participant_id,
        st.session_state.research_session_id,
        st.session_state.session_started_at,
        status=status,
    )


def _save_analysis_record():
    record = st.session_state.analysis_record
    record["updated_at"] = utc_now()
    _archive("analysis", record, st.session_state.research_session_id)


def _render_auto_download(record):
    """Ask the browser to download both files; visible buttons are the fallback."""
    stem = f"participant_{record['participant_id']}_{record['session_id']}"
    files = [
        (f"{stem}.txt", format_session_text(record).encode("utf-8"), "text/plain;charset=utf-8"),
        (f"{stem}.json", (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), "application/json;charset=utf-8"),
    ]
    for filename, content, mime in files:
        st.download_button(
            f"Download {filename}", content, file_name=filename, mime=mime,
            key=f"download:{record['session_id']}:{filename}",
        )
    if not st.session_state.get("download_dispatched"):
        encoded_files = [
            {"name": name, "mime": mime, "data": base64.b64encode(content).decode("ascii")}
            for name, content, mime in files
        ]
        st.components.v1.html(
            "<script>(function(){const files=" + json.dumps(encoded_files) + ";"
            "files.forEach((f,i)=>setTimeout(()=>{const raw=atob(f.data);"
            "const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));"
            "const url=URL.createObjectURL(new Blob([bytes],{type:f.mime}));"
            "const a=document.createElement('a');a.href=url;a.download=f.name;"
            "document.body.appendChild(a);a.click();a.remove();"
            "setTimeout(()=>URL.revokeObjectURL(url),1000);},i*700));})();</script>",
            height=0,
        )
        st.session_state.download_dispatched = True


st.set_page_config(page_title="TeachCL Co-design Assistant", layout="centered")
st.title("TeachCL Co-design Assistant")
st.caption("Co-design a lesson plan with AI, then review feedback and a visual reflection aid.")

defaults = {
    "conversation_history": [],
    "session_started_at": datetime.now(timezone.utc).isoformat(),
    "analysis": None,
    "chart_bytes": None,
    "collaboration_completed": False,
    "analysis_record": None,
    "analysis_stage": {},
    "archive_outbox": {},
    "archive_errors": {},
    "download_dispatched": False,
    "drive_setup_error": None,
    "api_key": "",
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default
if not str(st.session_state.get("participant_id", "")).isdigit():
    try:
        st.session_state.participant_id = allocate_participant_id(load_drive_config())
    except Exception as error:
        st.session_state.participant_id = allocate_participant_id(None)
        st.session_state.drive_setup_error = type(error).__name__
        print("Google Drive participant numbering unavailable; using an in-memory fallback number.")
if "research_session_id" not in st.session_state:
    st.session_state.research_session_id = uuid.uuid4().hex

with st.sidebar:
    st.header("Connection")
    st.caption(f"Model: `{MODEL_NAME}`")
    api_key = st.text_input(
        "OpenAI API key", type="password", key="api_key", placeholder="sk-...",
        help="Used for this browser session and not written to project files.",
    )
    if st.button("Start a new conversation"):
        # Flush queued records before switching sessions; keep any failed items queued.
        _flush_archive_outbox()
        st.session_state.conversation_history = []
        st.session_state.research_session_id = uuid.uuid4().hex
        st.session_state.session_started_at = datetime.now(timezone.utc).isoformat()
        st.session_state.analysis = None
        st.session_state.chart_bytes = None
        st.session_state.collaboration_completed = False
        st.session_state.analysis_record = None
        st.session_state.analysis_stage = {}
        st.session_state.completed_session_record = None
        st.session_state.download_dispatched = False
        st.rerun()

for message in st.session_state.conversation_history:
    if message.get("role") in {"user", "assistant"}:
        with st.chat_message(message["role"]):
            st.markdown(message.get("content", ""))

if not api_key:
    st.info("Enter your OpenAI API key in the sidebar to start.")

user_input = st.chat_input(
    "Share your instructional design ideas…",
    disabled=not api_key or st.session_state.collaboration_completed,
)
if user_input:
    timestamp = datetime.now(timezone.utc).isoformat()
    st.session_state.conversation_history.append({"role": "user", "content": user_input, "timestamp": timestamp})
    _archive("content", _conversation_record(), st.session_state.research_session_id)
    with st.chat_message("user"):
        st.markdown(user_input)
    streamed_chunks = []

    def _response_chunks():
        for chunk in stream_openai(
            system_prompt=CHATBOT_PROMPT,
            user_input=conversation_input(st.session_state.conversation_history),
            api_key=api_key,
        ):
            streamed_chunks.append(chunk)
            yield chunk

    try:
        with st.chat_message("assistant"):
            reply = st.write_stream(_response_chunks, cursor="▌")
        st.session_state.conversation_history.append({
            "role": "assistant", "content": reply,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        _archive("content", _conversation_record(), st.session_state.research_session_id)
    except Exception as error:
        if streamed_chunks:
            partial_reply = "".join(streamed_chunks)
            st.session_state.conversation_history.append({
                "role": "assistant", "content": partial_reply,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "partial": True,
            })
            _archive("content", _conversation_record(), st.session_state.research_session_id)
        st.error(f"Could not generate a response: {error}")

st.divider()
st.subheader("Review this collaboration")
st.write("Generate a reflection and visual summary after you finish co-designing the lesson plan.")
has_teacher_turn = any(m.get("role") == "user" for m in st.session_state.conversation_history)
if st.button(
    "Finish collaboration and generate reflection",
    disabled=not api_key or not has_teacher_turn or st.session_state.collaboration_completed,
):
    history = st.session_state.conversation_history
    _archive("content", _conversation_record(status="completed"), st.session_state.research_session_id)
    if st.session_state.analysis_record is None:
        st.session_state.analysis_record = build_analysis_record(
            st.session_state.participant_id,
            st.session_state.research_session_id,
            st.session_state.session_started_at,
        )
        st.session_state.analysis_record["analysis_timestamp"] = utc_now()
        st.session_state.analysis_stage = {}
    record = st.session_state.analysis_record
    stages = st.session_state.analysis_stage
    try:
        with st.spinner("Analyzing the collaboration and preparing feedback…"):
            if "coding" not in stages:
                coding = code_interaction(history, api_key=api_key)
                stages["coding"] = coding
                record["code_status"] = "complete"
                record["interaction_codes"] = coding
                _save_analysis_record()
            coding = stages["coding"]

            if "pattern" not in stages:
                pattern = detect_interaction_pattern(history, coding_result=coding, api_key=api_key)
                stages["pattern"] = pattern
                record["pattern_status"] = "complete"
                record["pattern"] = {
                    "name": pattern.get("pattern"),
                    "label": pattern.get("pattern_label"),
                    "confidence": pattern.get("confidence"),
                }
                record["evidence"] = pattern.get("evidence")
                _save_analysis_record()
            pattern = stages["pattern"]

            scaffold = select_scaffold(coding)
            if st.session_state.chart_bytes is None:
                st.session_state.chart_bytes = render_interaction_radar_chart(scaffold["data"])
            record["visualization"] = {"type": "radar", "code_counts": scaffold["data"]}

            if "feedback" not in stages:
                feedback = generate_feedback(
                    conversation_history=history,
                    pattern_result=pattern,
                    interaction_codes=coding,
                    api_key=api_key,
                )
                stages["feedback"] = feedback
                record["feedback_status"] = "complete"
                record["feedback_generated"] = True
                record["feedback_text"] = feedback.get("feedback")
                record["feedback_features"] = {
                    "validation": feedback.get("validation"),
                }
                record["analysis_status"] = "complete"
                _archive("feedback", {
                    "participant_id": st.session_state.participant_id,
                    "feedback_text": feedback.get("feedback", ""),
                    "chart_base64": base64.b64encode(
                        st.session_state.chart_bytes
                    ).decode("ascii"),
                }, st.session_state.research_session_id)
                _save_analysis_record()

            st.session_state.analysis = {
                "feedback": stages["feedback"],
            }
            completed_record = build_session_record(
                _conversation_record(status="completed"), record
            )
            st.session_state.completed_session_record = completed_record
            _archive("sheet", completed_record, st.session_state.research_session_id)
            st.session_state.collaboration_completed = True
    except Exception as error:
        record["analysis_status"] = "partial"
        record["last_error_type"] = type(error).__name__
        _save_analysis_record()
        st.error("Analysis could not be completed. Your conversation is still available; please retry.")

_flush_archive_outbox()
_show_archive_status()
if st.session_state.drive_setup_error:
    st.sidebar.warning(
        "Google Drive participant numbering could not be reached; check that the updated Apps Script is deployed."
    )

analysis = st.session_state.analysis
if analysis:
    st.divider()
    st.subheader("Visual reflection")
    if st.session_state.chart_bytes:
        st.image(st.session_state.chart_bytes, use_container_width=True)
    st.caption("The chart summarizes observable interaction frequencies and is not a rating of teaching ability.")
    st.subheader("Feedback on our collaboration")
    feedback = analysis["feedback"]
    st.markdown(feedback["feedback"])
    if not feedback["validation"]["is_valid"]:
        st.caption("Formatting note: " + " ".join(feedback["validation"]["errors"]))
    if st.session_state.get("completed_session_record"):
        st.divider()
        st.subheader("Save your session record")
        st.caption("Your browser may download the TXT and JSON files automatically. If it blocks them, use the download buttons below; files normally go to your Downloads folder.")
        _render_auto_download(st.session_state.completed_session_record)
