from flask import Flask, request, jsonify
from flask_cors import CORS  
from google.cloud import bigquery
from elasticsearch import Elasticsearch
import requests
import pandas as pd
import os


#####################
# CONNEXIONS ########
#####################

app = Flask(__name__)
CORS(app)

# Connecting to Big Query
client_google = bigquery.Client.from_service_account_json('./testapi-415115-18f8f1b39899.json')

# Connecting to Elastic Search thanks to the API
URL_ENDPOINT =   "https://67de47c1e10848d4a878638113b8bbb7.europe-west3.gcp.cloud.es.io:443"
API_KEY = "M2ZiRTBZNEJudktRZGNqdGxLVmc6MV9qazJKajRRWGVWaGE2UHd5MTlHQQ=="
INDEX_NAME = 'movie_recommendation'

client_elastic = Elasticsearch(URL_ENDPOINT, api_key=API_KEY)

# Little function that will set something by default when arriving on the backend's website
@app.route('/')
def index():
    return "Here is the backend's website"


############################
# Elastic Search Functions #
############################

# This function below will be the one that does the autocomplete search with elastic search
@app.route('/search', methods=['GET'])
def search_movies():
    # Get search query from request (so it search like that : link/searchq?=toy)
    query = request.args.get('q', '')

    if query:
        # Search for movies matching the query in Elasticsearch index - it will display only the first 50
        response = client_elastic.search(
            index=INDEX_NAME, 
            body={
                "query": {
                    "match_phrase_prefix": {
                        "title": {
                            "query": query,
                            "max_expansions": 50
                        }
                    }
                }
            }      
        )

        # Extract movie information (title, genre and movieId) from search results
        title_genre_id = [{
            "title": hit['_source']['title'],
            "genres": hit['_source'].get('genres', 'Unknown'),  # Use .get() to handle missing fields
            "movieId": hit['_source']['movieId']
        } for hit in response['hits']['hits']]

        return jsonify(title_genre_id) #then we put everything in a json so it's better for the sending to the frontend
    
    return jsonify([])

#######################
# Big Query Functions #
#######################

# Endpoint to load movies from BigQuery
@app.route('/load_movies', methods=['GET'])
def load_movies():
    # SQL query to fetch movies from BigQuery
    query = """
    SELECT m.*, l.imdbId, l.tmdbId FROM `testapi-415115.movie_recommendation.movies` m
    INNER JOIN `testapi-415115.movie_recommendation.links` l ON m.movieId = l.movieId;
    """
    
    # Execute the query and convert results to DataFrame
    query_job = client_google.query(query)
    movies_df = query_job.to_dataframe()

    return movies_df.to_json()

# Endpoint to get movie recommendations based on user favorites
@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    # Get JSON data from the request body
    data = request.json  
    
    # Retrieve user favorites from JSON request, defaulting to an empty list
    favorites = data.get('favorites', [])  
    
    # Set default favorites if none provided
    if not favorites:
        favorites = [64, 463]

    # SQL query to get movie recommendations from BigQuery using Machine Learning model
    query = """
    SELECT * FROM (
    SELECT
        userId,
        movieId,
        predicted_rating_im_confidence,
        ROW_NUMBER() OVER (PARTITION BY userId ORDER BY predicted_rating_im_confidence DESC) as rank
    FROM
        ML.RECOMMEND(MODEL `testapi-415115.movie_recommendation.MF-model`)
    )
    WHERE rank <= 10
    ORDER BY userId, predicted_rating_im_confidence DESC
    """
    
    # Execute the query and convert results to DataFrame
    results = client_google.query(query).to_dataframe()

    # Find similar users based on favorites
    best_predictions_by_users = results.groupby('userId')['movieId'].apply(list).reset_index(name='best_predictions')
    best_users = find_similar_users(favorites, best_predictions_by_users)
    best_movies = get_best_movies(best_users, favorites)

    return best_movies.to_json()


##############################
# Search other similar users #
##############################

# Function to find similar users based on preferences
def find_similar_users(preferences, predictions_by_users):
    similar_users = []  # Initialize an empty list to store similar users
    for index, row in predictions_by_users.iterrows():  # Iterate over predictions for each user
        user_id = row['userId']  # Get user ID
        predictions = row['best_predictions']  # Get movie predictions for the user
        common_movies = len(set(preferences) & set(predictions))  # Calculate the number of common movies between user preferences and predictions
        similarity_score = common_movies / len(preferences)  # Calculate similarity score
        # Add user data and similarity metrics to the list
        similar_users.append({'userId': user_id, 'best_predictions': predictions, 'number_similar_movies': common_movies, 'similarity_score': similarity_score})
    
    similar_users_df = pd.DataFrame(similar_users)  # Convert the list of similar users to a DataFrame
    similar_users_df = similar_users_df.sort_values(by=['number_similar_movies', 'similarity_score'], ascending=False)  # Sort the DataFrame by number of similar movies and similarity score
    return similar_users_df  # Return the DataFrame of similar users

# Function to get best movies based on similar users
def get_best_movies(users_df, base_user_movies):
    top_users_movies = users_df.iloc[0:2]['best_predictions'].tolist()  # Get predictions of top similar users
    recommended_movies = set(base_user_movies)  # Initialize a set with base user movies

    # Iterate over top users' predictions
    for movies in top_users_movies:
        for movie in movies:
            if movie not in base_user_movies:  # If the movie is not in base user's movies, add it to recommended movies
                recommended_movies.add(movie)

    # Filter out movies already in base user's movies and convert the set to a list
    recommended_movies_list = [movie for movie in recommended_movies if movie not in base_user_movies]

    return pd.DataFrame({'movieId': recommended_movies_list})  # Return DataFrame of recommended movies



#####################
# TMDB FUNCTIONS ####
#####################

# Function to get movie poster URL based on TMDB ID
@app.route('/posters', methods=['GET'])
def get_movie_poster():
    tmdb_id = request.args.get('tmdb_id')  # Get TMDB ID from request parameters

    api_key = "35a1a21523af09d62c97695abf6bc067"
    base_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images?api_key={api_key}"  # Construct API URL
    
    try:
        response = requests.get(base_url)  # Send request to TMDB API
        data = response.json()  # Parse JSON response
        
        # Check if posters are available in the response and return the URL of the first poster
        if "posters" in data and data["posters"]:
            poster_url = f"https://image.tmdb.org/t/p/w500{data['posters'][0]['file_path']}"
            return jsonify({"poster_url": poster_url})  # Returning JSON object with poster URL
        else:
            return jsonify({"poster_url": "/images/not_found.jpeg"})  # Return default image URL if no posters found
    except Exception as e:
        return jsonify({"error": f"Error fetching movie poster: {e}"}), 500  # Return error message if fetching fails


# Function to get movie details based on TMDB ID
@app.route('/details', methods=['GET'])
def get_movie_details():
    tmdb_id = request.args.get('tmdb_id')  # Get TMDB ID from request parameters

    api_key = "35a1a21523af09d62c97695abf6bc067"
    base_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}"  # Construct API URL
    
    try:
        response = requests.get(base_url)  # Send request to TMDB API
        data = response.json()  # Parse JSON response
        
        # Check if movie overview is available in the response and return it
        if "overview" in data:
            # Return movie overview in JSON format
            return jsonify({"overview": data["overview"]})
        else:
            return jsonify({"overview": "Movie details not found"})  # Return default message if movie details not found
    except Exception as e:
        return jsonify({"error": f"Error fetching movie details: {e}"}), 500  # Return error message if fetching fails


########
# MAIN #
########

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080)) #so the deployment works
    app.run(debug=True, host='0.0.0.0', port=port)