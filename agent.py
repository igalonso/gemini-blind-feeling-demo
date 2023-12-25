from dotenv import load_dotenv
from langchain.llms import VertexAI
from langchain.chat_models import ChatVertexAI
from langchain.schema.messages import HumanMessage
from google.cloud import texttospeech

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pygame
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import googlemaps


load_dotenv()
if __name__ == "__main__":
    pass

verbose = True
temp = 0
finish = 0

def get_image_metadata(image_path):
    # Open the image
    image = Image.open(image_path)

    # Extract the EXIF data
    exif_data = image._getexif()
    if exif_data is not None:
        # Translate the EXIF data to labelled data
        labelled_exif_data = {TAGS[key]: exif_data[key] for key in exif_data.keys() if key in TAGS and isinstance(exif_data[key], (bytes, str))}
        return labelled_exif_data
    else:
        return "No metadata found"
def get_geotagging(image_path):
    image = Image.open(image_path)
    exif = image._getexif()

    if not exif:
        raise ValueError("No EXIF metadata found")

    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                raise ValueError("No EXIF geotagging found")

            for (t, value) in GPSTAGS.items():
                if t in exif[idx]:
                    geotagging[value] = exif[idx][t]

    return geotagging

def get_location_by_coordinates(lat, lon):
    gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY"))
    reverse_geocode_result = gmaps.reverse_geocode((lat, lon))
    address = reverse_geocode_result[0]['formatted_address']
    return address

def get_decimal_from_dms(dms, ref):
    degrees, minutes, seconds = dms
    result = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        result = -result
    return result

def retrieve_song_title(query,temp: int):
    llm = VertexAI()
    message = f"Based on this description, name me a song I can play to feel this image. The song should reflect the mood of the image and not only describe it: \nDescription: {query} "
    output = llm(message)
    return output

def play_mp3(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Call the function with the path to your MP3 file
def text_to_speech(text, filename):
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by language code and name
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Studio-O",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE ,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    # Write the response to the output file.
    with open(filename, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to file "{filename}"')  
    play_mp3('description.mp3')


def start_song(song_name, author):
    # Set your Spotify app credentials
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")


    # Set the scope to allow control of Spotify playback
    scope = "user-modify-playback-state"

    # Authenticate with Spotify
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                   client_secret=SPOTIPY_CLIENT_SECRET,
                                                   redirect_uri=SPOTIPY_REDIRECT_URI,
                                                   scope=scope))

    # Search for the song
    results = sp.search(q=f'track:{song_name} artist:{author}', limit=1)
    if results['tracks']['items']:
        # Get the first song URI
        song_uri = results['tracks']['items'][0]['uri']

        # Start playing the song
        sp.start_playback(uris=[song_uri])
    else:
        print(f"No songs found for {song_name} by {author}")


def agent_start(temp: int, address: str ):
    llm = ChatVertexAI(model_name="gemini-pro-vision",temperature=temp)
    json_format = {
        'description': 'description of the picture',
        'song_name': 'name of the song',
        'author': 'author of the song',
        'reasoning': 'why this song was selected'
    }

    image_message = {
        "type": "image_url",
        "image_url": {"url": "image_example_2.jpg"},
    }
    text_message = {
        "type": "text",
        "text": f"I am a blind person so I can't see. You are a guide to help me feel the photos I share with you. Describe me this image with many details and be poetic when doing so. Give also details of how the weather should look like. What am I looking at? Based on this image, name me a song I can play to feel this image. The song should reflect the mood of the image and not only describe it.The picture was taken in the following address: {address} \n The response should be in json format like this: {json_format}",
    }
    print(text_message)
    message = HumanMessage(content=[text_message, image_message])

    output = llm([message])
    return(output.content)


with open("image_example.png", "rb") as image_file:
    image_bytes = image_file.read()


# # Call the function with the path to your image
# metadata = get_geotagging('image_example.jpeg')

# # Get the latitude and longitude in decimal degrees
# lat = get_decimal_from_dms(metadata['GPSLatitude'], metadata['GPSLatitudeRef'])
# lon = get_decimal_from_dms(metadata['GPSLongitude'], metadata['GPSLongitudeRef'])

# address = get_location_by_coordinates(lat, lon)
# # print(address)
# description = agent_start(0.5, address)
# description = description.replace('```json', '')
# description = description.replace('```', '')
# print(description)

description = {
    'description': 'In the middle of a wide avenue, a yellow tram is passing by. On the avenue, there are a few trees on each side and people are walking on the sidewalk. Tall buildings of different colors are lining up the avenue with their facades adorned with intricate details and cornices. The sky is clear and blue and the sun is shining brightly.',
    'song_name': 'Blue Danube',
    'author': 'Johann Strauss II',
    'reasoning': 'The song "Blue Danube" is a lively and cheerful piece that evokes the feeling of a warm and sunny day, and the joy of being outdoors. The song captures the essence of the image, which is bright and full of life.'
}
description = {
'description': 'The image is of a tree-lined street in Budapest. The leaves on the trees are mostly fallen, and the branches are bare. The street is cobblestone and has tracks for the trams . There is a yellow tram on the tracks, and it is surrounded by people walking on the street. The buildings on either side of the street are tall and imposing, with ornate facades. The sky is blue, and hazy and the sun is shining brightly.',
'song_name': 'Szomorú Vasárnap',
'author': 'Seress Rezső',
'reasoning': 'The song is a melancholic reflection on the end of a relationship. The lyrics describe the singers sadness and loneliness, and the music is slow and mournful. The song was written in 1933, and it has been recorded by many different artists over the years. It is a classic example of Hungarian folk music, and it is one of the most popular songs in the country.'
}
description = {
"description": "The image shows the beautiful city of Budapest, Hungary. The Danube River flows through the city, and there are many bridges crossing the river. The most prominent building in the image is the Hungarian Parliament Building, which is located on the banks of the Danube. The building is a beautiful example of Gothic Revival architecture, and it is one of the most popular tourist destinations in Budapest. The sky is blue with some dark clouds in the background and the sun is shining brightly, creating a warm and inviting atmosphere. There are many boats on the river, and there are people walking and biking along the banks. The image captures the beauty of Budapest and the Danube River, and it is a perfect place to relax and enjoy the scenery.",
"song_name": "Danube Waves",
"author": "Iosif Ivanovici",
"reasoning": "The song \u201cDanube Waves\u201d is an appropriate choice for this image because it is a waltz, and the image is of Budapest, Hungary, which is known for its beautiful architecture and music. The waltz is a traditional European dance that was popular in the 19th century, and is characterized by its slow, graceful movements. The song \u201cDanube Waves\u201d is a beautiful and evocative piece of music that captures the mood of this image perfectly."
}



# desc_json = json.loads(description)
print(description['description'])
start_song(description['song_name'], description['author'])
text_to_speech(description['description'], 'description.mp3')









