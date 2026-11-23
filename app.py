import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
from collections import Counter
from datetime import datetime, timezone, timedelta
import pandas as pd
import io
import random

# 💡 한국 표준시(KST, UTC+9) 설정
KST = timezone(timedelta(hours=9))

def get_kst_now():
    return datetime.now(KST)

# 💡 깃허브 유출 방지: Secrets에서 키를 가져오며 앞뒤 공백/줄바꿈 자동 제거
API_KEY = st.secrets["OPENAI_API_KEY"].strip()
client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="맞춤형 기초학력 지원 앱", layout="wide")

# ==========================================
# 1. 한 글자 읽기 데이터 (초·중·종성 및 출제 목록)
# ==========================================
CHOSUNG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
JUNGSUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
JONGSUNG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

# 1단계용: 쌍자음 제외 기본 자음 14개 + 이중모음 제외 기본 단모음 6개
BASIC_CHO = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
BASIC_JUNG = ['ㅏ', 'ㅓ', 'ㅗ', 'ㅜ', 'ㅡ', 'ㅣ']

# 2단계용: 실제 존재하며 글자 그대로 소리 나는(받침 ㄱ, ㄴ, ㄹ, ㅁ, ㅂ, ㅇ) 단음절 목록
STAGE2_WORDS = [
    "강", "공", "국", "글", "김", "길", "꿈", "눈", "달", "돌",
    "동", "말", "물", "문", "발", "밤", "밥", "방", "별", "봄",
    "북", "불", "산", "상", "섬", "손", "송", "술", "실", "집",
    "책", "창", "춤", "콩", "탑", "팔", "풀", "학", "힘", "곰",
    "굴", "금", "돈", "등", "땀", "땅", "떡", "목", "몸", "벽",
    "병", "빵", "성", "약", "양", "왕", "용", "원", "월", "입",
    "종", "줄"
]

def generate_word(stage, exclude_word=None):
    """단계에 맞는 랜덤 글자를 생성하되 직전 글자와 겹치지 않게 반환"""
    while True:
        if stage == 1:
            cho = random.choice(BASIC_CHO)
            jung = random.choice(BASIC_JUNG)
            cho_idx = CHOSUNG.index(cho)
            jung_idx = JUNGSUNG.index(jung)
            word = chr(0xAC00 + (cho_idx * 21 + jung_idx) * 28)
        else:
            word = random.choice(STAGE2_WORDS)
        
        if word != exclude_word:
            return word

# ==========================================
# 2. 띄어 읽기 연습 데이터 (초등 1~2학년 수준 2어절 / 3어절)
# ==========================================
SENTENCES_2_EOJEOL = [
    "나비가 날아간다.",
    "강아지가 달린다.",
    "꽃이 피었습니다.",
    "구름이 흘러간다.",
    "바람이 붑니다.",
    "아기가 웃습니다.",
    "새가 노래한다.",
    "비가 내립니다.",
    "사과가 맛있습니다.",
    "학교에 갑니다.",
    "책을 읽습니다.",
    "친구를 만났습니다.",
    "별이 반짝인다.",
    "나무가 자랍니다.",
    "고양이가 잠잔다."
]

SENTENCES_3_EOJEOL = [
    "아버지가 방에 들어가신다.",
    "아기가 방에서 놀아요.",
    "동생이 우유를 마신다.",
    "고양이가 생선을 먹는다.",
    "선생님이 책을 읽으신다.",
    "친구가 공을 던진다.",
    "엄마가 사과를 깎으신다.",
    "다람쥐가 도토리를 줍는다.",
    "개구리가 연못에 빠졌다.",
    "하늘에 무지개가 떴다.",
    "아이들이 운동장에서 논다.",
    "참새가 나무에 앉았다.",
    "할머니가 꽃을 가꾸신다.",
    "우리가 교실을 청소한다.",
    "형아가 연을 날린다."
]

def generate_sentence(stage, exclude_sentence=None):
    """2어절 또는 3어절 랜덤 문장을 생성하되 직전 문장과 겹치지 않게 반환"""
    pool = SENTENCES_2_EOJEOL if stage == 1 else SENTENCES_3_EOJEOL
    while True:
        sentence = random.choice(pool)
        if sentence != exclude_sentence:
            return sentence

def format_slash_hint(sentence):
    """문장의 어절 사이에 빗금(/)을 자동으로 삽입하여 반환"""
    end_punct = sentence[-1] if sentence[-1] in [".", "!", "?"] else ""
    body = sentence[:-1] if end_punct else sentence
    return " / ".join(body.split()) + end_punct

# ==========================================
# 3. 수학 학습 데이터 (크기 비교 및 문장제)
# ==========================================
def generate_compare_numbers(stage, exclude_pair=None):
    """단계별 두 숫자 생성 (1: 한 자릿수끼리, 2: 한/두 자릿수 혼합, 3: 두 자릿수끼리)"""
    while True:
        if stage == 1:
            a = random.randint(1, 9)
            b = a if random.random() < 0.15 else random.randint(1, 9)
        elif stage == 2:
            one_digit = random.randint(1, 9)
            two_digit = random.randint(10, 99)
            if random.choice([True, False]):
                a, b = one_digit, two_digit
            else:
                a, b = two_digit, one_digit
        else:
            if random.random() < 0.5:
                tens = random.randint(1, 9)
                a = tens * 10 + random.randint(0, 9)
                b = tens * 10 + random.randint(0, 9)
            else:
                a = random.randint(10, 99)
                b = random.randint(10, 99)
        
        if (a, b) != exclude_pair:
            return (a, b)

