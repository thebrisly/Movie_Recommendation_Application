from google.cloud import bigquery

client = bigquery.Client.from_service_account_json('../key/testapi-415115-18f8f1b39899.json')

# Define the evaluation query
evaluation_query = """
SELECT * FROM
ML.EVALUATE(MODEL `testapi-415115.movie_recommendation.MF-model`)
"""

# Run the evaluation query
evaluation_result = client.query(evaluation_query).to_dataframe()

# Display the evaluation results
print(evaluation_result)

# Define the recommendation query
recommendation_query = """
SELECT * FROM
ML.RECOMMEND(MODEL `testapi-415115.movie_recommendation.MF-model`,
(
SELECT DISTINCT userId
FROM `testapi-415115.movie_recommendation.ratings`
LIMIT 5))
"""

# Run the recommendation query
recommendation_result = client.query(recommendation_query).to_dataframe()

# Display the first 10 recommendations
print(recommendation_result.head(10))