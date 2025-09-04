import json
from datetime import date, datetime
import sqlite3
import streamlit as st
from pathlib import Path


demo_mode = True  
DB_PATH = Path("app.db") # 여긴 또 DB 연결

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def now_local():
    return datetime.now()

def within_diary_window(ts: datetime) -> bool:
    return (ts.hour >= 18) or (ts.hour < 2)

# ????? 미정
def demo_store():
    return st.session_state.demo_store

def is_registered() -> bool:
    if demo_mode:
        return bool(demo_store()["registered"])
    else:
        with get_conn() as con:
            cur = con.execute("SELECT registered FROM patient WHERE patient_id=1;")
            row = cur.fetchone()
            return bool(row[0]) if row else False

def get_per_day_doses() -> int | None:
    if demo_mode:
        return demo_store()["prescription"]["per_day_doses"]
    else:
        with get_conn() as con:
            cur = con.execute("SELECT per_day_doses FROM doctor_prescription WHERE patient_id=1 ORDER BY start_date DESC LIMIT 1;")
            row = cur.fetchone()
            return int(row[0]) if row else None

def save_daily(record_date: str, doses_taken: int, side_effects: list[str], severities: dict, emotion_text: str, phq9_score: float|None):
    if demo_mode:
        demo_store()["daily"][record_date] = {
            "doses_taken": doses_taken,
            "side_effects": side_effects,
            "severities": severities,
            "emotion_text": emotion_text,
            "phq9_score": phq9_score,
        }
    else:
        with get_conn() as con:
            con.execute("""
            INSERT OR REPLACE INTO daily_check(patient_id,record_date,doses_taken,side_effects,severities,emotion_text,phq9_score)
            VALUES(1,?,?,?,?,?,?);
            """, (record_date, doses_taken, json.dumps(side_effects), json.dumps(severities), emotion_text, phq9_score))
            con.commit()

SIDE_EFFECTS = [
    ("Dry mouth", "입마름"),
    ("Drowsiness", "졸림"),
    ("Insomnia", "불면"),
    ("Blurred vision", "시야 흐림"),
    ("Headache", "두통"),
    ("Constipation", "변비"),
    ("Diarrhoea", "설사"),
    ("Increased appetite", "식욕 증가"),
    ("Decreased appetite", "식욕 저하"),
    ("Nausea or vomiting", "구역감/구토"),
    ("Problems with urination", "배뇨 문제"),
    ("Problems with sexual function", "성기능 문제"),
    ("Palpitations", "가슴 두근거림"),
    ("Feeling light-headed on standing", "기립 시 어지러움"),
    ("Feeling like the room is spinning", "빙글빙글 도는 느낌"),
    ("Sweating", "발한"),
    ("Increased body temperature", "체온 상승"),
    ("Tremor", "떨림"),
    ("Disorientation", "지남력 장애"),
    ("Yawning", "하품"),
    ("Weight gain", "체중 증가"),
]

st.set_page_config(page_title="하루점검", page_icon="📝", layout="centered")


if not is_registered(): # -> 대시보드에서 구현할까 고민중
    st.warning("먼저 진료 등록을 해주세요.")
    st.page_link("../dashboard.py", label="대시보드로 돌아가기", icon="↩️")
    st.stop()

if "diary_step" not in st.session_state:
    st.session_state.diary_step = 1
if "diary_data" not in st.session_state:
    st.session_state.diary_data = {
        "record_date": date.today().isoformat(),
        "doses_taken": 0,
        "effects": [],
        "severities": {},  
        "emotion": "",
    }
saved_flag_key = "diary_saved_flag"
if saved_flag_key not in st.session_state:
    st.session_state[saved_flag_key] = False

per_day = get_per_day_doses() or 0

st.markdown(f"### {demo_store()['patient']['name'] if demo_mode else '환자'}님 하루점검")


if st.session_state.diary_step == 1:
    st.caption("다음의 질문에 답변해주세요.")
    st.write("오늘 하루 동안 약을 얼마나 복용했나요?")
    if per_day <= 0:
        st.error("의사 처방의 1일 복용 개수가 등록되어 있지 않습니다. (진료 등록에서 설정)")
    opts = list(range(0, (per_day or 0) + 1))
    st.session_state.diary_data["doses_taken"] = st.selectbox("복용 횟수", options=opts, index=0, key="dose_select")
    st.write(f" / {per_day}회")

    if st.button("다음", type="primary"):
        st.session_state.diary_step = 2
        st.experimental_rerun()


elif st.session_state.diary_step == 2:
    st.write("오늘, 약물 때문에 겪었다고 느끼는 증상이 있다면 체크해주세요.")
    # 보기 배치(행 단위 컬럼)
    chosen = []
    cols_per_row = 4
    rows = [SIDE_EFFECTS[i:i+cols_per_row] for i in range(0, len(SIDE_EFFECTS), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for (en, ko), c in zip(row, cols):
            with c:
                if st.checkbox(f"{ko}", help="부작용 설명(조사 필요)", key=f"ef_{en}"):
                    chosen.append(en)  # 내부 키는 영어로 저장

    st.session_state.diary_data["effects"] = chosen

    col1, col2 = st.columns(2)
    with col1:
        if st.button("뒤로"):
            st.session_state.diary_step = 1
            st.experimental_rerun()
    with col2:
        if st.button("다음", type="primary"):
            if len(chosen) == 0:
                # 아무것도 없으면 4단계로 스킵
                st.session_state.diary_step = 4
            else:
                st.session_state.diary_step = 3
            st.experimental_rerun()


elif st.session_state.diary_step == 3:
    st.write("선택한 증상의 정도를 선택해주세요 (1=약하게, 3=강하게).")
    effects = st.session_state.diary_data["effects"]
    severities = {}
    for en in effects:
        # 라벨은 한국어 표시
        ko = next((ko for (e, ko) in SIDE_EFFECTS if e == en), en)
        st.markdown(f"**{ko}**")
        val = st.radio(
            label=f"{ko} 강도",
            options=[1,2,3],
            index=0,
            horizontal=True,
            key=f"sev_{en}"
        )
        severities[en] = int(val)
    st.session_state.diary_data["severities"] = severities

    col1, col2 = st.columns(2)
    with col1:
        if st.button("뒤로"):
            st.session_state.diary_step = 2
            st.experimental_rerun()
    with col2:
        if st.button("다음", type="primary"):
            st.session_state.diary_step = 4
            st.experimental_rerun()

elif st.session_state.diary_step == 4:
    st.write("**오늘 하루의 기분 또는 느낌을 자유롭게 표현해주세요.**")
    st.session_state.diary_data["emotion"] = st.text_area(
        "감정 기록",
        placeholder="텍스트를 입력해주세요.",
        height=180
    )

    
    if st.button("저장", type="primary"):
        d = st.session_state.diary_data
        phq9_score = None
        if demo_mode:
            phq9_score = max(0, min(27, int(len(d["emotion"]) / 20)))

        save_daily(
            record_date=d["record_date"],
            doses_taken=int(d["doses_taken"]),
            side_effects=d["effects"],
            severities=d["severities"],
            emotion_text=d["emotion"],
            phq9_score=phq9_score
        )
        st.success("저장되었습니다.")
        st.session_state[saved_flag_key] = True


    if st.session_state[saved_flag_key]:
        st.page_link("../dashboard.py", label="닫기(대시보드로 이동)", icon="✅")


    if st.button("뒤로"):
        if st.session_state.diary_data["effects"]:
            st.session_state.diary_step = 3
        else:
            st.session_state.diary_step = 2
        st.experimental_rerun()
