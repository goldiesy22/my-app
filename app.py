import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
import io

# 💡 깃허브 유출 방지: API 키를 직접 적지 않고 Streamlit의 비밀 금고(Secrets)에서 가져옵니다.
API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="맞춤형 기초학력 지원 앱", layout="wide")

# ==========================================
# 세션 상태(Session State) 초기화
# ==========================================
if "show_slash_hint" not in st.session_state:
    st.session_state.show_slash_hint = False

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
            st.write("화면의 글자를 보고 또박또박 읽어보자!")
            
            target_word = "보" # 연습할 정답 글자
            st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{target_word}</h1>", unsafe_allow_html=True)
            
            st.info("👇 마이크를 누르고 **아이콘이 빨간색으로 변하면** 말하세요. (말한 뒤 마이크를 한 번 더 누르면 완료됩니다)")
            
            audio_bytes = audio_recorder(
                text="클릭해서 녹음 시작", 
                icon_size="2x", 
                pause_threshold=10.0
            )
            
            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
                
                with st.spinner("AI 선생님이 목소리를 듣고 있어요... 🤖"):
                    audio_file = io.BytesIO(audio_bytes)
                    audio_file.name = "record.wav"
                    
                    try:
                        # 음성 인식(STT) - 한국어 고정 및 한 글자 인식용 프롬프트 힌트 제공
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio_file,
                            language="ko",
                            prompt="보, 바, 가, 나, 다. 짧은 한 글자 단독 발음입니다."
                        )
                        
                        # 공백이나 특수기호 제거
                        spoken_text = transcript.text.strip().replace(" ", "").replace(".", "")
                        st.info(f"🎤 학생이 낸 소리: **{spoken_text}**")
                        
                        if target_word in spoken_text: 
                            st.success("🎉 참 잘했어요! 정확하게 읽었네요!")
                        else:
                            # 자음, 모음 분리 로직
                            if len(spoken_text) > 0 and '가' <= spoken_text[0] <= '힣':
                                CHOSUNG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
                                JUNGSUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
                                
                                target_code = ord(target_word) - ord('가')
                                target_cho = CHOSUNG[target_code // 588]
                                target_jung = JUNGSUNG[(target_code % 588) // 28]
                                
                                spoken_char = spoken_text[0]
                                spoken_code = ord(spoken_char) - ord('가')
                                spoken_cho = CHOSUNG[spoken_code // 588]
                                spoken_jung = JUNGSUNG[(spoken_code % 588) // 28]
                                
                                if spoken_cho != target_cho and spoken_jung == target_jung:
                                    st.error("💡 아쉽지만 자음을 잘못 읽었어요.")
                                    st.markdown(f"<h3 style='text-align: center;'>정답은 <span style='color: red;'>{target_cho}</span> + {target_jung} 예요. 다시 읽어볼까요?</h3>", unsafe_allow_html=True)
                                elif spoken_cho == target_cho and spoken_jung != target_jung:
                                    st.error("💡 아쉽지만 모음을 잘못 읽었어요.")
                                    st.markdown(f"<h3 style='text-align: center;'>정답은 {target_cho} + <span style='color: blue;'>{target_jung}</span> 예요. 다시 읽어볼까요?</h3>", unsafe_allow_html=True)
                                else:
                                    st.error("💡 자음과 모음을 모두 잘못 읽었어요.")
                                    st.markdown(f"<h3 style='text-align: center;'>정답은 <span style='color: red;'>{target_cho}</span> + <span style='color: blue;'>{target_jung}</span> 예요. 모양을 잘 보세요!</h3>", unsafe_allow_html=True)
                            else:
                                st.error("💡 무슨 말인지 잘 못 들었어요. 다시 크고 또박또박 말해볼까요?")
                                
                    except Exception as e:
                        st.warning("⚠️ 녹음된 소리가 너무 짧거나 마이크가 인식되지 않았어요. 마이크 연결과 권한을 확인해 주세요!")
                            
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
                        st.warning("⚠️ 녹음된 소리가 너무 짧거나 마이크가 인식되지 않았어요. 마이크 상태를 확인해 주세요!")

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
            st.write("두 숫자 사이에 들어갈 알맞은 말을 골라보자!")
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_a:
                st.markdown("<h1 style='text-align: center;'>5</h1>", unsafe_allow_html=True)
            with col_b:
                user_answer = st.selectbox("어느 쪽이 더 클까?", ["선택하세요", "크다 (>)", "작다 (<)", "같다 (=)"])
            with col_c:
                st.markdown("<h1 style='text-align: center;'>3</h1>", unsafe_allow_html=True)
            
            if st.button("정답 확인하기", key="math_btn_1"):
                if user_answer == "크다 (>)":
                    st.success("정답이야! 5가 3보다 크지!")
                elif user_answer == "선택하세요":
                    st.warning("알맞은 말을 먼저 선택해 줘.")
                else:
                    st.error("아쉽지만 다시 한번 생각해 볼까?")
                
        elif math_choice == "2. 차근차근 식 세우기":
            st.subheader("2. 차근차근 식 세우기")
            st.write("사과가 3개, 배가 2개 있습니다. 모두 몇 개일까요?")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.text_input("첫 번째 숫자", key="m_num1")
            with col2:
                st.selectbox("기호", ["+", "-", "*", "/"], key="m_op")
            with col3:
                st.text_input("두 번째 숫자", key="m_num2")
            with col4:
                st.markdown("<h3 style='text-align: center; margin-top: 30px;'>=</h3>", unsafe_allow_html=True)
            with col5:
                st.text_input("정답", key="m_ans")
                
            if st.button("정답 확인하기", key="math_btn_2"):
                st.success("여기에 AI 선생님의 친절한 맞춤형 피드백이 뜰 거야!")

# ==========================================
# 2. 교사용 화면
# ==========================================
elif mode == "교사용":
    st.title("👩‍🏫 교사 대시보드")
    st.write("학생들의 학습 현황과 성장 기록을 확인합니다.")
    st.info("이곳에는 학생이 자주 틀리는 글자나 연산 오류를 분석한 데이터가 표시될 예정입니다.")