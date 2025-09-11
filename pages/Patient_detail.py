import streamlit as st

st.title("🧾 환자 상세 정보")

if "selected_patient" not in st.session_state:
    st.warning("환자를 선택하지 않았습니다. 메인 화면으로 돌아가세요.")
    st.page_link("main_home.py", label="🏠 메인으로 돌아가기")
else:
    patient = st.session_state["selected_patient"]

    st.subheader(f"👤 {patient['이름']} 님의 프로필")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**나이**: {patient['나이']}")
        st.write(f"**성별**: {patient['성별']}")
    with col2:
        st.write(f"**키**: {patient['키']} cm")
        st.write(f"**몸무게**: {patient['몸무게']} kg")

    st.markdown("### 🧪 검사 수치")
    st.write(f"- 공복혈당: {patient['공복혈당']} mg/dL")
    st.write(f"- eGFR: {patient['eGFR']} mL/min/1.73㎡")
    st.write(f"- AST: {patient['AST']} IU/L")
    st.write(f"- ALT: {patient['ALT']} IU/L")

    # 돌아가기 버튼
    if st.button("⬅ 메인으로 돌아가기"):
        st.switch_page("main_home.py")
