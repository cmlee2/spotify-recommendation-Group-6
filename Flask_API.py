import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, Table, MetaData
import sqlite3
from flask_cors import CORS
from flask import Flask, jsonify, render_template, request


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///spotify.sqlite")

metadata = MetaData()
metadata.reflect(bind=engine)

# Save reference to the table
recommendation = metadata.tables['recommendation_table']
top_artist = metadata.tables['top_artist_table']


#################################################
# Copy from main.ipynb
#################################################

from dotenv import load_dotenv
import os
import base64
from requests import post,get
import json
import pprint


# Load Client Secret and Client ID
load_dotenv()

# Load Client Secret and Client ID
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# Get Token for API usage
def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization" : "Basic "+ auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

# Get Authorization Header for API
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

# Get Artist ID from name
def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    query_url = url + query
    result= get(query_url, headers = headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result) == 0:
        print("No artist with this name exists")
        return None
    
    return json_result[0]

# Get Song Recommendations based on artist ID
def get_songs_recommendations(token, artist_id, min_popularity, max_popularity):
    url = f"https://api.spotify.com/v1/recommendations?limit=100&market=US&seed_artists={artist_id}&min_popularity={min_popularity}&max_popularity={max_popularity}"
    headers = get_auth_header(token)
    result = get(url, headers= headers)
    json_result=json.loads(result.content)
    return json_result['tracks']

# Get top 10 songs by artist ID
def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers= headers)
    json_result=json.loads(result.content)["tracks"]
    return json_result

# Get audio features of songs
def get_song_audio_features(token, song_id):
    url = f"https://api.spotify.com/v1/audio-features?ids={','.join(song_id)}"
    headers = get_auth_header(token)
    response = requests.get(url, headers = headers)
    if response.status_code == 200:
        json_result = response.json()  # Use .json() method to parse the JSON data
        return json_result
    else:
        print(f"Failed to fetch audio features. Status code: {response.status_code}")
        return None




#################################################
# Flask Setup
#################################################
app = Flask(__name__)
CORS(app)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return(

        f"Available Routes:<br/>"
        f"/api/v1.0/artist/popularity<br/>"

    )

# @app.route("/results")
# def result():
    
#     return render_template("index.html")

@app.route("/api/v1.0/<artist>/<popularity>")


def names(artist, popularity):
    """Gather necessary recommendations and top songs by artist"""
    print(f"pop value: {popularity}")

    # Calculate range for maximum and minimum popularity
    popularity = int(popularity)
    if popularity <10:
        min_popularty = 0
        max_popularity = popularity +10
    elif popularity >90:
        min_popularty =popularity -10
        max_popularity = 100
    else:
        min_popularty= popularity - 10
        max_popularity = popularity +10

    # Run functions to get token
    token = get_token()

    # Save artist result name
    result = search_for_artist(token, artist)
    artist_id = result["id"]

    # Get song recommendation list
    songs = get_songs_recommendations(token, artist_id, min_popularty, max_popularity)

    # Save empty list to store song list and ID
    recommended_song_list = []
    recommended_song_id = []

    # Loop to save song ID and song recommendation list
    for song in songs:
    # print(song['name'])
    # print(song['id'])
        recommended_song_id.append(song['id'])
        for artist in song['artists']:
        # print(artist['name'])
        # print("------------")
            dict = {
                'name' : song['name'],
                'artist' : artist['name'],
                'id': song['id'],
                'popularity' : song['popularity'],

            }
            recommended_song_list.append(dict)

    # Get the top songs and artists and create empty lists to store them
    top_songs_by_artist = get_songs_by_artist(token, artist_id)
    song_list = []
    song_id = []

    # Loop through the list to save recesary information about top songs
    for song in top_songs_by_artist:
    # print(song['name'])
    # print(song['id'])
        song_id.append(song['id'])
        for artist in song['artists']:
        # print(artist['name'])
        # print("------------")
            dict = {
                'name' : song['name'],
                'artist' : artist['name'],
                'id': song['id'],
                'popularity' : song['popularity']
            }
            song_list.append(dict)

    # Get audio features for recommended songs and top songs
    recommended_features = get_song_audio_features(token, recommended_song_id)
    top_artist_features = get_song_audio_features(token, song_id)




    # Create DataFrames
    df_recommended_audiofeatures =pd.DataFrame(recommended_features['audio_features'])
    df_top_artist_audiofeatures = pd.DataFrame(top_artist_features['audio_features'])


    # Create additional dataFrames and drop duplicates
    df_recommended_song_list = pd.DataFrame(recommended_song_list)
    df_recommended_song_list = df_recommended_song_list.drop_duplicates(subset=['name']).reset_index(drop=True)

    df_top_artist_song_list = pd.DataFrame(song_list)
    df_top_artist_song_list = df_top_artist_song_list.drop_duplicates(subset=['name']).reset_index(drop=True)

    # Merge DF
    recommendations_df = pd.merge(df_recommended_song_list, df_recommended_audiofeatures, on ='id')

    # Add in seconds column
    recommendations_df['duration_s'] = recommendations_df['duration_ms'] / 1000
    recommendations_df

    # Merge DF and add seconds column
    top_artist_df = pd.merge(df_top_artist_song_list, df_top_artist_audiofeatures, on ='id')
    top_artist_df['duration_s'] = top_artist_df['duration_ms'] / 1000
    top_artist_df

    # Connect to SQLlite DB
    connection = sqlite3.connect("spotify.sqlite")

    # Save Tables to DB
    recommendation_table = 'recommendation_table'
    recommendations_df.to_sql(recommendation_table, connection, index = False, if_exists='replace')

    top_artist_table = 'top_artist_table'
    top_artist_df.to_sql(top_artist_table, connection, index = False, if_exists= 'replace')

    # Commit and Close Changes
    connection.commit()
    connection.close()

    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all passenger names"""
    # Query all top songs and recommendations
    top_songs = session.query(top_artist).all()
    top_recommendations = session.query(recommendation).all()

    session.close()
    
    # Save necessary info for top songs
    top_song_list = []


    for artist in top_songs:
        dict = {
            "song": artist.name,
            "artist": artist.artist,
            "popularity": artist.popularity,
            "danceability": artist.danceability,
            "energy": artist.energy,
            "loudness": artist.loudness,
            "speechiness": artist.speechiness,
            "acousticness": artist.acousticness,
            "instamentalness": artist.instrumentalness,
            "liveness": artist.liveness,
            "valence": artist.valence,
            "tempo": artist.tempo,
            "duration": artist.duration_s
        }
        top_song_list.append(dict)

    top_rec_list = []

    # Save necessary info for top recommendations
    for artist in top_recommendations:
        dict = {
            "song": artist.name,
            "artist": artist.artist,
            "popularity": artist.popularity,
            "danceability": artist.danceability,
            "energy": artist.energy,
            "loudness": artist.loudness,
            "speechiness": artist.speechiness,
            "acousticness": artist.acousticness,
            "instamentalness": artist.instrumentalness,
            "liveness": artist.liveness,
            "valence": artist.valence,
            "tempo": artist.tempo,
            "duration": artist.duration_s
        }
        top_rec_list.append(dict)
    data = [top_song_list, top_rec_list]
    return jsonify(data)



if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = 5501,debug=True)
