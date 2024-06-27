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
jurisdictions = ["All", 'US', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
keyword_query = ""
semantic_query = ""
jurisdiction = ""
after_date = None
before_date = None

# Create a Streamlit app
st.title("OpenProBono")
st.header("Court Opinion Search")
with st.expander("How to use this tool"):
    st.markdown("""Search by keyword and semantic.

The keyword search box will look for _exact_ matches to your query, and the semantic search box will look for _semantically similar_ matches to your query.

### Example

Say you want to look for cases that cite the [Jones Act](https://en.wikipedia.org/wiki/Merchant_Marine_Act_of_1920). You can do this with the keyword search "Jones Act." You can also use semantic search, however "Jones Act" won't yield as good of results.
                
A semantic search should be a _concept_, _idea_, or _definition_. For a named term or entity this is preferable to entering the name by itself. So, if you want to search for the Jones Act applied to workers' compensation, a semantic search query like "seaman workers compensation" yields more accurate results. These results don't always explicitly mention the term "Jones Act."

You can also combine these two methods. Continuing our example, a keyword search for "Jones Act" and a semantic search for "workers compensation" returns opinions that explicitly mention the name _and_ are related to workers compensation.""")
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
    headers = {"X-API-KEY": API_KEY}
    params = {
        "keyword_query": keyword_query,
        "query": semantic_query,
        "jurisdiction": jurisdiction.lower() if jurisdiction != "All" else None,
        "after_date": after_date.strftime("%Y-%m-%d") if after_date else None,
        "before_date": before_date.strftime("%Y-%m-%d") if before_date else None,
        "k": num_results,
    }
    try:
        response = requests.get(API_ENDPOINT, headers=headers, params=params)
    except:
        return None
    return response

def display_results(response_json: dict):
    results = response_json["results"]
    # Display search results as cards
    for i, result in enumerate(results, start=1):
        # case name
        if "case_name" in result["entity"]["metadata"]:
            case_name = result["entity"]["metadata"]["case_name"]
            if len(case_name) > 200:
                case_name = case_name[:200] + "..."
        else:
            case_name = "Unknown Case"
        # court name
        if "court_name" in result["entity"]["metadata"]:
            court_name = result["entity"]["metadata"]["court_name"]
        else:
            court_name = "Unknown Court"
        # author name
        if "author_name" in result["entity"]["metadata"]:
            author_name = result["entity"]["metadata"]["author_name"]
        elif "author_str" in result["entity"]["metadata"]:
            author_name = result["entity"]["metadata"]["author_str"]
        else:
            author_name = "Unknown Author"
        # AI summary
        if "ai_summary" in result["entity"]["metadata"]:
            ai_summary = result["entity"]["metadata"]["ai_summary"]
        else:
            ai_summary = "AI summary unavailable"
        # matched excerpt and full text link
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
        # date filed
        date_filed = datetime.datetime.strptime(result["entity"]["metadata"]["date_filed"], "%Y-%m-%d")
        date_filed = date_filed.strftime("%B %d, %Y")
        # display result
        st.markdown(f"""<div style="width: 100%; border: 1px solid #737373; padding: 10px;">
                <h3>{i}. {case_name}</h3>
                <p><i>Match score</i>: {round(max([0, (2 - result['distance']) / 2]), 5)}</p>
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
    keyword_query = st.text_input("Keyword search query:")
    semantic_query = st.text_input("Semantic search query:")
    jurisdiction = st.selectbox("Select jurisdiction:", jurisdictions)
    after_date = st.date_input("After date (optional):", value=None, min_value=datetime.date(1700, 1, 1), max_value=datetime.date.today(), format="MM/DD/YYYY")
    before_date = st.date_input("Before date (optional):", value=None, min_value=datetime.date(1700, 1, 1), max_value=datetime.date.today(), format="MM/DD/YYYY")
    num_results = st.selectbox("Display results:", [4, 8, 12], index=0)
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