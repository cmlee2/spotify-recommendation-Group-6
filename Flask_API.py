import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, Table, MetaData
import sqlite3

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
import requests

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

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

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

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

def get_songs_recommendations(token, artist_id, min_popularity, max_popularity):
    url = f"https://api.spotify.com/v1/recommendations?limit=100&market=US&seed_artists={artist_id}&min_popularity={min_popularity}&max_popularity={max_popularity}"
    headers = get_auth_header(token)
    result = get(url, headers= headers)
    json_result=json.loads(result.content)
    return json_result['tracks']

def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers= headers)
    json_result=json.loads(result.content)["tracks"]
    return json_result

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

    token = get_token()
    result = search_for_artist(token, artist)
    artist_id = result["id"]
    songs = get_songs_recommendations(token, artist_id, min_popularty, max_popularity)

    recommended_song_list = []
    recommended_song_id = []

    
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

    top_songs_by_artist = get_songs_by_artist(token, artist_id)
    song_list = []
    song_id = []

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

    recommended_features = get_song_audio_features(token, recommended_song_id)
    top_artist_features = get_song_audio_features(token, song_id)





    df_recommended_audiofeatures =pd.DataFrame(recommended_features['audio_features'])

    df_top_artist_audiofeatures = pd.DataFrame(top_artist_features['audio_features'])

    df_recommended_song_list = pd.DataFrame(recommended_song_list)
    df_recommended_song_list = df_recommended_song_list.drop_duplicates(subset=['name']).reset_index(drop=True)

    df_top_artist_song_list = pd.DataFrame(song_list)
    df_top_artist_song_list = df_top_artist_song_list.drop_duplicates(subset=['name']).reset_index(drop=True)

    recommendations_df = pd.merge(df_recommended_song_list, df_recommended_audiofeatures, on ='id')

    recommendations_df['duration_s'] = recommendations_df['duration_ms'] / 1000
    recommendations_df

    top_artist_df = pd.merge(df_top_artist_song_list, df_top_artist_audiofeatures, on ='id')
    top_artist_df['duration_s'] = top_artist_df['duration_ms'] / 1000
    top_artist_df

    connection = sqlite3.connect("spotify.sqlite")

    recommendation_table = 'recommendation_table'
    recommendations_df.to_sql(recommendation_table, connection, index = False, if_exists='replace')

    top_artist_table = 'top_artist_table'
    top_artist_df.to_sql(top_artist_table, connection, index = False, if_exists= 'replace')

    connection.commit()
    connection.close()

    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all passenger names"""
    # Query all passengers
    top_songs = session.query(top_artist).all()
    top_recommendations = session.query(recommendation).all()

    session.close()
    
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


# @app.route("/api/v1.0/recommendations")
# def passengers():
#     # Create our session (link) from Python to the DB
#     session = Session(engine)

#     """Return a list of passenger data including the name, age, and sex of each passenger"""
#     # Query all passengers
    

#     session.close()

    

#     for artist in top_recommendations:
#         dict = {
#             "song": artist.name,
#             "artist": artist.artist,
#             "popularity": artist.popularity,
#             "danceability": artist.danceability,
#             "energy": artist.energy,
#             "loudness": artist.loudness,
#             "speechiness": artist.speechiness,
#             "acousticness": artist.acousticness,
#             "instamentalness": artist.instrumentalness,
#             "liveness": artist.liveness,
#             "valence": artist.valence,
#             "tempo": artist.tempo,
#             "duration": artist.duration_s
#         }
#         top_rec_list.append(dict)


#     return jsonify(top_rec_list)


if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = 5501,debug=True)
