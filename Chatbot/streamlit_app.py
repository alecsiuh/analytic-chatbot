import streamlit as st
from datetime import datetime 

import os
from OpenAi.openai_client import OpenAIClient
import pandas as pd
import io
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Get the API key from the environment
api_key = os.getenv("OPENAI_API_KEY")

# Initialize your chatbot client with the API key from the environment
chatbot = OpenAIClient(api_key=api_key)

# Authorize Google Sheets API
def init_google_sheets_client(json_credentials):
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_credentials, scope)
    return gspread.authorize(credentials)

# Load service account credentials from Streamlit secrets
json_credentials = st.secrets["gcp_service_account"]

# Initialize the client
gc = init_google_sheets_client(json_credentials)

# Open the Google Sheet
spreadsheet_name = 'Feedback' 
worksheet_name = 'Sheet1' 
sheet = gc.open(spreadsheet_name).worksheet(worksheet_name)

### STYLING ###
# Update for deployed app
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
        response = chatbot.get_gpt3_response(prompt)

    # if the assistant response is a dataframe, display it as an interactive table
    if isinstance(response, pd.DataFrame):
        st.dataframe(response) 
        st.session_state.messages.append({"role": "assistant", "content": f"```{response.head(5)}```"})
    elif isinstance(response, plt.Figure):   
        st.pyplot(response)
        st.session_state.messages.append({"role": "assistant", "content": "Figure displayed"})
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

        data = [feedback_text, emoji_to_store, current_date_str, current_time_str]

        # Display a success message
        st.success("Feedback submited successfully!")