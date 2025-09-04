import streamlit as st

st.set_page_config(page_title="로그인", page_icon="💊", layout="centered")

st.session_state.setdefault("is_logged_in", False)
st.session_state.setdefault("patient_id", None)

col1, col2, col3 = st.columns([1,3,1])
with col2:
    st.title("로그인")

    patient_id = st.text_input("아이디", placeholder="아이디를 입력하세요.")
    password = st.text_input("비밀번호", type="password", placeholder = "비밀번호를 입력하세요.")

    login_clicked = st.button("로그인", use_container_width=True)

    left_col2, right_col2 = st.columns([5,2])
    with left_col2:
        st.write("만약, 아이디가 없다면")
    with right_col2:
        if st.button("회원가입", use_container_width=True):
            st.switch_page("pages/Register.py")

## 임시 로그인 확인 
    if login_clicked:
        if patient_id == "dsaintprofessor" and password == "fighting123@":
            st.session_state["is_logged_in"]= True
            st.session_state["patient_id"] = patient_id
            st.switch_page("pages/Dashboard(save).py")
        elif not (patient_id and password):
            st.error("모든 항목을 입력해주세요.")
        else:
            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")


# 이후에 추가
## DB 연결
## pasword Hash 처리
## 아이디가 DB에 없으면 "아이디를 찾을 수 없습니다." 메세지 출력.
