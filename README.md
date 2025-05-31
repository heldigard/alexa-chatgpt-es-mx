# Alexa ChatGPT Skill - Versión Mejorada

Skill de Amazon Alexa para interactuar con múltiples modelos avanzados de IA conversacional en español, usando voz. Soporta modelos gratuitos y premium de OpenAI, GitHub, OpenRouter y más.

## ✨ Características Principales

- **Selección aleatoria y fallback automático de proveedor/modelo**: Si un modelo falla, cambia automáticamente a otro disponible sin interrumpir la conversación.
- **Optimizado para español**: Responde siempre en español, con ejemplos y contexto latinoamericano.
- **Gestión inteligente de sesión**: Mantiene historial relevante y cambia de tema fácilmente.
- **Manejo robusto de errores**: Reintentos automáticos, logs detallados y mensajes claros para el usuario.
- **Fácil integración y despliegue en AWS Lambda**.

## 🤖 Proveedores y Modelos Soportados

La skill soporta decenas de modelos de IA conversacional. Puedes forzar el uso de cualquier modelo usando su nombre de proveedor (provider key) en la variable `FORCED_PROVIDER` de `config.py`.

**Lista de modelos y nombres de proveedor (actualizada a mayo 2025):**

| Proveedor      | Provider Key (FORCED_PROVIDER)                | Modelo (model)                                      |
|---------------|-----------------------------------------------|-----------------------------------------------------|
| **OpenAI**    | `openai`                                      | gpt-4.1-mini                                        |
|               | `openai_gpt4o_mini`                           | gpt-4o-mini                                         |
|               | `openai_o4_mini`                              | o4-mini                                             |
|               | `openai_o3_mini`                              | o3-mini                                             |
| **GitHub**    | `github`                                      | openai/gpt-4.1-mini                                 |
|               | `github_openai_o4_mini`                       | openai/o4-mini                                      |
|               | `github_openai_o3_mini`                       | openai/o3-mini                                      |
|               | `github_openai_gpt4o_mini`                    | openai/gpt-4o-mini                                  |
| **Gemini**    | `gemini_20`                                   | gemini-2.0-flash                                    |
| (Google)      | `gemini_25`                                   | gemini-2.5-flash-preview-05-20                      |
| **OpenRouter**| `openrouter`                                  | meta-llama/llama-4-maverick                         |
|               | `openrouter_llama_maverick`                   | meta-llama/llama-4-maverick:free                    |
|               | `openrouter_deepseek_r1`                      | deepseek/deepseek-r1                                |
|               | `openrouter_deepseek_r1_free`                 | deepseek/deepseek-r1:free                           |
|               | `openrouter_deepseek_r1_distill_llama_70b`    | deepseek/deepseek-r1-distill-llama-70b:free         |
|               | `openrouter_deepseek_r1_0528`                 | deepseek/deepseek-r1-0528                           |
|               | `openrouter_deepseek_r1_0528_free`            | deepseek/deepseek-r1-0528:free                      |
|               | `openrouter_deepseek_chimera`                 | tngtech/deepseek-r1t-chimera:free                   |
|               | `openrouter_deepseek_chat_v3`                 | deepseek/deepseek-chat-v3-0324                      |
|               | `openrouter_deepseek_chat_v3_free`            | deepseek/deepseek-chat-v3-0324:free                 |
|               | `openrouter_qwen3_235b`                       | qwen/qwen3-235b-a22b                                |
|               | `openrouter_qwen3_235b_free`                  | qwen/qwen3-235b-a22b:free                           |
|               | `openrouter_qwen_qwq`                         | qwen/qwq-32b                                        |
|               | `openrouter_qwen_qwq_free`                    | qwen/qwq-32b:free                                   |
|               | `openrouter_microsoft_mai`                    | microsoft/mai-ds-r1:free                            |
|               | `openrouter_openai_gpt41_mini`                | openai/gpt-4.1-mini                                 |
|               | `openrouter_openai_gpt4o_mini`                | openai/gpt-4o-mini                                  |
|               | `openrouter_openai_o4_mini`                   | openai/o4-mini                                      |
|               | `openrouter_openai_o3_mini`                   | openai/o3-mini                                      |
|               | `openrouter_google_gemini_20`                 | google/gemini-2.0-flash-001                         |
|               | `openrouter_google_gemini_25`                 | google/gemini-2.5-flash-preview-05-20               |
|               | `openrouter_nvidia_llama31_nemotron_ultra_253b_free` | nvidia/llama-3.1-nemotron-ultra-253b-v1:free |
|               | `openrouter_meta_llama33_70b_instruct_free`   | meta-llama/llama-3.3-70b-instruct:free              |
|               | `openrouter_meta_llama31_405b_free`           | meta-llama/llama-3.1-405b:free                      |
| **Cerebras**  | `cerebras`                                    | llama-4-scout-17b-16e-instruct                      |
|               | `cerebras_llama4_scout`                       | llama-4-scout-17b-16e-instruct                      |
|               | `cerebras_llama33_70b`                        | llama-3.3-70b                                       |
|               | `cerebras_qwen3_32b`                          | qwen-3-32b                                          |
|               | `cerebras_deepseek_r1_distill_llama_70b`      | deepseek-r1-distill-llama-70b                       |
| **DeepInfra** | `deepinfra_deepseek_v3`                       | deepseek-ai/DeepSeek-V3-0324                        |
|               | `deepinfra_qwen_qwq_32b`                      | Qwen/QwQ-32B                                        |
|               | `deepinfra_deepseek_r1`                       | deepseek-ai/DeepSeek-R1                             |
|               | `deepinfra_llama4_maverick`                   | meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8   |
|               | `deepinfra_qwen3_32b`                         | Qwen/Qwen3-32B                                      |
|               | `deepinfra_deepseek_r1_0528`                  | deepseek-ai/DeepSeek-R1-0528                        |
| **Moonshot**  | `moonshot`                                    | moonshot-v1-8k                                      |

