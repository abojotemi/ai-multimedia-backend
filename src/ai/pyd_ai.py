import os
from textwrap import dedent
from google import genai
from google.genai import types
import httpx
from google.genai.errors import ServerError, APIError
from src.schemas.ai import AIOCRResponse, AIResponse

from io import BytesIO
from PIL import Image, ImageDraw
import time


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")
MODELS = (GEMINI_MODEL, "gemini-2.0-flash", "gemini-1.5-flash")


client = genai.Client(api_key=GEMINI_API_KEY)


def run_gemini_chat(chat_messages: list):
    client = genai.Client(
        api_key = GEMINI_API_KEY
    )
    system_prompt = """
SYSTEM PROMPT: You are a customer care assistant with decades of experience. 
Your job is to answer any question related to the applications specification above. 
Always try to explain the problem in a detailed manner. Do you understand. 
Your result should be a txt document, not markdown. Make your answers less than 5 sentences.

Below is the description of the application:
# AI Multimedia Processing Application

Welcome to the AI Multimedia Processing Application! This user guide will help you understand how to use our powerful platform to organize, analyze, and gain insights from your media files.

## What This App Does

The AI Multimedia Processing Application helps you manage your media files (images, videos and audios) and uses artificial intelligence to analyze them. You can organize your media into collections, search through them easily, and get AI-powered insights about your content.

## Getting Started

### Creating Your Account

1. Visit the application's homepage
2. Click on "Sign Up" and enter your email, username, and password
3. Verify your email address if required
4. Log in with your new credentials

### Navigating the Dashboard

After logging in, you'll see your personalized dashboard with:
- Recent uploads
- Media statistics
- Quick access to collections
- Recent AI processing activities

## Working with Your Media

### Uploading Files

1. Click the "Upload" button in the side bar
2. Select files from your computer or drag and drop them
3. Add optional tags and descriptions
4. Click "Upload" to start the process

### Organizing Your Media

#### Creating Collections

1. Go to the "Collections" tab
2. Click "Create New Collection"
3. Name your collection and add an optional description
4. Set privacy settings
5. Add media files from your library or upload new ones

#### Adding Tags

1. Select a media item
2. Click "Edit" or "Manage Tags"
3. Add custom tags or use AI-suggested tags
4. Save your changes

## AI Features

### Processing Your Media

Select any media item and choose from these AI processing options:

#### For Images
- **Smart Analysis**: Identify objects, people, and scenes
- **Text Extraction**: Pull text from images
- **Auto-Tagging**: Get AI-suggested tags
- **Content Screening**: Check for sensitive content

#### For Videos
- **Scene Detection**: Identify objects and scenes
- **Transcription**: Convert speech to text
- **Content Screening**: Check for sensitive content
- **Summary Generation**: Get a concise overview

#### For Audio
- **Transcription**: Convert speech to text
- **Emotion Detection**: Analyze the emotional tone
- **Speaker Identification**: Distinguish between speakers
- **Content Screening**: Check for sensitive language

### Using Custom AI Prompts

1. Select a media item
2. Go to "Custom AI Analysis"
3. Enter your specific question or prompt
4. Wait for the AI to process your request
5. View and save the results

## Searching Your Media

### Basic Search

Use the search bar at the top of the page to find media by:
- Filename
- Tags
- Description
- AI-generated content


## Account Settings

### Profile Management

1. Click on your profile icon
2. Select "Profile Settings"
3. Update your profile information, password, or profile picture


## Privacy and Security

- All your media is stored securely
- You can delete your media  at any time


Enjoy using the AI Multimedia Processing Application to organize and gain insights from your media files"""

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=system_prompt),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="I understand")
            ]
        )
    ]
    for message in chat_messages:
        role: str = "model" if message["role"] == "ai" else message["role"]
        msg: types.Content = types.Content(
            role=role,
            parts=[
                types.Part.from_text(text=message['text']),
            ],
        )
        contents.append(msg)

    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        max_output_tokens=500,
        temperature=0.2,
        top_p=0.8,
        top_k=40,
        
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return response.text


