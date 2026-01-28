from llama_cpp import Llama
import os 

""""
Decidí usar Mistral como IA de recomendación para el mejorar el score de posicionamiento SEO por ser un modelo relativamente liviano de fácil integración con Python y por no existir dependencias
con APIS externas.

Limité el tamaño de ventana de contexto por tratarse de un prompt estructurado y corto.
La cantidad de 4 hilos de CPU es por cuestiones meramente operativas.
Tokens procesados en paralelo: 128. Mantiene equilibrio entre velocidad y memoria.

El prompt fue calibrado mediante evaluación asistida por IA -Chatgpt
"""

MODEL_PATH = os.getenv("LLM_MODEL_PATH")
if not MODEL_PATH:
    raise RuntimeError("La variable de entorno LLM_MODEL_PATH no está definida")

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    n_batch=128,
    verbose=False
)


def genera_recomendacion(data: dict) -> str:
    prompt = f"""

IMPORTANTE:
Respondé ÚNICAMENTE en español neutro.
NO utilices inglés bajo ninguna circunstancia.

Actuás como un consultor SEO técnico senior, especializado en auditorías editoriales.

Tu tarea es generar UNA ÚNICA recomendación SEO prioritaria basada exclusivamente en los datos proporcionados.

NO interpretes más de un problema.
NO propongas múltiples acciones.
NO agregues contexto adicional.
NO escribas texto fuera del formato solicitado.

Datos del análisis:
- Puntaje SEO total: {data['score_seo']}
- Puntaje de contenido: {data['contenido']}
- Puntaje de jerarquía semántica: {data['jerarquia']}
- Puntaje de enlaces: {data['links']}
- Puntaje de distribución del contenido: {data['distribucion']}


El puntaje máximo posible es 97.5.
Identificá el área con mayor impacto negativo y basá toda la recomendación únicamente en ese punto.

Respondé EXCLUSIVAMENTE con el siguiente formato, respetando exactamente títulos, orden y mayúsculas:

RESUMEN:
<máximo 2 líneas, sin listar>

PROBLEMA:
<una sola oración clara y técnica>

ACCIÓN:
<una sola acción concreta, específica y ejecutable>

RASONAMIENTO:
<1 o 2 líneas explicando por qué esa acción corrige el problema detectado>

Reglas obligatorias:
- NO uses separadores visuales (---, ###, etc.)
- NO repitas títulos ni secciones
- NO agregues ejemplos
- NO cambies de idioma
- NO escribas conclusiones
- NO continúes escribiendo después del bloque RASONAMIENTO
- El área con peor desempeño es: JERARQUÍA SEMÁNTICA. Debés basar TODA la recomendación únicamente en esta área. NO menciones otras áreas.
Finalizá la respuesta escribiendo exactamente el token <END>.

Ejemplo de respuesta válida (respetar exactamente este formato):

RESUMEN:
El sitio presenta deficiencias claras en su estructura semántica.

PROBLEMA:
La jerarquía de encabezados no está correctamente definida.

ACCIÓN:
Definir un único H1 principal y reorganizar los subtítulos H2 bajo ese eje.

RASONAMIENTO:
Una jerarquía clara permite a los motores de búsqueda interpretar mejor el contenido.

<END>

"""

    output = llm(
        prompt,
        max_tokens=140,
        temperature=0.15,
        top_p=0.9,
        stop=["<END>"]
    )

    return output["choices"][0]["text"].strip()