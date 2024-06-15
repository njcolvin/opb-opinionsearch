import datetime
import os
import streamlit as st
import requests
from bs4 import BeautifulSoup

# Define API endpoint URL
COURTLISTENER = "https://www.courtlistener.com"
API_ENDPOINT = "http://0.0.0.0:8080/search_opinions"
API_KEY = os.environ["OPB_TEST_API_KEY"]

# Initialize search query, jurisdiction, start date, and end date
search_query = ""
jurisdiction = ""
after_date = None
before_date = None

# Create a Streamlit app
st.title("OpenProBono")
st.header("Search Court Opinions")

# Add a text input for the search query
with st.form("search_form"):
    search_query = st.text_input("Enter your search query:")
    jurisdiction = st.selectbox("Select jurisdiction:", ["All", "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy"])
    after_date = st.date_input("After date (optional):", value=None, min_value=datetime.date(1700, 1, 1), max_value=datetime.date.today())
    before_date = st.date_input("Before date (optional):", value=None)
    num_results = st.selectbox("Display results:", [4, 8], index=0)
    submitted = st.form_submit_button("Search")

# Call the API endpoint with the search query and filters
if submitted:
    params = {
        "query": search_query,
        "api_key": API_KEY,
        "jurisdiction": jurisdiction if jurisdiction != "All" else None,
        "after_date": after_date.strftime("%Y-%m-%d") if after_date else None,
        "before_date": before_date.strftime("%Y-%m-%d") if before_date else None,
        "k": num_results,
    }
    response = requests.get(API_ENDPOINT, params=params)

    # Check if the API call was successful
    if response.status_code == 200:
        response_json = response.json()
        results = response_json["results"]
        # Display search results as cards
        for result in results:
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
            else:
                author_name = "Unknown Author"
            text = BeautifulSoup(result["entity"]["text"])
            for link in text.find_all("a"):
                if "href" in link.attrs:
                    href = link.attrs["href"]
                if href.startswith("/"):
                    href = COURTLISTENER + href
                    link.attrs["href"] = href
            text = text.prettify()
            url = COURTLISTENER + result["entity"]["metadata"]["absolute_url"]
            st.markdown(f"""<div style="width: 100%; border: 1px solid #ccc; padding: 10px;">
                    <h3>{case_name}</h3>
                    <p><i>Match score</i>: {max([0, 1 - result['distance']])}</p>
                    <p><b>Court</b>: {court_name}</p>
                    <p><b>Author</b>: {author_name}</p>
                    <p><b>Date filed</b>: {result['entity']['metadata']['date_filed']}</p>
                    <p><b>AI summary</b>: {result['entity']['metadata']['ai_summary']}</p>
                    <p><b>Full text link</b>: <a href="{url}">{url}</a></p>
                    <p><b>Matched excerpt</b>: </p>
                    <div style="border: 1px solid #ccc; overflow-y: scroll; max-height: 300px;">{text}</div>""",
                    unsafe_allow_html=True)
    else:
        st.error("Failed to retrieve search results.")