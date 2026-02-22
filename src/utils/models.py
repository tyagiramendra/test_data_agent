from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
load_dotenv()

model = init_chat_model(
    "gpt-5-mini-2025-08-07",
    temperature=0
)
