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
import re
from config import API_KEY, GITHUB_TOKEN, OPENROUTER_API_KEY, CEREBRAS_API_KEY, GEMINI_API_KEY, FORCED_PROVIDER, COUNTRY, TONE, DEEPINFRA_API_KEY, DEEPSEEK_API_KEY, MOONSHOT_API_KEY, CHUTES_API_KEY, GROQ_API_KEY

# =====================================================================
# CONFIGURACIÓN Y CONSTANTES GLOBALES
# =====================================================================

reprompts = [
    "¿Qué más te gustaría saber?",
    "¿Hay algo más que quieras preguntarme?",
    "¿Tienes otra pregunta?",
    "¿En qué más puedo ayudarte?",
    "¿Quieres que te explique algo más?",
    "¿Hay algún otro tema que te interese?",
    "¿Necesitas ayuda con algo más?"
]

retry_prompts = [
    "Parece que hubo un problema de conexión. ¿Quieres intentarlo de nuevo?",
    "No pude conectarme al servicio. ¿Quieres que lo intente otra vez?",
    "El modelo no respondió. ¿Deseas que lo intente de nuevo?",
    "Hubo un error temporal. ¿Intento responderte otra vez?",
    "No logré obtener respuesta. ¿Quieres reintentar tu pregunta?"
]

CONTENT_TYPE_JSON = "application/json"

# Constantes para OpenRouter
OPENROUTER_REFERER = "https://alexa-chatgpt.com"
OPENROUTER_TITLE = "Alexa ChatGPT Skill"

# IMPORTANTE: En producción, configurar estas variables
api_key = API_KEY
github_token = GITHUB_TOKEN
openrouter_api_key = OPENROUTER_API_KEY
cerebras_api_key = CEREBRAS_API_KEY
gemini_api_key = GEMINI_API_KEY
deepinfra_api_key = DEEPINFRA_API_KEY
deepseek_api_key = DEEPSEEK_API_KEY
moonshot_api_key = MOONSHOT_API_KEY
chutes_api_key = CHUTES_API_KEY
groq_api_key = GROQ_API_KEY

DEFAULT_MAX_TOKENS = 800
DEFAULT_TIMEOUT = 7

def is_valid_key(key):
    """Valida si una API_KEY es válida: no None, no vacía, no termina en API_KEY o TOKEN"""
    if key is None or key == '':
        return False
    if isinstance(key, str) and (key.strip().endswith('API_KEY') or key.strip().endswith('TOKEN')):
        return False
    return True

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# =====================================================================
# CLASE PARA MANEJAR PROVEEDORES DE IA
# =====================================================================

