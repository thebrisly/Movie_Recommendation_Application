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
    backend_url = 'https://caa-a2-laura-backend-6mfovafpza-oa.a.run.app//load_movies'
    response = requests.get(backend_url)
    return pd.DataFrame(response.json()) if response.status_code == 200 else st.error('Failed to fetch movies from the backend.')

@st.cache_data
def search(title):
    backend_url = "https://caa-a2-laura-backend-6mfovafpza-oa.a.run.app//search"
    response = requests.get(backend_url, params={"q": title})
    if response.status_code == 200:
        movies_found = pd.DataFrame(response.json())
        if movies_found.empty:
            return None  # Return None or an empty DataFrame to indicate no results
        return pd.merge(movies_found, fetch_movies(), on='movieId', how='left').rename(columns={'title_x': 'title', 'genres_x': 'genres'})
    else:
        st.error('Failed to search movies.')
        return None


# Function to fetch the poster URL for a given movie TMDB ID from the backend API
@st.cache_data
def posters(tmdb_id):
    backend_url = "https://caa-a2-laura-backend-6mfovafpza-oa.a.run.app//posters"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['poster_url']

# Function to fetch movie details for a given movie TMDB ID from the backend API
@st.cache_data
def details(tmdb_id):
    backend_url = "https://caa-a2-laura-backend-6mfovafpza-oa.a.run.app//details"
    response = requests.get(backend_url, params={"tmdb_id" : tmdb_id})
    return response.json()['overview']

# Function to get movie recommendations based on user favorites using the backend API
def recommendations(favorites):
    backend_url = "https://caa-a2-laura-backend-6mfovafpza-oa.a.run.app//recommendations"
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
    for idx, movie_id in enumerate(st.session_state['favorites']):
        movie_details = get_movie_details(movie_id)

        # Iterate over each row in movie details to get the title and the posters
        for index, row in movie_details.iterrows():
            st.markdown(f"{row['title']}")
            st.image(posters(row["tmdbId"]), width=150)

            # Generate a unique key for the remove button using the movie's position in the favorites list and index
            remove_button_key = f"remove_favorite_button_{idx}_{index}"
            if st.button("❌ I don't like it anymore", key=remove_button_key):
                st.session_state['favorites'].remove(movie_id)
                st.experimental_rerun()

# Main Streamlit UI
st.title('Movie Recommendation System')

# Initialize 'displayed_movies' in session state if not presentso it can save the movies
if 'displayed_movies' not in st.session_state:
    st.session_state['displayed_movies'] = fetch_movies().head(50)

# Implementing the search functionality (search bar)
search_query = st.text_input("Search a movie by its title!")

if search_query:
    search_result = search(search_query)
    if search_result is not None and not search_result.empty:
        st.session_state['displayed_movies'] = search_result
        st.session_state['show_like_button'] = True  # Allow showing the like button
    else:
        st.session_state['displayed_movies'] = pd.DataFrame()  # Clear any previous results
        st.info("No movies found for your search query.")  # Show message when no movies are found
else:
    st.session_state['displayed_movies'] = fetch_movies().head(50)  # Default to showing some movies
    st.session_state['show_like_button'] = True  # Allow showing the like button

# Splitting the next line into 3 columns to have buttons side by side
# Left column: Get recommendations based on user likes
# Middle column: Get 6 random movies
# Right column: Show All Movies
col1, col2, col3 = st.columns([1, 3, 3])

with col1:
    if st.button("All Movies"):
        # Reset the displayed_movies to the first 50 movies from the database
        st.session_state['displayed_movies'] = fetch_movies().head(50)
        st.session_state['show_like_button'] = True  # Ensure like buttons are visible for all movies
    

with col2:
    if st.button("Get recommendations based on your likes"):
        if st.session_state['favorites']:  # Check if there are favorites selected
            recommendations_df = recommendations(st.session_state['favorites'])
            if not recommendations_df.empty:
                st.session_state['displayed_movies'] = recommendations_df
                st.session_state['show_like_button'] = False  # Optionally control visibility of like buttons
            else:
                st.error("Failed to fetch recommendations. Please try again.")
        else:
            st.warning("You must add at least one movie to favorites to get recommendations.")

with col3:
    if st.button("Get 6 random movies"):
        random_movies_df = fetch_movies().sample(6)
        if not random_movies_df.empty:
            st.session_state['displayed_movies'] = random_movies_df
            st.session_state['show_like_button'] = False  # Optionally control visibility of like buttons
        else:
            st.error("Failed to fetch random movies.")
    



# Display movies in an aesthetic way: 3 posters per line
movies_to_display = 3

for i in range(0, len(st.session_state['displayed_movies']), movies_to_display):
    row_data = st.session_state['displayed_movies'].iloc[i:i+movies_to_display]
    cols = st.columns(movies_to_display)
    for col, (index, row) in zip(cols, row_data.iterrows()):
        with col:
            tmdb_id = row['tmdbId']
            key_id = f"{tmdb_id}_{index}"

            poster_url = posters(tmdb_id)
            st.image(poster_url, width=250)

            # Add favorite button for each movie with a unique key using index
            button_key = f"favorite_button_{key_id}"
            movie_id = row['movieId']  # Ensure you are retrieving the correct identifier for movieId
            if st.session_state.get('show_like_button', True):
                if st.button("❤️", key=button_key):
                    if movie_id not in st.session_state['favorites']:
                        st.session_state['favorites'].append(movie_id)  # Add the movieId to favorites if not already present
                        st.experimental_rerun()  # Rerun the Streamlit app to reflect changes
                    else:
                        st.warning("This movie is already in your favorites!")  # Display a warning message if the movie is already in favorites

            # Add expander for showing movie title + genres + details
            expander_key = f"details_expander_{key_id}"
            with st.expander("Show details", expanded=False):
                st.markdown(f"**Title:** {row['title']}")
                st.markdown(f"**Genre:** {row['genres']}")
                if pd.notna(tmdb_id):
                    detail = details(tmdb_id)
                    st.write(detail)
                else:
                    st.write("Details not available.")
