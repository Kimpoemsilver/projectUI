import streamlit as st
import calendar
from datetime import date, datetime, time, timedelta
import random
import pandas as pd
import sqlite3
from pathlib import Path
import base64
import logging
import altair as alt

# --- demo flag ---
demo_mode = True

st.set_page_config(page_title="Home", page_icon="💊", layout="wide")

if not st.session_state.get("is_logged_in", True):
    st.error("잘못된 접근입니다.")
    st.stop()

# --- Demo patient identity ---
if demo_mode:
    patient_id = st.session_state.get("patient_id", "demo-0001")
    st.session_state.setdefault("name", "김행근")
    st.session_state.setdefault("age", 43)
    st.session_state.setdefault("sex", "M")
    st.session_state.setdefault("height_cm", 172)
    st.session_state.setdefault("weight_kg", 70)
    st.session_state.setdefault("eGFR", 92)
    # previous prescription (example)
    st.session_state.setdefault("prev_prescription", {"dose_mg": 20, "freq_per_day": 1, "date":"2025-08-25"})
    # PK/PD model recommendation (example)
    st.session_state.setdefault("model_reco", {"dose_mg": 10, "freq_per_day": 1, "reason":"based on estimated CL↑ and eGFR"})
    # demo adherence history (date -> fraction of prescribed dose taken that day)
    st.session_state.setdefault("day_num_dose", {
        "2025-09-01": 1.0,
        "2025-09-02": 1/3,
        "2025-09-03": 2/3,
        "2025-09-04": 0.0,
        "2025-09-05": 1.0,
        "2025-09-06": 1.0,
        "2025-09-07": 0.5,
        "2025-09-08": 1.0,
        "2025-09-09": 1.0,
        "2025-09-10": 0.0,
        "2025-09-11": 1.0
    })
    # demo side effects list: each entry has date, symptom, severity 1-3
    st.session_state.setdefault("side_effects", [
        {"date":"2025-09-03","symptom":"구역감","severity":2},
        {"date":"2025-09-05","symptom":"두통","severity":1},
        {"date":"2025-09-09","symptom":"불면","severity":3}
    ])
    # demo diary (free text) entries for text->phq mapping
    st.session_state.setdefault("diary_texts", {
        "2025-09-01":"오늘 우울했고 잠도 못잤어요. 식욕도 없어요.",
        "2025-09-03":"조금 괜찮아졌어요. 산책함.",
        "2025-09-07":"아직 무기력하고 집중이 안돼요.",
        "2025-09-10":"오늘은 괜찮았어요. 친구랑 통화했어요.",
        "2025-09-11":"잠이 들기 힘들었고 불안했어요."
    })

# --- Header ---
name = st.session_state["name"]
header_col1, header_col2 = st.columns([4,1])
with header_col1:
    st.markdown(f"""
                <div style="padding: 1.2rem 1.5rem; border-radius: 12px; background-color: #f5f7fa; border: 1px solid #e5e7eb; width: fit-content; color:#111;">
                <span style="font-size: 2rem; font-weight: 800; letter-spacing: 0.5px;">{name} 님 </span> </div>
                """, unsafe_allow_html=True )

# --- Helper utilities ---

def image_to_base64(img_path:str) -> str:
    try:
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        logging.warning(f"이미지 로드 실패: {img_path} - {e}")
        return ""

# small rule-based text->PHQ9 estimator (very rough; replace with model when available)
PHQ_KEYWORDS = {
    "0": ["괜찮", "좋", "행복", "산책", "친구"],
    "1": ["졸리", "잠", "불면", "잠들"],
    "2": ["우울", "무기력", "의욕없", "짜증"],
    "3": ["자해", "죽고싶", "절망"]
}

# We'll implement a safer, simpler scoring using presence of symptom keywords mapped to points 0-3
keyword_score_map = {
    "우울":2, "무기력":2, "의욕":2, "불면":1, "불안":1, "식욕":1, "자해":3, "죽고":3, "절망":3
}


def estimate_phq_from_text(text: str) -> int:
    if not isinstance(text, str) or text.strip() == "":
        return 0
    score = 0
    txt = text.replace(" ", "")
    for kw, pts in keyword_score_map.items():
        if kw in txt:
            score += pts
    # clamp score to 0-27 (PHQ-9 range). We'll normalize to 0-27 by capping.
    return max(0, min(27, score))

