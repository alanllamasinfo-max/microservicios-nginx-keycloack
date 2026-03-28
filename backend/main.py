from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
from jose import jwt, JWTError

# ─── Configuración ────────────────────────────────────────────────────────────

KC_SERVER_URL = "http://keycloak_server:8080/auth/"
REALM_NAME    = "myrealm"
CLIENT_ID     = "my-backend-client"

keycloak_openid = KeycloakOpenID(
    server_url=KC_SERVER_URL,
    client_id=CLIENT_ID,
    realm_name=REALM_NAME,
)

bearer_scheme = HTTPBearer(
    scheme_name="Keycloak JWT",
    description="Token JWT obtenido del flujo PKCE de Keycloak. Incluir como `Bearer <token>`.",
)

# ─── Metadata OpenAPI ─────────────────────────────────────────────────────────

DESCRIPTION = """
## SecureGateway Backend API 🔐

Microservicio de datos protegido por autenticación **Keycloak + JWT (RS256)**.

### Autenticación

Esta API no gestiona credenciales directamente. El cliente debe:

1. Autenticarse contra **Keycloak** (`/auth/realms/myrealm`)
   usando el flujo **Authorization Code + PKCE**
2. Obtener un `access_token` JWT firmado con RS256
3. Incluirlo en cada petición como header:
   ```
   Authorization: Bearer <access_token>
   ```

### Validación de tokens

El backend valida cada token **localmente** sin hacer una llamada de red
por request — obtiene la clave pública RSA de Keycloak en el arranque
y verifica la firma criptográfica del JWT.

### Seguridad

| Mecanismo | Detalle |
|-----------|---------|
| Algoritmo | RS256 (RSA + SHA-256) |
| Emisor    | `http://keycloak_server:8080/auth/realms/myrealm` |
| Audiencia | Verificación desactivada para entornos Docker internos |
"""

TAGS_METADATA = [
    {
        "name": "datos-protegidos",
        "description": "Endpoints que requieren autenticación JWT válida.",
    },
    {
        "name": "health",
        "description": "Monitoreo y estado del servicio.",
    },
]

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SecureGateway API",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "Tu Nombre",
        "url": "https://github.com/tu-usuario",
        "email": "tu@email.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# ─── Dependencia de autenticación ─────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> dict:
    """
    Valida el token JWT Bearer contra la clave pública de Keycloak.
    Lanza 401 si el token es inválido, expirado o mal formado.
    """
    token = credentials.credentials
    try:
        key_der    = keycloak_openid.public_key()
        public_key = f"-----BEGIN PUBLIC KEY-----\n{key_der}\n-----END PUBLIC KEY-----"

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de autenticación: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get(
    "/secure-data",
    tags=["datos-protegidos"],
    summary="Obtener datos del usuario autenticado",
    description="""
Retorna información del usuario extraída del JWT validado.

**Requiere:** Header `Authorization: Bearer <token>` con un JWT válido de Keycloak.

El token se valida localmente usando la clave pública RSA del realm — no hay
llamada adicional a Keycloak por request.
    """,
    responses={
        200: {
            "description": "Usuario autenticado correctamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Bienvenido testuser",
                        "status": "success",
                        "email": "testuser@example.com",
                        "roles": ["offline_access", "uma_authorization"],
                    }
                }
            },
        },
        401: {
            "description": "Token ausente, expirado o con firma inválida",
            "content": {
                "application/json": {
                    "example": {"detail": "Token inválido: Signature verification failed"}
                }
            },
        },
    },
)
async def secure_endpoint(user: dict = Depends(get_current_user)):
    return {
        "message": f"Bienvenido {user.get('preferred_username')}",
        "status": "success",
        "email": user.get("email"),
        "roles": user.get("realm_access", {}).get("roles", []),
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Estado del servicio",
    responses={
        200: {
            "description": "Servicio operativo",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "keycloak": "reachable",
                        "version": "1.0.0",
                    }
                }
            },
        }
    },
)
async def health():
    """Verifica que el servicio está activo y puede contactar con Keycloak."""
    try:
        keycloak_openid.public_key()
        kc_status = "reachable"
    except Exception:
        kc_status = "unreachable"

    return {"status": "healthy", "keycloak": kc_status, "version": "1.0.0"}


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "SecureGateway API", "docs": "/docs"}


# ─── OpenAPI schema personalizado ─────────────────────────────────────────────

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        tags=app.openapi_tags,
        routes=app.routes,
    )
    # Definir el esquema de seguridad global
    schema["components"]["securitySchemes"] = {
        "KeycloakJWT": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token JWT obtenido del flujo PKCE de Keycloak.",
        }
    }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
