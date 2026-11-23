import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
from collections import Counter
import io
import random

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
            # 가끔 같은 숫자도 출제 (약 15% 확률)
            b = a if random.random() < 0.15 else random.randint(1, 9)
        elif stage == 2:
            one_digit = random.randint(1, 9)
            two_digit = random.randint(10, 99)
            # (한 자릿수, 두 자릿수) 또는 (두 자릿수, 한 자릿수) 무작위 배치
            if random.choice([True, False]):
                a, b = one_digit, two_digit
            else:
                a, b = two_digit, one_digit
        else:
            # 50% 확률로 십의 자리가 같은 수를 출제해 일의 자리 비교까지 훈련
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
# 세션 상태(Session State) 초기화
# ==========================================
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
    st.session_state.m2_prob = WORD_PROBLEMS[0]  # 첫 문제는 기본 사과/배 예시로 시작
if "m2_show_hint" not in st.session_state:
    st.session_state.m2_show_hint = False
if "m2_solved" not in st.session_state:
    st.session_state.m2_solved = False
if "m2_q_count" not in st.session_state:
    st.session_state.m2_q_count = 0

# --- 왼쪽 사이드바 (메뉴 선택) ---
st.sidebar.title("메뉴 선택")
mode = st.sidebar.radio("어디로 들어갈까요?", ["학생용", "교사용"])

