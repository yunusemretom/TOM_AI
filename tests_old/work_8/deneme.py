import asyncio
from ollama import Client
async def chat(content):
    client = Client(host='http://localhost:11434')  # Varsayılan host
    # GPU kullanımını kontrol etmek için
    response = client.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': content}],
        options={
            'num_gpu': 0  # GPU kullanımı için 1, CPU için 0
        }
    )
    return response.message['content']

print(response.message['content'])
    