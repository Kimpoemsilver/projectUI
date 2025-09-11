import streamlit as st
import json
import os

DATA_FILE = "patients.json"

def save_patient(data):
    # 파일 없으면 초기화
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    # 기존 데이터 불러오기
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        patients = json.load(f)

    # 새로운 데이터 추가
    patients.append(data)

    # 저장
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(patients, f, ensure_ascii=False, indent=2)

# ---------------------------------------------
# 환자 등록 UI
# ---------------------------------------------
st.markdown("## 환자 등록")

name = st.text_input("이름")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("나이", min_value=0, max_value=120, step=1)
with col2:
    sex = st.radio("성별", ["남", "여"], horizontal=True)

col3, col4 = st.columns(2)
with col3:
    height = st.number_input("키 (cm)", min_value=0.0, step=0.1)
with col4:
    weight = st.number_input("몸무게 (kg)", min_value=0.0, step=0.1)

st.write("### 검사 수치 입력")
glucose = st.text_input("공복혈당 (mg/dL)")
egfr = st.text_input("eGFR (mL/min/1.73㎡)")
ast = st.text_input("AST (IU/L)")
alt = st.text_input("ALT (IU/L)")

# ---------------------------------------------
# 프로필 저장 버튼
# ---------------------------------------------
if st.button("프로필 저장"):

    required_fields = [name, age, sex, height, weight, glucose, egfr, ast, alt]
    if any(str(value).strip() == "" for value in required_fields):
        st.error("모든 항목을 입력해주세요.")
        st.stop()

    try:
        glucose_val = float(glucose)
        egfr_val = float(egfr)
        ast_val = float(ast)
        alt_val = float(alt)
    except ValueError:
        st.error("검사 수치는 숫자로 입력해주세요.")
        st.stop()


    profile = {
        "이름": name,
        "나이": age,
        "성별": sex,
        "키": height,
        "몸무게": weight,
        "공복혈당": glucose_val,
        "eGFR": egfr_val,
        "AST": ast_val,
        "ALT": alt_val
    }

    # session_state에도 기록
    if "records" not in st.session_state:
        st.session_state["records"] = []
    st.session_state["records"].append(profile)

    # JSON 파일에도 기록
    save_patient(profile)

    st.success(f"{name} 환자 프로필이 저장되었습니다.")
    saved = True

if saved:
    if st.button("닫기"):   
        st.switch_page("pages/Patient_intake1.py")
    