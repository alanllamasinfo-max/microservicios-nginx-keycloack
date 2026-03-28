from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID
from jose import jwt # Importamos jose directamente
from prometheus_fastapi_instrumentator import Instrumentator #linea anadida para el uso de prometheus``

app = FastAPI()

Instrumentator().instrument(app).expose(app)

# Configuración interna
KC_SERVER_URL = "http://keycloak_server:8080/auth/"
REALM_NAME = "myrealm"
CLIENT_ID = "my-backend-client"

keycloak_openid = KeycloakOpenID(
    server_url=KC_SERVER_URL,
    client_id=CLIENT_ID,
    realm_name=REALM_NAME
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # 1. Obtener la llave pública de Keycloak
        key_der = keycloak_openid.public_key()
        public_key = "-----BEGIN PUBLIC KEY-----\n" + key_der + "\n-----END PUBLIC KEY-----"
        
        # 2. Decodificar usando la librería jose directamente para evitar errores de argumentos
        # Esto ignora la audiencia (aud) que suele dar guerra en Docker
        token_info = jwt.decode(
            token, 
            public_key, 
            algorithms=['RS256'],
            options={"verify_aud": False} 
        )
        return token_info

    except Exception as e:
        print(f"DEBUG: Error validando token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}"
        )

@app.get("/secure-data")
async def secure_endpoint(user: dict = Depends(get_current_user)):
    return {
        "message": f"Bienvenido {user.get('preferred_username')}",
        "status": "success",
        "email": user.get("email")
    }
