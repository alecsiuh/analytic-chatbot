import streamlit as st
from datetime import datetime

import os
import re
from OpenAi.openai_client import OpenAIClient
import pandas as pd
import io
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials

# Get the API key from the environment
api_key = os.getenv("OPENAI_API_KEY")

# Initialize your chatbot client with the API key from the environment
# Initialize chatbot if not already initialized
if "chatbot" not in st.session_state:
    st.session_state.chatbot = OpenAIClient(api_key=api_key)


# Authorize Google Sheets API
def init_google_sheets_client(json_credentials):
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(json_credentials, scopes=scope)
    return gspread.authorize(credentials)


# Load service account credentials from Streamlit secrets
json_credentials = st.secrets["gcp_service_account"]

# Open the Google Sheet
spreadsheet_name = 'https://docs.google.com/spreadsheets/d/18_AAt6mSaEaCPraqX8Tm_nDrTbUYAG-zva8XrxXS9rQ/edit?usp=sharing'
worksheet_name = 'Sheet1'

### STYLING ### 
st.markdown(
    """
    <style>
    .st-emotion-cache-1xw8zd0.e10yg2by1 {
        position: relative;
        margin-top: 120%;
        bottom: 0;
        width: 100%;
    }
    .st-emotion-cache-16txtl3.eczjsme4 {
        padding-top: 0;
        padding-bottom: 0;
        height: 100%;
    }
    .st-emotion-cache-k7vsyb.e1nzilvr2 {
        margin-top: 1em;
    }
    .st-emotion-cache-ch5dnh.ef3psqc5, .st-emotion-cache-6q9sum.ef3psqc4 {
        visibility: hidden;
    }
    .st-emotion-cache-0.1f1d6gn0 {
        border: none; 
    } 
    .st-at.st-au.st-av.st-aw.st-ae.st-ag.st-ah.st-af.st-c2.st-bo.st-c3.st-c4.st-c5.st-c6.st-am.st-an.st-ao.st-ap.st-c7.st-ar.st-as.st-bb.st-ax.st-ay.st-az.st-b0.st-b1 {
        width: 70%; 
        justify-content: space-between;
    } 
    .st-emotion-cache-bho8sy.eeusbqq1 {
        background-color: #7547FF;
    }
    .st-emotion-cache-1ghhuty.eeusbqq1 { 
        background-color: #E5B7E5;
    } 
    .st-emotion-cache-6qob1r.eczjsme3 { 
        border-top-right-radius: 1rem; 
        border-bottom-right-radius: 1rem;
        color: white;
        background-color: #7547FF;
    }   
    .st-emotion-cache-1sva07 {
        display: none;
    }
    .st-emotion-cache-k7vsyb.e1nzilvr2 {
        color: #FFFFFF;
    } 
    .st-emotion-cache-16txtl3 h1, .st-emotion-cache-16txtl3 h2, .st-emotion-cache-l9bjmx p {
        color: #FFFFFF;
    }
    .st-emotion-cache-163zt37.ef3psqc7 {
        color: #7547FF;
    }
    .stAlert {
        background-color: aliceblue;
        border-radius: 0.5rem;
    }
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("The Lab - FAN app")

st.sidebar.markdown(
    """
    Welcome to our proof of concept chatbot. The aim of this project is to make datasets talk by holding a conversation
     with a chatbot using natural language processing techniques and getting insights out of data in the process. Feel 
     free to mess with the chatbot and experiment with it. As of now, our chatbot is capable of suggesting topics based
      on the datasets available to it. It can also find datasets the best fit a topic or subject you are interested in 
      if it is available. The chatbot will show you the selected dataset if asked to and is able to preform analytics 
      operations on the datasets. As of now the chatbot is still unable to provide graphs or visual aids but we are 
      working on implementing this feature as soon as possible.
""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello there! How can I assist"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

buf = io.BytesIO()
# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user input in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)  # Display the user's input 
        response = st.session_state.chatbot.get_gpt3_response(prompt)

    # if the assistant response is a dataframe, display it as an interactive table
    if isinstance(response, pd.DataFrame):
        st.dataframe(response)
        st.session_state.messages.append({"role": "assistant", "content": f"```{response.head(5)}```"})
        # Check if the response is a tuple
    # if isinstance(response, tuple):
    #     result, df = response
    #
    #     pattern = r"python(.*?)"
    #     match = re.search(pattern, result, re.DOTALL)
    #     print(result)
    #     if match:
    #         code_snippet = match.group(1).strip()
    #         print("Extracted code snippet:")
    #         print(code_snippet)
    #     else:
    #         print("Code snippet not found in the text.")
    else:
        # Display assistant response in chat message container and add to chat history
        with st.chat_message("assistant"):
            st.markdown(response)  # Display the chatbot response
        st.session_state.messages.append({"role": "assistant", "content": response})

### FEEDBACK ###
emoji_options = ["😀 Happy", "😐 Neutral", "😒 Dissatisfied", "😠 Angry"]

with st.sidebar:
    form_expander = st.expander("Feedback", expanded=False)

# Feedback form
with form_expander:
    with st.form(key="feedback_form", clear_on_submit=True):
        st.header("Feedback Form")
        feedback_text = st.text_area(label="Please provide your feedback here:")
        selected_emoji = st.selectbox("How was your experience?", emoji_options)
        emoji_to_store = selected_emoji[0]
        submit_button = st.form_submit_button(label="Submit")

    if submit_button:
        # insert the time the feedback was submitted
        current_date = datetime.now().date()
        current_time = datetime.now().time()

        # Convert date and time to string format to store in Google Sheets
        current_date_str = current_date.isoformat()
        current_time_str = current_time.strftime('%H:%M:%S')

        client = init_google_sheets_client(json_credentials)
        sheet = client.open_by_url(spreadsheet_name).worksheet(worksheet_name)
        sheet.append_row([feedback_text, emoji_to_store, current_date_str, current_time_str])
        st.success("Feedback submitted successfully!")
        all_values = sheet.get_all_values()
        for row in all_values:
            print(row)
