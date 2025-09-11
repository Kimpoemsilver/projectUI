import streamlit as st
import json
import os

DATA_FILE = "patients.json"

BACK_PAGE_PATH = "pages/Dashboard.py"

def load_patients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

st.title("🏥 메인 화면")

st.header("📂 이전 환자 기록")
patients = load_patients()

if patients:
    for idx, p in enumerate(patients):
        # 환자 이름을 버튼으로 표시
        if st.button(f"{p['이름']} (나이 {p['나이']}, 성별 {p['성별']})", key=f"patient_{idx}"):
            st.session_state["selected_patient"] = p  # 클릭한 환자 저장
            st.switch_page("pages/Patient_detail.py")  # 상세 페이지로 이동
else:
    st.info("저장된 진료 기록이 없습니다.")

if st.button("새 진료 등록하기"):
    st.switch_page("pages/Patient_intake2.py")

st.button("돌아가기")
if st.button:
    st.session_state["is_logged_in"] = True
    st.switch_page(BACK_PAGE_PATH)