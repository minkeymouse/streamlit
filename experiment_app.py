import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import openai
import time

# Initialize session state variables
if 'init_done' not in st.session_state:
    st.session_state.init_done = False
    st.session_state.current_round = 1
    st.session_state.responses = pd.DataFrame()

# Updated function to generate a random budget line
def generate_budget_line():
    I = random.uniform(100, 200)
    min_px = I / 100
    max_px = I / 50
    p_x = random.uniform(min_px, max_px)
    min_py = I / 100
    max_py = I / 50
    p_y = random.uniform(min_py, max_py)
    return p_x, p_y, I

# Function to plot the budget line with enhanced display
def plot_budget_line(p_x, p_y, choice_x, I):
    y = np.arange(0, 100, 0.1)
    x = (I - p_y * y) / p_x
    plt.plot(x, y, '-r')
    choice_y = (I - p_x * choice_x) / p_y
    expected_x = p_x * choice_x * 0.5
    expected_y = p_y * choice_y * 0.5
    plt.text(50, 50, f"Expected Outcome: \n X = {100 * expected_x:.2f} won and Y = {100 * expected_y:.2f} won \n (50% chance)", fontsize=12, fontweight='bold')
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title(f'Move slider to choose best outcome. X price: {p_x:.2f} Y price: {p_y:.2f}')
    plt.grid(True)
    return plt

# Function to get GPT advice, now including prices
def get_gpt_advice(participant_data):
    # Use the OpenAI API key from Streamlit secrets
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    # System and assistant messages
    messages = [
        {"role": "system", "content": "You are a decision making assistant for subject participating choice experiment. In each round, randomly generated budget line with prices for optioin x and y are given. Subject make their choice of how much they allocate on x given budget line. After all rounds, researcher will reward the subject by randomly choosing one of the rounds and one of the options with chosen round's price"},
        {"role": "assistant", "content": "Please give advice in Korean less then 200 words, less then 10 sentences. Make your advice short and coherent. Don't list previous responses from subject. Your must give the best advice to subject each round in making their choices as rational as possible with revealed preference theorey."}
    ]

    # Adding user messages from participant data
    for _, row in participant_data.iterrows():
        user_message = f"Round {row['Round']} choice: X = {row['Choice_X']}, Y = {row['Choice_Y']}, Prices: P_X = {row['P_X']}, P_Y = {row['P_Y']}, Total Income = {row['Total_Income']}"
        messages.append({"role": "user", "content": user_message})

    # Call the OpenAI API for a chat completion
    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    return chat_completion.choices[0].message.content

# App title and instructions
st.title("Economic Decision Making Experiment")

# Introductory page logic with unique form key
if not st.session_state.init_done:
    with st.form("init_form"):
        participant_id = st.text_input("Enter your participant ID")
        age = st.number_input("Enter your age", min_value=18, max_value=100, step=1)
        sex = st.selectbox("Select your sex", ["Male", "Female", "Other"])
        start_session = st.form_submit_button("Start Session")

    if start_session:
        st.session_state.participant_id = participant_id
        st.session_state.age = age
        st.session_state.sex = sex
        st.session_state.init_done = True
        st.session_state.current_round = 1
        st.session_state.p_x, st.session_state.p_y, st.session_state.total_income = generate_budget_line()
        st.session_state.treatment_group = True
        st.session_state.responses = pd.DataFrame(columns=["Participant_ID", "Age", "Sex", "Round", "Choice_X", "Choice_Y", "P_X", "P_Y", "Total_Income", "Time_Taken", "Treatment_Group"])
        st.session_state.start_time = time.time()

# Main experiment logic
if st.session_state.init_done:
    if st.session_state.current_round <= 20:
        st.write(f"### Round {st.session_state.current_round}")
        st.write(f"### Treatment: {'Treatment' if st.session_state.treatment_group else 'Control'}")
        
        choice_x = st.slider("Select your x and y", 0, 100, 50, key=f"x_{st.session_state.current_round}")
        fig = plot_budget_line(st.session_state.p_x, st.session_state.p_y, choice_x, st.session_state.total_income)
        st.pyplot(fig)

        if st.button("Confirm choice"):
            choice_y = (st.session_state.total_income - st.session_state.p_x * choice_x) / st.session_state.p_y
            end_time = time.time()
            time_taken = end_time - st.session_state.start_time

            new_row = {
                "Participant_ID": st.session_state.participant_id,
                "Age": st.session_state.age,
                "Sex": st.session_state.sex,
                "Round": st.session_state.current_round,
                "Choice_X": choice_x,
                "Choice_Y": choice_y,
                "P_X": st.session_state.p_x,
                "P_Y": st.session_state.p_y,
                "Total_Income": st.session_state.total_income,
                "Time_Taken": time_taken,
                "Treatment_Group": "Treatment" if st.session_state.treatment_group else "Control"
            }

            # Update the DataFrame with the new row
            st.session_state.responses = pd.concat([st.session_state.responses, pd.DataFrame([new_row])])

            if st.session_state.current_round < 20:
                st.session_state.current_round += 1
                st.session_state.p_x, st.session_state.p_y, st.session_state.total_income = generate_budget_line()
                st.session_state.start_time = time.time()
            else:
                # This else condition now only sets a flag to show the download button
                st.session_state.show_download = True

            if st.session_state.treatment_group and st.session_state.current_round > 10:
                participant_data = st.session_state.responses[st.session_state.responses["Participant_ID"] == st.session_state.participant_id]
                advice = get_gpt_advice(participant_data)
                st.write(advice)

    # Check for the flag to show the download button
    if st.session_state.get("show_download", False):
        st.write("Thank you for participating! Please download your responses.")
        # Convert DataFrame to CSV for download
        csv = st.session_state.responses.to_csv(index=False)
        # Create download button
        st.download_button(
            label="Download your responses",
            data=csv,
            file_name="experiment_responses.csv",
            mime="text/csv",
        )
        st.session_state.show_download = False  # Reset the flag





