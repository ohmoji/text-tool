import streamlit as st
import re

# ==============================================================================
# 1. 💡 텍스트 처리 핵심 로직 함수
#    - 대사(Dialogue) 패턴을 토큰화하여 먼저 분리한 후, 스크립트(Script)를 처리합니다.
# ==============================================================================
def parse_and_process_text(input_text, use_prefix, script_prefix, dialogue_prefix):
    
    # 대사 패턴 정규식: "이름 : "문장"" (이름, 문장을 그룹으로 캡처)
    dialogue_pattern = r'(\w+)\s*:\s*"(.*?)"'
    
    dialogue_map = {} # 처리된 대사를 저장할 맵
    dialogue_counter = 0

    # 1. Dialogue Replacer: 대사 패턴을 찾아 처리 후 임시 토큰으로 치환
    def dialogue_replacer(match):
        nonlocal dialogue_counter
        # 캡처된 그룹: name (이름), text (대사 내용)
        name, text = match.groups()
        token = f"[[DIALOGUE_{dialogue_counter}]]"
        
        # 대사 처리 규칙 적용: '!!이름 대사 내용'
        dialogue_line = f"!!{name.strip()} {text.strip()}"
        
        # Prefix 적용 (활성화된 경우)
        if use_prefix:
            dialogue_line = f"{dialogue_prefix}{dialogue_line}"
            
        dialogue_map[token] = dialogue_line
        dialogue_counter += 1
        return token

    # 본문에서 대사를 찾아 토큰으로 치환하고 dialogue_map에 저장
    tokenized_script = re.sub(dialogue_pattern, dialogue_replacer, input_text)
    
    # 2. 스크립트(Script) 및 토큰 처리
    
    # 토큰화된 스크립트를 줄바꿈(\n) 기준으로 분리 (단락/문장 단위로 처리)
    script_paragraphs = tokenized_script.split('\n')
    
    final_output_lines = []
    
    for p in script_paragraphs:
        p = p.strip()
        if not p:
            continue
            
        # 해당 문장이 순수한 Dialogue 토큰인 경우 (이미 처리 완료)
        if re.match(r'\[\[DIALOGUE_\d+\]\]', p):
            # 맵에서 처리된 최종 대사 내용을 가져와 추가
            final_output_lines.append(dialogue_map.get(p, p))
            continue
            
        # 스크립트 부분: 줄바꿈 규칙 적용
        # 규칙: '.' 또는 ',' 뒤에 공백이 있으면 그 자리를 줄바꿈으로 치환 (예: ", " -> ",\n")
        # 정규식: ([.,]) 는 점이나 쉼표를 찾고 (\1)로 다시 사용하며, \s+는 공백 1개 이상을 찾음.
        script_final = re.sub(r'([.,])\s+', r'\1\n', p)
        
        # 줄바꿈이 적용된 스크립트를 다시 줄 단위로 분리
        script_lines = script_final.split('\n')
        
        # 각 스크립트 줄에 Prefix 적용 및 최종 결과에 추가
        for line in script_lines:
            if line.strip():
                prefixed_line = line.strip()
                
                # Script Prefix 적용 (활성화된 경우)
                if use_prefix:
                    prefixed_line = f"{script_prefix}{prefixed_line}"
                
                # 스크립트 중간에 남아있을 수 있는 Dialogue 토큰을 최종 대사로 치환
                def final_replacer(match):
                    token = match.group(0)
                    return dialogue_map.get(token, token)
                    
                processed_line = re.sub(r'\[\[DIALOGUE_\d+\]\]', final_replacer, prefixed_line)
                
                final_output_lines.append(processed_line)

    return "\n".join(final_output_lines)

# ==============================================================================
# 2. 🖥️ Streamlit 인터페이스 구성
# ==============================================================================
def main():
    st.set_page_config(layout="wide")

    st.title('📚 스크립트/대사 자동 처리 도구 (Python)')
    st.markdown('긴 텍스트를 붙여넣으면, **스크립트**와 **대사** 규칙에 따라 자동 처리됩니다.')
    st.markdown('---')

    # --- 처리 기준 설명 ---
    st.info("""
    **✅ 현재 적용된 처리 규칙:**
    1.  **대사 (Dialogue):** `이름 : "문장"` 형태는 `!!이름 문장` 형태로 치환되며 줄바꿈되지 않습니다.
    2.  **스크립트 (Script):** 일반 문장은 `.` 또는 `,` 뒤에 공백이 있을 경우 (예: `어쩌고, `) 그 자리에서 줄바꿈됩니다.
    """)

    # --- 추가 기능 설정 섹션 (Prefix) ---
    with st.expander("🛠️ 추가 기능: 앞 문자열(Prefix) 설정", expanded=True):
        # Prefix 기능 활성화 체크박스
        use_prefix = st.checkbox("스크립트/대사 앞에 사용자 정의 문자열 추가 (Prefix 기능 활성화)", value=False)
        
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
    example_input = '어쩌고 저쩌고, 어쩌고 저쩌고. 또 다른 스크립트 문장입니다. Smith : "Hello. How are you?" 이 문장은 스크립트입니다.'
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