def tag_files(file: dict, tags: list):
    max_retries = 3
    backoff = 1
    mime_type = file["mime_type"]
    mime_type = "jpeg" if mime_type == "jpg" else mime_type
    file_type = file["file_type"] if file["file_type"] != "document" else "application"
    media_response = httpx.get(file["file_url"])
    system_prompt = [
        dedent(f"""
                SYSTEM PROMPT: You are a professional multimedia manager. Your work is to classify/tag, name and describe the content of the {file_type} below. You should give at least 3 descriptive tags and your description of the file should be very detailed. The name should be very short and descriptive. You can use any of the existing tags below or make up yours if you deem it fit. \n{", ".join(tags)}\n. Do you understand?
                """),
        """MODEL: Understood.""",
    ]
    content = media_response.content
    data = types.Part.from_bytes(
        data=content,
        mime_type=f"{file_type}/{mime_type}",
    )
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODELS[attempt - 1],
                contents=[
                    *system_prompt,
                    data,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AIResponse,
                },
            )
            ai_response: AIResponse = response.parsed
            return ai_response
        except ServerError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(
                    f"ServerError on attempt {attempt}, Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed. Exiting.")
                raise
        except APIError as e:
            print(f"APIError: {e.message}")
            raise


def ocr_text_extraction(file: dict):
    max_retries = 3
    backoff = 1
    media_response = httpx.get(file["file_url"])
    system_prompt = [
        dedent(f"""
                SYSTEM PROMPT: You are a professional at extracting text data from {file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}s. Your work is to extract and format text from  the file below. You should make sure the extracted text is formatted in a very readable and clean format. Do you understand?
                """),
        """MODEL: Understood.""",
    ]
    content = media_response.content
    print(f"File Url {file['file_url']}")
    data = types.Part.from_bytes(
        data=content,
        mime_type=f"{file['file_type']}/{file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}",
    )
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODELS[attempt - 1],
                contents=[
                    *system_prompt,
                    data,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AIOCRResponse,
                },
            )
            ai_response: AIOCRResponse = response.parsed
            return ai_response
        except ServerError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(
                    f"ServerError on attempt {attempt}, Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed. Exiting.")
                raise
        except APIError as e:
            print(f"APIError: {e.message}")
            raise


def object_scene_recognition(file: dict):
    max_retries = 3
    backoff = 1
    media_response = httpx.get(file["file_url"])
    system_prompt = [
        dedent(f"""
                SYSTEM PROMPT: You are a professional at identifying objects and scenes in {file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}s. Your work is to identify objects and describe scenes in the file below. Do you understand?
                """),
        """MODEL: Understood.""",
    ]
    content = media_response.content
    print(f"File Url {file['file_url']}")
    data = types.Part.from_bytes(
        data=content,
        mime_type=f"{file['file_type']}/{file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}",
    )
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODELS[attempt - 1],
                contents=[
                    *system_prompt,
                    data,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AIOCRResponse,
                },
            )
            ai_response: AIOCRResponse = response.parsed
            return ai_response
        except ServerError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(
                    f"ServerError on attempt {attempt}, Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed. Exiting.")
                raise
        except APIError as e:
            print(f"APIError: {e.message}")
            raise


def file_summarization(file: dict):
    max_retries = 3
    backoff = 1
    media_response = httpx.get(file["file_url"])
    system_prompt = [
        dedent(f"""
                SYSTEM PROMPT: You are a professional at summarizing {file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}s. Your work is to summarize the file below. You should make sure the summary is formatted in a very readable and clean format. Do you understand?
                """),
        """MODEL: Understood.""",
    ]
    content = media_response.content
    print(f"File Url {file['file_url']}")
    data = types.Part.from_bytes(
        data=content,
        mime_type=f"{file['file_type']}/{file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}",
    )
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODELS[attempt - 1],
                contents=[
                    *system_prompt,
                    data,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AIOCRResponse,
                },
            )
            ai_response: AIOCRResponse = response.parsed
            return ai_response
        except ServerError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(
                    f"ServerError on attempt {attempt}, Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed. Exiting.")
                raise
        except APIError as e:
            print(f"APIError: {e.message}")
            raise


def audio_transcription(file: dict):
    max_retries = 3
    backoff = 1
    media_response = httpx.get(file["file_url"])
    system_prompt = [
        dedent("""
                SYSTEM PROMPT: You are a professional at transcribing audio files. Your work is to transcribe the file below. You should make sure the transcription is formatted in a very readable and clean format. Do you understand?
                """),
        """MODEL: Understood.""",
    ]
    content = media_response.content
    print(f"File Url {file['file_url']}")
    data = types.Part.from_bytes(
        data=content,
        mime_type=f"{file['file_type']}/{file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}",
    )
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODELS[attempt - 1],
                contents=[
                    *system_prompt,
                    data,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AIOCRResponse,
                },
            )
            ai_response: AIOCRResponse = response.parsed
            return ai_response
        except ServerError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(
                    f"ServerError on attempt {attempt}, Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed. Exiting.")
                raise
        except APIError as e:
            print(f"APIError: {e.message}")
            raise


