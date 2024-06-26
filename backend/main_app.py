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
URL_ENDPOINT =   # private end point here
API_KEY = # private key here
INDEX_NAME = 'movie_recommendation'

client_elastic = Elasticsearch(URL_ENDPOINT, api_key=API_KEY)

@app.route('/')
def index():
    return "Here is the backend's website"


############################
# Elastic Search Functions #
############################

# Function for the autocomplete
@app.route('/search', methods=['GET'])
def search_movies():
    query = request.args.get('q', '')

    if query:
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

        title_genre_id = [{
            "title": hit['_source']['title'],
            "genres": hit['_source'].get('genres', 'Unknown'),  # Use .get() to handle missing fields
            "movieId": hit['_source']['movieId']
        } for hit in response['hits']['hits']]

        return jsonify(title_genre_id)
    
    return jsonify([])


#######################
# Big Query Functions #
#######################

@app.route('/load_movies', methods=['GET'])
def load_movies():
    query = """
    SELECT m.*, l.imdbId, l.tmdbId FROM `testapi-415115.movie_recommendation.movies` m
    INNER JOIN `testapi-415115.movie_recommendation.links` l ON m.movieId = l.movieId
    ORDER BY m.title;
    """
    
    # Execute the query and convert results to DataFrame
    query_job = client_google.query(query)
    movies_df = query_job.to_dataframe()

    return movies_df.to_json()


@app.route('/recommendations', methods=['POST', 'GET'])
def get_recommendations():
    
    #cold_user_movies = request.args.get('favorites')
    
    data = request.get_json()
    cold_user_movies = data.get('favorites', "No data received")


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
    results = client_google.query(query).to_dataframe()

    best_predictions_by_users = results.groupby('userId')['movieId'].apply(list).reset_index(name='best_predictions')
    best_users = find_similar_users(cold_user_movies, best_predictions_by_users)
    best_movies = get_best_movies(best_users, cold_user_movies)

    return best_movies.to_json()


##############################
# Search other similar users #
##############################

def find_similar_users(preferences, predictions_by_users):
    similar_users = []
    for index, row in predictions_by_users.iterrows():
        user_id = row['userId']
        predictions = row['best_predictions']
        common_movies = len(set(preferences) & set(predictions))
        similarity_score = common_movies / len(preferences)
        similar_users.append({'userId': user_id, 'best_predictions': predictions, 'number_similar_movies': common_movies, 'similarity_score': similarity_score})
    
    similar_users_df = pd.DataFrame(similar_users)
    similar_users_df = similar_users_df.sort_values(by=['number_similar_movies', 'similarity_score'], ascending=False)
    return similar_users_df
    

def get_best_movies(users_df, base_user_movies):
    top_users_movies = users_df.iloc[0:2]['best_predictions'].tolist()  # Récupérer les films des 2 premiers utilisateurs
    recommended_movies = set()

    for movies in top_users_movies:
        for movie in movies:
            if movie not in base_user_movies:  # Vérifier si le film n'est pas déjà dans les préférences de l'utilisateur de base
                recommended_movies.add(movie)

    recommended_movies_list = list(recommended_movies)

    return pd.DataFrame({'movieId': recommended_movies_list})



#####################
# TMDB FUNCTIONS ####
#####################

@app.route('/posters', methods=['GET'])
def get_movie_poster():
    tmdb_id = request.args.get('tmdb_id')

    api_key =  # private key here
    base_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images?api_key={api_key}"
    
    try:
        response = requests.get(base_url)
        data = response.json()
        if "posters" in data and data["posters"]:
            poster_url = f"https://image.tmdb.org/t/p/w500{data['posters'][0]['file_path']}"
            return jsonify({"poster_url": poster_url})  # Returning JSON object with poster URL
        else:
            return jsonify({"poster_url": "./images/not_found.jpeg"})
    except Exception as e:
        return jsonify({"error": f"Error fetching movie poster: {e}"}), 500


@app.route('/details', methods=['GET'])
def get_movie_details():
    tmdb_id = request.args.get('tmdb_id')  # Pour obtenir le tmdb_id à partir des paramètres de la requête

    api_key = # private key here
    base_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}"
    
    try:
        response = requests.get(base_url)
        data = response.json()
        if "overview" in data:
            # Retourne les détails du film au format JSON
            return jsonify({"overview": data["overview"]})
        else:
            return jsonify({"overview": "Movie details not found"})
    except Exception as e:
        return jsonify({"error": f"Error fetching movie details: {e}"}), 500

########
# MAIN #
########

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
