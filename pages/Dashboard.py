import streamlit as st
import calendar
from datetime import date, datetime, time
import random
import pandas as pd
import sqlite3
from pathlib import Path 
import base64
import logging
import altair as alt
# Altair = 파이썬 데이터 시각화 라이브러리
# -> 데이터 프레임을 간단하게 그래프로 보여줄 때 유용(데이터프레임 -> 차트 변환에 유용).

demo_mode = True

st.set_page_config(page_title="Home", page_icon="💊", layout="wide")

if not st.session_state.get("is_logged_in", False):
    st.error("잘못된 접근입니다.")
    st.stop()

if demo_mode:
    patient_id = st.session_state["patient_id"]
    st.session_state.setdefault("name", "김행근")
    name = st.session_state["name"]

header_col1, header_col2 = st.columns([4,1])
with header_col1:
    st.markdown( f""" 
                <div style="padding: 1.2rem 1.5rem; border-radius: 12px; 
                background-color: #f5f7fa; border: 1px solid #e5e7eb; 
                width: fit-content; color:#111;"> 
                <span style="font-size: 2rem; font-weight: 800; 
                letter-spacing: 0.5px;"> 
                {name} 님 </span> </div> """, 
                unsafe_allow_html=True )

def is_diary_time(now: datetime) -> bool:
    now_time = now.time()
    return now_time >= time(18, 0) or now_time <= time(2,0)
    # now.time() = datetime 객체에서 시간만 뽑아내는 메서드.
    # -> datetime(2025, 08, 26, 20, 30)에서 now.time()은 20:30
now = datetime.now()

left, right = st.columns([2,1])
st.markdown(" ")
st.markdown(" ")
with right:
    right_col1, right_col2 = st.columns([1,1])
    with right_col2:
        button_1, button_2 = st.columns([1,1])
        with button_1:
            if st.button("프로필 등록", use_container_width=True):
                st.switch_page("pages/Patient_intake1.py")

        with button_2:
            if st.button("하루점검", use_container_width=True):
                if demo_mode:
                    st.switch_page("pages/Patient_diary.py")
                else:
                    if "진료 등록하지 않았을 경우":
                        st.warning("먼저 진료 등록을 해주세요!")
                    elif is_diary_time(now):
                        st.switch_page("pages/Patient_diary.py")
                    else:
                        st.success("하루 점검은 오후 6시부터 가능합니다.")

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

def with_tooltip(title: str, tip: str) -> str:
                return f"""
                <div style="display:inline-flex; align-items:center; font-size:1.4rem; font-weight:600;">
                    {title}
                    <span style="
                        display:inline-block; 
                        margin-left:8px; 
                        width:22px; 
                        height:22px; 
                        border-radius:50%; 
                        background:#e5e7eb; 
                        color:#374151; 
                        font-size:1rem; 
                        font-weight:bold;
                        text-align:center; 
                        line-height:22px; 
                        cursor:default;" 
                        title="{tip}">?
                    </span>
                </div>
                """

today_str = date.today().isoformat()

st.session_state.setdefault("day_num_dose", {})

if demo_mode:
    st.session_state["day_num_dose"] = {
    "2025-09-01": 1.0,
    "2025-09-02": 1/3,
    "2025-09-03": 2/3,
    "2025-09-04": 0.0,
    "2025-09-05": 1.0
}

st.session_state.setdefault("daily_msg",{})
if today_str not in st.session_state["daily_msg"]:
    rnd = random.Random(f"{name}-{today_str}")
    st.session_state["daily_msg"][today_str] = rnd.choice(MESSAGES)
    # st.session_state[key][subkey] 
    # -> st.session_state 안에 있는 딕셔너리 key를 먼저 찾고, 
    # -> 그 안에서 또 다른 key(subkey)를 찾아서 값(value)에 접근.
    # daily_msg에 ""가 붙는 이유: 문자열 그 자체를 key로 쓰기 때문. 딕셔너리 이름이 daily_msg
    # today_str에 ""가 안붙는 이유: 변수에 저장된 값을 key로 쓰기 때문. 매일 바뀌는 날짜가 변수에 저장되고 그걸 key로 쓰나까.

msg = st.session_state["daily_msg"][today_str]

