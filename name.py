import streamlit as st
import random
import time

def bird_guessing_game():
    st.header("🦅 The AI Challenge: Can you beat the Nexus?")
    
    # 1. Setup session state so the image doesn't change when the user clicks 'Guess'
    if 'current_bird_img' not in st.session_state:
        # In a real app, this would be a random choice from your 'assets/' folder
        st.session_state['current_bird_img'] = "bird_aerial_1.jpg" 
        st.session_state['actual_count'] = 42 # The 'Ground Truth' from your data
        st.session_state['ai_guess'] = 39     # What the Roboflow API returned

    col_img, col_guess = st.columns([2, 1])

    with col_img:
        st.image(st.session_state['current_bird_img'], caption="Aerial view of South Biloxi Shoreline")

    with col_guess:
        user_guess = st.number_input("How many birds do you see?", min_value=0, step=1)
        if st.button("Submit Guess"):
            st.session_state['game_submitted'] = True

    # 2. The Big Reveal
    if st.session_state.get('game_submitted'):
        st.divider()
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.markdown(f"### Your Guess: **{user_guess}**")
            diff = abs(user_guess - st.session_state['actual_count'])
            st.write(f"You were off by {diff} birds!")

        with res_col2:
            with st.spinner("AI is analyzing pixels..."):
                time.sleep(1.5) # Maurice's thinking time
                st.markdown(f"### AI Guess: **{st.session_state['ai_guess']}**")
                # Here you could show the version of the image with bounding boxes
                st.image("bird_aerial_1_detected.jpg", caption="AI detection view")