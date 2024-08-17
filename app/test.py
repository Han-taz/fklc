from openai import OpenAI
from dotenv import load_dotenv
load_dotenv("/home/kevin/PycharmProjects/fklcProject/.env")

client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "담배를 맛있게 피는 법"
        },

    ]
)

print(completion.choices[0].message.content)