def image_to_base64(img_path:str) -> str:
    try:
    # try: 오류가 날 수도 있는 코드 except: 오류가 나면 실행되는 코드
        with open(img_path, "rb") as f:
        # open() = 파일을 여는 함수
        # rb = r(읽기) + b(바이너리) = 바이너리(이진 데이터)로 읽겠다.
        # -> 여기서는 이미지 파일을 이진 데이터로 읽겠다는 뜻. 
        # r(읽기), w(쓰기), a(이어쓰기), b(바이너리) -> 모드를 뜻하는 인자들.
        # with: = 파일을 열고, 끝나면 자동으로 닫아주는 안전한 문법.
        # as ... = ...으로 부르겠다(별명 지정).
            b64 = base64.b64encode(f.read()).decode("utf-8")
            # read() = 파일 내용을 전부 읽어서 반환해줌.
            # -> read니까 문자열을 반환함. 
            # encode() = 문자열(str)을 이진 데이터(bytes)로 바꿔줌.
            # decode() - bytes를 문자열로 바꿔줌.
            # base64는 데이터를 문자로 안전하게 표현하는 방법.
            # utf-g = 문자 <-> 바이트 변환을 할 때 쓰는 규칙 중 하나. 
            # HTML에는 이미지(이진 데이터)를 직접 넣을 수 없음. -> 텍스트로 바꿔주어야 함.
        return f"data:image/png;base64,{b64}"
        # data:[MIME 타입];base64,[데이터]
        # MIME = 데이텉가 어떤 종류인지 알려주는 태그 역할.
    except Exception as e:
    # Exception = 파이썬에서 발생할 수 있는 모든 에외(Error)의 부모 class.
        logging.warning(f"이미지 로드 실패: {img_path} - {e}")
        # logging: 프로그램이 실행되는 동안 생기는 기록인 로그(log)를 기록하고 관리하는 것. 
        # -> 주로 콘솔(터미널)에 기록됨, 디버깅(오류) 확인용으로 많이 사용. 
        return ""

def image_to_base64(img_path:str) -> str:
    try:
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        logging.warning(f"이미지 로드 실패: {img_path} - {e}")
        return ""

IMG_ELIF_10 = image_to_base64("images/elif_1.0.png")
IMG_ELIF_066  = image_to_base64("images/elif_0.6.png")
IMG_ELSE = image_to_base64("images/else.png")

def get_adherence_imoji(r):
    if r is None:
        return ""
    if r >= 1.0:
        src = IMG_ELIF_10
    elif r >= (2/3):
        src = IMG_ELIF_066
    else:
        src = IMG_ELSE
    if not src:
        return ""
    return f"<img src='{src}' class='mark-img' alt='adherence'/>"
    # class 속성: HTML에서 요소를 특정 그룹으로 묶어주는 속성.
    # alt 속성: <img>에서만 쓰이는 속성, 대체 텍스트라는 뜻.
    # -> 이미지가 깨져서 안 보일 때 대신 보여줄 텍스트.

    # if 다음 코드가 한 줄일 땐 문단을 띄우지 않아도 괜찮음.
    # elif = 그렇지 않으면(if와 else 사이에 낑겨있음.)
    # if-elif-else 구조: 조건이 맞으면 아래는 전혀 안 봄, 하나만 실행, 중복 실행 걱정 X.
    # if-if-if 구조: 각 조건이 독립적으로 모두 검사됨.
    # return은 함수가 즉시 종료되는 명령으로, 실행되면 함수 바깥으로 값을 돌려주고 함수 실행이 끝남. 
    # -> 그래서 if-if-if 구조를 사용해도 문제가 없었던 것.
    # 그치만 난 안전빵으로 elif를 쓰겠다.
    # <img.../> or <img> = 이미지를 화면에 보여주기 위한 태그 문법.
    # src = source의 줄임말, 이미지 파일이 어디 있는지 알려주는 경로.

