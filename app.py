import datetime
import os
import pathlib
import streamlit as st
import requests
from bs4 import BeautifulSoup
import base64

# Define API endpoint URL
COURTLISTENER = "https://www.courtlistener.com"
API_ENDPOINT = "http://0.0.0.0:8080/search_opinions"
API_KEY = os.environ["OPB_TEST_API_KEY"]

# Initialize search query, jurisdiction, start date, and end date
jurisdictions = ["All", 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
search_query = ""
jurisdiction = ""
after_date = None
before_date = None

# Create a Streamlit app
st.title("OpenProBono")
st.header("Court Opinion Search")
st.info("Note: Search may be slow as opinions are summarized by AI.")
st.warning("Disclaimer: AI summaries are not always 100% accurate.")

with pathlib.Path("bg.png").open("rb") as f:
    data = f.read()
bin_str = base64.b64encode(data).decode()
page_bg_img = """<style>
.stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
}
</style>
""" % bin_str
st.markdown(page_bg_img, unsafe_allow_html=True)

def disable():
    st.session_state.disabled = True

if "disabled" not in st.session_state:
    st.session_state.disabled = False
if "error" not in st.session_state:
    st.session_state.error = False

def search():
    params = {
        "query": search_query,
        "api_key": API_KEY,
        "jurisdiction": jurisdiction.lower() if jurisdiction != "All" else None,
        "after_date": after_date.strftime("%Y-%m-%d") if after_date else None,
        "before_date": before_date.strftime("%Y-%m-%d") if before_date else None,
        "k": num_results,
    }
    try:
        response = requests.get(API_ENDPOINT, params=params)
    except:
        return None
    return response

def display_results(response_json: dict):
    results = response_json["results"]
    # Display search results as cards
    for i, result in enumerate(results, start=1):
        if "case_name" in result["entity"]["metadata"]:
            case_name = result["entity"]["metadata"]["case_name"]
        else:
            case_name = "Unknown Case"
        if len(case_name) > 200:
            case_name = case_name[:200] + "..."
        if "court_name" in result["entity"]["metadata"]:
            court_name = result["entity"]["metadata"]["court_name"]
        else:
            court_name = "Unknown Court"
        if "author_name" in result["entity"]["metadata"]:
            author_name = result["entity"]["metadata"]["author_name"]
        elif "author_str" in result["entity"]["metadata"]:
            author_name = result["entity"]["metadata"]["author_str"]
        else:
            author_name = "Unknown Author"
        if "ai_summary" in result["entity"]["metadata"]:
            ai_summary = result["entity"]["metadata"]["ai_summary"]
        else:
            ai_summary = "AI summary unavailable"
        if result["source"] == "courtlistener":
            text = BeautifulSoup(result["entity"]["text"], features="html.parser")
            for link in text.find_all("a"):
                if "href" in link.attrs:
                    href = link.attrs["href"]
                if href.startswith("/"):
                    href = COURTLISTENER + href
                    link.attrs["href"] = href
            text = text.prettify()
            url = COURTLISTENER + result["entity"]["metadata"]["absolute_url"]
            full_text = f"""<p><b>Full text link</b>: <a href="{url}">{url}</a></p>"""
        else: # cap
            text = f"""<p>{result["entity"]["text"]}</p>"""
            full_text = "<p><b>Full text link</b>: Full text unavailable</p>"
        date_filed = datetime.datetime.strptime(result["entity"]["metadata"]["date_filed"], "%Y-%m-%d")
        date_filed = date_filed.strftime("%B %d, %Y")
        st.markdown(f"""<div style="width: 100%; border: 1px solid #737373; padding: 10px;">
                <h3>{i}. {case_name}</h3>
                <p><i>Match score</i>: {max([0, (2 - result['distance']) / 2])}</p>
                <p><b>Court</b>: {court_name}</p>
                <p><b>Author</b>: {author_name}</p>
                <p><b>Date filed</b>: {date_filed}</p>
                <p><b>AI summary</b>: {ai_summary}</p>
                {full_text}
                <p><b>Matched excerpt</b>: </p>
                <div style="border: 1px solid #737373; overflow-y: scroll; max-height: 300px;">{text}</div>""",
                unsafe_allow_html=True)

# Add a text input for the search query
with st.form("search_form"):
    search_query = st.text_input("Enter your search query:")
    jurisdiction = st.selectbox("Select jurisdiction:", jurisdictions)
    after_date = st.date_input("After date (optional):", value=None, min_value=datetime.date(1700, 1, 1), max_value=datetime.date.today(), format="MM/DD/YYYY")
    before_date = st.date_input("Before date (optional):", value=None, min_value=datetime.date(1700, 1, 1), max_value=datetime.date.today(), format="MM/DD/YYYY")
    num_results = st.selectbox("Display results:", [4, 8], index=0)
    submitted = st.form_submit_button("Search", on_click=disable, disabled=st.session_state.disabled)

if "response_json" in st.session_state:
    display_results(st.session_state.response_json)

if st.session_state.error:
    st.error("Something went wrong. Please try again later.")

if submitted:
    # Call the API endpoint with the search query and filters
    response = search()
    # Check if the API call was successful
    if response is not None and response.status_code == 200:
        response_json = response.json()
        if response_json["message"] != "Success":
            st.session_state.error = True
        else:
            st.session_state.error = False
            st.session_state.response_json = response_json
    else:
        st.session_state.error = True
    submitted = False
    st.session_state.disabled = False
    st.rerun()