from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import connect_db, close_db
from .routers import archivos, auth, incidencias, usuarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="UTM Desk – API de Incidencias NoSQL Cloud",
    description=(
        "Sistema integral de gestión, resolución y analítica de incidencias en el campus UTM. "
        "Arquitectura documental sobre MongoDB Atlas M0, Redis y FastAPI. "
        "Implementa los 7 casos de uso, matriz de roles y seguridad JWT."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Errores de validación → HTTP 400 Bad Request ─────────────────────────────
# FastAPI responde 422 por defecto; el proyecto exige 400 para datos inválidos.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = [
        {
            "campo": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
            "mensaje": err.get("msg"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Datos inválidos: "
            + "; ".join(
                f"{e['campo']}: {e['mensaje']}" if e["campo"] else str(e["mensaje"]).removeprefix("Value error, ")
                for e in errores
            ),
            "errores": errores,
        },
    )


# ── Registro de Enrutadores ───────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(incidencias.router)
app.include_router(archivos.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "status": "ok",
        "mensaje": "UTM Desk NoSQL Cloud API funcionando 🚀",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