def emotion_analysis(file: dict):
    max_retries = 3
    backoff = 1
    media_response = httpx.get(file["file_url"])
    system_prompt = [
        dedent("""
                SYSTEM PROMPT: You are a professional at analyzing emotions in audio files. Your work is to analyze the emotions in the file below. You should make sure the analysis is formatted in a very readable and clean format. Do you understand?
                """),
        """MODEL: Understood.""",
    ]
    content = media_response.content
    print(f"File Url {file['file_url']}")
    data = types.Part.from_bytes(
        data=content,
        mime_type=f"{file['file_type']}/{file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}",
    )
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODELS[attempt - 1],
                contents=[
                    *system_prompt,
                    data,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AIOCRResponse,
                },
            )
            ai_response: AIOCRResponse = response.parsed
            return ai_response
        except ServerError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(
                    f"ServerError on attempt {attempt}, Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed. Exiting.")
                raise
        except APIError as e:
            print(f"APIError: {e.message}")
            raise


def speaker_identification(file: dict):
    max_retries = 3
    backoff = 1
    media_response = httpx.get(file["file_url"])
    system_prompt = [
        dedent("""
                SYSTEM PROMPT: You are a professional at identifying speakers in audio files. Your work is to identify the different speakers in the file below and the timestamp at when they started talking. You should make sure the identification is formatted in a very readable and clean format. Do you understand?
                """),
        """MODEL: Understood.""",
    ]
    content = media_response.content
    print(f"File Url {file['file_url']}")
    data = types.Part.from_bytes(
        data=content,
        mime_type=f"{file['file_type']}/{file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}",
    )
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODELS[attempt - 1],
                contents=[
                    *system_prompt,
                    data,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AIOCRResponse,
                },
            )
            ai_response: AIOCRResponse = response.parsed
            return ai_response
        except ServerError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(
                    f"ServerError on attempt {attempt}, Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed. Exiting.")
                raise
        except APIError as e:
            print(f"APIError: {e.message}")
            raise


def draw_on_img(url: str, boxes: list[tuple]):
    response = httpx.get(url)
    img = Image.open(BytesIO(response.content)).convert("RGBA")

    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    for x, y, w, h in boxes:
        bbox = (x, y, x + w, y + h)
        draw.rectangle(bbox, fill=(255, 0, 0, 128), outline=(255, 0, 0, 255), width=3)

    combined = Image.alpha_composite(img, overlay)
    return combined


def object_face_recognition(file: dict):
    max_retries = 3
    backoff = 1
    media_response = httpx.get(file["file_url"])
    system_prompt = [
        dedent(f"""
                SYSTEM PROMPT: You are a professional at identifying objects and faces in {file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}s. Your work is to identify objects and faces in the file below. Do you understand?
                """),
        """MODEL: Understood.""",
    ]
    content = media_response.content
    print(f"File Url {file['file_url']}")
    data = types.Part.from_bytes(
        data=content,
        mime_type=f"{file['file_type']}/{file['mime_type'] if file['mime_type'] != 'jpg' else 'jpeg'}",
    )
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODELS[attempt - 1],
                contents=[
                    *system_prompt,
                    data,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AIOCRResponse,
                },
            )
            ai_response: AIOCRResponse = response.parsed
            return ai_response
        except ServerError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(
                    f"ServerError on attempt {attempt}, Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                print("All attempts failed. Exiting.")
                raise
        except APIError as e:
            print(f"APIError: {e.message}")
            raise


# Processing_option: Function_mapping
image_processing_options = {
    "Content Categorization": tag_files,
    "Object/Face Recognition": object_face_recognition,
    "Content Moderation": tag_files,
    "OCR Text Extraction": ocr_text_extraction,
    "Auto Tagging": tag_files,
}

video_processing_options = {
    "Content Categorization": tag_files,
    "Object/Scene Recognition": object_scene_recognition,
    "Audio Transcription": audio_transcription,
    "Content Moderation": tag_files,
    "Auto Tagging": tag_files,
    "Video Summarization": file_summarization,
}

audio_processing_options = {
    "Content Categorization": tag_files,
    "Audio Transcription": audio_transcription,
    "Content Moderation": tag_files,
    "Emotion Analysis": emotion_analysis,
    "Speaker Identification": speaker_identification,
}

document_processing_options = {
    "Content Categorization": tag_files,
    "OCR Processing": ocr_text_extraction,
    "Document Summarization": file_summarization,
    "Document Classification": tag_files,
    "Entity Extraction": ocr_text_extraction,
}