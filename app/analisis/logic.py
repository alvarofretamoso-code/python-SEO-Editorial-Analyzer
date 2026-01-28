from bs4 import BeautifulSoup
import requests
import json
import tldextract as tl

"""
El flujo de trabajo  en un escenario ideal se desarolla de la siguiente manera:
1. Usuario ingresa URL
2. Se toma el html y se parsea con con BeautifulSoup
3. Extracción de los elementos necesarios para el análisi seo
4. A partir de la estructura se determina el tipo de página.
5. Entra en juego el árbol de decisiones:
    5.A Si el schema incluye "Product":
       - Se ejecuta la función de análisis de producto.
    5.B Si existe la etiqueta <article>:
       - Se ejecuta la función de análisis editorial.
    5.C Si existe la etiqueta <main>:
       - Se ejecuta la función de análisis webpage.
    5.D Si solo existe la etiqueta <body>:
       - Se ejecuta la función de análisis webpage como fallback.
6. Se calculan los puntajes según:
    - Contenido de texto
    - Distribución de párrafos
    - Jerarquía de encabezados
    - Enlaces internos y externos
7. Se ajustan los pesos de los puntajes según el tipo de contenido detectado
8. Se normaliza el puntaje final.
9. Se devuelven los resultados obtenidos
"""

