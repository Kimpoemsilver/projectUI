import streamlit as st
import json
import os

DATA_FILE = "patients.json"
BACK_PAGE_PATH = "pages/Dashboard.py"

def load_patients():
    if os.path.exists(DATA_FILE):
    # DATA_FILE이 있는지 확인함. 
    # exists() = 주어진 경로가 실제로 존재하는지 확인하는 함수.
        with open(DATA_FILE, "r", encoding="utf-8") as f:
        # open("파일경로", "모드", encoding="인코딩방식")
            return json.load(f)
            # load() = 파일에서 읽어서 변환.
            # json.load(file_object) = 파일 객체 안에 있는 JSON 문자열을 읽어서
            # 파이썬 객체(딕셔너리/리스트 등)로 변환.
            # load() 안에 str이 인자로 들어가면 문자열에서 읽어서 변환. 
    return []

name = st.session_state.get("name", "김행근")
st.title(f"{name}님 프로필")

patients = load_patients()

if not patients:
    st.info("프로필을 입력해주세요.")
    if st.button("프로필 등록하기"):
        st.session_state["edit_mode"] = False
        st.switch_page("pages/Patient_intake2.py")
else:
    profile = patients[-1]
    # 파이썬 리스트는 인덱스(index)로 요소에 접근함.
    # 인덱스: 리스트 안에서 각 원소(값)에 붙여진 번호표.
    # patients[0] = 리스트에 저장된 첫 번째 환자
    # patients[1] = 리스트에 저장된 두 번째 환자.
    # [-1] = 리스트의 마지막 요소.
    # [-2] = 뒤에서 두 번째 요소

    left, right = st.columns([6,3])
    with left:
        st.subheader(f"👤 {profile['이름']} 님의 프로필")

    with right:
        if st.button("수정"):
            st.session_state["edit_mode"] = True
            st.session_state["selected_patient"] = profile
            st.switch_page("pages/Patient_intake2.py")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**나이**: {profile['나이']}")
        st.write(f"**성별**: {profile['성별']}")
    with col2:
        st.write(f"**키**: {profile['키']} cm")
        st.write(f"**몸무게**: {profile['몸무게']} kg")

    st.markdown("### 검사 수치")
    st.write(f"- 공복혈당: {profile['공복혈당']} mg/dL")
    st.write(f"- eGFR: {profile['eGFR']} mL/min/1.73㎡")
    st.write(f"- AST: {profile['AST']} IU/L")
    st.write(f"- ALT: {profile['ALT']} IU/L")

if st.button("돌아가기"):
    st.session_state["is_logged_in"] = True
    st.switch_page("pages/Dashboard.py")