# ==========================================
# 1. 학생용 화면
# ==========================================
if mode == "학생용":
    st.title("🎒 즐거운 배움터")
    st.write("안녕! 오늘은 어떤 공부를 해볼까?")
    
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
                                st.session_state.k2_solved = True
                                st.session_state.k2_last_spoken = clean_spoken_2
                                st.session_state.show_slash_hint = False
                                st.rerun()
                            else:
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
            
            # 1~2학년 수준 3단계 난이도 선택
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
                        st.session_state.m1_solved = True
                        st.rerun()
                    else:
                        # 단계별 자릿값 원리 맞춤형 피드백
                        if st.session_state.m1_stage == 2:
                            st.error("💡 아쉽지만 다시 생각해 볼까? **한 자릿수(1~9)**보다 **두 자릿수(10~99)**가 항상 더 커요!")
                        elif st.session_state.m1_stage == 3:
                            if (num_left // 10) != (num_right // 10):
                                st.error("💡 아쉽지만 다시 생각해 볼까? 두 자릿수는 **십의 자리(앞자리) 숫자**가 큰 쪽이 더 커요!")
                            else:
                                st.error("💡 십의 자리 숫자가 같네요! 이럴 때는 **일의 자리(뒷자리) 숫자** 크기를 비교해 보세요!")
                        else:
                            st.error("💡 아쉽지만 다시 한번 수의 순서를 떠올리며 비교해 볼까?")
                
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
            
            # 문제 텍스트 강조 박스
            st.info(f"📖 **문제:** {prob['text']}")
            
            # 기본 숫자 식 입력 영역
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
            
            # 힌트 보기 버튼 (클릭 시 그림 변환 UI 활성화)
            if not st.session_state.m2_show_hint:
                if st.button("💡 힌트 보기 (그림으로 알아보기)", key=f"m2_hint_btn_{q_idx}"):
                    st.session_state.m2_show_hint = True
                    st.rerun()
            
            # 힌트 보기 활성화 시: 글로 된 문제를 이모지 그림으로 변환하여 제시
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
            
            # 정답 완료 상태일 때
            if st.session_state.m2_solved:
                st.balloons()
                st.success(f"🎉 참 잘했어요! **{prob['n1']} {prob['op']} {prob['n2']} = {prob['ans']}**, 정확하게 풀었네요!")
                if st.button("➡️ 다음 문제 풀기", type="primary", use_container_width=True):
                    st.session_state.m2_prob = generate_word_problem(exclude_text=prob["text"])
                    st.session_state.m2_show_hint = False
                    st.session_state.m2_solved = False
                    st.session_state.m2_q_count += 1
                    st.rerun()
            
            # 아직 풀이 중일 때: 정답 확인 버튼 (숫자 식 OR 그림 힌트 식 둘 중 하나만 맞게 입력해도 정답 처리)
            else:
                if st.button("정답 확인하기", key="math_btn_2", type="primary"):
                    main_filled = (num1_in.strip() != "" or num2_in.strip() != "" or ans_in.strip() != "" or op_in != "선택")
                    hint_filled = (st.session_state.m2_show_hint and (hint_op_in != "선택" or hint_ans_in.strip() != ""))
                    
                    if not main_filled and not hint_filled:
                        st.warning("빈칸에 숫자와 기호를 먼저 입력해 주세요!")
                    else:
                        is_correct = False
                        feedback_msg = ""
                        
                        # 1) 그림 힌트 칸에 기호와 답을 입력한 경우 우선 검증
                        if hint_filled:
                            if hint_op_in == "선택" or hint_ans_in.strip() == "":
                                feedback_msg = "💡 그림 힌트의 **기호(+, -)**와 **정답** 칸을 모두 채워주세요!"
                            elif not hint_ans_in.strip().isdigit():
                                feedback_msg = "💡 정답 칸에는 숫자만 입력해 주세요!"
                            elif hint_op_in != prob["op"]:
                                if prob["op"] == "+":
                                    feedback_msg = "💡 모두 합하면 몇 개인지 묻는 문제예요. 더하기(+) 기호를 선택해 볼까요?"
                                else:
                                    feedback_msg = "💡 먹거나 주어서 줄어들거나 차이를 묻는 문제예요. 빼기(-) 기호를 선택해 볼까요?"
                            elif int(hint_ans_in.strip()) != prob["ans"]:
                                feedback_msg = "💡 기호는 정확하게 골랐어요! 위의 그림 개수를 손가락으로 하나씩 짚어가며 다시 세어볼까요?"
                            else:
                                is_correct = True
                        
                        # 2) 위쪽 기본 숫자 식 칸에 입력한 경우 검증
                        if not is_correct and main_filled:
                            if num1_in.strip() == "" or op_in == "선택" or num2_in.strip() == "" or ans_in.strip() == "":
                                if not feedback_msg:
                                    feedback_msg = "💡 첫 번째 숫자, 기호, 두 번째 숫자, 정답 빈칸을 모두 채워주세요!"
                            elif not (num1_in.strip().isdigit() and num2_in.strip().isdigit() and ans_in.strip().isdigit()):
                                feedback_msg = "💡 숫자 칸에는 숫자만 입력해 주세요!"
                            else:
                                u_n1 = int(num1_in.strip())
                                u_n2 = int(num2_in.strip())
                                u_ans = int(ans_in.strip())
                                
                                # 덧셈은 앞뒤 순서 교환(예: 2+3=5)도 정답으로 인정
                                nums_ok = ((u_n1 == prob["n1"] and u_n2 == prob["n2"]) or
                                           (prob["op"] == "+" and u_n1 == prob["n2"] and u_n2 == prob["n1"]))
                                
                                if not nums_ok:
                                    feedback_msg = "💡 문제에 나온 두 숫자를 다시 한번 잘 살펴볼까요? 필요하다면 아래 **'힌트 보기'** 버튼을 눌러보세요!"
                                elif op_in != prob["op"]:
                                    if prob["op"] == "+":
                                        feedback_msg = "💡 숫자는 잘 찾았어요! 모두 합하는 문제이니 **더하기(+)** 기호를 선택해 볼까요?"
                                    else:
                                        feedback_msg = "💡 숫자는 잘 찾았어요! 줄어들거나 차이를 구하는 문제이니 **빼기(-)** 기호를 선택해 볼까요?"
                                elif u_ans != prob["ans"]:
                                    feedback_msg = "💡 식은 아주 잘 세웠어요! 계산 결과만 다시 한번 확인해 볼까요? 아래 **'힌트 보기'**를 누르면 그림으로 세어볼 수 있어요!"
                                else:
                                    is_correct = True
                        
                        if is_correct:
                            st.session_state.m2_solved = True
                            st.rerun()
                        else:
                            st.error(feedback_msg)
                
                st.write("")
                if st.button("🔄 다른 문제로 바꾸기", key="skip_m2_btn"):
                    st.session_state.m2_prob = generate_word_problem(exclude_text=prob["text"])
                    st.session_state.m2_show_hint = False
                    st.session_state.m2_q_count += 1
                    st.rerun()

# ==========================================
# 2. 교사용 화면
# ==========================================
elif mode == "교사용":
    st.title("👩‍🏫 교사 대시보드")
    st.write("학생들의 학습 현황과 성장 기록을 확인합니다.")
    st.info("이곳에는 학생이 자주 틀리는 글자나 연산 오류를 분석한 데이터가 표시될 예정입니다.")
