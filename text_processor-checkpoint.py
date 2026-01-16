import streamlit as st
import re

# ==============================================================================
# 1. 텍스트 처리 
# ==============================================================================
def parse_and_process_text(input_text, use_prefix, script_prefix, dialogue_prefix):
    
    # 대사 패턴 정규식: "이름 : "문장"" 
    dialogue_pattern = r'([\w\s\(\)]+?)\s*:\s*["“”]?(.*?)["“”]?(?=\n|$|\[\[META)'
    
    dialogue_map = {}
    dialogue_counter = 0

    def dialogue_replacer(match):
        nonlocal dialogue_counter
        name, text = match.groups()
        token = f"[[DIALOGUE_{dialogue_counter}]]"
        
        dialogue_line = f"!!{name.strip()} {text.strip()}"
        
        if use_prefix:
            dialogue_line = f"{dialogue_prefix}{dialogue_line}"
            
        dialogue_map[token] = dialogue_line
        dialogue_counter += 1
        return token

    tokenized_script = re.sub(dialogue_pattern, dialogue_replacer, input_text)
    
    script_paragraphs = tokenized_script.split('\n')
    
    final_output_lines = []
    
    for p in script_paragraphs:
        p = p.strip()
        if not p:
            continue
        p = re.sub(r'\s*(\[\[DIALOGUE_\d+\]\])\s*', r'\n\1\n', p)
        
        if re.match(r'\[\[DIALOGUE_\d+\]\]', p):
            final_output_lines.append(dialogue_map.get(p, p))
            continue
            
        script_final = re.sub(r'([.,?!…])\s+', r'\1\n', p)
        script_lines = script_final.split('\n')
        
        for line in script_lines:
            if line.strip():
                prefixed_line = line.strip()
                
                if use_prefix:
                    prefixed_line = f"{script_prefix}{prefixed_line}"
                
                def final_replacer(match):
                    token = match.group(0)
                    return dialogue_map.get(token, token)
                    
                processed_line = re.sub(r'\[\[DIALOGUE_\d+\]\]', final_replacer, prefixed_line)
                
                final_output_lines.append(processed_line)

    return "\n".join(final_output_lines)

# ==============================================================================
# 2. Streamlit 인터페이스 구성
# ==============================================================================
def main():
    st.set_page_config(layout="wide")

    st.title('Roll-BBANG 스크립트/대사 자동 처리')
    st.markdown('긴 텍스트를 붙여넣으면, **스크립트**와 **대사** 규칙에 따라 자동 처리됩니다.')
    st.markdown('---')

    # --- 처리 기준 ---
    st.info("""
    **✅ 사용 방법:**
    1.  **스크립트 (Script):** 일반 문장은 문장 기호를 기준으로 줄바꿈됩니다. 
    2.  **대사 (Dialogue):** `이름 : "문장"`, `이름 : 문장` 형태는 `!!이름 문장` 형태로 치환되며 중간에 줄바꿈되지 않습니다.
    3. Prefix를 활성화하고 스크립트 앞에 `!... /desc `, `/desc`, 대사 앞에 `!... ` 등을 넣어 활용하시면 됩니다. (롤20에서 사용 시 Prefix 맨 뒤 공백 필수)
    *양천일염 님의 롤20 API as_autofiller.js (`https://kibkibe.github.io/roll20/`) 명령어 사용을 가정하고 대사 처리하였습니다.*
    """)

    # --- (Prefix) ---
    with st.expander("🛠️ 앞 문자열(Prefix) 설정", expanded=True):
        # Prefix 기능 활성화 체크박스
        use_prefix = st.checkbox("스크립트/대사 앞에 문자 추가 (Prefix 기능)", value=False)
        
        col_script, col_dialogue = st.columns(2)
        
        with col_script:
            # 스크립트 Prefix 입력
            script_prefix = st.text_input(
                '스크립트 앞에 붙일 문자열:',
                value='[S] ',
                max_chars=30,
                disabled=not use_prefix,
                help="일반 문장 앞에 추가됩니다."
            )
            
        with col_dialogue:
            # 대사 Prefix 입력
            dialogue_prefix = st.text_input(
                '대사 앞에 붙일 문자열:',
                value='[D] ',
                max_chars=30,
                disabled=not use_prefix,
                help="!!이름 문장 앞에 추가됩니다."
            )

    st.markdown('---')

    # --- 텍스트 입력 및 실행 섹션 ---
    example_input = '예를 들어서, 이런 것은 스크립트로 분류 됩니다! 또 다른 스크립트 문장입니다. \n Theo : "Hello. How are you?" \n 위 문장은 대사로 분류되어 중간에 줄바꿈되지 않습니다. 이런 식으로 문단을 통으로 넣으면, 알아서 롤20 채팅창에 붙여넣기 좋게 나눠줍니다.'
    user_input = st.text_area(
        "여기에 **긴 본문 전체**를 붙여넣으세요:",
        height=400,
        placeholder=example_input
    )

    if st.button('🚀 텍스트 처리 및 변환'):
        if user_input.strip():
            
            # 텍스트 처리 함수 실행
            final_processed_text = parse_and_process_text(
                input_text=user_input,
                use_prefix=use_prefix,
                script_prefix=script_prefix,
                dialogue_prefix=dialogue_prefix
            )

            st.subheader('✅ 처리 결과')
            st.code(final_processed_text, language='text')

        else:
            st.warning('텍스트 입력창에 본문을 넣어주세요.')

if __name__ == '__main__':
    main()
