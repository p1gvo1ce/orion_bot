import asyncio
import httpx
import json
import re
from openai import OpenAI
import logging
import os
import random



# Инициализируем клиента с параметрами из файла
client = OpenAI(
    api_key="sk-aitunnel-YxpaQk9kuLd0NqJhhIoiM8EE1DWdHu5Z",
    base_url="https://api.aitunnel.ru/v1/"
)

# Расчёт стоимости токенов
def calculate_cost(total_tokens, price_per_1k_tokens=0.03):
    return (total_tokens / 1000) * price_per_1k_tokens

# Резервная функция через туннель
async def gen_open_ai_text_tunnel(role, text):
    print("Стучимся в OpenAI через туннель")
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": text}
            ],
            max_tokens=1000,
            model="gpt-4.1-mini",
            temperature=0.8
        )
        # Извлечение статистики по токенам
        usage = completion.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
        cost = calculate_cost(total_tokens)

        print(f"Стоимость запроса: ${cost:.6f}")

        return completion.choices[0].message.content

    except Exception as e:
        print(f"OpenAI клиент ошибка: {e}")
        return None

# Функция выбора метода вызова
async def gpt_call(text, role):
    result = await gen_open_ai_text_tunnel(role, text)
    return result

# Тестовая функция
async def main():
    role = "You are a helpful assistant."
    text = "Привет! Как дела?"

    response = await gpt_call(text, role)
    if response:
        print(f"Ответ ИИ: {response}")
    else:
        print("Не удалось получить ответ от обеих функций.")

if __name__ == '__main__':
    asyncio.run(main())