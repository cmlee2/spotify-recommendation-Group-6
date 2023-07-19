from dotenv import load_dotenv
import os
import base64

import json
import pprint
import requests
from requests import post,get

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

token = get_token()
result = search_for_artist(token, "Tyler, the Creator")
artist_id = result["id"]
songs = get_songs_recommendations(token, artist_id, 20, 40)
top_songs_by_artist = get_songs_by_artist(token, artist_id)


audio = get_song_audio_features(token, '410ZZP746AQeiywhKvXWCo')
print(audio)