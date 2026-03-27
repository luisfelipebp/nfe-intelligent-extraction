from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from database import engine, Base
from routers import notas
from contextlib import asynccontextmanager
from fastapi import HTTPException as FastAPIHTTPException

from estado import recursos_ia

from services.extractor import NFeProcessor

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando o servidor...")
    
    recursos_ia["extrator_nfe"] = NFeProcessor()
    
    yield 
    
    print("Desligando o servidor...")
    recursos_ia.clear() 
    print("Memória liberada!")

app = FastAPI(
    title="API de Extração de Documentos",
    description="""
    Serviço para extração de dados de notas fiscais via OCR
    e transcrição de áudios via Whisper.

    ## Funcionalidades
    - **Notas Fiscais**: extração, listagem, atualização de status e exclusão
    - **Áudios**: transcrição assíncrona com polling de status
    """,
    version="1.0.0",
    docs_url="/docs",       # documentação interativa Swagger UI
    redoc_url="/redoc",      # documentação alternativa ReDoc
    lifespan=lifespan
)

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Captura ValueErrors não tratados e retorna 400 com mensagem clara."""
    return JSONResponse(
        status_code=400,
        content={
            "erro": "Dado inválido",
            "detalhe": str(exc)
        }
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """
    Captura qualquer erro não tratado.
    Em produção: logue o erro aqui antes de retornar 500.
    """
    if isinstance(exc, FastAPIHTTPException):
        raise exc
    
    
    return JSONResponse(
        status_code=500,
        content={
            "erro": "Erro interno do servidor",
            "detalhe": "Um erro inesperado ocorreu. Tente novamente."
        }
    )





# -----------------------------------------------------------------------------
# Registro dos Routers
# -----------------------------------------------------------------------------
# prefix  → prefixo adicionado a todas as rotas do router
# tags    → agrupa as rotas na documentação /docs
# -----------------------------------------------------------------------------



app.include_router(
    notas.router,
    prefix="/notas",
    tags=["Notas Fiscais"]
)


# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Endpoint simples para verificar se a API está no ar.
# Usado pelo Docker healthcheck e por ferramentas de monitoramento.
# -----------------------------------------------------------------------------

@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "versao": "1.0.0"}
