# Movie_Recommendation_Application

This project entails creating a movie recommendation application utilizing Google Cloud services and advanced analytics techniques. The application allows users to input their movie preferences and receive personalized recommendations based on those preferences.

Here is an example of what it looks like :

<img width="1502" alt="Capture d’écran 2024-04-15 à 11 11 02" src="https://github.com/thebrisly/Movie_Recommendation_Application/assets/84352348/23235078-0e3b-4c94-9eb4-87ae00cf3fd1">

# Website link
Link to the website : https://ass2-frontend-oeouywpojq-oa.a.run.app/

## Functionalities implemented 

### Backend (Flask Web Application):

- Trained a movie recommender system using BigQuery ML.
- Implemented autocomplete functionality using Elasticsearch to aid users in exploring movie titles.
- Identified users in the dataset most similar to the web application user using SQL queries.
- Generated movie recommendations using the trained model.
- Retrieved movie posters from The Movie Database.

### Frontend (Streamlit Application):

- Implemented a movie title search bar with autocomplete functionality.
- Enabled users to select multiple movies before requesting recommendations.
- Displayed recommended movie titles along with their corresponding posters.

  ## Method for Computing User Similarity
To compute user similarity, we compared the movie preferences of the web application user with those of users in the dataset. Users with a higher number of shared movie preferences were considered more similar. SQL queries were utilized to identify the top similar users, whose recommendations were used to provide suggestions for the web application user.

------------------

This project is part of the course "Cloud & Advanced Analytics" at the University of Lausanne given by the professor Michalis Vlachos
