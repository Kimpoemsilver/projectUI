import streamlit as st
import re

demo_mode = True

st.set_page_config(page_title="회원가입", page_icon="💊", layout="centered")

# 임시 DB
dummy_users = ["Sieuni", "Yeonju", "Dongchan", "Junseo", "Jooyoung"]

st.session_state.setdefault("is_id_checked", False)
st.session_state.setdefault("id_available", None)
st.session_state.setdefault("last_checked_id", "")

id_pattern = re.compile(r"^(?=.*[A-Za-z])[A-Za-z0-9]{6,20}$")
pw_pattern = re.compile(r"^(?=.*[A-Za-z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,20}$")

def is_valid_id(patient_id:str) -> bool:
    return bool(id_pattern.fullmatch(patient_id or ""))

def is_valid_pw(password:str) -> bool:
    return bool(pw_pattern.fullmatch(password or ""))

def reset_id_check():
    st.session_state["is_id_checked"] = False
    st.session_state["id_available"] = None

co11, col2, col3 = st.columns([1,5,1])

with col2:
    st.title("회원가입")

    left_col2_1, right_col2_1= st.columns([5,2], vertical_alignment="bottom")    
    with left_col2_1:
        name = st.text_input("이름")
        patient_id = st.text_input(
        "아이디", 
        key = "register_patient_id",
        placeholder = "영문과 숫자 입력 가능, 6-20자",
        on_change = reset_id_check)


    with right_col2_1:
        checked_clicked = st.button("중복확인", use_container_width=True)

    if patient_id and not is_valid_id(patient_id):
        st.error("아이디 조건을 확인해주세요.")
    elif checked_clicked: 
        if not is_valid_id(patient_id):
            st.error("아이디 조건을 확인해주세요.")
        else:
            st.session_state["is_id_checked"] = True
            st.session_state["last_checked_id"] = patient_id
            st.session_state["id_available"] = patient_id not in dummy_users
            if st.session_state["id_available"]:
                st.success("사용 가능한 아이디입니다.")
            else:
                st.error("이미 사용 중인 아이디입니다.")

    password = st.text_input(   
        "비밀번호",
        type = "password",
        placeholder = "영문+숫자+특수문자 조합, 8-20자")

    if password and not is_valid_pw(password):
        st.error("비밀번호 조건을 확인해주세요.")

    password_check = st.text_input(
        "비밀번호 확인", 
        type="password",
        placeholder="비밀번호를 다시 입력해주세요.")
    
    if password_check and password != password_check:
        st.error("비밀번호가 일치하지 않습니다.")

    if st.button("회원가입", use_container_width=True):
        if not (name and patient_id and password and password_check):
            st.error("모든 항목을 입력해주세요.")
            st.stop()

        if not st.session_state["is_id_checked"] or st.session_state["last_checked_id"]!=patient_id:
            st.error("아이디 중복 확인을 해주세요.")
            st.stop()

        if not (is_valid_id(patient_id) and is_valid_pw(password)):
            st.error("아이디 혹은 비밀번호 조건을 다시 확인해주세요.")
            st.stop()

        if not st.session_state["id_available"]:
            st.error("중복된 아이디입니다.")
            st.stop()
        
        if not demo_mode:
            dummy_users.append(patient_id)

        st.session_state["is_logged_in"] = True
        st.session_state["patient_id"] = patient_id
        st.session_state["name"] = name
        st.switch_page("pages/Dashboard(save).py")


    left_col2_2, right_col2_2= st.columns([5,2])
    with left_col2_2:
        st.write("만약, 아이디가 있다면")
    with right_col2_2:
        if st.button("로그인", use_container_width=True):
            st.switch_page("Login.py")

