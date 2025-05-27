from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
import ask_sdk_core.utils as ask_utils
import requests
import logging
import json
import random
import os
from config import API_KEY, GITHUB_TOKEN, OPENROUTER_API_KEY, CEREBRAS_API_KEY, GEMINI_API_KEY, FORCED_PROVIDER, COUNTRY, TONE

reprompts = [
    "¿Qué más te gustaría saber?",
    "¿Hay algo más que quieras preguntarme?",
    "¿Tienes otra pregunta?",
    "¿En qué más puedo ayudarte?",
    "¿Quieres que te explique algo más?",
    "¿Hay algún otro tema que te interese?",
    "¿Necesitas ayuda con algo más?"
]

CONTENT_TYPE_JSON = "application/json"

# Constantes para OpenRouter
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_REFERER = "https://alexa-chatgpt.com"
OPENROUTER_TITLE = "Alexa ChatGPT Skill"

# IMPORTANTE: En producción, configurar estas variables
api_key = API_KEY
github_token = GITHUB_TOKEN
openrouter_api_key = OPENROUTER_API_KEY
cerebras_api_key = CEREBRAS_API_KEY
gemini_api_key = GEMINI_API_KEY

# Configuración para cada proveedor
PROVIDERS = {
    # Gemini 2.0 Flash (Google API directo, solo texto)
    "gemini_20": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "model": "gemini-2.0-flash",
        "get_headers": lambda key: {
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: gemini_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    # Gemini 2.5 Flash Preview (Google API directo, solo texto)
    "gemini_25": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent",
        "model": "gemini-2.5-flash-preview-05-20",
        "get_headers": lambda key: {
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: gemini_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4.1-mini",  # Modelo más actualizado y eficiente
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: api_key,
        "max_tokens": 800,
        "timeout": 8
    },
    "github": {
        "url": "https://models.github.ai/inference/chat/completions",
        "model": "openai/gpt-4.1-mini",  # Modelo GPT-4.1 Mini a través de GitHub
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: github_token,
        "max_tokens": 800,
        "timeout": 8
    },
    "openrouter": {
        "url": OPENROUTER_URL,
        "model": "meta-llama/llama-4-maverick",  # Modelo más inteligente para conversaciones
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,  # Requerido por OpenRouter
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    # Nuevos modelos gratuitos de OpenRouter
    "deepseek_r1_distill_llama_70b": {
        "url": OPENROUTER_URL,
        "model": "deepseek/deepseek-r1-distill-llama-70b:free",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "deepseek_r1": {
        "url": OPENROUTER_URL,
        "model": "deepseek/deepseek-r1",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "deepseek_r1_free": {
        "url": OPENROUTER_URL,
        "model": "deepseek/deepseek-r1:free",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "deepseek_chimera": {
        "url": OPENROUTER_URL,
        "model": "tngtech/deepseek-r1t-chimera:free",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "qwen3_235b_free": {
        "url": OPENROUTER_URL,
        "model": "qwen/qwen3-235b-a22b:free",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "qwen3_235b": {
        "url": OPENROUTER_URL,
        "model": "qwen/qwen3-235b-a22b",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "microsoft_mai": {
        "url": OPENROUTER_URL,
        "model": "microsoft/mai-ds-r1:free",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "llama_maverick": {
        "url": OPENROUTER_URL,
        "model": "meta-llama/llama-4-maverick:free",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "qwen_qwq_free": {
        "url": OPENROUTER_URL,
        "model": "qwen/qwq-32b:free",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "qwen_qwq": {
        "url": OPENROUTER_URL,
        "model": "qwen/qwq-32b",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    # DeepSeek Chat v3 versión actualizada
    "deepseek_chat_v3": {
        "url": OPENROUTER_URL,
        "model": "deepseek/deepseek-chat-v3-0324",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "deepseek_chat_v3_free": {
        "url": OPENROUTER_URL,
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    # OpenAI GPT-4.1 Mini (versión mejorada)
    "openai_gpt41_mini": {
        "url": OPENROUTER_URL,
        "model": "openai/gpt-4.1-mini",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    # Google Gemini 2.0 Flash (solo texto para Alexa)
    "google_gemini_20": {
        "url": OPENROUTER_URL,
        "model": "google/gemini-2.0-flash-001",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    # Google Gemini 2.5 Flash Preview (solo texto para Alexa)
    "google_gemini_25": {
        "url": OPENROUTER_URL,
        "model": "google/gemini-2.5-flash-preview-05-20",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        },
        "get_key": lambda: openrouter_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "model": "llama-4-scout-17b-16e-instruct",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: cerebras_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "cerebras_llama4_scout": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "model": "llama-4-scout-17b-16e-instruct",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: cerebras_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "cerebras_llama33_70b": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "model": "llama-3.3-70b",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: cerebras_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "cerebras_qwen3_32b": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "model": "qwen-3-32b",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: cerebras_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
    "cerebras_deepseek_r1_distill_llama_70b": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "model": "deepseek-r1-distill-llama-70b",
        "get_headers": lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON
        },
        "get_key": lambda: cerebras_api_key,
        "max_tokens": 800,
        "timeout": 10
    },
}

def select_random_provider():
    """Selecciona un proveedor aleatorio de los disponibles o el forzado si está definido"""
    if FORCED_PROVIDER and FORCED_PROVIDER in AVAILABLE_PROVIDERS:
        return FORCED_PROVIDER
    return random.choice(AVAILABLE_PROVIDERS)

def get_next_provider(current_provider, failed_providers):
    """Obtiene el siguiente proveedor disponible excluyendo los que han fallado"""
    available = [p for p in AVAILABLE_PROVIDERS if p not in failed_providers]
    if not available:
        return None
    # Si el proveedor current_provider aún no ha fallado, lo excluimos de las opciones
    if current_provider in available:
        available.remove(current_provider)
    return random.choice(available) if available else None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Validar que al menos una API key esté configurada
available_providers = []
if api_key:
    available_providers.append("openai")
if github_token:
    available_providers.append("github")
if openrouter_api_key:
    # Agregar OpenRouter original y todos los modelos gratuitos
    # DeepSeek: Modelos especializados en razonamiento y chat
    # Qwen: Modelos de Alibaba con capacidades multilingües
    # Microsoft MAI: Modelo de razonamiento de Microsoft
    # Meta Llama: Último modelo de Meta (solo texto para Alexa)
    available_providers.extend([
        "openrouter",        # Llama 4 Maverik
        "deepseek_r1_distill_llama_70b",     # DeepSeek Distill Llama 70B
        "deepseek_r1",       # DeepSeek R1 reasoning
        "deepseek_r1_free",  # DeepSeek R1 reasoning (gratuito)
        "deepseek_chimera",  # DeepSeek R1T Chimera (gratuito)
        "qwen3_235b_free",   # Qwen 235B (gratuito)
        "qwen3_235b",        # Qwen 235B (pago)
        "microsoft_mai",     # Microsoft MAI DS R1 (gratuito)
        "llama_maverick",    # Meta Llama 4 Maverick (gratuito)
        "qwen_qwq_free",     # Qwen QwQ 32B (gratuito)
        "qwen_qwq",          # Qwen QwQ 32B (pago)
        "deepseek_chat_v3",  # DeepSeek Chat v3 actualizado
        "deepseek_chat_v3_free",    # DeepSeek Chat v3 gratuito
        "openai_gpt41_mini", # OpenAI GPT-4.1 Mini (mejorado)
        "google_gemini_20",  # Google Gemini 2.0 Flash
        "google_gemini_25"   # Google Gemini 2.5 Flash Preview
    ])
if gemini_api_key:
    available_providers.extend([
        "gemini_20",  # Gemini 2.0 Flash (Google API directo)
        "gemini_25"   # Gemini 2.5 Flash Preview (Google API directo)
    ])
# Cerebras: agregar si la API key está presente
if cerebras_api_key:
    available_providers.extend([
        "cerebras",  # Llama 4 Scout (por defecto)
        "cerebras_llama4_scout",
        "cerebras_llama33_70b",
        "cerebras_qwen3_32b",
        "cerebras_deepseek_r1_distill_llama_70b"
    ])

if not available_providers:
    logger.error("No hay API keys configuradas")
    raise ValueError("Por favor configura al menos una API key en las variables de entorno")

# Actualizar lista de proveedores disponibles basado en las API keys configuradas
AVAILABLE_PROVIDERS = available_providers
logger.info(f"Proveedores disponibles: {AVAILABLE_PROVIDERS}")

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Hola, soy tu asistente inteligente. ¿En qué puedo ayudarte hoy?"

        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["chat_history"] = []
        # Seleccionar proveedor aleatorio al inicio de la sesión
        session_attr["current_provider"] = select_random_provider()
        session_attr["failed_providers"] = []

        logger.info(f"Sesión iniciada con proveedor: {session_attr['current_provider']}")

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(random.choice(reprompts))
                .response
        )

class GptQueryIntentHandler(AbstractRequestHandler):
    """Handler for Gpt Query Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            query = handler_input.request_envelope.request.intent.slots["query"].value

            # Verificar que la query no esté vacía
            if not query or not query.strip():
                speak_output = "No he recibido tu pregunta correctamente. ¿Puedes repetirla?"
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask(random.choice(reprompts))
                        .response
                )

            session_attr = handler_input.attributes_manager.session_attributes
            # Mantener memoria durante toda la sesión
            if "chat_history" not in session_attr:
                session_attr["chat_history"] = []
            if "current_provider" not in session_attr:
                session_attr["current_provider"] = select_random_provider()
            # Seleccionar proveedor aleatorio al inicio de la sesión
            if "failed_providers" not in session_attr:
                session_attr["failed_providers"] = []

            response, error_type = generate_gpt_response(session_attr, query)

            logger.info(f"Respuesta final - error_type: {error_type}, longitud_respuesta: {len(response) if response else 0}")

            # Si hay error de conexión/modelo, invitar a reintentar
            if error_type == "connection":
                speak_output = random.choice(retry_prompts)
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask(speak_output)
                        .response
                )

            # Verificar que la respuesta no esté vacía
            if not response or not response.strip():
                response = "Lo siento, no pude generar una respuesta en este momento. ¿Puedes intentar con otra pregunta?"

            # Solo agregar al historial si la respuesta fue exitosa (no contiene "Error")
            if error_type is None:
                session_attr["chat_history"].append((query, response))
                # Mantener solo las últimas 8 interacciones para optimizar tokens
                if len(session_attr["chat_history"]) > 8:
                    session_attr["chat_history"] = session_attr["chat_history"][-8:]

            return (
                handler_input.response_builder
                    .speak(response)
                    .ask(random.choice(reprompts))
                    .response
            )

        except Exception as e:
            logger.error(f"Error en GptQueryIntentHandler: {str(e)}")
            fallback_response = "Disculpa, tuve un problema procesando tu pregunta. ¿Puedes intentar de nuevo?"
            return (
                handler_input.response_builder
                    .speak(fallback_response)
                    .ask(random.choice(reprompts))
                    .response
            )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        logger.error(f"Error global capturado: {str(exception)}", exc_info=True)

        # Respuestas de error más específicas según el tipo de excepción
        if "timeout" in str(exception).lower():
            speak_output = "El servicio está tardando más de lo normal. Por favor, intenta de nuevo."
        elif "connection" in str(exception).lower():
            speak_output = "Hay un problema de conexión temporalmente. Por favor, inténtalo en unos momentos."
        elif "json" in str(exception).lower():
            speak_output = "Hubo un problema procesando la respuesta. ¿Puedes intentar con otra pregunta?"
        else:
            speak_output = "Lo siento, tuve un problema al procesar tu solicitud. Por favor, intenta de nuevo."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .set_should_end_session(True)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "¡Hasta pronto! Espero haberte sido de ayuda. Puedes volver a preguntarme cuando quieras."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = ("Soy tu asistente inteligente personal. Puedes preguntarme sobre cualquier tema: "
                       "ciencia, historia, tecnología, cocina, deportes, entretenimiento y mucho más. "
                       "Por ejemplo, puedes decir: 'explícame qué es la inteligencia artificial' o "
                       "'cuéntame sobre la cultura mexicana'. ¿Qué te gustaría saber?")
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("¿Sobre qué tema te gustaría que conversemos?")
                .response
        )

class NewTopicIntentHandler(AbstractRequestHandler):
    """Handler para cambiar de tema o reiniciar conversación"""
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.StartOverIntent")(handler_input) or
                ask_utils.is_intent_name("NewTopicIntent")(handler_input))

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes

        # Prevenir loop: si ya se reinició el tema en este turno, no volver a hacerlo
        if session_attr.get("just_restarted_topic"):
            speak_output = "¿Sobre qué tema te gustaría conversar?"
            # No repite el loop, solo repregunta una vez
            session_attr["just_restarted_topic"] = False
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(random.choice(reprompts))
                    .response
            )

        # Limpiar historial pero mantener el proveedor actual
        session_attr["chat_history"] = []
        session_attr["just_restarted_topic"] = True

        speak_output = "¡Perfecto! Empecemos con un tema nuevo. ¿Sobre qué te gustaría conversar ahora?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(random.choice(reprompts))
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> None
        session_attr = handler_input.attributes_manager.session_attributes
        current_provider = session_attr.get("current_provider", "unknown")

        logger.info(f"Sesión terminada. Proveedor usado: {current_provider}")

        # Cleanup any session data if needed
        # No response is returned for SessionEndedRequest
        return None

# Mensajes para reintentar en caso de error de conexión/modelo
retry_prompts = [
    "Parece que hubo un problema de conexión. ¿Quieres intentarlo de nuevo?",
    "No pude conectarme al servicio. ¿Quieres que lo intente otra vez?",
    "El modelo no respondió. ¿Deseas que lo intente de nuevo?",
    "Hubo un error temporal. ¿Intento responderte otra vez?",
    "No logré obtener respuesta. ¿Quieres reintentar tu pregunta?"
]

def generate_gpt_response(session_attr, new_question):
    """
    Genera respuesta usando el proveedor actual con fallback automático en caso de error
    Devuelve (respuesta, tipo_de_error) donde tipo_de_error puede ser None, 'connection', 'other'
    """
    # Si hay un proveedor forzado, siempre usarlo
    if FORCED_PROVIDER and FORCED_PROVIDER in AVAILABLE_PROVIDERS:
        session_attr["current_provider"] = FORCED_PROVIDER
        session_attr["failed_providers"] = []

    current_provider = session_attr.get("current_provider")
    failed_providers = session_attr.get("failed_providers", [])
    chat_history = session_attr.get("chat_history", [])

    # Si no hay proveedor actual, seleccionar uno
    if not current_provider or current_provider in failed_providers:
        available = [p for p in AVAILABLE_PROVIDERS if p not in failed_providers]
        if available:
            current_provider = random.choice(available)
            session_attr["current_provider"] = current_provider
        else:
            # Si todos han fallado, reiniciar la lista de fallos y intentar de nuevo
            session_attr["failed_providers"] = []
            current_provider = select_random_provider()
            session_attr["current_provider"] = current_provider

    logger.info(f"Intentando con proveedor principal: {current_provider}")

    # Intentar con el proveedor actual
    response, error_type = try_provider(current_provider, chat_history, new_question)

    logger.info(f"Resultado del proveedor {current_provider}: error_type={error_type}, respuesta_vacia={not response or not response.strip()}")

    # SOLO hacer fallback si realmente hay un error de conexión
    if error_type == "connection" and current_provider not in failed_providers:
        logger.warning(f"Proveedor {current_provider} falló con error de conexión, iniciando fallback...")
        session_attr["failed_providers"].append(current_provider)

        # Intentar hasta 3 proveedores diferentes
        for attempt in range(3):
            next_provider = get_next_provider(current_provider, session_attr["failed_providers"])

            if next_provider:
                session_attr["current_provider"] = next_provider
                logger.info(f"Fallback intento {attempt + 1}: Cambiando a proveedor: {next_provider}")
                response, error_type = try_provider(next_provider, chat_history, new_question)
                logger.info(f"Resultado del fallback {next_provider}: error_type={error_type}")

                if error_type is None:
                    # Éxito con el fallback, salir del bucle
                    logger.info(f"Fallback exitoso con {next_provider}")
                    break
                else:
                    # Este proveedor también falló
                    session_attr["failed_providers"].append(next_provider)
                    current_provider = next_provider
            else:
                # No hay más proveedores disponibles
                logger.warning("No hay más proveedores disponibles para fallback")
                break

        # Si aún hay error después de todos los intentos
        if error_type == "connection":
            # Reiniciar lista de proveedores fallidos para el siguiente intento
            session_attr["failed_providers"] = []
            session_attr["current_provider"] = select_random_provider()
            response = "Lo siento, todos los servicios de inteligencia artificial están temporalmente no disponibles. Por favor, inténtalo de nuevo en unos minutos."
            logger.error("Todos los proveedores fallaron, devolviendo mensaje de error")
            return response, "connection"
    else:
        if error_type is None:
            logger.info(f"Respuesta exitosa del proveedor principal: {current_provider}")
        elif error_type != "connection":
            logger.warning(f"Error no relacionado con conexión en {current_provider}: {error_type}")

    # Si la respuesta fue exitosa, limpiar la lista de proveedores fallidos
    if error_type is None:
        session_attr["failed_providers"] = []

    return response, error_type

def try_provider(provider_name, chat_history, new_question):
    """
    Intenta obtener respuesta de un proveedor específico
    Devuelve (respuesta, tipo_de_error) donde tipo_de_error puede ser None, 'connection', 'other'
    """

    try:
        if provider_name not in PROVIDERS:
            logger.error(f"Proveedor {provider_name} no encontrado en configuración")
            return f"Error: Proveedor {provider_name} no configurado", "other"

        provider = PROVIDERS[provider_name]
        key = provider["get_key"]()

        # Verificar que la API key esté disponible
        if not key or key == "YOUR_API_KEY":
            logger.error(f"API key no configurada para {provider_name}")
            return f"Error: API key no configurada para {provider_name}", "other"

        headers = provider["get_headers"](key)
        url = provider["url"]
        model = provider["model"]
        timeout = provider.get("timeout", 8)

        # Gemini Google API (directo)
        if provider_name in ["gemini_20", "gemini_25"]:
            # Construir el prompt para Gemini
            system_prompt = f"""Eres un asistente de inteligencia artificial especializado en responder en español de manera clara y concisa para personas de {COUNTRY}.

REGLAS IMPORTANTES:
- Responde SIEMPRE en español, sin importar el idioma de la pregunta
- Sé conversacional, amigable y natural como si fueras un amigo conocedor con un toque {TONE}
- Máximo 150 palabras por respuesta para mantener la atención
- Usa ejemplos y referencias culturales de {COUNTRY} cuando sea relevante
- Si no sabes algo, admítelo honestamente
- Evita jerga técnica excesiva, explica de forma simple

Tu objetivo es ser útil, informativo y entretenido para usuarios de habla hispana de {COUNTRY}."""
            contents = []

            # Agregar el system prompt como parte inicial si aplica
            if system_prompt:
                contents.append({
                    "role": "user",
                    "parts": [{"text": system_prompt}]
                })

            # Historial (últimas 6 interacciones)
            for question, answer in chat_history[-6:]:
                contents.append({"role": "user", "parts": [{"text": question}]})
                contents.append({"role": "model", "parts": [{"text": answer}]})
            # Agregar la nueva pregunta del usuario
            contents.append({"role": "user", "parts": [{"text": new_question}]})

            data = {"contents": contents}
            # La API key va en la URL como ?key=...
            url = f"{url}?key={key}"
            logger.info(f"Enviando request a Gemini directo: {provider_name}")
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout)
            if not response.ok:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f": {error_data['error'].get('message', 'Error desconocido')}"
                except json.JSONDecodeError:
                    error_msg += f": {response.text[:100]}"
                logger.error(f"Error HTTP en Gemini: {error_msg}")
                if response.status_code >= 500:
                    return f"Error {error_msg}", "connection"
                return f"Error {error_msg}", "other"
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                logger.error("Error parseando JSON de Gemini: %s", str(e))
                return "Error: Respuesta inválida de Gemini", "other"
            logger.info(f"Respuesta JSON recibida de Gemini: {list(response_data.keys())}")
            # Gemini responde con 'candidates' y dentro 'content'->'parts'
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                candidate = response_data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    # Concatenar todos los textos de los parts
                    content = " ".join([p.get('text', '') for p in candidate['content']['parts']]).strip()
                    if content:
                        logger.info(f"Respuesta exitosa de Gemini: {len(content)} caracteres")
                        return content, None
                    else:
                        logger.error("Respuesta vacía de Gemini")
                        return "Error: Respuesta vacía de Gemini", "connection"
                else:
                    logger.error("Formato de respuesta inválido de Gemini: candidate=%s", str(candidate))
                    return "Error: Formato de respuesta inválido de Gemini", "other"
            else:
                error_msg = response_data.get('error', {}).get('message', 'Formato de respuesta inesperado')
                logger.error(f"Error en respuesta de Gemini: {error_msg}, keys={list(response_data.keys())}")
                return f"Error: {error_msg}", "connection"

        # Otros proveedores (OpenAI, OpenRouter, etc)
        # Crear mensajes optimizados para español
        messages = [{
            "role": "system",
            "content": f"""Eres un asistente de inteligencia artificial con un toque latino {TONE}, especializado en responder de manera clara, concisa y amigable, ideal para una conversación por voz.

REGLAS CLAVE PARA RESPONDER:
- Habla siempre en español latino {TONE}, con un tono amable y cercano.
- Tus respuestas deben ser como una charla fluida: naturales, conversacionales y fáciles de entender al escucharlas.
- Sé breve y al grano: idealmente no más de 120-180 palabras, para que sea fácil seguirte la conversación solo con audio.
- Cuando sea apropiado y encaje de forma natural, incluye ejemplos o referencias culturales de {COUNTRY}.
- Si no tienes la respuesta a algo, admítelo con sinceridad. Es mejor ser honesto.
- Explica las cosas de forma sencilla, evitando términos muy técnicos, para que todos te puedan entender.

Tu misión es ser un parcero conversador y útil: que la gente en {COUNTRY} disfrute charlar contigo y encuentre valor en tus respuestas."""
        }]

        # Agregar historial reciente (máximo 6 intercambios para optimizar tokens)
        for question, answer in chat_history[-6:]:
            messages.append({"role": "user", "content": question})
            messages.append({"role": "assistant", "content": answer})

        messages.append({"role": "user", "content": new_question})

        data = {
            "model": model,
            "messages": messages,
            "max_tokens": provider.get("max_tokens", 800),
            "temperature": 0.8,  # Más creatividad para conversaciones naturales
        }

        # Ajustes específicos por proveedor
        if provider_name == "github":
            data.pop("presence_penalty", None)
            data.pop("frequency_penalty", None)
            data["top_p"] = 0.9
        elif provider_name in [
            "openrouter", "deepseek_r1_distill_llama_70b", "deepseek_r1", "deepseek_r1_free",
            "deepseek_chimera", "qwen3_235b_free", "qwen3_235b", "microsoft_mai", "llama_maverick",
            "qwen_qwq_free", "qwen_qwq", "deepseek_chat_v3", "deepseek_chat_v3_free",
            "openai_gpt41_mini", "google_gemini_20", "google_gemini_25"
        ]:
            # Configuración optimizada para modelos de OpenRouter (incluye nuevos modelos)
            data["presence_penalty"] = 0.1
            data["frequency_penalty"] = 0.1
            data["top_p"] = 0.9
        elif provider_name.startswith("cerebras"):
            # Configuración específica para Cerebras
            data["stream"] = False
            data["seed"] = 0
            data["top_p"] = 1
            data["max_completion_tokens"] = data.pop("max_tokens", 800)
            # Cerebras no usa presence_penalty ni frequency_penalty
        else:  # OpenAI
            data["presence_penalty"] = 0.2
            data["frequency_penalty"] = 0.2

        logger.info(f"Enviando request a {provider_name} con modelo {model}")
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout)

        # Verificar respuesta HTTP
        if not response.ok:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f": {error_data['error'].get('message', 'Error desconocido')}"
            except json.JSONDecodeError:
                error_msg += f": {response.text[:100]}"
            logger.error(f"Error HTTP en {provider_name}: {error_msg}")
            # Solo considerar error de conexión si es 5xx o timeout
            if response.status_code >= 500:
                return f"Error {error_msg}", "connection"
            return f"Error {error_msg}", "other"

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de {provider_name}: {str(e)}")
            return f"Error: Respuesta inválida de {provider_name}", "other"

        logger.info(f"Respuesta JSON recibida de {provider_name}: {list(response_data.keys())}")

        if 'choices' in response_data and len(response_data['choices']) > 0:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content'].strip()
                # Verificar que la respuesta no esté vacía
                if content:
                    logger.info(f"Respuesta exitosa de {provider_name}: {len(content)} caracteres")
                    return content, None
                else:
                    logger.error(f"Respuesta vacía de {provider_name}")
                    return f"Error: Respuesta vacía de {provider_name}", "connection"
            else:
                logger.error(f"Formato de respuesta inválido de {provider_name}: choice={choice}")
                return f"Error: Formato de respuesta inválido de {provider_name}", "other"
        else:
            error_msg = response_data.get('error', {}).get('message', 'Formato de respuesta inesperado')
            logger.error(f"Error en respuesta de {provider_name}: {error_msg}, keys={list(response_data.keys())}")
            return f"Error: {error_msg}", "connection"

    except requests.exceptions.Timeout:
        logger.error(f"Timeout en {provider_name}")
        return f"Error: Tiempo de espera agotado para {provider_name}", "connection"
    except requests.exceptions.ConnectionError:
        logger.error(f"Error de conexión en {provider_name}")
        return f"Error: Problema de conexión con {provider_name}", "connection"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de request en {provider_name}: {str(e)}")
        return f"Error: Problema de comunicación con {provider_name}", "connection"
    except KeyError as e:
        logger.error(f"Error de configuración en {provider_name}: {str(e)}")
        return f"Error: Configuración incompleta para {provider_name}", "other"
    except Exception as e:
        logger.error(f"Error inesperado en {provider_name}: {str(e)}")
        return f"Error: Problema inesperado con {provider_name}", "other"


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(NewTopicIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
