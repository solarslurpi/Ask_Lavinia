import streamlit as st
from llama_index import Prompt
import sqlite3
from logging_handler import LoggingHandler
import logging

logger = LoggingHandler(log_level=logging.DEBUG)


@st.cache_data
def get_questions(visible=True):
    # Open a connection to the SQLite database
    conn = sqlite3.connect("askl.db")
    # Get a cursor to retrieve rows
    c = conn.cursor()
    query_str = "SELECT question, response FROM qa_table"
    if visible:
        query_str = query_str + " WHERE visible = 1"
    try:
        c.execute(query_str)
    except sqlite3.OperationalError as e:
        pass  # No qa db is empty.
        # if e.args[0] == "table 'qa_table' does not exist":
        #     print("The qa_table does not exist.")
        # else:
        #     raise e

    # Fetch all rows from the result of the SELECT statement
    records = c.fetchall()

    # Close the connection to the SQLite database
    conn.close()

    return records


def ui_display_questions():
    records = get_questions()
    questions = [rec[0] for rec in records]
    responses = {rec[0]: rec[1] for rec in records}

    st.sidebar.header("Previous Questions")
    for question in questions:
        if st.sidebar.button(question):
            st.markdown(f"Response: {responses[question]}")


# Show summary in a sidebar:


def ui_add_sidebar():
    st.sidebar.markdown(
        "**:blue[2022-2024 Evergreen Employment Agreement with Nurses Union]**"
    )
    st.sidebar.markdown("# Summary")
    st.sidebar.markdown(
        "This document is an employment agreement between EvergreenHealth and the Washington State Nurses Association that outlines the wages, hours of work, and conditions of employment for nurses employed by EvergreenHealth. It covers topics such as membership and dues, management rights, definitions, employment practices, seniority, layoff and recall, hours of work and overtime, compensation, holidays, vacations, sick leave, leaves of absence, employee benefits, committees, no strike-no lockout, grievance procedure, and general provisions. "
    )
    ui_display_questions()
    # st.sidebar.markdown("# Examples of questions the document can answer")
    # st.sidebar.markdown("Questions that this document can answer include:")
    # st.sidebar.markdown("- What are the wages and hours of work? ")
    # st.sidebar.markdown("- What are the conditions of employment? ")
    # st.sidebar.markdown("- What are the seniority, layoff and recall policies?")
    # st.sidebar.markdown("- What are the overtime policies?")
    # st.sidebar.markdown("- What are the compensation policies?")
    # st.sidebar.markdown("- What is the grievance procedure?")
    # st.sidebar.markdown("- What are the holiday policies?")
    # st.sidebar.markdown("- What are the sick leave policies?")
    # st.sidebar.markdown("- What are the vacation policies?")
    # st.sidebar.markdown("- What is the no strike-no lockout policy?")


# I'm not using this because it got overly complicated to add.
# The intent is to show a yes and no button to be pressed after the answer was given.
# Then return whether the question was useful or not.
def ui_add_useful_buttons(prompt_text: str) -> bool:
    if "useful" not in st.session_state:
        st.session_state.useful = None
    if "not_useful" not in st.session_state:
        st.session_state.not_useful = None

    with st.form(key="quality_form"):
        col1, col2 = st.columns([1, 3])
        st.write(prompt_text)
        st.session_state.useful = col1.form_submit_button("Yes")
        st.session_state.not_useful = col2.form_submit_button("No")
        if st.session_state.useful:
            return True
        elif st.session_state.not_useful:
            return False


def ui_add_header():
    st.header("👩‍⚕️ Ask Lavinia")
    # Create two columns
    col1, col2 = st.columns([1, 3])
    # Place the image in the first column
    col1.image("lavinia_dock.jpg")
    # Place the button in the second column
    link = """
    <a href="https://en.wikipedia.org/wiki/Lavinia_Dock" target="_blank">
        <input type="button" value="About Lavinia" style="color: white; background-color: #3399ff; border: none; border-radius: 15px; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 2px; cursor: pointer; transition-duration: 0.4s;">
    </a>
    """
    col2.markdown(link, unsafe_allow_html=True)
    st.subheader("About the Employment Agreement with Evergreen")


@st.cache_data
def ui_build_prompt():
    PROMPT_TMPL_STR = (
        "Given this context information --> {context_str} <-- \n"
        "and no prior knowledge, answer the question: {query_str}.\n"
        "If you do not think this is a question, return and let the user know in kind words to rephrase the question since you didn't understand it.\n"
        "If the question has nothing to do with a question one would ask a hospital and Nurses' unions employment contract, return and kindly let the user know."
        "The response should adhere to these guidelines:\n"
        "Start by writing out what the question was: {query_str} then:\n"
        "- Provide the answer as a markdown formatted unordered (bulleted) list. \n"
        "- Each bullet point should include a fact and the article number where the fact is discussed.\n"
        "- Make sure each sub-answer on the list appears on a new line using markdown unordered list format.\n"
        "- The text should be comprehensible to a high school student.\n"
    )

    return Prompt(PROMPT_TMPL_STR)


import base64


@st.cache_data
def ui_get_pdf_display(filename: str):
    try:
        with open(filename, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="800" type="application/pdf"></iframe>'
            logger.INFO("Opened the Evergreen pdf file for display.")
            return pdf_display
    except FileNotFoundError:
        logger.ERROR(f("PDF file {filename} could not be opened."))
    except IOError:
        logger.ERROR("An error occurred while reading the PDF file {filename}.")

    return pdf_display