WORD_PROBLEMS = [
    {"text": "사과가 3개, 배가 2개 있습니다. 모두 몇 개일까요?", "n1": 3, "op": "+", "n2": 2, "ans": 5, "e1": "🍎", "e2": "🍐"},
    {"text": "딸기가 4개, 바나나가 5개 있습니다. 과일은 모두 몇 개일까요?", "n1": 4, "op": "+", "n2": 5, "ans": 9, "e1": "🍓", "e2": "🍌"},
    {"text": "강아지 2마리와 고양이 4마리가 놀고 있습니다. 동물은 모두 몇 마리일까요?", "n1": 2, "op": "+", "n2": 4, "ans": 6, "e1": "🐶", "e2": "🐱"},
    {"text": "빨간 풍선 5개와 파란 풍선 3개가 있습니다. 풍선은 모두 몇 개일까요?", "n1": 5, "op": "+", "n2": 3, "ans": 8, "e1": "🎈", "e2": "🔵"},
    {"text": "연필이 6자루, 공책이 2권 있습니다. 학용품은 모두 몇 개일까요?", "n1": 6, "op": "+", "n2": 2, "ans": 8, "e1": "✏️", "e2": "📒"},
    {"text": "병아리 4마리가 있었는데 3마리가 더 왔습니다. 병아리는 모두 몇 마리일까요?", "n1": 4, "op": "+", "n2": 3, "ans": 7, "e1": "🐤", "e2": "🐤"},
    {"text": "축구공이 3개, 농구공이 3개 있습니다. 공은 모두 몇 개일까요?", "n1": 3, "op": "+", "n2": 3, "ans": 6, "e1": "⚽", "e2": "🏀"},
    {"text": "사탕이 6개 있었습니다. 그중에서 2개를 먹었습니다. 남은 사탕은 몇 개일까요?", "n1": 6, "op": "-", "n2": 2, "ans": 4, "e1": "🍬", "e2": "🍬"},
    {"text": "주차장에 자동차가 7대 있었습니다. 3대가 떠났다면 남은 자동차는 몇 대일까요?", "n1": 7, "op": "-", "n2": 3, "ans": 4, "e1": "🚗", "e2": "🚗"},
    {"text": "쿠키가 8개 있었습니다. 동생에게 5개를 주었습니다. 남은 쿠키는 몇 개일까요?", "n1": 8, "op": "-", "n2": 5, "ans": 3, "e1": "🍪", "e2": "🍪"},
    {"text": "꽃밭에 나비가 5마리 앉아 있었습니다. 2마리가 날아갔습니다. 남은 나비는 몇 마리일까요?", "n1": 5, "op": "-", "n2": 2, "ans": 3, "e1": "🦋", "e2": "🦋"},
    {"text": "토끼가 당근 9개를 가지고 있었습니다. 4개를 먹었다면 남은 당근은 몇 개일까요?", "n1": 9, "op": "-", "n2": 4, "ans": 5, "e1": "🥕", "e2": "🥕"},
    {"text": "초콜릿이 7개, 사탕이 4개 있습니다. 초콜릿이 사탕보다 몇 개 더 많을까요?", "n1": 7, "op": "-", "n2": 4, "ans": 3, "e1": "🍫", "e2": "🍬"},
    {"text": "귤이 8개, 복숭아가 3개 있습니다. 귤이 복숭아보다 몇 개 더 많을까요?", "n1": 8, "op": "-", "n2": 3, "ans": 5, "e1": "🍊", "e2": "🍑"}
]

def generate_word_problem(exclude_text=None):
    """직전 문제와 겹치지 않게 문장제 문제를 랜덤 반환"""
    while True:
        prob = random.choice(WORD_PROBLEMS)
        if prob["text"] != exclude_text:
            return prob

# ==========================================
# 4. 실제 학습 이력 기록(Logging) 함수 (한국 시간 KST 적용)
# ==========================================
def log_attempt(subject, activity, question, student_answer, is_correct, error_type, hint_used=False):
    """학생용 탭에서 실제로 풀이한 결과만 한국 시간(KST)과 함께 저장"""
    s_info = st.session_state.student_info or {"grade": "미입력", "class": "미입력", "number": 0, "name": "미입력"}
    student_label = f"{s_info['grade']} {s_info['class']} {s_info['number']}번 {s_info['name']}"
    
    st.session_state.learning_logs.insert(0, {
        "시간(KST)": get_kst_now().strftime("%Y-%m-%d %H:%M:%S"),
        "학년": s_info["grade"],
        "반": s_info["class"],
        "번호": s_info["number"],
        "이름": s_info["name"],
        "학생 식별": student_label,
        "영역": subject,
        "활동": activity,
        "문제": question,
        "학생 응답": student_answer,
        "결과": "정답" if is_correct else "오답",
        "오류 유형": "없음" if is_correct else error_type,
        "힌트 사용": "사용" if hint_used else "미사용"
    })

# ==========================================
# 세션 상태(Session State) 초기화
# ==========================================
if "student_info" not in st.session_state:
    st.session_state.student_info = None

if "learning_logs" not in st.session_state:
    st.session_state.learning_logs = []

# [국어 1] 비슷한 글자 찾기 상태
if "k1_stage" not in st.session_state:
    st.session_state.k1_stage = 1
if "k1_streak" not in st.session_state:
    st.session_state.k1_streak = 0
if "k1_target" not in st.session_state:
    st.session_state.k1_target = generate_word(1)
if "k1_solved" not in st.session_state:
    st.session_state.k1_solved = False
if "k1_q_count" not in st.session_state:
    st.session_state.k1_q_count = 0
if "k1_last_spoken" not in st.session_state:
    st.session_state.k1_last_spoken = ""
if "k1_leveled_up" not in st.session_state:
    st.session_state.k1_leveled_up = False

# [국어 2] 띄어 읽기 연습 상태
if "k2_stage" not in st.session_state:
    st.session_state.k2_stage = 1
if "k2_target" not in st.session_state:
    st.session_state.k2_target = generate_sentence(1)
if "k2_solved" not in st.session_state:
    st.session_state.k2_solved = False
if "k2_q_count" not in st.session_state:
    st.session_state.k2_q_count = 0
if "k2_last_spoken" not in st.session_state:
    st.session_state.k2_last_spoken = ""
if "show_slash_hint" not in st.session_state:
    st.session_state.show_slash_hint = False

# [수학 1] 크기 비교 상태
if "m1_stage" not in st.session_state:
    st.session_state.m1_stage = 1
if "m1_pair" not in st.session_state:
    st.session_state.m1_pair = generate_compare_numbers(1)
if "m1_solved" not in st.session_state:
    st.session_state.m1_solved = False
if "m1_q_count" not in st.session_state:
    st.session_state.m1_q_count = 0

# [수학 2] 문장제 상태
if "m2_prob" not in st.session_state:
    st.session_state.m2_prob = WORD_PROBLEMS[0]
if "m2_show_hint" not in st.session_state:
    st.session_state.m2_show_hint = False
if "m2_solved" not in st.session_state:
    st.session_state.m2_solved = False
if "m2_q_count" not in st.session_state:
    st.session_state.m2_q_count = 0

def reset_student_progress():
    """새로운 학생으로 전환할 때 현재 풀이 화면 상태 초기화"""
    st.session_state.k1_stage = 1
    st.session_state.k1_streak = 0
    st.session_state.k1_target = generate_word(1)
    st.session_state.k1_solved = False
    st.session_state.k1_last_spoken = ""
    st.session_state.k1_leveled_up = False
    st.session_state.k1_q_count += 1
    
    st.session_state.k2_stage = 1
    st.session_state.k2_target = generate_sentence(1)
    st.session_state.k2_solved = False
    st.session_state.k2_last_spoken = ""
    st.session_state.show_slash_hint = False
    st.session_state.k2_q_count += 1
    
    st.session_state.m1_stage = 1
    st.session_state.m1_pair = generate_compare_numbers(1)
    st.session_state.m1_solved = False
    st.session_state.m1_q_count += 1
    
    st.session_state.m2_prob = WORD_PROBLEMS[0]
    st.session_state.m2_show_hint = False
    st.session_state.m2_solved = False
    st.session_state.m2_q_count += 1

# --- 왼쪽 사이드바 (메뉴 선택) ---
st.sidebar.title("메뉴 선택")
mode = st.sidebar.radio("어디로 들어갈까요?", ["학생용", "교사용"])

