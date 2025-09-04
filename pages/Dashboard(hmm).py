# dashboard.py
import calendar
from datetime import date, datetime, timedelta
import json
import sqlite3
from pathlib import Path
import streamlit as st
import pandas as pd
import random

demo_mode = True  
DB_PATH = Path("app.db")

# (DB + 데모) ????
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables():
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS patient(
            patient_id   INTEGER PRIMARY KEY,
            name         TEXT NOT NULL,
            registered   INTEGER NOT NULL DEFAULT 0
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS doctor_prescription(
            patient_id     INTEGER NOT NULL,
            start_date     TEXT NOT NULL,
            per_day_doses  INTEGER NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patient(patient_id) ON DELETE CASCADE
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_check(
            patient_id     INTEGER NOT NULL,
            record_date    TEXT NOT NULL,
            doses_taken    INTEGER NOT NULL,
            side_effects   TEXT,          -- JSON list of strings
            severities     TEXT,          -- JSON dict {effect:1|2|3}
            emotion_text   TEXT,
            phq9_score     REAL,          -- TODO: 감정→PHQ9 변환 후 저장
            PRIMARY KEY (patient_id, record_date),
            FOREIGN KEY(patient_id) REFERENCES patient(patient_id) ON DELETE CASCADE
        );
        """)
        con.commit()

# 데모 저장소 (앱 재시작시 초기화됨)
if "demo_store" not in st.session_state:
    st.session_state.demo_store = {
        "registered": False,
        "patient": {"patient_id": "dsaintprofessor", "name": "김행근"},  # 데모용 기본값
        "prescription": {"per_day_doses": None, "start_date": date.today().isoformat()},
        "daily": {} ,  # key: 'YYYY-MM-DD' → {"doses_taken":int, "side_effects":[], "severities":{}, "emotion_text":"", "phq9_score":int}
    }


def now_local():
    return datetime.now()

def within_diary_window(ts: datetime) -> bool:
    """18:00~02:00 허용"""
    h = ts.hour
    return (h >= 18) or (h < 2)

def get_patient_name() -> str:
    if demo_mode:
        return st.session_state.demo_store["patient"]["name"]
    else:
        # 실제 환경: 로그인/세션으로 patient_id 전달된다고 가정
        # 여기선 단일 환자(1) 가정. 연동 부: 연주언니 TODO
        with get_conn() as con:
            cur = con.execute("SELECT name FROM patient WHERE patient_id=1;")
            row = cur.fetchone()
            return row[0] if row else "이름미등록"

def is_registered() -> bool:
    if demo_mode:
        return bool(st.session_state.demo_store["registered"])
    else:
        with get_conn() as con:
            cur = con.execute("SELECT registered FROM patient WHERE patient_id=1;")
            row = cur.fetchone()
            return bool(row[0]) if row else False

def set_registration(name: str, per_day_doses: int):
    if demo_mode:
        st.session_state.demo_store["patient"]["name"] = name
        st.session_state.demo_store["registered"] = True
        st.session_state.demo_store["prescription"]["per_day_doses"] = per_day_doses
        st.session_state.demo_store["prescription"]["start_date"] = date.today().isoformat()
    else:
        create_tables()
        with get_conn() as con:
            con.execute("INSERT OR REPLACE INTO patient(patient_id,name,registered) VALUES(1,?,1);", (name,))
            con.execute("DELETE FROM doctor_prescription WHERE patient_id=1;")
            con.execute(
                "INSERT INTO doctor_prescription(patient_id,start_date,per_day_doses) VALUES(1,?,?);",
                (date.today().isoformat(), per_day_doses)
            )
            con.commit()

def get_per_day_doses() -> int | None:
    if demo_mode:
        return st.session_state.demo_store["prescription"]["per_day_doses"]
    else:
        with get_conn() as con:
            cur = con.execute("SELECT per_day_doses FROM doctor_prescription WHERE patient_id=1 ORDER BY start_date DESC LIMIT 1;")
            row = cur.fetchone()
            return int(row[0]) if row else None

def get_daily_records_for_month(year: int, month: int) -> dict:
    """return: { 'YYYY-MM-DD': {'doses_taken':int, 'phq9_score':float, ...}, ... }"""
    if demo_mode:
        return {k: v for k, v in st.session_state.demo_store["daily"].items()
                if k.startswith(f"{year:04d}-{month:02d}-")}
    else:
        start = date(year, month, 1)
        _, last = calendar.monthrange(year, month)
        end = date(year, month, last)
        with get_conn() as con:
            cur = con.execute("""
            SELECT record_date, doses_taken, side_effects, severities, emotion_text, phq9_score
            FROM daily_check
            WHERE patient_id=1 AND record_date BETWEEN ? AND ?;
            """, (start.isoformat(), end.isoformat()))
            out = {}
            for r in cur.fetchall():
                out[r[0]] = {
                    "doses_taken": r[1],
                    "side_effects": json.loads(r[2]) if r[2] else [],
                    "severities": json.loads(r[3]) if r[3] else {},
                    "emotion_text": r[4],
                    "phq9_score": r[5],
                }
            return out

def adherence_emoji(ratio: float) -> str:
    if ratio is None:
        return ""
    if ratio >= 1.0:
        return "D:\\neproject25\\projectUI\\images\\elif 1.png"
    if ratio >= (2/3):
        return "D:\\neproject25\\projectUI\\images\\elif 0.6.png"
    return "D:\\neproject25\\projectUI\\images\\else.png"


st.set_page_config(page_title="Home", page_icon="💊", layout="wide")

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = True

# 헤더
col_a, col_b = st.columns([1.8, 1])
with col_a:
    st.markdown(f"## {get_patient_name()} 님")
with col_b:
    # “하루점검” 버튼 가드: 등록 → 시간
    if st.button("하루점검", use_container_width=True):
        if not is_registered():
            st.warning("먼저 **진료 등록**을 해주세요.")
        else:
            if within_diary_window(now_local()):
                # Streamlit 1.32+: switch_page 사용
                try:
                    st.switch_page("pages/patient_diary.py")
                except Exception:
                    st.session_state.go_diary = True
                    st.experimental_rerun()
            else:
                st.info("하루 점검 페이지는 저녁 6시 ~ 새벽 2시에 작성할 수 있어요!")


with st.expander("진료 등록", expanded=not is_registered()):
    with st.form("reg_form", clear_on_submit=False):
        name = st.text_input("이름", value=get_patient_name() if get_patient_name() != "이름미등록" else "")
        per_day = st.number_input("하루 복용해야 하는 약 봉지 개수(의사 처방)", min_value=1, max_value=12, value=3, step=1)
        ok = st.form_submit_button("등록/업데이트")
        if ok:
            set_registration(name.strip() or "이름미등록", int(per_day))
            st.success("등록이 완료되었습니다.")


left, right = st.columns([1.2, 1], gap="large")


with left:
    st.subheader("칭찬 기록")
    today = date.today()
    y, m = today.year, today.month
    per_day_doses = get_per_day_doses()
    records = get_daily_records_for_month(y, m)

    
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(y, m)
    
    import numpy as np
    import pandas as pd
    data = []
    for week in weeks:
        row = []
        for d in week:
            label = ""
            if d.month == m:
                label = f"{d.day}"
                if per_day_doses and (d.isoformat() in records):
                    taken = records[d.isoformat()].get("doses_taken", 0)
                    r = taken / per_day_doses if per_day_doses else None
                    label = f"{d.day}\n{adherence_emoji(r)}"
            row.append(label)
        data.append(row)
    df = pd.DataFrame(data, columns=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
    st.dataframe(df, use_container_width=True, height=260)


with right:
    st.subheader("오늘의 응원 메시지")
   
    MESSAGES = [
    "오늘도 잘 버텨낸 당신, 충분히 잘하고 있어요!", 
    "오늘 하루도 정말 수고 많았어요.(토닥토닥)",
    "당신은 생각보다 훨씬 잘하고 있어요!",
    "힘든 하루였지만 여기까지 온 당신이 대단해요.",
    "실수해도 괜찮아요, 그건 배우고 있다는 증거니까요.",
    "당신의 오늘은 분명 의미 있었어요.",
    "오늘의 당신은 분명 어제보다 더 나은 사람이에요.",
    "지금 이 순간에도 성장 중이에요 🌱",
    "마음이 무거운 날엔 가볍게 쉬어도 괜찮아요.",
    "쉬어 가도 괜찮아요. 이런 날도 있어야죠!",
    "자신을 칭찬해 주세요. 스스로를 향한 믿음이 가장 힘이 세답니다.",
    "당신은 충분히 잘하고 있고, 잘 해낼 거예요.",
    "누구보다 당신이 당신을 아껴야 해요.💖",
    "오늘 하루도 버텨낸 당신에게 박수를 보내요!👏🏻",
    "힘들 땐 잠시 쉬어가도 괜찮아요.",
    "당신은 존재만으로도 커다란 의미를 주는 사람이에요.",
    "지금의 노력은 분명 좋은 결과로 돌아올 거예요. 믿어봐요!",
    "언제나 당신의 편에 서있을테니 함께 해봐요!",
    "지금 당신이 부단히 보낸 하루하루가 모여 평안한 매일이 되기를.",
    "조금 느려도 괜찮아요. 당신은 당신의 속도일 때 가장 자유로워요.",
    "완벽하지 않아도 충분히 아름다워요.",
    "다가올 당신의 모든 시간을 사랑하세요!",
    "당신이 만든 작은 변화가 당신을 크게 도울거에요.",
    "사랑할 줄 아는 당신을 정말 사랑해요!",
    "어떤 순간에도 자신을 믿어요!",
    "당신은 무너져도 다시 일어날 수 있는 사람이에요.",
    "오늘의 감정도, 당신의 일부이기에 그것마저 소중하고 귀하답니다.",
    "오늘을 살아낸 당신은 이미 그것만으로 충분히 자랑스러워요.",
    "당신의 감정을 이해해요. 오늘 하루도 정말 수고 많았어요.",
    "당신의 오늘이 어제보다 나아지길 바라요🌈"
    ]
    if MESSAGES:
        st.success(random.choice(MESSAGES))
    else:
        st.info("응원 메시지를 등록해주세요. (코드의 MESSAGES 리스트)")

    st.subheader("마음 기록 (PHQ-9 추정 점수)")
    items = sorted(records.items())[-5:]
    if items:
        series = pd.Series(
            [v.get("phq9_score", None) for _, v in items],
            index=[k[5:] for k, _ in items]  # MM-DD 라벨
        )
        series = series.fillna(0)
        st.bar_chart(series)
    else:
        st.caption("표시할 데이터가 아직 없어요. 먼저 하루점검을 저장해줘!")

if st.session_state.get("go_diary"):
    st.session_state.go_diary = False
    st.page_link("pages/patient_diary.py", label="하루점검으로 이동", icon="📝")
