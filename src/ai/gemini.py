import os
from textwrap import dedent
import google.generativeai as genai
import base64
import httpx

prompt = dedent("""
        You are analyzing a math problem presented as an image. 
        Do not attempt to solve the problem. Your task is to extract and structure all relevant information 
        from the image that will aid the solver. This includes any text, variables, constants, 
        equations, formulas, symbols, and diagrams. Label each component clearly and provide a detailed description 
        of the mathematical content, such as identifying variables, constants, and the type of equation or expression. 
        Focus on organizing this information in a structured format that can be easily used by the math solver.
""")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL")
genai.configure(api_key=GEMINI_API_KEY)


def run_gemini(argument: str) -> str:
    model = genai.GenerativeModel(model_name=MODEL_NAME)
    missing_padding = len(argument) % 4
    if missing_padding:
        argument += "=" * (4 - missing_padding)
    image_data = base64.b64decode(argument)

    # Construct messages for the generative model
    messages = [{"mime_type": "image/png", "data": image_data}, {"text": prompt}]

    response = model.generate_content(messages)
    return response.text

def run_gemini_chat(message: str):
    messages = [
        {
            "role": "user",
            "parts": [
                {
                    "text": dedent("""
                    SYSTEM PROMPT: You are a professional Mathematics tutor with decades of experience. 
                    Your job is to answer any question mathematically related. 
                    You refrain from answering any question that isn't related to the mathematics. 
                    Your name is MathBOT
                    You always explain the problem in great details. Do you understand?
                    """)
                }
            ],
        },
        {
            "role": "model",
            "parts": [{"text": "Understood."}],
        },
    ]
    model = genai.GenerativeModel(model_name=MODEL_NAME)

    role = "user"
    msg: dict[str, str | list] = {"role": role, "parts": []}
    if message.get("image"):
        response = httpx.get(message["image"])
        mime_type = response.headers.get("Content-Type")
        msg["parts"].append(
            {
                "mime_type": f"image/{mime_type}",
                "data": base64.b64encode(s=response.content).decode("utf-8"),
            }
        )

    if message.get("audio"):
        response = httpx.get(message["audio"])
        mime_type = response.headers.get("Content-Type")
        msg["parts"].append(
            {"mime_type": f"audio/{mime_type}", "data": response.content}
        )

    if message.get("text"):
        msg["parts"].append({"text": message["text"]})

    messages.append(msg)
    response = model.generate_content(messages)
    return response.text
