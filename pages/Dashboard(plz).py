import calendar
from datetime import date, datetime, time
import random
import pandas as pd
import streamlit as st

demo_mode = True

st.set_page_config(page_title="Home", page_icon="💊", layout="wide")

if not st.session_state.get("is_logged_in", False):
    st.error("잘못된 접근입니다.")
    st.stop()

if demo_mode:
    patient_id = st.session_state["patient_id"]
    st.session_state.setdefault("name", "김행근")
    name = st.session_state["name"]

header_col1, header_col2 = st.columns([4,1])
with header_col1:
    st.markdown(
        f"""
        <div style="padding: 1.2rem 1.5rem; border-radius: 12px; background-color: #1f1f1f; border: 1px solid #444; width: fit-content;">
            <span style="font-size: 2rem; font-weight: 800; letter-spacing: 0.5px;">{name} 님</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def is_diary_time(now: datetime) -> bool:
    now_time = now.time()
    return now_time >= time(18, 0) or now_time <= time(2,0)
    # now.time() = datetime 객체에서 시간만 뽑아내는 메서드.
    # -> datetime(2025, 08, 26, 20, 30)에서 now.time()은 20:30
now = datetime.now()

left, right = st.columns([1,1])
st.markdown(" ")
st.markdown(" ")
with right:
    right_col1, right_col2 = st.columns([1,1])
    with right_col2:
        button_1, button_2 = st.columns([1,1])
        with button_1:
            if st.button("진료등록", use_container_width=True):
                st.switch_page("pages/Patient_intake.py")

        with button_2:
            if st.button("하루점검", use_container_width=True):
                if demo_mode:
                    st.switch_page("pages/Patient_diary.py")
                else:
                    if "진료 등록하지 않았을 경우":
                        st.warning("먼저 진료 등록을 해주세요!")
                    elif is_diary_time(now):
                        st.switch_page("pages/Patient_diary.py")
                    else:
                        st.success("하루 점검은 오후 6시부터 가능합니다.")
                
