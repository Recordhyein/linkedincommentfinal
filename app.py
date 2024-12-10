import streamlit as st
import os
from dotenv import load_dotenv
import anthropic

# 초기 설정
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.responses = []


# API 초기화
client = anthropic.Client(api_key=st.secrets["CLAUDE_API_KEY"])

def show_progress_steps(current_step: int):
    """진행 단계 표시"""
    steps = ["Profile", "Post", "Reflection", "Experience", "Value", "Review"]
    progress_html = '<div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin: 20px 0;">'
    
    for i, step in enumerate(steps, 1):
        if i < current_step:
            style = "color: #0A66C2; font-weight: bold;"
            icon = "✓"
        elif i == current_step:
            style = "color: #0A66C2; font-weight: bold;"
            icon = "⦿"
        else:
            style = "color: #666666;"
            icon = "○"
        
        progress_html += f'<span style="{style}">[{icon} {step}]</span>'
        if i < len(steps):
            progress_html += '<span style="color: #666666;">→</span>'
    
    progress_html += '</div>'
    st.markdown(progress_html, unsafe_allow_html=True)

def generate_question_and_examples(post_content, previous_responses=None, user_profile=None):
    """질문과 예시 답변 생성"""
    # 질문 생성
    if not previous_responses:
        prompt = f"""Given this LinkedIn post and user profile, generate:
        1. A thought-provoking question that helps identify what resonates personally and professionally
        2. Three example responses (2-3 sentences each)
        3. Key phrases/points they might consider
        
        Post: {post_content}
        Profile: {user_profile}
        
        Format: 
        QUESTION: [your question]
        EXAMPLES:
        1. [example 1]
        2. [example 2]
        3. [example 3]
        CONSIDER:
        - [key point 1]
        - [key point 2]
        - [key point 3]"""
    else:
        prompt = f"""Based on previous responses, generate:
        1. A follow-up question that builds on their thoughts
        2. Three potential ways to expand their response
        3. Key points to consider
        
        Post: {post_content}
        Previous Responses: {previous_responses}
        
        Follow same format as above."""

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    return response.content[0].text.strip()

def main():
    st.title("LinkedIn Comment Crafter")
    
    if st.session_state.step > 1:
        show_progress_steps(st.session_state.step)
    
    # 사용자 프로필 입력
    if st.session_state.step == 1:
        st.header("Your Professional Profile")
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name")
                title = st.text_input("Role", placeholder="e.g. Senior Product Manager")
            with col2:
                industry = st.selectbox(
                    "Industry",
                    ["Technology", "Healthcare", "Finance", "Education", 
                     "Marketing", "Consulting", "Other"]
                )
                expertise = st.text_area(
                    "Areas of Expertise",
                    placeholder="Your key experiences and skills...",
                    height=100
                )
            
            if st.form_submit_button("Continue") and all([name, title, expertise]):
                st.session_state.profile = {
                    "name": name,
                    "title": title,
                    "industry": industry,
                    "expertise": expertise
                }
                st.session_state.step = 2
                st.rerun()
    
        # LinkedIn 포스트 입력
    elif st.session_state.step == 2:
        st.header("What post would you like to comment on?")
        post = st.text_area(
            "Paste the LinkedIn post here",
            height=200,
            placeholder="Paste the complete post content..."
        )
        
        if st.button("Continue") and post:
            st.session_state.post = post
            st.session_state.step = 3
            st.rerun()
    
    # 질문과 답변 단계
    elif 3 <= st.session_state.step <= 5:
        step_titles = [
            "What resonates with you?",
            "Connect to your experience",
            "Add unique value"
        ]
        current_step = st.session_state.step - 3
        
        st.header(step_titles[current_step])
        
        # 질문과 예시 생성
        result = generate_question_and_examples(
            st.session_state.post,
            st.session_state.responses if current_step > 0 else None,
            st.session_state.profile
        )
        
        # 결과 파싱
        sections = result.split("\n\n")
        question = sections[0].replace("QUESTION: ", "").strip()
        examples = [ex.strip() for ex in sections[1].replace("EXAMPLES:\n", "").split("\n")]
        tips = sections[2].replace("CONSIDER:\n", "").split("\n")
        
        st.write(question)
        
        # 텍스트 입력 영역
        response = st.text_area(
            "Your response",
            height=200,
            key=f"response_{current_step}"
        )
        
        # 예시와 팁 (아래에 표시)
        with st.expander("💡 Examples and tips to help you craft your response"):
            for i, example in enumerate(examples, 1):
                st.markdown(f"**Example {i}**")
                if st.button(f"Use this", key=f"example_{i}"):
                    st.session_state[f"response_{current_step}"] = example
                st.write(example)
                st.write("---")
            
            st.markdown("**Key points to consider:**")
            for tip in tips:
                st.write(tip)
        
        # Continue 버튼
        if st.button("Continue" if current_step < 2 else "Create Draft"):
            if response:
                st.session_state.responses.append(response)
                st.session_state.step += 1
                st.rerun()
    
    elif st.session_state.step == 6:
        st.header("Review and Finalize")
        
        # 톤 선택 섹션
        st.write("Select commenting tone:")
        
        # 가로로 배치된 라디오 버튼 스타일
        st.markdown("""
            <style>
            div.row-widget.stRadio > div {
                flex-direction: row;
                align-items: stretch;
            }
            div.row-widget.stRadio > div[role="radiogroup"] > label {
                background-color: white;
                border: 1px solid #0A66C2;
                border-radius: 20px;
                padding: 8px 16px;
                margin: 4px 8px;
                display: flex;
                align-items: center;
                font-size: 15px;
                transition: all 0.2s;
            }
            div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
                background-color: #E7F3FF;
            }
            div.row-widget.stRadio > div[role="radiogroup"] label[data-baseweb="radio"] {
                background-color: transparent;
                border: none;
            }
            div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child {
                display: none;
            }
            </style>
        """, unsafe_allow_html=True)

        tones = {
            "💼 Professional": "Formal and business-focused",
            "🤝 Collaborative": "Engaging and solution-oriented",
            "🎓 Expert": "Authoritative and analytical",
            "💪 Supportive": "Encouraging and constructive"
        }

        selected_tone = st.radio(
            "Select tone",
            list(tones.keys()),
            label_visibility="collapsed",
            horizontal=True,
            help="\n".join([f"{k}: {v}" for k, v in tones.items()])
        )
        
        # 선택된 톤에서 이모지 제거
        selected_tone_clean = selected_tone.split()[1]
        
        # 댓글 생성
        prompt = f"""Create a {selected_tone_clean.lower()} LinkedIn comment that:
        1. Integrates these responses thoughtfully: {st.session_state.responses}
        2. Maintains professional LinkedIn standards
        3. Shows authentic engagement with the original post
        4. Includes a relevant question or discussion point
        5. Is concise yet impactful
        
        Original post: {st.session_state.post}"""
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        comment = response.content[0].text.strip()
        
        st.text_area(
            "Your comment is ready to post",
            value=comment,
            height=200
        )
        
        if st.button("Start Over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
   main()