class AnalizadorSEO:

    def __init__(self, url):

        self.url = url
        dominio_extraido = tl.extract(url)
        self.dominio_base = f"{dominio_extraido.domain}.{dominio_extraido.suffix}"

        response = requests.get(url, timeout=100)
        self.soup = BeautifulSoup(response.content, "html.parser")

        #Estructura HTML
        self.html = self.soup.find("html")
        self.idioma = self.html.get("lang") if self.html else None

        self.body = self.soup.find("body")
        self.main = self.soup.find("main")
        self.articles = self.soup.find_all("article")

        self.all_links = self.soup.find_all("a", href=True)

        #Análisis de los elementos de Head
        self.titles = self.soup.find_all("title")
        self.meta_desc = self.soup.find_all("meta", attrs={"name": "description"})
        self.meta_robots = self.soup.find_all("meta", attrs={"name": "robots"})
        self.canonicals = self.soup.find_all("link", attrs={"rel": "canonical"})

        self.og_title = self.soup.find_all("meta", attrs={"property": "og:title"})
        self.og_desc = self.soup.find_all("meta", attrs={"property": "og:description"})
        self.og_img = self.soup.find_all("meta", attrs={"property": "og:image"})
        self.og_site = self.soup.find_all("meta", attrs={"property": "og:site_name"})

        #Datos estructurados
        self.json_ld = self.soup.find_all("script", type="application/ld+json")
        self.microdata = self.soup.find_all(attrs={"itemscope": True})
        self.json_types = []

        #Scores iniciales en 0
        self.score_links = 0
        self.score_contenido_texto = 0
        self.score_distribucion_parrafos_caracteres = 0
        self.score_jerarquia_encabezados = 0

        self.score_final_link = 0
        self.score_final_contenido_texto = 0
        self.score_final_distribucion_parrafos_caracteres = 0
        self.score_final_jerarquia_encabezados = 0

        self.score_sin_normalizar = 0
        self.score_normalizado = 0

    #utilidades

    def json_limpia(self):
        for j in self.json_ld:
            try:
                data = json.loads(j.string)
                if isinstance(data, dict):
                    self.json_types.append(data.get("@type"))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            self.json_types.append(item.get("@type"))
            except Exception:
                pass

    def es_producto(self):
        return "Product" in self.json_types

    #Flujo princial del análisis

    def funcion_analisis(self):
        if self.es_producto():
            self._analisis_producto()
        elif self.articles:
            self._analisis_editorial()
        elif self.main:
            self._analisis_webpage(self.main)
        elif self.body:
            self._analisis_webpage(self.body)

    #Análisis concreto

    def _analisis_editorial(self):
        dominante = max(self.articles, key=lambda a: len(a.find_all("p")), default=None)
        if not dominante:
            return
        self._analisis_webpage(dominante)

    def _analisis_producto(self):
        if self.main:
            self._analisis_webpage(self.main)
        elif self.body:
            self._analisis_webpage(self.body)

    def _analisis_webpage(self, contenedor):
        parrafos = [p for p in contenedor.find_all("p") if p.get_text(strip=True)]
        texto_total = sum(len(p.get_text(strip=True)) for p in parrafos)

        #Análisis sobre contenido
        if texto_total < 300:
            self.score_contenido_texto = 0
        elif texto_total < 800:
            self.score_contenido_texto = 8
        elif texto_total < 2000:
            self.score_contenido_texto = 15
        else:
            self.score_contenido_texto = 20

        #Análisis sobre distribución
        if parrafos:
            promedio = texto_total / len(parrafos)
            if promedio < 40:
                self.score_distribucion_parrafos_caracteres = 5
            elif promedio <= 80:
                self.score_distribucion_parrafos_caracteres = 15
            elif promedio <= 200:
                self.score_distribucion_parrafos_caracteres = 25
            elif promedio <= 300:
                self.score_distribucion_parrafos_caracteres = 15
            else:
                self.score_distribucion_parrafos_caracteres = 5

        #Análisis sobre titulares/encabezados
        h1 = contenedor.find_all("h1")
        h2 = contenedor.find_all("h2")
        h3 = contenedor.find_all("h3")

        if h1 and h2 and h3:
            self.score_jerarquia_encabezados = 30
        elif h1 and h2:
            self.score_jerarquia_encabezados = 22
        elif h1:
            self.score_jerarquia_encabezados = 10
        else:
            self.score_jerarquia_encabezados = 0

        #Análisis sobre enlaces
        self.score_links = self._analizar_links(contenedor)

    def _analizar_links(self, contenedor):
        internos = externos = 0

        for a in contenedor.find_all("a", href=True):
            href = a.get("href")
            if not href or href.startswith(("#", "mailto", "tel", "javascript")):
                continue
            if href.startswith(("http://", "https://", "//")):
                if self.dominio_base in href:
                    internos += 1
                else:
                    externos += 1
            else:
                internos += 1

        total = internos + externos
        score = 0

        if 1 <= total <= 2:
            score += 3
        elif total >= 3:
            score += 5

        if internos and externos:
            score += 5
        elif internos:
            score += 3
        elif externos:
            score += 2

        return score

    #Ajuste de pesos de puntaje

    def ajuste_pesos_por_type(self):

        if "NewsArticle" in self.json_types:
            score_max = 92
            self.score_final_jerarquia_encabezados = self.score_jerarquia_encabezados * 1.1
            self.score_final_contenido_texto = self.score_contenido_texto * 1.2
            self.score_final_distribucion_parrafos_caracteres = self.score_distribucion_parrafos_caracteres * 0.8
            self.score_final_link = self.score_links

        elif "Article" in self.json_types:
            score_max = 90
            self.score_final_jerarquia_encabezados = self.score_jerarquia_encabezados
            self.score_final_contenido_texto = self.score_contenido_texto
            self.score_final_distribucion_parrafos_caracteres = self.score_distribucion_parrafos_caracteres
            self.score_final_link = self.score_links

        elif "Product" in self.json_types:
            score_max = 88
            self.score_final_jerarquia_encabezados = self.score_jerarquia_encabezados * 0.9
            self.score_final_contenido_texto = self.score_contenido_texto * 0.7
            self.score_final_distribucion_parrafos_caracteres = self.score_distribucion_parrafos_caracteres * 0.8
            self.score_final_link = self.score_links * 1.2

        else:
            score_max = 85
            self.score_final_jerarquia_encabezados = self.score_jerarquia_encabezados
            self.score_final_contenido_texto = self.score_contenido_texto * 0.8
            self.score_final_distribucion_parrafos_caracteres = self.score_distribucion_parrafos_caracteres * 0.9
            self.score_final_link = self.score_links * 1.1

        self.score_sin_normalizar = (
            self.score_final_jerarquia_encabezados +
            self.score_final_contenido_texto +
            self.score_final_distribucion_parrafos_caracteres +
            self.score_final_link
        )

        self.score_normalizado = (self.score_sin_normalizar / score_max) * 100


    def analizar(self):
        self.json_limpia()
        self.funcion_analisis()
        self.ajuste_pesos_por_type()
        return self.score_normalizado


def logica(url_ingresada):
    try:
        analizador = AnalizadorSEO(url_ingresada)
        score_final = analizador.analizar()
        return {
            "score_seo": round(score_final, 2),
            "titulo": analizador.titles[0].get_text() if analizador.titles else "Sin título",
            "contenido": round(analizador.score_final_contenido_texto,2),
            "jerarquia": round(analizador.score_final_jerarquia_encabezados,2),
            "links": round(analizador.score_final_link,2),
            "distribucion": round(analizador.score_final_distribucion_parrafos_caracteres,2)
        }
    except Exception:
        return {"error": "No se pudo analizar la URL ingresada"}