class ProviderManager:
    """Maneja la configuración y selección de proveedores de IA"""

    # URLs constantes para evitar duplicación
    CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
    GEMINI_20_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    GEMINI_25_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
    OPENAI_URL = "https://api.openai.com/v1/chat/completions"
    GITHUB_URL = "https://models.github.ai/inference/chat/completions"
    DEEPINFRA_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MOONSHOT_URL = "https://api.moonshot.cn/v1/chat/completions"
    CHUTES_URL = "https://llm.chutes.ai/v1/chat/completions"
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.providers = self._configure_providers()
        self.available_providers = self._get_available_providers()

        if not self.available_providers:
            logger.error("No hay API keys configuradas")
            raise ValueError("Por favor configura al menos una API key en las variables de entorno")

        logger.info(f"Proveedores disponibles: {self.available_providers}")

    def _configure_providers(self):
        """Configura la información de todos los proveedores, dividiendo por origen para mejor mantenimiento"""
        providers = {}
        providers.update(self._get_gemini_providers())
        providers.update(self._get_openai_providers())
        providers.update(self._get_github_providers())
        providers.update(self._get_openrouter_providers())
        providers.update(self._get_cerebras_providers())
        providers.update(self._get_deepinfra_providers())
        providers.update(self._get_moonshot_providers())
        providers.update(self._get_chutes_providers())
        providers.update(self._get_groq_providers())
        return providers

    def _get_gemini_providers(self):
        return {
            # Gemini 2.0 Flash (Google API directo, solo texto)
            "gemini_20": {
                "url": self.GEMINI_20_URL,
                "model": "gemini-2.0-flash",
                "get_headers": lambda key: {"Content-Type": CONTENT_TYPE_JSON},
                "get_key": lambda: gemini_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            # Gemini 2.5 Flash Preview (Google API directo, solo texto)
            "gemini_25": {
                "url": self.GEMINI_25_URL,
                "model": "gemini-2.5-flash-preview-05-20",
                "get_headers": lambda key: {"Content-Type": CONTENT_TYPE_JSON},
                "get_key": lambda: gemini_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_openai_providers(self):
        return {
            "openai": {
                "url": self.OPENAI_URL,
                "model": "gpt-4.1-mini",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON
                },
                "get_key": lambda: api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openai_gpt4o_mini": {
                "url": self.OPENAI_URL,
                "model": "gpt-4o-mini",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON
                },
                "get_key": lambda: api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openai_o4_mini": {
                "url": self.OPENAI_URL,
                "model": "o4-mini",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON
                },
                "get_key": lambda: api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openai_o3_mini": {
                "url": self.OPENAI_URL,
                "model": "o3-mini",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON
                },
                "get_key": lambda: api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_github_providers(self):
        return {
            "github": {
                "url": self.GITHUB_URL,
                "model": "openai/gpt-4.1-mini",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON
                },
                "get_key": lambda: github_token,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "github_openai_o4_mini": {
                "url": self.GITHUB_URL,
                "model": "openai/o4-mini",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON
                },
                "get_key": lambda: github_token,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "github_openai_o3_mini": {
                "url": self.GITHUB_URL,
                "model": "openai/o3-mini",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON
                },
                "get_key": lambda: github_token,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "github_openai_gpt4o_mini": {
                "url": self.GITHUB_URL,
                "model": "openai/gpt-4o-mini",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON
                },
                "get_key": lambda: github_token,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_openrouter_providers(self):
        return {
            "openrouter": {
                "url": self.OPENROUTER_URL,
                "model": "meta-llama/llama-4-maverick",
                "get_headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": CONTENT_TYPE_JSON,
                    "HTTP-Referer": OPENROUTER_REFERER,
                    "X-Title": OPENROUTER_TITLE
                },
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_deepseek_r1": {
                "url": self.OPENROUTER_URL,
                "model": "deepseek/deepseek-r1",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_deepseek_r1_free": {
                "url": self.OPENROUTER_URL,
                "model": "deepseek/deepseek-r1:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_deepseek_r1_0528": {
                "url": self.OPENROUTER_URL,
                "model": "deepseek/deepseek-r1-0528",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_deepseek_r1_0528_free": {
                "url": self.OPENROUTER_URL,
                "model": "deepseek/deepseek-r1-0528:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_deepseek_chimera": {
                "url": self.OPENROUTER_URL,
                "model": "tngtech/deepseek-r1t-chimera:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_qwen3_235b_free": {
                "url": self.OPENROUTER_URL,
                "model": "qwen/qwen3-235b-a22b:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_qwen3_235b": {
                "url": self.OPENROUTER_URL,
                "model": "qwen/qwen3-235b-a22b",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_microsoft_mai": {
                "url": self.OPENROUTER_URL,
                "model": "microsoft/mai-ds-r1:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_llama_maverick": {
                "url": self.OPENROUTER_URL,
                "model": "meta-llama/llama-4-maverick:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_qwen_qwq_free": {
                "url": self.OPENROUTER_URL,
                "model": "qwen/qwq-32b:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_qwen_qwq": {
                "url": self.OPENROUTER_URL,
                "model": "qwen/qwq-32b",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_deepseek_chat_v3": {
                "url": self.OPENROUTER_URL,
                "model": "deepseek/deepseek-chat-v3-0324",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_deepseek_chat_v3_free": {
                "url": self.OPENROUTER_URL,
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_google_gemini_20": {
                "url": self.OPENROUTER_URL,
                "model": "google/gemini-2.0-flash-001",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_google_gemini_25": {
                "url": self.OPENROUTER_URL,
                "model": "google/gemini-2.5-flash-preview-05-20",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_openai_gpt41_mini": {
                "url": self.OPENROUTER_URL,
                "model": "openai/gpt-4.1-mini",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_openai_gpt4o_mini": {
                "url": self.OPENROUTER_URL,
                "model": "openai/gpt-4o-mini",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_openai_o4_mini": {
                "url": self.OPENROUTER_URL,
                "model": "openai/o4-mini",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_nvidia_llama31_nemotron_ultra_253b_free": {
                "url": self.OPENROUTER_URL,
                "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_meta_llama33_70b_instruct_free": {
                "url": self.OPENROUTER_URL,
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "openrouter_meta_llama31_405b_free": {
                "url": self.OPENROUTER_URL,
                "model": "meta-llama/llama-3.1-405b:free",
                "get_headers": self._get_openrouter_headers,
                "get_key": lambda: openrouter_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_cerebras_providers(self):
        return {
            "cerebras": {
                "url": self.CEREBRAS_URL,
                "model": "llama-4-scout-17b-16e-instruct",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: cerebras_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "cerebras_llama4_scout": {
                "url": self.CEREBRAS_URL,
                "model": "llama-4-scout-17b-16e-instruct",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: cerebras_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "cerebras_llama33_70b": {
                "url": self.CEREBRAS_URL,
                "model": "llama-3.3-70b",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: cerebras_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "cerebras_qwen3_32b": {
                "url": self.CEREBRAS_URL,
                "model": "qwen-3-32b",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: cerebras_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "cerebras_deepseek_r1_distill_llama_70b": {
                "url": self.CEREBRAS_URL,
                "model": "deepseek-r1-distill-llama-70b",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: cerebras_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_deepinfra_providers(self):
        return {
            "deepinfra_deepseek_v3": {
                "url": self.DEEPINFRA_URL,
                "model": "deepseek-ai/DeepSeek-V3-0324",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: deepinfra_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "deepinfra_qwen_qwq_32b": {
                "url": self.DEEPINFRA_URL,
                "model": "Qwen/QwQ-32B",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: deepinfra_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "deepinfra_deepseek_r1": {
                "url": self.DEEPINFRA_URL,
                "model": "deepseek-ai/DeepSeek-R1",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: deepinfra_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "deepinfra_llama4_maverick": {
                "url": self.DEEPINFRA_URL,
                "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: deepinfra_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "deepinfra_qwen3_32b": {
                "url": self.DEEPINFRA_URL,
                "model": "Qwen/Qwen3-32B",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: deepinfra_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "deepinfra_deepseek_r1_0528": {
                "url": self.DEEPINFRA_URL,
                "model": "deepseek-ai/DeepSeek-R1-0528",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: deepinfra_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_chutes_providers(self):
        return {
            "chutes_deepseek_r1_0528": {
                "url": self.CHUTES_URL,
                "model": "deepseek-ai/DeepSeek-R1-0528",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: chutes_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "chutes_deepseek_r1": {
                "url": self.CHUTES_URL,
                "model": "deepseek-ai/DeepSeek-R1",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: chutes_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "chutes_deepseek_v3": {
                "url": self.CHUTES_URL,
                "model": "deepseek-ai/DeepSeek-V3-0324",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: chutes_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "chutes_deepseek_chimera": {
                "url": self.CHUTES_URL,
                "model": "tngtech/DeepSeek-R1T-Chimera",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: chutes_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "chutes_qwen3_235b": {
                "url": self.CHUTES_URL,
                "model": "Qwen/Qwen3-235B-A22B",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: chutes_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "chutes_microsoft_mai": {
                "url": self.CHUTES_URL,
                "model": "microsoft/MAI-DS-R1-FP8",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: chutes_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            "chutes_glm4_32b": {
                "url": self.CHUTES_URL,
                "model": "THUDM/GLM-4-32B-0414",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: chutes_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_moonshot_providers(self):
        return {
            "moonshot": {
                "url": self.MOONSHOT_URL,
                "model": "moonshot-v1-8k",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: moonshot_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_groq_providers(self):
        return {
            # Compound Beta (Groq)
            "groq_compound_beta": {
                "url": self.GROQ_URL,
                "model": "compound-beta",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: groq_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            # Compound Beta Mini (Groq)
            "groq_compound_beta_mini": {
                "url": self.GROQ_URL,
                "model": "compound-beta-mini",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: groq_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            # Llama 4 Maverick (Groq)
            "groq_llama4_maverick": {
                "url": self.GROQ_URL,
                "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: groq_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
            # Qwen QwQ 32B (Groq)
            "groq_qwen_qwq_32b": {
                "url": self.GROQ_URL,
                "model": "qwen-qwq-32b",
                "get_headers": self._get_bearer_headers,
                "get_key": lambda: groq_api_key,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "timeout": DEFAULT_TIMEOUT
            },
        }

    def _get_openrouter_headers(self, key):
        """Headers estándar para OpenRouter"""
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON,
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        }

    def _get_bearer_headers(self, key):
        """Headers estándar para proveedores tipo Bearer"""
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": CONTENT_TYPE_JSON
        }

    def _get_available_providers(self):
        """Determina qué proveedores están disponibles basado en las API keys válidas"""
        available = []
        # Solo agregar si la key es válida (no es None, vacía, ni valor por defecto)
        if is_valid_key(api_key):
            available.extend([
                "openai",
                "openai_gpt4o_mini",
                "openai_o4_mini",
                "openai_o3_mini"
            ])
        if is_valid_key(github_token):
            available.extend([
                "github",
                "github_openai_o4_mini",
                "github_openai_o3_mini",
                "github_openai_gpt4o_mini"
            ])
        if is_valid_key(openrouter_api_key):
            available.extend([
                # Modelos Llama
                "openrouter",  # meta-llama/llama-4-maverick
                "openrouter_llama_maverick",  # meta-llama/llama-4-maverick:free

                # Modelos DeepSeek
                "openrouter_deepseek_r1",  # deepseek/deepseek-r1
                "openrouter_deepseek_r1_free",  # deepseek/deepseek-r1:free
                "openrouter_deepseek_r1_0528",  # deepseek/deepseek-r1-0528
                "openrouter_deepseek_r1_0528_free",  # deepseek/deepseek-r1-0528:free
                "openrouter_deepseek_chimera",  # tngtech/deepseek-r1t-chimera:free
                "openrouter_deepseek_chat_v3",  # deepseek/deepseek-chat-v3-0324
                "openrouter_deepseek_chat_v3_free",  # deepseek/deepseek-chat-v3-0324:free

                # Modelos Qwen
                "openrouter_qwen3_235b",  # qwen/qwen3-235b-a22b
                "openrouter_qwen3_235b_free",  # qwen/qwen3-235b-a22b:free
                "openrouter_qwen_qwq_free",  # qwen/qwq-32b:free

                # Modelos Microsoft
                "openrouter_microsoft_mai",  # microsoft/mai-ds-r1:free

                # Modelos OpenAI vía OpenRouter
                "openrouter_openai_gpt41_mini",  # openai/gpt-4.1-mini
                "openrouter_openai_gpt4o_mini",  # openai/gpt-4o-mini
                "openrouter_openai_o4_mini",  # openai/o4-mini

                # Modelos Google Gemini vía OpenRouter
                "openrouter_google_gemini_20",  # google/gemini-2.0-flash-001
                "openrouter_google_gemini_25",  # google/gemini-2.5-flash-preview-05-20

                # Modelos NVIDIA y Meta nuevos
                "openrouter_nvidia_llama31_nemotron_ultra_253b_free",  # nvidia/llama-3.1-nemotron-ultra-253b-v1:free
                "openrouter_meta_llama33_70b_instruct_free",  # meta-llama/llama-3.3-70b-instruct:free
                "openrouter_meta_llama31_405b_free",  # meta-llama/llama-3.1-405b:free
            ])
        if is_valid_key(gemini_api_key):
            available.extend(["gemini_20", "gemini_25"])
        if is_valid_key(cerebras_api_key):
            available.extend([
                "cerebras",
                "cerebras_llama4_scout",
                "cerebras_llama33_70b",
                "cerebras_qwen3_32b",
                "cerebras_deepseek_r1_distill_llama_70b"
            ])
        if is_valid_key(deepinfra_api_key):
            available.extend([
                "deepinfra_deepseek_v3",
                "deepinfra_qwen_qwq_32b",
                "deepinfra_deepseek_r1",
                "deepinfra_llama4_maverick",
                "deepinfra_qwen3_32b",
                "deepinfra_deepseek_r1_0528"
            ])
        if is_valid_key(moonshot_api_key):
            available.append("moonshot")
        if is_valid_key(CHUTES_API_KEY):
            available.extend([
                "chutes_deepseek_r1_0528",
                "chutes_deepseek_r1",
                "chutes_deepseek_v3",
                "chutes_deepseek_chimera",
                "chutes_qwen3_235b",
                "chutes_microsoft_mai",
                "chutes_glm4_32b"
            ])
        if is_valid_key(groq_api_key):
            available.extend([
                "groq_compound_beta",
                "groq_compound_beta_mini",
                "groq_llama4_maverick",
                "groq_qwen_qwq_32b"
            ])

        return available

    def select_random_provider(self):
        """Selecciona un proveedor aleatorio de los disponibles o el forzado si está definido"""
        if FORCED_PROVIDER and FORCED_PROVIDER in self.available_providers:
            return FORCED_PROVIDER
        return random.choice(self.available_providers)

    def get_next_provider(self, current_provider, failed_providers):
        """Obtiene el siguiente proveedor disponible excluyendo los que han fallado"""
        available = [p for p in self.available_providers if p not in failed_providers]
        if not available:
            return None

        # Si el proveedor current_provider aún no ha fallado, lo excluimos de las opciones
        if current_provider in available:
            available.remove(current_provider)

        return random.choice(available) if available else None

    def get_provider_config(self, provider_name):
        """Obtiene la configuración de un proveedor específico"""
        return self.providers.get(provider_name)

# =====================================================================
# CLASE PARA GENERAR RESPUESTAS DE IA
# =====================================================================

class ResponseGenerator:
    """Maneja la generación de respuestas usando diferentes proveedores de IA"""

    def __init__(self, provider_manager):
        self.provider_manager = provider_manager

    def generate_response(self, session_attr, new_question):
        """
        Genera respuesta usando el proveedor actual con fallback automático en caso de error
        Devuelve (respuesta, tipo_de_error) donde tipo_de_error puede ser None, 'connection', 'other'
        """
        # Si hay un proveedor forzado, siempre usarlo
        if FORCED_PROVIDER and FORCED_PROVIDER in self.provider_manager.available_providers:
            session_attr["current_provider"] = FORCED_PROVIDER
            session_attr["failed_providers"] = []
            current_provider = FORCED_PROVIDER
            failed_providers = []
        else:
            current_provider = session_attr.get("current_provider")
            failed_providers = session_attr.get("failed_providers", [])

        chat_history = session_attr.get("chat_history", [])

        # Si no hay proveedor actual, seleccionar uno
        current_provider = self._ensure_valid_provider(session_attr, current_provider, failed_providers)

        logger.info(f"Intentando con proveedor principal: {current_provider}")

        # Intentar con el proveedor actual
        response, error_type = self._try_provider(current_provider, chat_history, new_question)

        logger.info(f"Resultado del proveedor {current_provider}: error_type={error_type}, respuesta_vacia={not response or not response.strip()}")

        # Hacer fallback si hay error de conexión o respuesta vacía
        if ((error_type == "connection" or not response or not response.strip()) and current_provider not in failed_providers):
            if not (FORCED_PROVIDER and FORCED_PROVIDER in self.provider_manager.available_providers):
                response, error_type = self._handle_fallback(session_attr, current_provider, chat_history, new_question)

        # Si la respuesta fue exitosa, limpiar la lista de proveedores fallidos
        if error_type is None:
            session_attr["failed_providers"] = []

        return response, error_type

    def _ensure_valid_provider(self, session_attr, current_provider, failed_providers):
        """Asegura que tengamos un proveedor válido"""
        # Si hay FORCED_PROVIDER, siempre usarlo
        if FORCED_PROVIDER and FORCED_PROVIDER in self.provider_manager.available_providers:
            session_attr["current_provider"] = FORCED_PROVIDER
            return FORCED_PROVIDER
        if not current_provider or current_provider in failed_providers:
            available = [p for p in self.provider_manager.available_providers if p not in failed_providers]
            if available:
                current_provider = random.choice(available)
                session_attr["current_provider"] = current_provider
            else:
                # Si todos han fallado, reiniciar la lista de fallos y intentar de nuevo
                session_attr["failed_providers"] = []
                current_provider = self.provider_manager.select_random_provider()
                session_attr["current_provider"] = current_provider

        return current_provider

    def _handle_fallback(self, session_attr, current_provider, chat_history, new_question):
        """Maneja el fallback a otros proveedores en caso de error"""
        # Si hay FORCED_PROVIDER, no hacer fallback
        if FORCED_PROVIDER and FORCED_PROVIDER in self.provider_manager.available_providers:
            logger.error(f"FORCED_PROVIDER '{FORCED_PROVIDER}' falló, no se hará fallback a otros proveedores.")
            response = "Lo siento, el proveedor de IA seleccionado no está disponible temporalmente. Por favor, inténtalo de nuevo en unos minutos."
            return response, "connection"
        logger.warning(f"Proveedor {current_provider} falló con error de conexión, iniciando fallback...")
        session_attr["failed_providers"].append(current_provider)

        # Intentar hasta 3 proveedores diferentes
        for attempt in range(3):
            next_provider = self.provider_manager.get_next_provider(current_provider, session_attr["failed_providers"])

            if next_provider:
                session_attr["current_provider"] = next_provider
                logger.info(f"Fallback intento {attempt + 1}: Cambiando a proveedor: {next_provider}")
                response, error_type = self._try_provider(next_provider, chat_history, new_question)
                logger.info(f"Resultado del fallback {next_provider}: error_type={error_type}")

                if error_type is None:
                    # Éxito con el fallback, salir del bucle
                    logger.info(f"Fallback exitoso con {next_provider}")
                    return response, error_type
                else:
                    # Este proveedor también falló
                    session_attr["failed_providers"].append(next_provider)
                    current_provider = next_provider
            else:
                # No hay más proveedores disponibles
                logger.warning("No hay más proveedores disponibles para fallback")
                break

        # Si aún hay error después de todos los intentos
        session_attr["failed_providers"] = []
        session_attr["current_provider"] = self.provider_manager.select_random_provider()
        response = "Lo siento, todos los servicios de inteligencia artificial están temporalmente no disponibles. Por favor, inténtalo de nuevo en unos minutos."
        logger.error("Todos los proveedores fallaron, devolviendo mensaje de error")
        return response, "connection"

    def _try_provider(self, provider_name, chat_history, new_question):
        """
        Intenta obtener respuesta de un proveedor específico
        Devuelve (respuesta, tipo_de_error) donde tipo_de_error puede ser None, 'connection', 'other'
        """
        try:
            provider = self.provider_manager.get_provider_config(provider_name)
            if not provider:
                logger.error(f"Proveedor {provider_name} no encontrado en configuración")
                return f"Error: Proveedor {provider_name} no configurado", "other"

            key = provider["get_key"]()
            if not self._validate_api_key(key):
                return f"Error: API key no configurada para {provider_name}", "other"

            # Determinar el tipo de proveedor y procesar la respuesta
            if provider_name in ["gemini_20", "gemini_25"]:
                return self._handle_gemini_request(provider, key, chat_history, new_question, provider_name)
            else:
                return self._handle_standard_request(provider, key, chat_history, new_question, provider_name)

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

    def _validate_api_key(self, key):
        """Valida que la API key esté configurada"""
        return key and key != "YOUR_API_KEY"

    def _build_chat_history(self, chat_history, new_question, system_prompt=None, format_type="standard"):
        """Construye el historial de chat en el formato requerido (standard o gemini)"""
        if format_type == "gemini":
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            for question, answer in chat_history[-6:]:
                contents.append({"role": "user", "parts": [{"text": question}]})
                contents.append({"role": "model", "parts": [{"text": answer}]})
            contents.append({"role": "user", "parts": [{"text": new_question}]})
            return contents
        else:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            for question, answer in chat_history[-6:]:
                messages.append({"role": "user", "content": question})
                messages.append({"role": "assistant", "content": answer})
            messages.append({"role": "user", "content": new_question})
            return messages

    def _handle_gemini_request(self, provider, key, chat_history, new_question, provider_name):
        """Maneja las peticiones específicas para Gemini (Google API directo)"""
        headers = provider["get_headers"](key)
        url = f"{provider['url']}?key={key}"
        timeout = provider.get("timeout", 8)
        system_prompt = self._get_system_prompt()
        contents = self._build_chat_history(chat_history, new_question, system_prompt, format_type="gemini")
        data = {"contents": contents}
        logger.info(f"Enviando request a Gemini directo: {provider_name}")
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout)
        return self._process_gemini_response(response, provider_name)

    def _send_standard_request(self, provider, key, messages, provider_name, custom_data=None):
        """Envía una petición estándar (OpenAI, OpenRouter, Cerebras, Moonshot, etc.)"""
        headers = provider["get_headers"](key)
        url = provider["url"]
        model = provider["model"]
        timeout = provider.get("timeout", DEFAULT_TIMEOUT)
        if custom_data is not None:
            data = custom_data
        else:
            data = self._build_request_data(provider, model, messages, provider_name)
        logger.info(f"Enviando request a {provider_name} con modelo {model}")
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout)
        return self._process_standard_response(response, provider_name)

    def _handle_standard_request(self, provider, key, chat_history, new_question, provider_name):
        """Maneja las peticiones estándar (OpenAI, OpenRouter, Cerebras, etc.)"""
        system_prompt = self._get_system_prompt()
        messages = self._build_chat_history(chat_history, new_question, system_prompt, format_type="standard")
        return self._send_standard_request(provider, key, messages, provider_name)

    def _get_system_prompt(self):
        """Genera el prompt del sistema optimizado para conversaciones en español"""
        return f"""Eres un asistente de inteligencia artificial con un toque {TONE}, especializado en responder de manera clara, concisa y amigable, ideal para una conversación por voz.

REGLAS CLAVE PARA RESPONDER:
- Habla siempre en español latino {TONE}, con un tono amable y cercano.
- Tus respuestas deben ser como una charla fluida: naturales, conversacionales y fáciles de entender al escucharlas.
- Sé breve y al grano: idealmente no más de 120-180 palabras, para que sea fácil seguirte la conversación solo con audio.
- Cuando sea apropiado y encaje de forma natural, incluye ejemplos o referencias culturales de {COUNTRY}.
- Si no tienes la respuesta a algo, admítelo con sinceridad. Es mejor ser honesto.
- Explica las cosas de forma sencilla, evitando términos muy técnicos, para que todos te puedan entender.

Tu misión es ser un interlocutor conversador y útil: que la gente en {COUNTRY} disfrute charlar contigo y encuentre valor en tus respuestas."""

    def _build_request_data(self, provider, model, messages, provider_name):
        """Construye los datos de la petición según el tipo de proveedor"""
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": provider.get("max_tokens", 800),
            "temperature": 0.8,
        }

        # Ajustes específicos por proveedor
        if provider_name == "github":
            data["top_p"] = 0.9
        elif provider_name.startswith("cerebras"):
            data.update({
                "stream": False,
                "seed": 0,
                "top_p": 1,
                "max_completion_tokens": data.pop("max_tokens", 800)
            })
        elif provider_name.startswith("chutes"):
            data.update({
                "stream": True,
                "top_p": 0.9
            })
        elif any(provider_name.startswith(prefix) for prefix in ["openrouter", "deepseek", "qwen", "microsoft", "llama", "google"]):
            data.update({
                "presence_penalty": 0.1,
                "frequency_penalty": 0.1,
                "top_p": 0.9
            })
        else:  # OpenAI
            data.update({
                "presence_penalty": 0.2,
                "frequency_penalty": 0.2
            })

        return data

    def _process_gemini_response(self, response, provider_name):
        """Procesa la respuesta de Gemini"""
        if not response.ok:
            return self._handle_http_error(response, provider_name)

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

    def _process_standard_response(self, response, provider_name):
        """Procesa la respuesta estándar (OpenAI, OpenRouter, etc.)"""
        if not response.ok:
            return self._handle_http_error(response, provider_name)

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

    def _handle_http_error(self, response, provider_name):
        """Maneja errores HTTP"""
        error_msg = f"HTTP {response.status_code}"
        try:
            error_data = response.json()
            if 'error' in error_data:
                error_msg += f": {error_data['error'].get('message', 'Error desconocido')}"
        except json.JSONDecodeError:
            error_msg += f": {response.text[:100]}"

        logger.error(f"Error HTTP en {provider_name}: {error_msg}")

        # Solo considerar error de conexión si es 5xx
        if response.status_code >= 500:
            return f"Error {error_msg}", "connection"
        return f"Error {error_msg}", "other"

def remove_think_tags(text):
    """Elimina cualquier bloque <think>...</think> del texto (incluyendo etiquetas)."""
    if not text:
        return text
    return re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE).strip()

# Inicializar instancias globales
provider_manager = ProviderManager()
response_generator = ResponseGenerator(provider_manager)

# =====================================================================
# HANDLERS DE ALEXA SKILL
# =====================================================================

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Hola, soy tu asistente inteligente. ¿En qué puedo ayudarte hoy?"

        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["chat_history"] = []
        # Seleccionar proveedor forzado o aleatorio al inicio de la sesión
        if FORCED_PROVIDER and FORCED_PROVIDER in provider_manager.available_providers:
            session_attr["current_provider"] = FORCED_PROVIDER
        else:
            session_attr["current_provider"] = provider_manager.select_random_provider()
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
                if FORCED_PROVIDER and FORCED_PROVIDER in provider_manager.available_providers:
                    session_attr["current_provider"] = FORCED_PROVIDER
                else:
                    session_attr["current_provider"] = provider_manager.select_random_provider()
            if "failed_providers" not in session_attr:
                session_attr["failed_providers"] = []

            response, error_type = response_generator.generate_response(session_attr, query)

            logger.info(f"Respuesta final - error_type: {error_type}, longitud_respuesta: {len(response) if response else 0}")

            # Limpiar la respuesta de <think>...</think>
            response_clean = remove_think_tags(response)

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
            if not response_clean or not response_clean.strip():
                response_clean = "Lo siento, no pude generar una respuesta en este momento. ¿Puedes intentar con otra pregunta?"

            # Solo agregar al historial si la respuesta fue exitosa (no contiene "Error")
            if error_type is None:
                session_attr["chat_history"].append((query, response_clean))
                # Mantener solo las últimas 8 interacciones para optimizar tokens
                if len(session_attr["chat_history"]) > 8:
                    session_attr["chat_history"] = session_attr["chat_history"][-8:]

            return (
                handler_input.response_builder
                    .speak(response_clean)
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
        # Registrar la solicitud que causó el error de despacho
        try:
            logger.error(f"Solicitud causando error de despacho: {json.dumps(handler_input.request_envelope.to_dict())}")
        except Exception as e:
            logger.error(f"Error registrando el envelope de la solicitud: {str(e)}")

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

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent.

    AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speak_output = ("Lo siento, no entendí eso. Puedes pedirme ayuda o "
                        "intentar tu pregunta de otra manera.")
        reprompt = random.choice(reprompts) # Usando tus reprompts existentes

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes
        current_provider = session_attr.get("current_provider", "unknown")
        reason = "Desconocida"
        if handler_input.request_envelope.request and hasattr(handler_input.request_envelope.request, 'reason'):
            reason = handler_input.request_envelope.request.reason

        logger.info(f"Sesión terminada. Proveedor usado: {current_provider}. Razón: {reason}")
        # El SDK espera un objeto Response, incluso si está vacío para SessionEndedRequest
        return handler_input.response_builder.response

# =====================================================================
# CONFIGURACIÓN DE LA SKILL Y LAMBDA HANDLER
# =====================================================================

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(NewTopicIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
