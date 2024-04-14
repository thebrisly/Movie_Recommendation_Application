import streamlit as st
import pandas as pd
import requests

st.set_page_config(layout="wide")
##########################
# Functions from backend #
##########################

# Caches and fetches movie details from the backend
@st.cache_data
def fetch_movies():
    backend_url = 'http://127.0.0.1:8080/load_movies'
    response = requests.get(backend_url)
    return pd.DataFrame(response.json()) if response.status_code == 200 else st.error('Failed to fetch movies from the backend.')

@st.cache_data
def search(title):
    backend_url = "http://127.0.0.1:8080/search"
    response = requests.get(backend_url, params={"q" : title})   
    movies_found = pd.DataFrame(response.json())
    return pd.merge(movies_found, fetch_movies(), on='movieId', how='left').rename(columns={'title_x': 'title', 'genres_x': 'genres'})

@st.cache_data
def posters(tmdb_id):
    backend_url = "http://127.0.0.1:8080/posters"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['poster_url']

@st.cache_data
def details(tmdb_id):
    backend_url = "http://127.0.0.1:8080/details"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['overview']

def recommendations(favorites):
    backend_url = "http://127.0.0.1:8080/recommendations"
    response = requests.get(backend_url, params={"cold_user_movies" : favorites})
    dt_rec = pd.DataFrame(response.json()) if response.status_code == 200 else st.error('Failed to get recommendations.')
    return pd.merge(dt_rec, fetch_movies(), on='movieId', how='left')

@st.cache_data
def get_movie_details(movie_id):
    movies_list = fetch_movies()
    return movies_list[movies_list['movieId'] == movie_id]


#####################
# App Design ########
#####################

if 'favorites' not in st.session_state:
    st.session_state['favorites'] = []

with st.sidebar:
    st.title("Favorites")
    for movie_id in st.session_state['favorites']:
        bruh = get_movie_details(movie_id)
        for index,row in bruh.iterrows() :
            st.markdown(f"{row['title']}")  # Afficher le titre du film
            st.image(posters(row["tmdbId"]), width=150)  # Afficher le poster du film

# Streamlit UI
st.title('Movie Recommendation System')

# Initializes the 'displayed_movies' key in the session state
if 'displayed_movies' not in st.session_state:
    st.session_state['displayed_movies'] = fetch_movies().head(50)

search_query = st.text_input("Search a movie by its title!")

col1, col2 = st.columns(2)

# Check if a search has been made and update displayed_movies accordingly
if search_query:
    st.session_state['displayed_movies'] = search(search_query)

with col1:
    if st.button("Get recommendations based on your likes"):
        # If the user clicks the recommendations button, update the displayed_movies
        st.session_state['displayed_movies'] = recommendations(st.session_state.get('favorites', []))
with col2:
    if st.button("Get random movies"):
        # If the user clicks the random movies button, update the displayed_movies
        st.session_state['displayed_movies'] = fetch_movies().sample(50)



# Now, we have a single block of code that displays the movies
movies_to_display = 3
for i in range(0, len(st.session_state['displayed_movies']), movies_to_display):
    row_data = st.session_state['displayed_movies'].iloc[i:i+movies_to_display]
    cols = st.columns(movies_to_display)
    for col, (_, row) in zip(cols, row_data.iterrows()):
        with col:
            poster_url = posters(row['tmdbId'])
            st.image(poster_url, width=250)
            button_key = f"favorite_button_{row['tmdbId']}"
            if st.button("❤️", key=button_key):
                st.session_state['favorites'].append(row['movieId'])
                st.experimental_rerun()
            expander_key = f"details_expander_{row['tmdbId']}"
            with st.expander("Show details", expanded=False):
                st.markdown(f"**Genre:** {row['genres']}")
                detail = details(row['tmdbId'])
                st.write(detail)