with left:
    calendar_left, spacer_left = st.columns([9,1])
    with calendar_left:
        st.markdown(" ")
        st.markdown(" ")
        st.markdown(with_tooltip("칭찬 기록", 
                                 "약을 얼마나 잘 복용하고 있는지, 한 달 간의 복용 기록을 확인할 수 있어요. \n처방받은 약을 전부 복용했을 경우 : 너무 훌륭해! 스티커 \n처방받은 약을 2/3 이상 복용했을 경우 : 넌 할 수 있어! 스티커 \n처방받은 약을 2/3 미만으로 복용했을 경우 : 좀 더 열심히~ 스티커"), 
                                 unsafe_allow_html=True)

        today = date.today()
        st.markdown(f"### {today.year}년 {today.month}월")
        monthly_calendar = calendar.Calendar(firstweekday=0)
        # calendar.Calendar = calendar 모듈에서 달력 객체(Calendar)를 만들겠다는 뜻.
        # firstweekday=0 = 월요일부터 시작하는 달력을 만들겠다는 뜻(0=Monday).
        weeks = monthly_calendar.monthdayscalendar(today.year, today.month)
        # today.year, today.month는 몇 년도 몇 월의 달력을 만들지 지정해주기 위함.
        # today.day는 여기선 없어도 됨.(내가 헷갈렸던 부분)

        st.markdown("""
                <style>
                .cal-wrap{
                    max-width: 860px;
                    width: 100%;
                }
                table.calendar{
                    border-collapse: collapse;
                    width: 100%;
                    table-layout: fixed;
                }
                table.calendar th, table.calendar td{
                    border: 1px solid #ddd;
                    width: 14.2857%;
                    height: 110px;
                    position: relative;
                    background: #fafafa;
                    padding: 0;
                    vertical-align: middle;
                }
                table.calendar th{
                    background:#f7f7f9;
                    color:#111;
                    font-weight:700;
                    height: 42px;
                }
                table.calendar td .day-num{
                    position: absolute;
                    top: 6px;
                    left: 8px;
                    font-size: 0.85rem;
                    font-weight: 700;
                    color: #374151;
                    z-index: 2;
                }
                table.calendar td .mark-wrap{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                }
                img.mark-img{
                    width: 72px;
                    height: 72px;
                    object-fit: contain;
                    display: block;
                    margin: 0 auto;
                }
                td.empty{ background:#fdfdfd; }
                </style>
                """, unsafe_allow_html=True)
                # img.mark-img -> 여기에 'mark-img'라는 딕셔너리 만들어놓음.

        header_html = "<tr>" + "".join(f"<th>{d}</th>" for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]) + "</tr>"

        rows_html = ""
        for week in weeks:
            row_tds = ""
            for daynum in week:
                if daynum == 0:
                    row_tds += "<td class='empty'></td>"
                else:
                    cell_date = date(today.year, today.month, daynum)
                    key = cell_date.isoformat()
                    r = st.session_state["day_num_dose"].get(key)
                    mark_html = get_adherence_imoji(r)
                    row_tds += f"<td><div class='day-num'>{daynum}</div><div class='mark-wrap'>{mark_html}</div></td>"
            rows_html += f"<tr>{row_tds}</tr>"

        table_html = f"<table class='calendar'>{header_html}{rows_html}</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        with right:
            st.markdown(with_tooltip("오늘의 메세지",
                                      "매일 랜덤 메세지를 띄워줍니다. \n하루동안 유지되어 당신의 하루를 응원해요."), 
                                      unsafe_allow_html=True)
            st.write(f"> {msg}")
            # 중간에 들어간 > = Markdown 문법, 인용구를 만들 때 주로 사용.
            # -> 깔끔한 박스 스타일로 한 줄 메세지를 보여줄 수 있음.

            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(with_tooltip("마음 기록", "하루점검에서 작성한 하루 기록 텍스트를 phq9 기반 감정 점수로 변환하여 그래프로 나타내줘요. \n우울감의 정도와 감정 변화를 확인할 수 있어요."), unsafe_allow_html=True)
            dummy_phq = pd.DataFrame({
                "today_str": ["2025-09-01", "2025-09-02", "2025-09-03", "2025-09-04", "2025-09-05"],
                "phq_score": [18, 20, 24, 25, 19]
            })

            chart = (
                alt.Chart(dummy_phq.tail(7))
                .mark_bar()
                # mark_bar() = 차트를 막대그래프로 그려라. 
                .encode(
                    x=alt.X("today_str:N", title="날짜", axis=alt.Axis(labelAngle=0)), 
                    y=alt.Y("phq_score:Q", title="점수")
                    )
                    .properties(width="container", height=360)
                    )
                    # today_str:N에서 콜론(:) 앞은 열 이름, 뒤는 타입 약어.
                    # N = Nominal(범주), O = Ordinal(순서), Q = Quantitative(수치), T = Temporal(시간)
                    # axis=alt.Axis(labelAngle=0) -> 축 스타일 객체에서 라벨 각도 0도 -> 라벨 가로로.
                    # .encode() = 데이터를 축/색/크기 등에 매핑. 
                    # .properties() = 차트의 외형을 정함.
                    # -> 데이터와 무관한 그림(차트) 자체의 크기, 제목, 위치 등.
            st.altair_chart(chart, use_container_width=True)


            if not demo_mode: # 여기 코드 모르겠음. 보류. 
                query = "i dont know"
                conn = "i dont know"
                df = pd.read_sql_query(query, conn)

                if not df.empty: # 물론 여기도 모르겠음. 보류. 
                    df = df.tail(7)
                    # .tail(숫자) = 마지막 (숫자)만큼의 줄만 잘라서 가져오는 함수.
                    # .tail(7)이면 마지막 7줄만 잘라서 가져옴.
                    df = df.set_index("today_str")
                    # set.idex() = 기존 열(column) 중 하나를 행(row)을 구분하는 꼬리표(index)로 바꾸는 것.
                    # 기본 index는 숫자임(0,1,2...) -> 이건 자동으로 붙음.
                    # 근데 set.index()의 인자로 열이었던 데이터를 집어넣으면
                    # -> 원래 열이었던 데이터가 숫자로 구분되던 index 자리로 가서 행을 구분하는 index가 되는 것.
                    st.bar_chart(df)
                    # st.bar_chart() = 막대 그래프(bar chart)를 그리는 함수.
                    # df는 반드시 인덱스가 x축, 열이 y축인 표 형태야야 제대로 작동함. 
                else:
                    st.info("아직 감정 기록이 없어요..ㅠㅠ 하루점검에서 기록해 보세요!")


            st.markdown("---")
            spacer, logout_button = st.columns([7,2])
            with logout_button:
                if st.button("로그아웃", use_container_width=True):
                    st.session_state.clear()
                    st.switch_page("Login.py")