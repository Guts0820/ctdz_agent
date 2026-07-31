import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_client = OpenAI(
    api_key=os.getenv("QIANFAN_API_KEY"),
    base_url="https://qianfan.baidubce.com/v2"
)

def call_llm(system_prompt: str, user_prompt: str, model: str = "ernie-4.5-turbo-32k") -> str:
    completion = _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return completion.choices[0].message.content