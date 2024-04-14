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

def search(title):
    backend_url = "http://127.0.0.1:8080/search"
    response = requests.get(backend_url, params={"q" : title})
    return pd.DataFrame(response.json())

def posters(tmdb_id):
    backend_url = "http://127.0.0.1:8080/posters"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['poster_url']

def details(tmdb_id):
    backend_url = "http://127.0.0.1:8080/details"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['overview']

def recommendations(favorites):
    backend_url = "http://127.0.0.1:8080/recommendations"
    response = requests.get(backend_url)
    return pd.DataFrame(response.json()) if response.status_code == 200 else st.error('Failed to get recommendations.')



#####################
# App Design ########
#####################

# Streamlit UI
st.title('Movie Recommendation System')
#movies_df = fetch_movies()
movies_df = fetch_movies().head(50)

search_query = st.text_input("Search a movie by its title !")


#if 'favorites' not in st.session_state:
#    st.session_state['favorites'] = []

# Vérifie si la clé 'favorites' existe dans st.session_state, sinon initialise à une liste vide
movies_info = {}  # clé: movieId, valeur: (title, poster_url)

# Remplir le dictionnaire avec les informations des films
for _, row in movies_df.iterrows():
    movies_info[row['movieId']] = (row['title'], posters(row['tmdbId']))


if 'favorites' not in st.session_state:
    st.session_state['favorites'] = []

with st.sidebar:
    st.title("Favorites")
    for movie_id in st.session_state['favorites']:
        # Vérifier si l'ID du film est présent dans le dictionnaire
        if movie_id in movies_info:
            title, poster_url = movies_info[movie_id]
            st.markdown(f"### {title}")  # Afficher le titre du film
            st.image(poster_url, width=150)  # Afficher le poster du film
        else:
            st.write(f"Film avec l'ID {movie_id} introuvable")

if search_query:
    search_results = search(search_query)
    st.write(search_results)
else:
    movies_to_display = 3

    for i in range(0, len(movies_df), movies_to_display):
        row_data = movies_df.iloc[i:i+movies_to_display]
        cols = st.columns(movies_to_display)
        for col, (_, row) in zip(cols, row_data.iterrows()):
            with col:
                poster_url = posters(row['tmdbId']) 
                st.image(poster_url, width=250)
                # Ajoute l'icône de cœur en haut à droite du poster
                button_key = f"favorite_button_{row['tmdbId']}"
                if st.button("❤️", key=button_key):
                    st.session_state['favorites'].append(row['movieId'])
                    st.experimental_rerun()
                expander_key = f"details_expander_{row['tmdbId']}"
                with st.expander("Afficher les détails", expanded=False):
                    st.markdown(f"**Genre:** {row['genres']}")
                    detail = details(row['tmdbId'])
                    st.write(detail)
