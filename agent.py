# from agents.get_agents import agent_template
from dotenv import load_dotenv
# from utils.callbacks import LLMInstrumentationHandler
# import os
from langchain.llms import VertexAI
from langchain.chat_models import ChatVertexAI
from langchain.schema.messages import HumanMessage
import base64

load_dotenv()
if __name__ == "__main__":
    pass

verbose = True
temp = 0

def retrieve_song_title(query,temp: int):
    llm = VertexAI()
    message = f"Based on this description, name me a song I can play to feel this image. The song should reflect the mood of the image and not only describe it: \nDescription: {query} "
    output = llm(message)
    return output


# Define your agent's flow here. From agent_start, call your other agents orchestating the desired flow. You can use the template below
def agent_start(image, temp: int ):
    llm = ChatVertexAI(model_name="gemini-pro-vision",temperature=temp)
    # image_message = {
    #     "type": "image_url",
    #     "url": f"data:image/jpeg;base64,{base64.b64encode(image).decode('utf-8')}",
    # }

    image_message = {
        "type": "image_url",
        "image_url": {"url": "image_example.png"},
    }
    text_message = {
        "type": "text",
        "text": "I am a blind person so I can't see. Describe me this image with many details and be poetic when doing so. What am I looking at?",
    }
    message = HumanMessage(content=[text_message, image_message])

    output = llm([message])
    return(output.content)


with open("image_example.png", "rb") as image_file:
    image_bytes = image_file.read()

description = agent_start(image_bytes,1.0)
print(description)
print(retrieve_song_title(description,1.0))
