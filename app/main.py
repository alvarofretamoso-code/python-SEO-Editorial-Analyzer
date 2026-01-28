from fastapi import FastAPI, Form
from app.analisis.logic  import logica
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from app.ia.cerebro import genera_recomendacion




app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request:Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.post("/resultados")
def resultados(request: Request, url: str = Form(...)):
    data = logica(url)

    if "error" in data:
        return templates.TemplateResponse(
            "resultados.html",
            {
                "request": request,
                "url": url,
                "titulo": "URL inválida o inaccesible",
                "puntaje_contenido": "-",
                "puntaje_jerarquia": "-",
                "puntaje_enlaces": "-",
                "puntaje_distribucion": "-",
                "puntaje_seo": "Error",
                "descripcion": data["error"]
            }
        )

    recomendacion_ia = genera_recomendacion(data)

    return templates.TemplateResponse(
        "resultados.html",
        {
            "request": request,
            "url": url,
            "titulo": data["titulo"],
            "puntaje_contenido": data["contenido"],
            "puntaje_jerarquia": data["jerarquia"],
            "puntaje_enlaces": data["links"],
            "puntaje_distribucion": data["distribucion"],
            "puntaje_seo": data["score_seo"],
            "descripcion": recomendacion_ia
        }
    )