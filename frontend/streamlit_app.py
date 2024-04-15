import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(layout="wide") #to display everything in big

##########################
# Functions from backend #
##########################

# The functions below have :
# - a backend_url that corresponds to my deployed backend and the corresponding function just after the / #
# - a response -> the frontend will send a GET or POST request to the backend API with the provided TMDB ID as query parameter

# Function to fetch the list of movies from the backend API
@st.cache_data
def fetch_movies():
    backend_url = 'https://ass2-backend-oeouywpojq-oa.a.run.app/load_movies'
    response = requests.get(backend_url)
    return pd.DataFrame(response.json()) if response.status_code == 200 else st.error('Failed to fetch movies from the backend.')

# Function to search for movies by title using the backend API
@st.cache_data
def search(title):
    backend_url = "https://ass2-backend-oeouywpojq-oa.a.run.app/search"
    response = requests.get(backend_url, params={"q" : title})   
    movies_found = pd.DataFrame(response.json())
    return pd.merge(movies_found, fetch_movies(), on='movieId', how='left').rename(columns={'title_x': 'title', 'genres_x': 'genres'})

# Function to fetch the poster URL for a given movie TMDB ID from the backend API
@st.cache_data
def posters(tmdb_id):
    backend_url = "https://ass2-backend-oeouywpojq-oa.a.run.app/posters"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['poster_url']

# Function to fetch movie details for a given movie TMDB ID from the backend API
@st.cache_data
def details(tmdb_id):
    backend_url = "https://ass2-backend-oeouywpojq-oa.a.run.app/details"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['overview']

# Function to get movie recommendations based on user favorites using the backend API
def recommendations(favorites):
    backend_url = "https://ass2-backend-oeouywpojq-oa.a.run.app/recommendations"
    headers = {'Content-Type': 'application/json'}  # Specify content type as JSON
    data = {'favorites': favorites}
    
    response = requests.post(backend_url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        dt_rec = pd.DataFrame(response.json()) if response.json() else pd.DataFrame()  # Convert JSON response to DataFrame
        
        # Merge recommendations with movie data
        movies_df = fetch_movies()  # Get movie data
        merged_df = pd.merge(dt_rec, movies_df, on='movieId', how='left')  # Merge recommendations with movie data to get the tmdb id and everything
        return merged_df
    else:
        st.error('Failed to get recommendations.') #if an error occurs, then we will throw an error.

# Function to get details of a specific movie by movie ID
@st.cache_data
def get_movie_details(movie_id):
    movies_list = fetch_movies()
    return movies_list[movies_list['movieId'] == movie_id]


#####################
# App Design ########
#####################

# Initialize 'favorites' in session state if not present, so it can save the movies
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = []

# Display favorites in the sidebar
with st.sidebar:
    st.title("Favorites")
    # Iterate over each movie ID in favorites to get the details of a movie
    for movie_id in st.session_state['favorites']:

        bruh = get_movie_details(movie_id)
        
        # Iterate over each row in movie details to get the title and the posters
        for index, row in bruh.iterrows():
            st.markdown(f"{row['title']}")
            st.image(posters(row["tmdbId"]), width=150)

            # Add remove button for each favorite movie (will removie it from the list favorites)
            remove_button_key = f"remove_favorite_button_{row['tmdbId']}"
            if st.button("❌ I don't like it anymore", key=remove_button_key):
                st.session_state['favorites'].remove(row['movieId'])
                st.experimental_rerun()

# Main Streamlit UI
st.title('Movie Recommendation System')

# Initialize 'displayed_movies' in session state if not presentso it can save the movies
if 'displayed_movies' not in st.session_state:
    st.session_state['displayed_movies'] = fetch_movies().head(50)

# Implementing the search functionality (search bar)
search_query = st.text_input("Search a movie by its title!")

# Check if a search has been made and update displayed_movies accordingly
if search_query:
    st.session_state['displayed_movies'] = search(search_query)
else :
    st.session_state['displayed_movies'] = fetch_movies().head(50)

# Splitting the next line into 2 columns to have to buttons side by side
# Left column: Get recommendations based on user likes wit the recommendation function coded in the backend
# Right column: Get 6 random movies (it will just display 6 rando numbers from the list of all movies)
col1, col2 = st.columns(2)

with col1:
    if st.button("Get recommendations based on your likes"):
        recommendations_df = recommendations(st.session_state.get('favorites', []))
        st.session_state['displayed_movies'] = recommendations_df
with col2:
    if st.button("Get 6 random movies"):
        st.session_state['displayed_movies'] = fetch_movies().sample(6)


# Display movies in an esthetic way : 3 posters per line
movies_to_display = 3

for i in range(0, len(st.session_state['displayed_movies']), movies_to_display):
    row_data = st.session_state['displayed_movies'].iloc[i:i+movies_to_display]
    cols = st.columns(movies_to_display)
    for col, (_, row) in zip(cols, row_data.iterrows()):
        with col:
            poster_url = posters(row['tmdbId']) #displaying the posters 
            st.image(poster_url, width=250)

            # Add favorite button for each movie
            button_key = f"favorite_button_{row['tmdbId']}"
            if st.button("❤️", key=button_key):
                st.session_state['favorites'].append(row['movieId'])  #it will add the movieId in the list of favorites movies
                st.experimental_rerun() #this line is here to rerun the Streamlit app to reflect changes in session state

            # Add expander for showing movie title + genres + details
            expander_key = f"details_expander_{row['tmdbId']}"
            with st.expander("Show details", expanded=False):
                st.markdown(f"**Title:** {row['title']}")
                st.markdown(f"**Genre:** {row['genres']}")
                detail = details(row['tmdbId'])
                st.write(detail)
