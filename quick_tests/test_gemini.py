from google import genai

# Especificando explicitamente a variável de ambiente para a chave da API do Gemini
# ---
import os
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# ---


# Utilizando a variável de ambiente padrão (GEMINI_API_KEY)
# ---
# client = genai.Client()
# ---


# Exibindo uma lista das propriedades de um objeto
print([prop for prop in dir(client.models) if not prop.startswith("_")])

# Gerando um conteúdo com o modelo gemini-3.8-flash
response = client.models.generate_content(model="gemini-3.8-flash", contents="Hello, world!")
print(response.text)

#print([prop for prop in dir(client.models) if not prop.startswith("_")])