> **Nota:** El nombre de proveedor (provider key) es el que debes usar en `FORCED_PROVIDER` si quieres forzar un modelo específico.

Consulta siempre `lambda/lambda_function.py` para la lista más actualizada de modelos soportados y sus nombres.

## 🔑 Configuración de API Keys

> **Nota:** Si no configuras al menos una API key válida, la skill no funcionará.
> 
> **Importante:** Si dejas el valor por defecto (por ejemplo, `"OPENAI_API_KEY"`, `""` o similar) en alguna de las variables `API_KEY`, `GITHUB_TOKEN`, `OPENROUTER_API_KEY` o `CEREBRAS_API_KEY` en `lambda/config.py`, los modelos de ese proveedor NO estarán disponibles para la skill. Solo se consideran los proveedores cuya clave ha sido configurada correctamente.

Coloca tus claves en las variables `API_KEY`, `GITHUB_TOKEN`, `OPENROUTER_API_KEY` y/o `CEREBRAS_API_KEY` según los proveedores que quieras usar.

Opcionalmente, puedes forzar el uso de un proveedor específico configurando la variable `FORCED_PROVIDER` en `lambda/config.py` (por ejemplo: `'openai'`, `'cerebras_llama4_scout'`, etc.).

## 📁 Estructura del Proyecto

```
alexa-chatgpt/
├── skill.json
├── interactionModels/
│   └── custom/
│       └── es-MX.json
├── lambda/
│   ├── lambda_function.py
│   ├── config.py
│   ├── requirements.txt
└── README.md
```

## 🚀 Instalación y Despliegue

1. **Instala dependencias:**
   ```bash
   cd lambda
   pip install -r requirements.txt
   ```
2. **Configura tus API keys:**
   - Edita el archivo `lambda/config.py` y coloca tus claves en las variables `API_KEY`, `GITHUB_TOKEN`, `OPENROUTER_API_KEY` y/o `CEREBRAS_API_KEY` según los proveedores que quieras usar.
   - Para forzar un proveedor específico, asigna su nombre a la variable `FORCED_PROVIDER` en el mismo archivo. Ejemplo:
     ```python
     FORCED_PROVIDER = 'cerebras_llama4_scout'
     ```
