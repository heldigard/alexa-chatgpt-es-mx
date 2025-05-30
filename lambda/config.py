# config.py
# Archivo de configuración para las API keys y otros parámetros sensibles


API_KEY = 'OPENAI_API_KEY'
GITHUB_TOKEN = 'GITHUB_TOKEN'
OPENROUTER_API_KEY = 'OPENROUTER_API_KEY'
CEREBRAS_API_KEY = 'CEREBRAS_API_KEY'
GEMINI_API_KEY = 'GEMINI_API_KEY'
DEEPINFRA_API_KEY = 'DEEPINFRA_API_KEY'  # Nueva API key para Deepinfra

# Puedes forzar el proveedor deseado aquí, por ejemplo: 'openai', 'cerebras_llama4_scout', 'gemini', etc.
FORCED_PROVIDER = None  # Ejemplo: 'openai', 'cerebras_llama4_scout', 'gemini', etc.

# Personalización de país y tono
COUNTRY = "Colombia"
TONE = "colombiano"
