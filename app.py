import streamlit as st
import google.generativeai as genai
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile

st.set_page_config(page_title="EPUB 요약 에이전트", page_icon="📚")
st.title("📚 EPUB 도서 요약 에이전트")

# API 키 입력창
api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if api_key:
    genai.configure(api_key=api_key)

# EPUB 텍스트 추출 함수
def extract_text_from_epub(epub_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
        tmp_file.write(epub_file.getvalue())
        tmp_path = tmp_file.name

    book = epub.read_epub(tmp_path)
    text_content = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text_content.append(soup.get_text())
            
    return "\n\n".join(text_content)

# 파일 업로드
uploaded_file = st.file_uploader("요약할 EPUB 파일을 업로드하세요", type=["epub"])

if uploaded_file and api_key:
    if st.button("책 요약하기"):
        with st.spinner("책 내용을 분석하고 요약하는 중입니다... (1~2분 소요)"):
            try:
                # 텍스트 추출
                full_text = extract_text_from_epub(uploaded_file)
                
                # 무료 토큰 한도 초과 방지 (150,000자 절삭)
                truncated_text = full_text[:150000]
                
                # 계정에서 지원하는 모델 목록 자동 조회
                available_models = [
                    m.name for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods
                ]
                
                # 모델 자동 선택 (gemini-3.8-flash 또는 사용 가능한 flash 모델)
                selected_model_name = next(
                    (m for m in available_models if '3.8-flash' in m or 'flash' in m), 
                    available_models[0]
                )
                
                model = genai.GenerativeModel('gemini-3.8-flash')
                
                prompt = f"""
                다음은 도서의 내용 일부입니다. 아래 형식에 맞춰 한글로 상세하게 요약해주세요.

                1. **한 줄 요약**: 전체 핵심 메시지
                2. **주요 등장인물/개념**: 핵심 인물이나 키워드 정리
                3. **핵심 줄거리 및 내용**: 주요 스토리 단원별 내용 요약
                4. **핵심 시사점 및 인사이트**: 이 내용에서 얻을 수 있는 결론

                [도서 텍스트]
                {truncated_text}
                """
                
                response = model.generate_content(prompt)
                
                st.subheader("📖 요약 결과")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
elif uploaded_file and not api_key:
    st.warning("왼쪽 사이드바에 Gemini API Key를 먼저 입력해주세요.")