3. **Despliega en AWS Lambda:**
   - Comprime el contenido de `lambda/` (no la carpeta, solo los archivos).
   - Sube el ZIP a tu función Lambda.
   - Configura las variables de entorno.
4. **Configura la Alexa Skill:**
   - Importa `skill.json` e `interactionModels/custom/es-MX.json` en el Developer Console de Alexa.
   - Conecta la skill con tu función Lambda.

## Personalización de país y tono

Puedes personalizar el país y el tono de las respuestas editando el archivo `config.py`:

```python
COUNTRY = "Colombia"   # Cambia por el país que desees
TONE = "colombiano"    # Cambia por el tono o gentilicio adecuado (ej: mexicano, argentino, chileno)
```

Esto hará que la skill adapte sus respuestas y ejemplos culturales al país y tono que configures.

## 🧠 Lógica de Proveedor y Fallback

- Al iniciar sesión, se selecciona aleatoriamente un proveedor/modelo disponible (a menos que uses `FORCED_PROVIDER`).
- Si un proveedor falla (timeout, error, etc.), la skill intenta automáticamente con otros modelos disponibles (hasta 3 intentos por pregunta).
- Si defines `FORCED_PROVIDER`, siempre se usará ese proveedor para todas las consultas.
- El historial de conversación se mantiene por sesión (máximo 8 interacciones recientes para optimizar tokens).
- Puedes reiniciar el tema diciendo "nuevo tema" o "empezar de nuevo".

## 📝 Ejemplo de Uso

```
Usuario: "Alexa, abre modo chat"
Alexa: "¡Hola! Soy tu asistente inteligente. Puedes preguntarme sobre cualquier tema..."

Usuario: "Explícame qué es la inteligencia artificial"
Alexa: "La inteligencia artificial es la capacidad de las máquinas para imitar procesos cognitivos humanos..."

Usuario: "Nuevo tema"
Alexa: "¡Perfecto! Empecemos con un tema nuevo. ¿Sobre qué te gustaría conversar ahora?"

Usuario: "Háblame sobre la cocina mexicana"
Alexa: "La cocina mexicana es una de las más ricas y diversas del mundo..."
```

## 🛡️ Seguridad

- **Nunca subas tus API keys a repositorios públicos.**
- Usa variables de entorno en AWS Lambda para producción.
- Para mayor seguridad, considera usar AWS Secrets Manager.
- Si compartes el código, elimina o reemplaza las claves en `.env.example`.

## 🛠️ Troubleshooting / Errores Comunes

- **Timeout:** El modelo puede estar saturado. Intenta de nuevo o usa otro proveedor.
- **Problemas de conexión:** Verifica tu red o la validez de las API keys.
- **Respuestas vacías:** Puede ser un error temporal del modelo. Intenta otra pregunta o espera unos minutos.
- **No hay proveedores disponibles:** Asegúrate de tener al menos una API key válida configurada.

Consulta los logs de CloudWatch (AWS Lambda) para detalles de errores y debugging.

## ➕ Agregar nuevos modelos/proveedores

Para agregar un nuevo modelo, edita el diccionario `PROVIDERS` en `lambda_function.py` siguiendo el formato de los modelos existentes. Asegúrate de:
- Definir el nombre, URL, modelo, headers y cómo obtener la API key.
- Agregar el nombre del proveedor a la lista `available_providers` si la key está configurada.

## 🤝 Contribuciones

1. Haz fork del repositorio
2. Crea una rama para tu feature
3. Implementa tus cambios y agrega tests si es necesario
4. Haz un Pull Request

---

## 📋 TODO / Mejoras Futuras

- [ ] Implementar cache de respuestas para consultas similares
- [ ] Agregar soporte para más idiomas
- [ ] Análisis de sentimiento para ajustar respuestas
- [ ] Métricas de uso por proveedor
- [ ] Rate limiting
- [ ] Soporte para streaming de respuestas
- [ ] Dashboard de monitoreo
