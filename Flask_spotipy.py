# import necessary modules
import pandas as pd
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, Table, MetaData
from flask_cors import CORS
import spotipy
from flask import Flask, request, url_for, session, redirect,jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS
from spotipy.oauth2 import SpotifyClientCredentials


load_dotenv()

def get_token():
    cid = os.getenv("CLIENT_ID")
    secret =  os.getenv("CLIENT_SECRET")
    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp



# initialize Flask app

app = Flask(__name__)
CORS(app)

def song_rec_dict(songs):
    recommended_song_id = []
    recommended_song_list = []
    for song in songs:
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
    return {
        'song_id': recommended_song_id,
        'song_list': recommended_song_list
        }


# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = 'YOUR_SECRET_KEY'

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

# route to handle logging in
@app.route('/')
def login():
    return """
    /api/v1.0/artist <br>
    /api/v1.0/artist/popularity"""


@app.route('/api/v1.0/<artist>')
def top_songs(artist):

    # create a Spotipy instance with the access token
    sp = get_token()

    artist_id = sp.search(q=artist, type = 'artist')
    artist_id = artist_id['artists']['items'][0]['uri']
    
    top_tracks = sp.artist_top_tracks(artist_id, country = 'US')

    song_list = []
    song_id = []

    # Loop through the list to save recesary information about top songs
    for song in top_tracks['tracks']:
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


    # Get audiofeatures from top songs
    top_artist_features = sp.audio_features(song_id)

    # Create DataFrames
    df_top_artist_audiofeatures = pd.DataFrame(top_artist_features)



    # Create additional dataFrames and drop duplicates
    df_top_artist_song_list = pd.DataFrame(song_list)
    df_top_artist_song_list = df_top_artist_song_list.drop_duplicates(subset=['name']).reset_index(drop=True)



    # Merge DF and add seconds column
    top_artist_df = pd.merge(df_top_artist_song_list, df_top_artist_audiofeatures, on ='id')
    top_artist_df['duration_s'] = top_artist_df['duration_ms'] / 1000
    top_artist_df = top_artist_df[[
        'name','artist','popularity','danceability','energy','loudness','speechiness','acousticness',
        'instrumentalness','liveness','valence','tempo','duration_s']]

    top_artist_songs = top_artist_df.values.tolist() 

    top_song_list = []


    for song in top_artist_songs:
        dict = {
            "song": song[0],
            "artist": song[1],
            "popularity": song[2],
            "danceability": song[3],
            "energy": song[4],
            "loudness": song[5],
            "speechiness": song[6],
            "acousticness": song[7],
            "instrumentalness": song[8],
            "liveness": song[9],
            "valence":song[10],
            "tempo": song[11],
            "duration": song[12],
        }
        top_song_list.append(dict)

    data = top_song_list
    return jsonify(data)


@app.route('/api/v1.0/<artist>/<popularity>')
def top_recs(artist,popularity):

    # Calculate range for maximum and minimum popularity
    popularity = int(popularity)
    if popularity <10:
        min_popularty = 0
        max_popularity = popularity +20
    elif popularity >80:
        min_popularty =popularity -20
        max_popularity = 100
    else:
        min_popularty= popularity - 20
        max_popularity = popularity +20


    # create a Spotipy instance with the access token
    sp = get_token()

    artist_id = sp.search(q=artist, type = 'artist')
    artist_id = artist_id['artists']['items'][0]['uri']

    hundred_recs = sp.recommendations(seed_artists=[artist_id], limit=100, country='US', min_popularity = min_popularty, max_popularity = max_popularity)
    
    hundred_recs = hundred_recs['tracks']

    song_lists = song_rec_dict(hundred_recs)

    top_rec_features = sp.audio_features(song_lists['song_id'])

    # Create DataFrames
    df_top_rec_audiofeatures = pd.DataFrame(top_rec_features)



    # Create additional dataFrames and drop duplicates
    df_top_rec_song_list = pd.DataFrame(song_lists['song_list'])
    df_top_rec_song_list = df_top_rec_song_list.drop_duplicates(subset=['name']).reset_index(drop=True)

    top_rec_df = pd.merge(df_top_rec_song_list, df_top_rec_audiofeatures, on ='id')
    top_rec_df['duration_s'] = top_rec_df['duration_ms'] / 1000
    top_rec_df = top_rec_df[[
        'name','artist','popularity','danceability','energy','loudness','speechiness','acousticness',
        'instrumentalness','liveness','valence','tempo','duration_s']]

    top_rec_songs = top_rec_df.values.tolist() 

    top_rec_list = []


    for song in top_rec_songs:
        dict = {
            "song": song[0],
            "artist": song[1],
            "popularity": song[2],
            "danceability": song[3],
            "energy": song[4],
            "loudness": song[5],
            "speechiness": song[6],
            "acousticness": song[7],
            "instrumentalness": song[8],
            "liveness": song[9],
            "valence":song[10],
            "tempo": song[11],
            "duration": song[12],
        }
        top_rec_list.append(dict)

    data = top_rec_list
    return jsonify(data)




if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = 5501,debug=True)