# Produce a short text summary (very simple) from diary texts
POS_WORDS = ["괜찮", "좋", "행복", "안정", "회복", "웃"]
NEG_WORDS = ["우울","무기력","불면","불안","죽고","절망","짜증"]

def summarize_texts(texts: dict) -> str:
    # texts: {date: text}
    combined = " ".join(texts.values())
    pos = sum(1 for w in POS_WORDS if w in combined)
    neg = sum(1 for w in NEG_WORDS if w in combined)
    if neg == 0 and pos == 0:
        return "특이사항 없음."
    if neg > pos:
        return "최근 감정은 부정적 경향이 있습니다. 추가 모니터링 및 면담을 권장합니다."
    if pos >= neg:
        return "최근 감정이 비교적 안정적입니다. 계속 경과 관찰하세요."

# --- New UI: Patient basic info + model recommendation panel ---
left, spacer, right = st.columns([5,1,4])

with left:
    st.markdown("")
    st.subheader("환자 기본 정보")
    info_cols = st.columns([1,1])
    with info_cols[0]:
        st.markdown(f"**이름**: {st.session_state.get('name', '')}")
        st.markdown(f"**나이**: {st.session_state.get('age', '')}")
        st.markdown(f"**성별**: {st.session_state.get('sex', '')}")
        st.markdown(f"**키(cm)**: {st.session_state.get('height_cm', '')}")
    with info_cols[1]:
        st.markdown(f"**몸무게(kg)**: {st.session_state.get('weight_kg', '')}")
        st.markdown(f"**eGFR**: {st.session_state.get('eGFR', '')}")
        prev = st.session_state.get('prev_prescription', {})
        st.markdown(f"**이전 처방**: {prev.get('dose_mg','-')} mg, {prev.get('freq_per_day','-')} /day (처방일: {prev.get('date','-')})")

    st.markdown("---")
    st.subheader("모델 추천 (PK/PD 기반)")
    model_reco = st.session_state.get('model_reco', {})
    st.markdown(f"**권장 용량**: {model_reco.get('dose_mg','-')} mg / {model_reco.get('freq_per_day','-')} per day")
    st.markdown(f"**권장 이유 (요약)**: {model_reco.get('reason','-')}")

    # Compare previous vs recommended
    if prev and model_reco:
        prev_d = prev.get('dose_mg', None)
        reco_d = model_reco.get('dose_mg', None)
        if prev_d is not None and reco_d is not None:
            if reco_d > prev_d:
                st.success(f"용량: 증가 → {prev_d} mg → {reco_d} mg")
            elif reco_d < prev_d:
                st.info(f"용량: 감소 → {prev_d} mg → {reco_d} mg")
            else:
                st.write(f"용량: 유지 ({prev_d} mg)")

    st.markdown("---")

# --- Adherence summary ---

def adherence_percent_over_days(day_num_dose: dict, days: int) -> float:
    if not day_num_dose:
        return 0.0
    today = date.today()
    values = []
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        v = day_num_dose.get(d)
        if v is None:
            continue
        values.append(min(1.0, float(v)))
    if not values:
        return 0.0
    return float(sum(values) / len(values) * 100)

with left:
    st.subheader("순응도 (Adherence)")
    day_map = st.session_state.get('day_num_dose', {})
    adh_7 = adherence_percent_over_days(day_map, 7)
    adh_14 = adherence_percent_over_days(day_map, 14)
    st.metric("최근 7일 평균 복용률", f"{adh_7:.0f}%")
    st.metric("최근 14일 평균 복용률", f"{adh_14:.0f}%")
    if adh_7 < 70:
        st.warning("최근 7일 복용률이 낮습니다. 용량 조정 전 복약지도(상담)를 권장합니다.")

    st.markdown("---")

