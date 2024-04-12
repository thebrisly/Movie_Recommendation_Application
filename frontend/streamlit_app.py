import streamlit as st
import pandas as pd
import requests

##########################
# Functions from backend #
##########################

# Caches and fetches movie details from the backend
@st.cache_data
def fetch_movies():
    backend_url = 'http://127.0.0.1:8080/load_movies'
    response = requests.get(backend_url)
    return pd.DataFrame(response.json()) if response.status_code == 200 else st.error('Failed to fetch movies from the backend.')

def search(title):
    backend_url = "http://127.0.0.1:8080/search"
    response = requests.get(backend_url, params={"q" : title})
    return pd.DataFrame(response.json())

def posters(tmdb_id):
    backend_url = "http://127.0.0.1:8080/posters"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['poster_url']



#####################
# App Design ########
#####################

# Streamlit UI
st.title('Movie Recommendation System')
movies_df = fetch_movies()

search_query = st.text_input("Rechercher un film par titre")
if search_query:
    search_results = search(search_query)
    st.write(search_results)
else:
    #st.write(movies_df)

    for index, row in movies_df.head(50).iterrows():
        #poster_url = posters(row['tmdbId']) 
        #st.image(poster_url, width=50)
        st.markdown(f"{row['title']}")
        st.markdown(f"{row['genres']}")
        st.markdown(f"{row['tmdbId']}")
        st.markdown("<hr style='border-top: 0.1px solid #eee; margin: 1px 0;'>", unsafe_allow_html=True)
    