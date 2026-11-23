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
# 한글 음소(초성·중성·종성) 및 문제 출제 데이터
# ==========================================
CHOSUNG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
JUNGSUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
JONGSUNG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

# 1단계용: 쌍자음 제외 기본 자음 14개 + 이중모음(ㅑ, ㅕ, ㅛ, ㅠ 등) 제외 기본 단모음 6개
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
# 세션 상태(Session State) 초기화
# ==========================================
if "show_slash_hint" not in st.session_state:
    st.session_state.show_slash_hint = False

if "k1_stage" not in st.session_state:
    st.session_state.k1_stage = 1  # 1: 초성+중성, 2: 초성+중성+종성
if "k1_streak" not in st.session_state:
    st.session_state.k1_streak = 0  # 연속 정답 횟수
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
    
    # --- 국어 학습 탭 ---
    with tab_korean:
        korean_choice = st.radio("어떤 연습을 할까요?", ["1. 비슷한 글자 찾기", "2. 띄어 읽기 연습"], horizontal=True)
        st.divider() # 구분선
        
        if korean_choice == "1. 비슷한 글자 찾기":
            st.subheader("1. 비슷한 글자 찾기 연습")
            
            # 상단 단계 및 연속 정답 진행도 표시
            col_stat1, col_stat2 = st.columns([2, 1])
            with col_stat1:
                if st.session_state.k1_stage == 1:
                    st.markdown("🌱 **현재 단계: 1단계 (기본 자음 + 기본 모음)** — *5개 연속 맞히면 받침 있는 글자로 넘어가요!*")
                    st.progress(min(st.session_state.k1_streak / 5, 1.0))
                else:
                    st.markdown("🌳 **현재 단계: 2단계 (자음 + 모음 + 받침)** — *받침 소리까지 정확히 읽어보자!*")
                    st.progress(1.0)
            with col_stat2:
                st.metric(label="연속 정답 기록", value=f"{st.session_state.k1_streak}개 연속")
            
            st.write("화면의 글자를 보고 또박또박 읽어보자!")
            
            target_word = st.session_state.k1_target
            st.markdown(f"<h1 style='text-align: center; font-size: 110px; margin: 10px 0;'>{target_word}</h1>", unsafe_allow_html=True)
            
            # 정답을 맞힌 상태일 때: 축하 메시지 + 다음 글자 버튼 표시
            if st.session_state.k1_solved:
                if st.session_state.k1_last_spoken:
                    st.info(f"🎤 학생이 낸 소리: **{st.session_state.k1_last_spoken}**")
                
                if st.session_state.k1_leveled_up:
                    st.balloons()
                    st.success("🎊 대단해요! 5개 연속 정답을 달성해서 이제 **받침이 있는 2단계 글자**로 올라갑니다!")
                else:
                    st.success("🎉 참 잘했어요! 정확하게 읽었네요!")
                
                if st.button("➡️ 다음 글자 연습하기", type="primary", use_container_width=True):
                    st.session_state.k1_target = generate_word(st.session_state.k1_stage, exclude_word=target_word)
                    st.session_state.k1_solved = False
                    st.session_state.k1_last_spoken = ""
                    st.session_state.k1_leveled_up = False
                    st.session_state.k1_q_count += 1
                    st.rerun()
            
            # 아직 문제를 푸는 중일 때: 녹음기 및 음성 인식 평가 실행
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
                            # 단계에 맞춰 음성 인식(STT) 힌트 프롬프트 최적화
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
                            
                            # 인식된 결과에서 한글 완성형 음절('가'~'힣')만 추출
                            hangul_chars = [ch for ch in spoken_text if '가' <= ch <= '힣']
                            
                            if len(hangul_chars) > 0:
                                counts = Counter(hangul_chars)
                                max_count = counts.most_common(1)[0][1]
                                
                                # 정답 판정 (최빈값 또는 동점 포함)
                                if counts[target_word] == max_count:
                                    st.session_state.k1_solved = True
                                    st.session_state.k1_last_spoken = spoken_text
                                    st.session_state.k1_streak += 1
                                    
                                    # 1단계에서 연달아 5개 맞힌 경우 2단계로 승급
                                    if st.session_state.k1_stage == 1 and st.session_state.k1_streak >= 5:
                                        st.session_state.k1_stage = 2
                                        st.session_state.k1_leveled_up = True
                                    
                                    st.rerun()
                                else:
                                    # 오답 시 1단계 연속 정답 카운트 초기화
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
                                    
                                    # 틀린 음소별 맞춤 안내 문구 생성
                                    wrong_parts = []
                                    if not cho_ok:
                                        wrong_parts.append("자음(첫소리)")
                                    if not jung_ok:
                                        wrong_parts.append("모음(가운뎃소리)")
                                    if not jong_ok:
                                        wrong_parts.append("받침(끝소리)")
                                    
                                    wrong_desc = ", ".join(wrong_parts)
                                    st.error(f"💡 주로 '{spoken_char}'(으)로 읽었네요. 아쉽지만 **{wrong_desc}** 부분을 잘못 읽었어요.")
                                    
                                    # 시각적 색상 강조 (자음: 빨강, 모음: 파랑, 받침: 초록)
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
                            
        elif korean_choice == "2. 띄어 읽기 연습":
            st.subheader("2. 알맞게 띄어 읽기 연습")
            st.write("문장의 뜻이 잘 통하게 띄어 읽어보자!")
            
            text_placeholder = st.empty()
            hint_placeholder = st.empty()
            
            if st.session_state.show_slash_hint:
                text_placeholder.markdown("<h2 style='text-align: center; color: #FF4B4B;'>아버지가 / 방에 / 들어가신다.</h2>", unsafe_allow_html=True)
                hint_placeholder.info("💡 선생님 힌트: 빗금(/)이 있는 곳에서 숨을 살짝 고르고 다시 읽어볼까요?")
            else:
                text_placeholder.markdown("<h2 style='text-align: center;'>아버지가 방에 들어가신다.</h2>", unsafe_allow_html=True)
            
            st.info("👇 마이크를 누르고 **아이콘이 빨간색으로 변하면** 읽어보세요. (다 읽은 뒤 한 번 더 클릭)")
            
            audio_bytes_2 = audio_recorder(
                text="클릭해서 녹음 시작", 
                icon_size="2x", 
                pause_threshold=10.0,
                key="k_mic_2"
            )
            
            if audio_bytes_2:
                st.audio(audio_bytes_2, format="audio/wav")
                
                with st.spinner("AI 선생님이 목소리를 듣고 있어요... 🤖"):
                    audio_file_2 = io.BytesIO(audio_bytes_2)
                    audio_file_2.name = "record_2.wav"
                    
                    try:
                        transcript_2 = client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio_file_2,
                            language="ko",
                            prompt="아버지가 방에 들어가신다. 아버지 가방에 들어가신다."
                        )
                        
                        spoken_text_2 = transcript_2.text.strip()
                        clean_text_2 = spoken_text_2.replace(".", "").replace(",", "").replace("!", "").replace("?", "")
                        st.info(f"🎤 학생이 낸 소리: **{clean_text_2}**")
                        
                        if "가방에" in clean_text_2:
                            st.error("💡 아뿔싸! 아버지가 '가방'에 들어가셨네요. 띄어 읽기가 잘못되어 뜻이 달라졌어요.")
                            st.session_state.show_slash_hint = True
                            
                            text_placeholder.markdown("<h2 style='text-align: center; color: #FF4B4B;'>아버지가 / 방에 / 들어가신다.</h2>", unsafe_allow_html=True)
                            hint_placeholder.info("💡 선생님 힌트: 빗금(/)이 있는 곳에서 숨을 살짝 고르고 다시 읽어볼까요?")
                        
                        elif "아버지가" in clean_text_2 and "방에" in clean_text_2:
                            st.success("🎉 참 잘했어요! 알맞게 띄어 읽어서 뜻이 잘 통하네요!")
                            st.session_state.show_slash_hint = False
                        
                        else:
                            st.warning("💡 음, 글자를 잘못 읽었거나 띄어 읽기가 어색해요. 다시 한번 또박또박 읽어볼까요?")
                            st.session_state.show_slash_hint = True
                            
                            text_placeholder.markdown("<h2 style='text-align: center; color: #FF4B4B;'>아버지가 / 방에 / 들어가신다.</h2>", unsafe_allow_html=True)
                            hint_placeholder.info("💡 선생님 힌트: 빗금(/)이 있는 곳에서 숨을 살짝 고르고 다시 읽어볼까요?")
                            
                    except Exception as e:
                        if "audio_too_short" in str(e):
                            st.warning("⚠️ 녹음된 소리가 너무 짧거나 마이크가 인식되지 않았어요. 마이크 상태를 확인해 주세요!")
                        else:
                            st.error(f"❌ 시스템 오류가 발생했습니다: {e}")

            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ (테스트용) 오답 감지 시뮬레이션", key="test_btn_1"):
                    st.session_state.show_slash_hint = True
                    st.rerun()
            with col2:
                if st.session_state.show_slash_hint:
                    if st.button("🔄 다시 처음으로 (힌트 숨기기)", key="reset_btn_1"):
                        st.session_state.show_slash_hint = False
                        st.rerun()

    # --- 수학 학습 탭 ---
    with tab_math:
        math_choice = st.radio("어떤 연습을 할까요?", ["1. 알맞은 말과 기호 찾기", "2. 차근차근 식 세우기"], horizontal=True)
        st.divider()
        
        if math_choice == "1. 알맞은 말과 기호 찾기":
            st.subheader("1. 알맞은 말과 기호 찾기")
            st.write