# --- Side effects summary ---
with right:
    st.markdown("")
    st.subheader("최근 부작용 (최근 7일 기준)")
    sfx = st.session_state.get('side_effects', [])
    recent_cutoff = (date.today() - timedelta(days=7)).isoformat()
    recent = [s for s in sfx if s.get('date','') >= recent_cutoff]
    if recent:
        # group by symptom, pick max severity
        df_sfx = pd.DataFrame(recent)
        sfx_agg = df_sfx.groupby('symptom').severity.max().reset_index().sort_values('severity', ascending=False)
        st.table(sfx_agg.rename(columns={'symptom':'부작용','severity':'심각도(1-3)'}))
        total_score = int(df_sfx.severity.sum())
        st.markdown(f"**총 부작용 점수(최근 7일)**: {total_score}")
        # heatmap-like chart: symptom vs severity
        chart = alt.Chart(df_sfx).mark_rect().encode(
            x=alt.X('symptom:N', title='증상'),
            y=alt.Y('date:N', title='날짜'),
            color=alt.Color('severity:Q', title='심각도')
        ).properties(width='container', height=200)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("최근 7일간 보고된 주요 부작용이 없습니다.")

    st.markdown("---")

# --- Patient status summary (text analysis) ---
with right:
    st.subheader("환자 상태 요약 (자동요약)")
    diary_texts = st.session_state.get('diary_texts', {})
    status_summary = summarize_texts(diary_texts)
    st.write(status_summary)

# --- PHQ-9 estimate and trend ---
# Build PHQ dataframe from stored diary_texts and any explicit phq scores in session
phq_rows = []
# explicit numeric scores if provided
explicit = st.session_state.get('phq_records', {})
for d, txt in diary_texts.items():
    est = estimate_phq_from_text(txt)
    explicit_score = explicit.get(d)
    phq_rows.append({"date":d, "phq_est": est, "text": txt, "phq_explicit": explicit_score})

phq_df = pd.DataFrame(phq_rows)
if not phq_df.empty:
    phq_df['date'] = pd.to_datetime(phq_df['date'])
    phq_df = phq_df.sort_values('date')
    # show latest estimate
    latest = phq_df.tail(1).iloc[0]
    st.subheader("PHQ-9 (텍스트 기반 추정)")
    st.markdown(f"**최근 추정 PHQ-9 점수**: {int(latest['phq_est'])}")
    # trend chart (last 21 days)
    window_start = date.today() - timedelta(days=21)
    phq_plot = phq_df[phq_df['date'] >= pd.to_datetime(window_start)]
    if not phq_plot.empty:
        chart = alt.Chart(phq_plot).mark_line(point=True).encode(
            x=alt.X('date:T', title='날짜'),
            y=alt.Y('phq_est:Q', title='추정 PHQ-9 점수')
        ).properties(width='container', height=200)
        st.altair_chart(chart, use_container_width=True)

# --- Place the calendar & message & small mood chart into left column (kept similar to original) ---

# (The rest of the left column reuses original calendar rendering code and the small "오늘의 메세지" + 마음 기록 chart.)
# For brevity and to avoid accidental duplication, keep the existing left-column calendar code here unchanged.

st.markdown("\n---\n")
# Export summary CSV
summary = {
    'patient_id': st.session_state.get('patient_id','demo'),
    'name': st.session_state.get('name',''),
    'age': st.session_state.get('age',''),
    'eGFR': st.session_state.get('eGFR',''),
    'adh_7_pct': adh_7,
    'adh_14_pct': adh_14,
    'latest_phq_est': int(latest['phq_est']) if not phq_df.empty else None,
    'side_effects_score_7d': int(sum([s['severity'] for s in recent])) if recent else 0
}
summary_df = pd.DataFrame([summary])

csv = summary_df.to_csv(index=False).encode('utf-8')
st.download_button("환자 요약 CSV 다운로드", data=csv, file_name=f"summary_{st.session_state.get('patient_id','demo')}.csv", mime='text/csv')







st.markdown("---")
spacer, logout_button = st.columns([7,2])
with logout_button:
    if st.button("로그아웃", use_container_width=True):
        st.session_state.clear()
        st.switch_page("Patient_search.py")

# Note: This file intentionally focuses on adding panels & computations for the requested items.
# - The PHQ estimator is rule-based and intentionally simple; replace with a validated model before using clinically.
# - Side-effect aggregation uses severity values stored in session_state['side_effects'].
# - Model recommendation is read from st.session_state['model_reco']; in production it should be computed by a secure PK/PD service.
# - The calendar and many UI niceties from the original file should be merged into the left column section; to keep this example focused on new features, the left column calendar code from your original file can be pasted above where indicated.
