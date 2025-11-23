from flask import Flask, request, render_template
import pickle
import pandas as pd
import requests

# --- 1. TMDB API Key and Helper Function ---
TMDB_API_KEY = '4a8a9ef55022158be86fe6ff86e238b3'

def fetch_poster(movie_id):
    """Fetches the poster URL for a given TMDB movie ID."""
    response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}')
    response.raise_for_status() 
    data = response.json()
    
    poster_path = data.get('poster_path')
    
    if poster_path:
        return "https://image.tmdb.org/t/p/w500" + poster_path
    return "" 

# --- 2. Data Loading (Executed Once on Startup) ---
try:
    # Load your movie data and similarity matrix
    movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except FileNotFoundError:
    print("FATAL ERROR: Required pickle files (movies_dict.pkl or similarity.pkl) not found. Check your directory.")
    exit()
except Exception as e:
    print(f"FATAL ERROR during data loading: {e}")
    exit()

# --- 3. Recommendation Logic Function ---
def recommend(movie_title):
    """Finds the top 5 similar movies and fetches their names and posters."""
    try:
        movie_index = movies[movies['title'] == movie_title].index[0]
    except IndexError:
        # Return default structure if movie is not found
        return [("Movie not found.", "")] * 5 

    distances = similarity[movie_index]

    # Sort the scores and get top 5 indices
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommendations = []

    for i in movies_list:
        # Get the TMDB 'movie_id' from the DataFrame using the internal index
        movie_id = movies.iloc[i[0]]['movie_id'] 
        
        # Append tuple (name, poster_url)
        recommendations.append((movies.iloc[i[0]].title, fetch_poster(movie_id)))

    return recommendations

# --- 4. Flask Application Setup ---
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    # Get the list of all movie titles for the dropdown menu
    movie_titles = movies['title'].values.tolist()
    
    recommendation_data = None
    selected_movie = None
    
    if request.method == 'POST':
        # --- Handle Form Submission ---
        # Get the selected movie name from the form input named 'movie_name'
        selected_movie = request.form.get('movie_name')
        
        if selected_movie:
            # Get recommendations as a list of tuples: [(name1, poster1), (name2, poster2), ...]
            recommendation_data = recommend(selected_movie)

    # Render the index.html template, passing the data it needs
    return render_template(
        'index.html', 
        movie_titles=movie_titles, 
        recommendation_data=recommendation_data,
        selected_movie=selected_movie
    )

if __name__ == "__main__":
    app.run(debug=True)