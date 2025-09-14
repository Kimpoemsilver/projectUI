import streamlit as st
import json
import os

DATA_FILE = "patients.json"

def save_patient(data, edit_mode=False):
    # 파일 없으면 초기화
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
            # json.dump(obj, fp, ...) = 파이썬 객체를 josn 형식으로 변환해서 파일에 저장. 
            # -> josn.load()와 반대 역할.
            # obj: 저장할 파이썬 객체(딕셔너리, 리스트 등)
            # fp: JSON을 기록할 파일 객체
            # ensure_asci=False: 한글이 꺠지지 않게 그대로 저장하라는 옵션.
            # -> 만약 True일 경우, 유니코드로 변환되어 저장됨.
            # indent: 들여쓰기를 몇 칸 줄지 정해주는 옵션.

    # 파일 읽기
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        patients = json.load(f)

    # 파일 수정할 경우
    if edit_mode and patients:
    # patients가 비어있지 않아야하기 때문에 if patients도 붙여줌.
    # -> 환자 목록 최소 1개 이상 있을 때만!
        patients[-1] = data
    else:
        patients.append(data)
        # 리스트.append() = 리스트 맨 뒤에 새로운 요소 추가해줌.

    # 파일 쓰기
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(patients, f, ensure_ascii=False, indent=2)



st.markdown("## 프로필 등록")

name = st.session_state.get("name", "김행근")
st.text_input("이름", value=name, disabled=True)
# value: 초기값(기본으로 들어가 있는 값)을 정하는 인자.
# name 변수를 불러와서 입력칸 안에 미리 넣어둠.
# disabled: 이 입력칸을 읽기 전용(수정 불가)으로 만드는 옵션.
# -> True면 사용자 직접 입력/수정 불가.


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
if "saved" not in st.session_state:
    st.session_state["saved"] = False

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
    edit_mode = st.session_state.get("edit_mode", False)
    save_patient(profile, edit_mode)
    if "records" not in st.session_state:
        st.session_state["records"] = []
    st.session_state["records"].append(profile)

    # JSON 파일에도 기록
    save_patient(profile)

    st.success(f"{name} 환자 프로필이 저장되었습니다.")
    st.session_state["saved"] = True
    st.session_state["edit_mode"] = False

if st.session_state["saved"]:
    if st.button("닫기"):
        st.session_state["saved"] = False  
        st.switch_page("pages/Patient_intake1.py")