# ==========================================
# 1. 학생용 화면
# ==========================================
if mode == "학생용":
    # ------------------------------------------
    # [STEP 0] 학생 정보(학년, 반, 번호, 이름) 미입력 시 입력창 먼저 표시
    # ------------------------------------------
    if st.session_state.student_info is None:
        st.title("🎒 즐거운 배움터 입장하기")
        st.write("공부를 시작하기 전에 **학년, 반, 번호, 이름**을 입력해 주세요! 선생님이 학습 기록을 확인할 수 있어요.")
        
        with st.form("student_login_form"):
            col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 2])
            with col1:
                grade_in = st.selectbox("학년", ["1학년", "2학년", "3학년", "4학년", "5학년", "6학년"])
            with col2:
                class_in = st.selectbox("반", [f"{i}반" for i in range(1, 11)])
            with col3:
                number_in = st.number_input("번호", min_value=1, max_value=40, value=1, step=1)
            with col4:
                name_in = st.text_input("이름", placeholder="예: 김민준")
            
            submitted = st.form_submit_button("🚀 학습 시작하기", type="primary", use_container_width=True)
            
            if submitted:
                if name_in.strip() == "":
                    st.warning("⚠️ 이름을 입력해 주세요!")
                else:
                    st.session_state.student_info = {
                        "grade": grade_in,
                        "class": class_in,
                        "number": int(number_in),
                        "name": name_in.strip()
                    }
                    reset_student_progress()
                    st.rerun()
    
    # ------------------------------------------
    # [STEP 1] 학생 정보 입력 완료 후 학습 화면
    # ------------------------------------------
    else:
        s_info = st.session_state.student_info
        
        # 상단 학생 프로필 및 학생 변경 버튼
        top_col1, top_col2 = st.columns([4, 1.2])
        with top_col1:
            st.title("🎒 즐거운 배움터")
            st.markdown(f"👋 **{s_info['grade']} {s_info['class']} {s_info['number']}번 {s_info['name']}** 학생, 오늘도 힘차게 공부해 보자!")
        with top_col2:
            st.write("")
            if st.button("🔄 학생 변경", use_container_width=True):
                st.session_state.student_info = None
                st.rerun()
        
        # 국어, 수학 2개의 탭 만들기
        tab_korean, tab_math = st.tabs(["📖 국어", "🧮 수학"])
        
        # ==========================================
        # --- 국어 학습 탭 ---
        # ==========================================
        with tab_korean:
            korean_choice = st.radio("어떤 연습을 할까요?", ["1. 비슷한 글자 찾기", "2. 띄어 읽기 연습"], horizontal=True)
            st.divider()
            
            # ------------------------------------------
            # [국어 1] 비슷한 글자 찾기
            # ------------------------------------------
            if korean_choice == "1. 비슷한 글자 찾기":
                st.subheader("1. 비슷한 글자 찾기 연습")
                
                stage_options = ["1단계: 받침 없는 글자", "2단계: 받침 있는 글자"]
                selected_stage_label = st.radio(
                    "연습할 글자 종류를 선택하세요:",
                    stage_options,
                    index=st.session_state.k1_stage - 1,
                    horizontal=True
                )
                selected_stage = 1 if selected_stage_label == stage_options[0] else 2
                
                if selected_stage != st.session_state.k1_stage:
                    st.session_state.k1_stage = selected_stage
                    st.session_state.k1_streak = 0
                    st.session_state.k1_solved = False
                    st.session_state.k1_last_spoken = ""
                    st.session_state.k1_leveled_up = False
                    st.session_state.k1_target = generate_word(selected_stage)
                    st.session_state.k1_q_count += 1
                    st.rerun()
                
                col_stat1, col_stat2 = st.columns([2, 1])
                with col_stat1:
                    if st.session_state.k1_stage == 1:
                        st.markdown("🌱 **현재 단계: 받침 없는 글자** — *3개 연속 맞히면 받침 있는 글자로 넘어가요!*")
                        st.progress(min(st.session_state.k1_streak / 3, 1.0))
                    else:
                        st.markdown("🌳 **현재 단계: 받침 있는 글자** — *받침 소리까지 정확히 읽어보자!*")
                        st.progress(1.0)
                with col_stat2:
                    st.metric(label="연속 정답 기록", value=f"{st.session_state.k1_streak}개 연속")
                
                st.write("화면의 글자를 보고 또박또박 읽어보자!")
                
                target_word = st.session_state.k1_target
                st.markdown(f"<h1 style='text-align: center; font-size: 110px; margin: 10px 0;'>{target_word}</h1>", unsafe_allow_html=True)
                
                if st.session_state.k1_solved:
                    if st.session_state.k1_last_spoken:
                        st.info(f"🎤 학생이 낸 소리: **{st.session_state.k1_last_spoken}**")
                    
                    if st.session_state.k1_leveled_up:
                        st.balloons()
                        st.success("🎊 대단해요! 3개 연속 정답을 달성해서 이제 **받침이 있는 글자**로 올라갑니다!")
                    else:
                        st.success("🎉 참 잘했어요! 정확하게 읽었네요!")
                    
                    if st.button("➡️ 다음 글자 연습하기", type="primary", use_container_width=True):
                        st.session_state.k1_target = generate_word(st.session_state.k1_stage, exclude_word=target_word)
                        st.session_state.k1_solved = False
                        st.session_state.k1_last_spoken = ""
                        st.session_state.k1_leveled_up = False
                        st.session_state.k1_q_count += 1
                        st.rerun()
                
                else:
                    st.info("👇 마이크를 누르고 **아이콘이 빨간색으로 변하면** 글자를 읽어보세요. (한 번만 읽어도 되고, 여러 번 반복해서 읽어도 좋아요!)")
                    
                    audio_bytes = audio_recorder(
                        text="클릭해서 녹음 시작", 
                        icon_size="2x", 
                        pause_threshold=10.0,
                        key=f"k_mic_1_{st.session_state.k1_q_count}"
                    )
                    
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/wav")
                        
                        with st.spinner("AI 선생님이 목소리를 듣고 있어요... 🤖"):
                            audio_file = io.BytesIO(audio_bytes)
                            audio_file.name = "record.wav"
                            
                            try:
                                if st.session_state.k1_stage == 1:
                                    stt_prompt = f"{target_word}. {target_word}, {target_word}, {target_word}. 가, 나, 다, 라, 마, 바, 보, 사, 아, 자. 받침 없는 한 글자 발음입니다."
                                else:
                                    stt_prompt = f"{target_word}. {target_word}, {target_word}, {target_word}. 강, 공, 달, 물, 별, 봄, 산, 손, 집, 책. 받침 있는 한 글자 발음입니다."
                                
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1", 
                                    file=audio_file,
                                    language="ko",
                                    prompt=stt_prompt
                                )
                                
                                spoken_text = transcript.text.strip()
                                st.info(f"🎤 학생이 낸 소리: **{spoken_text}**")
                                
                                hangul_chars = [ch for ch in spoken_text if '가' <= ch <= '힣']
                                
                                if len(hangul_chars) > 0:
                                    counts = Counter(hangul_chars)
                                    max_count = counts.most_common(1)[0][1]
                                    
                                    if counts[target_word] == max_count:
                                        log_attempt("국어", "비슷한 글자 찾기", target_word, spoken_text, True, "없음")
                                        st.session_state.k1_solved = True
                                        st.session_state.k1_last_spoken = spoken_text
                                        st.session_state.k1_streak += 1
                                        
                                        if st.session_state.k1_stage == 1 and st.session_state.k1_streak >= 3:
                                            st.session_state.k1_stage = 2
                                            st.session_state.k1_leveled_up = True
                                        
                                        st.rerun()
                                    else:
                                        if st.session_state.k1_stage == 1:
                                            st.session_state.k1_streak = 0
                                        
                                        spoken_char = counts.most_common(1)[0][0]
                                        
                                        target_code = ord(target_word) - 0xAC00
                                        target_cho = CHOSUNG[target_code // 588]
                                        target_jung = JUNGSUNG[(target_code % 588) // 28]
                                        target_jong = JONGSUNG[target_code % 28]
                                        
                                        spoken_code = ord(spoken_char) - 0xAC00
                                        spoken_cho = CHOSUNG[spoken_code // 588]
                                        spoken_jung = JUNGSUNG[(spoken_code % 588) // 28]
                                        spoken_jong = JONGSUNG[spoken_code % 28]
                                        
                                        cho_ok = (spoken_cho == target_cho)
                                        jung_ok = (spoken_jung == target_jung)
                                        jong_ok = (spoken_jong == target_jong)
                                        
                                        wrong_parts = []
                                        if not cho_ok:
                                            wrong_parts.append("자음(첫소리)")
                                        if not jung_ok:
                                            wrong_parts.append("모음(가운뎃소리)")
                                        if not jong_ok:
                                            wrong_parts.append("받침(끝소리)")
                                        
                                        wrong_desc = ", ".join(wrong_parts)
                                        log_attempt("국어", "비슷한 글자 찾기", target_word, spoken_char, False, f"{wrong_desc} 오류")
                                        st.error(f"💡 주로 '{spoken_char}'(으)로 읽었네요. 아쉽지만 **{wrong_desc}** 부분을 잘못 읽었어요.")
                                        
                                        cho_html = f"<span style='color: red;'>{target_cho}</span>" if not cho_ok else target_cho
                                        jung_html = f"<span style='color: blue;'>{target_jung}</span>" if not jung_ok else target_jung
                                        
                                        if target_jong != "":
                                            jong_html = f"<span style='color: #2E8B57;'>{target_jong}</span>" if not jong_ok else target_jong
                                            st.markdown(f"<h3 style='text-align: center;'>정답은 {cho_html} + {jung_html} + {jong_html} 예요. 다시 읽어볼까요?</h3>", unsafe_allow_html=True)
                                        else:
                                            if not jong_ok:
                                                st.markdown(f"<h3 style='text-align: center;'>정답은 받침이 없는 {cho_html} + {jung_html} 예요. 다시 읽어볼까요?</h3>", unsafe_allow_html=True)
                                            else:
                                                st.markdown(f"<h3 style='text-align: center;'>정답은 {cho_html} + {jung_html} 예요. 다시 읽어볼까요?</h3>", unsafe_allow_html=True)
                                else:
                                    st.error("💡 무슨 말인지 잘 못 들었어요. 다시 크고 또박또박 말해볼까요?")
                                        
                            except Exception as e:
                                if "audio_too_short" in str(e):
                                    st.warning("⚠️ 녹음된 소리가 너무 짧거나 마이크가 인식되지 않았어요. 마이크 연결과 권한을 확인해 주세요!")
                                else:
                                    st.error(f"❌ 시스템 오류가 발생했습니다: {e}")
                    
                    st.write("")
                    if st.button("🔄 다른 글자로 바꾸기", key="skip_word_btn"):
                        st.session_state.k1_target = generate_word(st.session_state.k1_stage, exclude_word=target_word)
                        st.session_state.k1_q_count += 1
                        st.rerun()

            # ------------------------------------------
            # [국어 2] 띄어 읽기 연습
            # ------------------------------------------
            elif korean_choice == "2. 띄어 읽기 연습":
                st.subheader("2. 알맞게 띄어 읽기 연습")
                
                eojeol_options = ["1단계: 2어절 문장 (예: 나비가 날아간다)", "2단계: 3어절 문장 (예: 아버지가 방에 들어가신다)"]
                selected_eojeol_label = st.radio(
                    "연습할 문장 길이를 선택하세요:",
                    eojeol_options,
                    index=st.session_state.k2_stage - 1,
                    horizontal=True
                )
                selected_eojeol_stage = 1 if selected_eojeol_label == eojeol_options[0] else 2
                
                if selected_eojeol_stage != st.session_state.k2_stage:
                    st.session_state.k2_stage = selected_eojeol_stage
                    st.session_state.k2_target = generate_sentence(selected_eojeol_stage)
                    st.session_state.k2_solved = False
                    st.session_state.k2_last_spoken = ""
                    st.session_state.show_slash_hint = False
                    st.session_state.k2_q_count += 1
                    st.rerun()
                
                st.write("문장의 뜻이 잘 통하게 의미 단위로 띄어 읽어보자!")
                
                target_sentence = st.session_state.k2_target
                text_placeholder = st.empty()
                hint_placeholder = st.empty()
                
                if st.session_state.k2_solved:
                    text_placeholder.markdown(f"<h2 style='text-align: center; margin: 20px 0;'>{target_sentence}</h2>", unsafe_allow_html=True)
                    if st.session_state.k2_last_spoken:
                        st.info(f"🎤 학생이 낸 소리: **{st.session_state.k2_last_spoken}**")
                    st.success("🎉 참 잘했어요! 알맞게 띄어 읽어서 뜻이 잘 통하네요!")
                    
                    if st.button("➡️ 다음 문장 연습하기", type="primary", use_container_width=True):
                        st.session_state.k2_target = generate_sentence(st.session_state.k2_stage, exclude_sentence=target_sentence)
                        st.session_state.k2_solved = False
                        st.session_state.k2_last_spoken = ""
                        st.session_state.show_slash_hint = False
                        st.session_state.k2_q_count += 1
                        st.rerun()
                
                else:
                    if st.session_state.show_slash_hint:
                        slashed_sentence = format_slash_hint(target_sentence)
                        text_placeholder.markdown(f"<h2 style='text-align: center; color: #FF4B4B; margin: 20px 0;'>{slashed_sentence}</h2>", unsafe_allow_html=True)
                        hint_placeholder.info("💡 선생님 힌트: 빗금(/)이 있는 곳에서 숨을 살짝 고르고 다시 읽어볼까요?")
                    else:
                        text_placeholder.markdown(f"<h2 style='text-align: center; margin: 20px 0;'>{target_sentence}</h2>", unsafe_allow_html=True)
                    
                    st.info("👇 마이크를 누르고 **아이콘이 빨간색으로 변하면** 읽어보세요. (다 읽은 뒤 한 번 더 클릭)")
                    
                    audio_bytes_2 = audio_recorder(
                        text="클릭해서 녹음 시작", 
                        icon_size="2x", 
                        pause_threshold=10.0,
                        key=f"k_mic_2_{st.session_state.k2_q_count}"
                    )
                    
                    if audio_bytes_2:
                        st.audio(audio_bytes_2, format="audio/wav")
                        
                        with st.spinner("AI 선생님이 목소리를 듣고 있어요... 🤖"):
                            audio_file_2 = io.BytesIO(audio_bytes_2)
                            audio_file_2.name = "record_2.wav"
                            
                            try:
                                stt_prompt_2 = "초등학교 1, 2학년 국어 문장 읽기 연습입니다. 띄어 읽기에 주의하며 또박또박 읽은 소리입니다."
                                
                                transcript_2 = client.audio.transcriptions.create(
                                    model="whisper-1", 
                                    file=audio_file_2,
                                    language="ko",
                                    prompt=stt_prompt_2
                                )
                                
                                spoken_text_2 = transcript_2.text.strip()
                                clean_spoken_2 = spoken_text_2.replace(".", "").replace(",", "").replace("!", "").replace("?", "").strip()
                                clean_target_2 = target_sentence.replace(".", "").replace(",", "").replace("!", "").replace("?", "").strip()
                                
                                st.info(f"🎤 학생이 낸 소리: **{clean_spoken_2}**")
                                
                                spoken_words = clean_spoken_2.split()
                                target_words = clean_target_2.split()
                                
                                if spoken_words == target_words:
                                    log_attempt("국어", "띄어 읽기 연습", target_sentence, clean_spoken_2, True, "없음", hint_used=st.session_state.show_slash_hint)
                                    st.session_state.k2_solved = True
                                    st.session_state.k2_last_spoken = clean_spoken_2
                                    st.session_state.show_slash_hint = False
                                    st.rerun()
                                else:
                                    err_type = "띄어 읽기 오류" if "".join(spoken_words) == "".join(target_words) else "어절·띄어 읽기 오류"
                                    log_attempt("국어", "띄어 읽기 연습", target_sentence, clean_spoken_2, False, err_type, hint_used=st.session_state.show_slash_hint)
                                    
                                    st.session_state.show_slash_hint = True
                                    slashed_sentence = format_slash_hint(target_sentence)
                                    text_placeholder.markdown(f"<h2 style='text-align: center; color: #FF4B4B; margin: 20px 0;'>{slashed_sentence}</h2>", unsafe_allow_html=True)
                                    hint_placeholder.info("💡 선생님 힌트: 빗금(/)이 있는 곳에서 숨을 살짝 고르고 다시 읽어볼까요?")
                                    
                                    if "아버지가" in clean_target_2 and "가방에" in clean_spoken_2:
                                        st.error("💡 아뿔싸! 아버지가 '가방'에 들어가셨네요. 띄어 읽기가 잘못되어 뜻이 달라졌어요.")
                                    elif "".join(spoken_words) == "".join(target_words):
                                        st.warning("💡 글자는 정확히 읽었지만 띄어 읽기가 어색해요. 빗금(/) 표시가 있는 곳에서 잠깐 멈추어 다시 읽어볼까요?")
                                    else:
                                        st.warning("💡 음, 글자가 빠졌거나 띄어 읽기가 붙어서 다른 말처럼 들렸어요. 빗금(/) 표시를 보며 의미 단위로 끊어서 다시 읽어볼까요?")
                                    
                            except Exception as e:
                                if "audio_too_short" in str(e):
                                    st.warning("⚠️ 녹음된 소리가 너무 짧거나 마이크가 인식되지 않았어요. 마이크 상태를 확인해 주세요!")
                                else:
                                    st.error(f"❌ 시스템 오류가 발생했습니다: {e}")

                    st.write("")
                    if st.button("🔄 다른 문장으로 바꾸기", key="skip_sentence_btn"):
                        st.session_state.k2_target = generate_sentence(st.session_state.k2_stage, exclude_sentence=target_sentence)
                        st.session_state.show_slash_hint = False
                        st.session_state.k2_q_count += 1
                        st.rerun()

        # ==========================================
        # --- 수학 학습 탭 ---
        # ==========================================
        with tab_math:
            math_choice = st.radio("어떤 연습을 할까요?", ["1. 알맞은 말과 기호 찾기", "2. 차근차근 식 세우기"], horizontal=True)
            st.divider()
            
            # ------------------------------------------
            # [수학 1] 알맞은 말과 기호 찾기 (크기 비교)
            # ------------------------------------------
            if math_choice == "1. 알맞은 말과 기호 찾기":
                st.subheader("1. 알맞은 말과 기호 찾기")
                
                m1_options = [
                    "1단계: 한 자릿수끼리 비교",
                    "2단계: 한 자릿수와 두 자릿수 비교",
                    "3단계: 두 자릿수끼리 비교"
                ]
                selected_m1_label = st.radio(
                    "연습할 수의 크기를 선택하세요:",
                    m1_options,
                    index=st.session_state.m1_stage - 1,
                    horizontal=True
                )
                selected_m1_stage = m1_options.index(selected_m1_label) + 1
                
                if selected_m1_stage != st.session_state.m1_stage:
                    st.session_state.m1_stage = selected_m1_stage
                    st.session_state.m1_pair = generate_compare_numbers(selected_m1_stage)
                    st.session_state.m1_solved = False
                    st.session_state.m1_q_count += 1
                    st.rerun()
                
                st.write("두 숫자의 크기를 비교해 알맞은 말과 기호를 골라보자!")
                
                num_left, num_right = st.session_state.m1_pair
                if num_left > num_right:
                    correct_choice = "크다 (>)"
                elif num_left < num_right:
                    correct_choice = "작다 (<)"
                else:
                    correct_choice = "같다 (=)"
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_a:
                    st.markdown(f"<h1 style='text-align: center; font-size: 70px;'>{num_left}</h1>", unsafe_allow_html=True)
                with col_b:
                    user_answer = st.selectbox(
                        f"왼쪽 수({num_left})는 오른쪽 수({num_right})보다...",
                        ["선택하세요", "크다 (>)", "작다 (<)", "같다 (=)"],
                        key=f"m1_select_{st.session_state.m1_q_count}"
                    )
                with col_c:
                    st.markdown(f"<h1 style='text-align: center; font-size: 70px;'>{num_right}</h1>", unsafe_allow_html=True)
                
                if st.session_state.m1_solved:
                    st.success(f"🎉 정답이에요! **{num_left}**은(는) **{num_right}**보다 **{correct_choice}**가 맞습니다!")
                    if st.button("➡️ 다음 숫자 비교하기", type="primary", use_container_width=True):
                        st.session_state.m1_pair = generate_compare_numbers(st.session_state.m1_stage, exclude_pair=(num_left, num_right))
                        st.session_state.m1_solved = False
                        st.session_state.m1_q_count += 1
                        st.rerun()
                else:
                    if st.button("정답 확인하기", key="math_btn_1", type="primary"):
                        if user_answer == "선택하세요":
                            st.warning("알맞은 말과 기호를 먼저 선택해 줘.")
                        elif user_answer == correct_choice:
                            log_attempt("수학", "수 크기 비교", f"{num_left} ○ {num_right}", user_answer, True, "없음")
                            st.session_state.m1_solved = True
                            st.rerun()
                        else:
                            if st.session_state.m1_stage == 2:
                                err_label = "자릿수 비교 오류"
                                st.error("💡 아쉽지만 다시 생각해 볼까? **한 자릿수(1~9)**보다 **두 자릿수(10~99)**가 항상 더 커요!")
                            elif st.session_state.m1_stage == 3:
                                if (num_left // 10) != (num_right // 10):
                                    err_label = "십의 자리 비교 오류"
                                    st.error("💡 아쉽지만 다시 생각해 볼까? 두 자릿수는 **십의 자리(앞자리) 숫자**가 큰 쪽이 더 커요!")
                                else:
                                    err_label = "일의 자리 비교 오류"
                                    st.error("💡 십의 자리 숫자가 같네요! 이럴 때는 **일의 자리(뒷자리) 숫자** 크기를 비교해 보세요!")
                            else:
                                err_label = "한 자릿수 크기 비교 오류"
                                st.error("💡 아쉽지만 다시 한번 수의 순서를 떠올리며 비교해 볼까?")
                            
                            log_attempt("수학", "수 크기 비교", f"{num_left} ○ {num_right}", user_answer, False, err_label)
                    
                    st.write("")
                    if st.button("🔄 다른 숫자로 바꾸기", key="skip_m1_btn"):
                        st.session_state.m1_pair = generate_compare_numbers(st.session_state.m1_stage, exclude_pair=(num_left, num_right))
                        st.session_state.m1_q_count += 1
                        st.rerun()
                    
            # ------------------------------------------
            # [수학 2] 차근차근 식 세우기 (문장제 + 그림 힌트)
            # ------------------------------------------
            elif math_choice == "2. 차근차근 식 세우기":
                st.subheader("2. 차근차근 식 세우기")
                
                prob = st.session_state.m2_prob
                q_idx = st.session_state.m2_q_count
                
                st.info(f"📖 **문제:** {prob['text']}")
                
                st.write("문제에 알맞은 숫자와 기호를 넣어 식을 세워보자!")
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 2])
                with col1:
                    num1_in = st.text_input("첫 번째 숫자", key=f"m_num1_{q_idx}")
                with col2:
                    op_in = st.selectbox("기호", ["선택", "+", "-"], key=f"m_op_{q_idx}")
                with col3:
                    num2_in = st.text_input("두 번째 숫자", key=f"m_num2_{q_idx}")
                with col4:
                    st.markdown("<h2 style='text-align: center; margin-top: 25px;'>=</h2>", unsafe_allow_html=True)
                with col5:
                    ans_in = st.text_input("정답", key=f"m_ans_{q_idx}")
                
                if not st.session_state.m2_show_hint:
                    if st.button("💡 힌트 보기 (그림으로 알아보기)", key=f"m2_hint_btn_{q_idx}"):
                        st.session_state.m2_show_hint = True
                        st.rerun()
                
                hint_op_in = "선택"
                hint_ans_in = ""
                if st.session_state.m2_show_hint:
                    st.divider()
                    st.markdown("#### 🎨 그림 힌트")
                    st.write("그림의 개수를 직접 세어 보고, **그림 사이의 기호(+, -)**와 **등호(=) 옆 정답**을 채워도 정답으로 인정돼요!")
                    
                    emoji_group_1 = " ".join([prob["e1"]] * prob["n1"])
                    emoji_group_2 = " ".join([prob["e2"]] * prob["n2"])
                    
                    hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([3, 2, 3, 1, 2])
                    with hcol1:
                        st.markdown(
                            f"<div style='background-color: #FFF8DC; padding: 15px; border-radius: 10px; text-align: center; font-size: 32px;'>{emoji_group_1}</div>",
                            unsafe_allow_html=True
                        )
                    with hcol2:
                        hint_op_in = st.selectbox("기호 선택", ["선택", "+", "-"], key=f"m_hint_op_{q_idx}")
                    with hcol3:
                        st.markdown(
                            f"<div style='background-color: #FFF8DC; padding: 15px; border-radius: 10px; text-align: center; font-size: 32px;'>{emoji_group_2}</div>",
                            unsafe_allow_html=True
                        )
                    with hcol4:
                        st.markdown("<h2 style='text-align: center; margin-top: 15px;'>=</h2>", unsafe_allow_html=True)
                    with hcol5:
                        hint_ans_in = st.text_input("정답 입력", key=f"m_hint_ans_{q_idx}")
                
                st.write("")
                
                if st.session_state.m2_solved:
                    st.balloons()
                    st.success(f"🎉 참 잘했어요! **{prob['n1']} {prob['op']} {prob['n2']} = {prob['ans']}**, 정확하게 풀었네요!")
                    if st.button("➡️ 다음 문제 풀기", type="primary", use_container_width=True):
                        st.session_state.m2_prob = generate_word_problem(exclude_text=prob["text"])
                        st.session_state.m2_show_hint = False
                        st.session_state.m2_solved = False
                        st.session_state.m2_q_count += 1
                        st.rerun()
                
                else:
                    if st.button("정답 확인하기", key="math_btn_2", type="primary"):
                        main_filled = (num1_in.strip() != "" or num2_in.strip() != "" or ans_in.strip() != "" or op_in != "선택")
                        hint_filled = (st.session_state.m2_show_hint and (hint_op_in != "선택" or hint_ans_in.strip() != ""))
                        
                        if not main_filled and not hint_filled:
                            st.warning("빈칸에 숫자와 기호를 먼저 입력해 주세요!")
                        else:
                            is_correct = False
                            feedback_msg = ""
                            err_category = ""
                            recorded_ans = ""
                            
                            # 1) 그림 힌트 칸 검증
                            if hint_filled:
                                recorded_ans = f"[그림 힌트] {hint_op_in} {hint_ans_in.strip()}"
                                if hint_op_in == "선택" or hint_ans_in.strip() == "":
                                    feedback_msg = "💡 그림 힌트의 **기호(+, -)**와 **정답** 칸을 모두 채워주세요!"
                                elif not hint_ans_in.strip().isdigit():
                                    feedback_msg = "💡 정답 칸에는 숫자만 입력해 주세요!"
                                elif hint_op_in != prob["op"]:
                                    err_category = "연산 기호(+/-) 오류"
                                    if prob["op"] == "+":
                                        feedback_msg = "💡 모두 합하면 몇 개인지 묻는 문제예요. 더하기(+) 기호를 선택해 볼까요?"
                                    else:
                                        feedback_msg = "💡 먹거나 주어서 줄어들거나 차이를 묻는 문제예요. 빼기(-) 기호를 선택해 볼까요?"
                                elif int(hint_ans_in.strip()) != prob["ans"]:
                                    err_category = "수 세기·계산 오류"
                                    feedback_msg = "💡 기호는 정확하게 골랐어요! 위의 그림 개수를 손가락으로 하나씩 짚어가며 다시 세어볼까요?"
                                else:
                                    is_correct = True
                            
                            # 2) 기본 숫자 식 칸 검증
                            if not is_correct and main_filled:
                                recorded_ans = f"{num1_in.strip()} {op_in} {num2_in.strip()} = {ans_in.strip()}"
                                if num1_in.strip() == "" or op_in == "선택" or num2_in.strip() == "" or ans_in.strip() == "":
                                    if not feedback_msg:
                                        feedback_msg = "💡 첫 번째 숫자, 기호, 두 번째 숫자, 정답 빈칸을 모두 채워주세요!"
                                elif not (num1_in.strip().isdigit() and num2_in.strip().isdigit() and ans_in.strip().isdigit()):
                                    feedback_msg = "💡 숫자 칸에는 숫자만 입력해 주세요!"
                                else:
                                    u_n1 = int(num1_in.strip())
                                    u_n2 = int(num2_in.strip())
                                    u_ans = int(ans_in.strip())
                                    
                                    nums_ok = ((u_n1 == prob["n1"] and u_n2 == prob["n2"]) or
                                               (prob["op"] == "+" and u_n1 == prob["n2"] and u_n2 == prob["n1"]))
                                    
                                    if not nums_ok:
                                        err_category = "문장제 숫자 추출 오류"
                                        feedback_msg = "💡 문제에 나온 두 숫자를 다시 한번 잘 살펴볼까요? 필요하다면 아래 **'힌트 보기'** 버튼을 눌러보세요!"
                                    elif op_in != prob["op"]:
                                        err_category = "연산 기호(+/-) 오류"
                                        if prob["op"] == "+":
                                            feedback_msg = "💡 숫자는 잘 찾았어요! 모두 합하는 문제이니 **더하기(+)** 기호를 선택해 볼까요?"
                                        else:
                                            feedback_msg = "💡 숫자는 잘 찾았어요! 줄어들거나 차이를 구하는 문제이니 **빼기(-)** 기호를 선택해 볼까요?"
                                    elif u_ans != prob["ans"]:
                                        err_category = "수 세기·계산 오류"
                                        feedback_msg = "💡 식은 아주 잘 세웠어요! 계산 결과만 다시 한번 확인해 볼까요? 아래 **'힌트 보기'**를 누르면 그림으로 세어볼 수 있어요!"
                                    else:
                                        is_correct = True
                            
                            if is_correct:
                                log_attempt("수학", "문장제 식 세우기", prob["text"], recorded_ans, True, "없음", hint_used=st.session_state.m2_show_hint)
                                st.session_state.m2_solved = True
                                st.rerun()
                            else:
                                if err_category:
                                    log_attempt("수학", "문장제 식 세우기", prob["text"], recorded_ans, False, err_category, hint_used=st.session_state.m2_show_hint)
                                st.error(feedback_msg)
                    
                    st.write("")
                    if st.button("🔄 다른 문제로 바꾸기", key="skip_m2_btn"):
                        st.session_state.m2_prob = generate_word_problem(exclude_text=prob["text"])
                        st.session_state.m2_show_hint = False
                        st.session_state.m2_q_count += 1
                        st.rerun()

# ==========================================
# 2. 교사용 화면 (실제 학생 학습 데이터 분석 대시보드)
# ==========================================
elif mode == "교사용":
    top_t1, top_t2 = st.columns([4, 1.2])
    with top_t1:
        st.title("👩‍🏫 교사 대시보드")
        st.write(f"학생용 탭에서 실제로 풀이한 기록을 바탕으로 학년·반·학생별 오류 패턴을 분석합니다. *(기준 시각: 한국 표준시 KST {get_kst_now().strftime('%H:%M')})*")
    with top_t2:
        st.write("")
        if st.button("🗑️ 학습 기록 초기화", use_container_width=True):
            st.session_state.learning_logs = []
            st.rerun()
            
    st.divider()
    
    if len(st.session_state.learning_logs) == 0:
        st.info("📭 아직 저장된 학습 기록이 없습니다. 왼쪽 메뉴에서 **'학생용'**으로 이동해 학생 정보를 입력하고 문제를 풀면 이곳에 실시간으로 기록됩니다.")
    else:
        raw_df = pd.DataFrame(st.session_state.learning_logs)
        
        # ------------------------------------------
        # [필터 영역] 학년별 / 반별 / 학생별 조회
        # ------------------------------------------
        st.subheader("🔍 대상 학생 필터링")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            grade_list = ["전체 학년"] + sorted(raw_df["학년"].unique().tolist())
            selected_grade = st.selectbox("학년 선택", grade_list)
        
        df_after_grade = raw_df if selected_grade == "전체 학년" else raw_df[raw_df["학년"] == selected_grade]
        
        with f_col2:
            class_list = ["전체 반"] + sorted(df_after_grade["반"].unique().tolist())
            selected_class = st.selectbox("반 선택", class_list)
            
        df_after_class = df_after_grade if selected_class == "전체 반" else df_after_grade[df_after_grade["반"] == selected_class]
        
        with f_col3:
            student_list = ["전체 학생"] + sorted(df_after_class["학생 식별"].unique().tolist())
            selected_student = st.selectbox("개별 학생 선택", student_list)
            
        df = df_after_class if selected_student == "전체 학생" else df_after_class[df_after_class["학생 식별"] == selected_student]
        
        st.divider()
        
        # ------------------------------------------
        # 1. 핵심 지표(KPI) 요약
        # ------------------------------------------
        target_title = selected_student if selected_student != "전체 학생" else f"{selected_grade} / {selected_class} 전체"
        st.subheader(f"📌 학습 요약 ({target_title})")
        
        total_cnt = len(df)
        correct_cnt = len(df[df["결과"] == "정답"])
        overall_acc = round((correct_cnt / total_cnt) * 100, 1) if total_cnt > 0 else 0.0
        
        kr_df = df[df["영역"] == "국어"]
        kr_acc = round((len(kr_df[kr_df["결과"] == "정답"]) / len(kr_df)) * 100, 1) if len(kr_df) > 0 else 0.0
        
        math_df = df[df["영역"] == "수학"]
        math_acc = round((len(math_df[math_df["결과"] == "정답"]) / len(math_df)) * 100, 1) if len(math_df) > 0 else 0.0
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("총 풀이 문항 수", f"{total_cnt}문항")
        kpi2.metric("전체 정답률", f"{overall_acc}%", f"{correct_cnt}/{total_cnt} 정답")
        kpi3.metric("📖 국어(읽기) 정답률", f"{kr_acc}%", f"총 {len(kr_df)}회 시도")
        kpi4.metric("🧮 수학(연산) 정답률", f"{math_acc}%", f"총 {len(math_df)}회 시도")
        
        st.divider()
        
        # ------------------------------------------
        # 2. 학생별 종합 성취도 비교표 (여러 학생이 선택된 경우)
        # ------------------------------------------
        if selected_student == "전체 학생":
            st.subheader("🧑‍🎓 학생별 학습 현황 한눈에 보기")
            summary_rows = []
            for (g, c, num, nm), grp in df.groupby(["학년", "반", "번호", "이름"], sort=True):
                tot = len(grp)
                corr = len(grp[grp["결과"] == "정답"])
                acc = f"{round((corr / tot) * 100, 1)}%"
                
                k_grp = grp[grp["영역"] == "국어"]
                k_rate = f"{round((len(k_grp[k_grp['결과'] == '정답']) / len(k_grp)) * 100, 1)}%" if len(k_grp) > 0 else "-"
                
                m_grp = grp[grp["영역"] == "수학"]
                m_rate = f"{round((len(m_grp[m_grp['결과'] == '정답']) / len(m_grp)) * 100, 1)}%" if len(m_grp) > 0 else "-"
                
                errs = grp[grp["결과"] == "오답"]["오류 유형"]
                main_err = errs.value_counts().idxmax() if len(errs) > 0 else "오류 없음"
                hints = len(grp[grp["힌트 사용"] == "사용"])
                
                summary_rows.append({
                    "학년": g,
                    "반": c,
                    "번호": num,
                    "이름": nm,
                    "총 풀이 수": f"{tot}문항",
                    "전체 정답률": acc,
                    "국어 정답률": k_rate,
                    "수학 정답률": m_rate,
                    "주요 취약 오류": main_err,
                    "힌트 사용": f"{hints}회"
                })
            
            summary_df = pd.DataFrame(summary_rows)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            st.divider()
        
        # ------------------------------------------
        # 3. 영역별 오류 유형 시각화 분석
        # ------------------------------------------
        st.subheader("📈 영역별 오답 원인 분석")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### 📖 국어 (난독증 읽기 오류 패턴)")
            kr_errors = kr_df[kr_df["결과"] == "오답"]
            if len(kr_errors) > 0:
                kr_err_counts = kr_errors["오류 유형"].value_counts().reset_index()
                kr_err_counts.columns = ["오류 유형", "오답 횟수"]
                st.bar_chart(kr_err_counts.set_index("오류 유형"), color="#FF6B6B")
            elif len(kr_df) > 0:
                st.success("🎉 국어 영역에서 발생한 오답이 없습니다!")
            else:
                st.info("국어 풀이 기록이 아직 없습니다.")
                
        with chart_col2:
            st.markdown("#### 🧮 수학 (난산증 수 개념·연산 오류 패턴)")
            math_errors = math_df[math_df["결과"] == "오답"]
            if len(math_errors) > 0:
                math_err_counts = math_errors["오류 유형"].value_counts().reset_index()
                math_err_counts.columns = ["오류 유형", "오답 횟수"]
                st.bar_chart(math_err_counts.set_index("오류 유형"), color="#4D96FF")
            elif len(math_df) > 0:
                st.success("🎉 수학 영역에서 발생한 오답이 없습니다!")
            else:
                st.info("수학 풀이 기록이 아직 없습니다.")
                
        st.divider()
        
        # ------------------------------------------
        # 4. 개별화 지도(IEP) 맞춤형 교육 처방 제안
        # ------------------------------------------
        st.subheader("💡 누적 데이터 기반 맞춤형 지도 제안")
        guide_col1, guide_col2 = st.columns(2)
        
        with guide_col1:
            kr_errors = kr_df[kr_df["결과"] == "오답"]
            if len(kr_errors) > 0:
                top_kr_err = kr_errors["오류 유형"].value_counts().idxmax()
                if "자음" in top_kr_err:
                    st.warning(f"**[국어 집중 지도: {top_kr_err}]**\n\n예사소리(`ㅂ, ㄷ, ㄱ`)와 거센소리(`ㅍ, ㅌ, ㅋ`) 변별에 어려움이 보입니다. 목에 손을 대고 바람이 터지는 느낌을 비교하며 1단계 단음절 카드를 반복 연습하도록 지도해 주세요.")
                elif "모음" in top_kr_err:
                    st.warning(f"**[국어 집중 지도: {top_kr_err}]**\n\n입술 모양에 따른 단모음(`ㅗ/ㅜ`, `ㅏ/ㅓ`) 구별이 흔들리고 있습니다. 거울을 보며 입 모양 크기를 과장해 소리 내는 조음 훈련을 권장합니다.")
                elif "받침" in top_kr_err:
                    st.warning(f"**[국어 집중 지도: {top_kr_err}]**\n\n끝소리(종성)를 탈락시키고 모음으로만 발음하는 경향이 있습니다. 글자 끝에서 혀나 입술을 닫아 소리를 멈추는 연습이 필요합니다.")
                else:
                    st.warning(f"**[국어 집중 지도: {top_kr_err}]**\n\n조사나 어절 경계를 붙여 읽어 문장 의미 파악에 오류가 발생합니다. 빗금(`/`)이 표시된 2어절 문장부터 끊어 읽는 호흡 훈련을 진행해 주세요.")
            elif len(kr_df) > 0:
                st.info("**[국어 지도 안내]** 현재까지 읽기 정확도가 매우 우수합니다. 3어절 문장 읽기 단계로 확장해 유창성을 길러주세요.")
            else:
                st.info("**[국어 지도 안내]** 국어 학습 기록이 쌓이면 맞춤형 지도 방안이 표시됩니다.")
                
        with guide_col2:
            math_errors = math_df[math_df["결과"] == "오답"]
            hint_used_cnt = len(math_df[math_df["힌트 사용"] == "사용"])
            if len(math_errors) > 0:
                top_math_err = math_errors["오류 유형"].value_counts().idxmax()
                if "자릿수" in top_math_err or "십의 자리" in top_math_err:
                    st.warning(f"**[수학 집중 지도: {top_math_err}]**\n\n수의 자릿값 개념보다 개별 숫자의 크기(`9 > 1`)만 보고 판단하는 오류가 나타납니다. 십 모형(10개 묶음)과 낱개 모형을 나란히 놓고 비교하는 구체물 활동을 병행해 주세요.")
                elif "연산 기호" in top_math_err:
                    st.warning(f"**[수학 집중 지도: {top_math_err}]**\n\n문장제 속 상황을 덧셈(`+`)과 뺄셈(`-`) 기호로 연결하는 데 혼동이 있습니다. '모두', '더 왔습니다'와 '먹었습니다', '남은' 같은 핵심 어휘에 동그라미 치며 식을 세우도록 지도해 주세요.")
                else:
                    st.warning(f"**[수학 집중 지도: {top_math_err}]**\n\n식은 바르게 세웠으나 수 세기 과정에서 일대일 대응 오류가 발생합니다. 현재 그림 힌트를 **{hint_used_cnt}회** 활용했으므로, 화면 속 그림을 하나씩 짚으며 세는 연습을 충분히 제공해 주세요.")
            elif len(math_df) > 0:
                st.info(f"**[수학 지도 안내]** 수 크기 비교 및 문장제 식 세우기를 안정적으로 수행하고 있습니다. (그림 힌트 활용: {hint_used_cnt}회)")
            else:
                st.info("**[수학 지도 안내]** 수학 학습 기록이 쌓이면 맞춤형 지도 방안이 표시됩니다.")
                
        st.divider()
        
        # ------------------------------------------
        # 5. 상세 학습 이력 테이블 및 CSV 내보내기
        # ------------------------------------------
        st.subheader("📋 상세 풀이 이력")
        
        filter_subj = st.radio("영역별 필터:", ["전체", "국어", "수학"], horizontal=True)
        filtered_df = df if filter_subj == "전체" else df[df["영역"] == filter_subj]
        
        display_cols = ["시간(KST)", "학년", "반", "번호", "이름", "영역", "활동", "문제", "학생 응답", "결과", "오류 유형", "힌트 사용"]
        st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)
        
        csv_data = filtered_df[display_cols].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 학습 분석 리포트(CSV) 다운로드",
            data=csv_data,
            file_name=f"학습분석리포트_{target_title.replace(' ', '_')}_{get_kst_now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
