from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID

app = FastAPI()

# Configuración interna de red Docker
KC_SERVER_URL = "http://keycloak_server:8080/auth/"
REALM_NAME = "myrealm"
CLIENT_ID = "my-backend-client"

# Inicialización de Keycloak
keycloak_openid = KeycloakOpenID(
    server_url=KC_SERVER_URL,
    client_id=CLIENT_ID,
    realm_name=REALM_NAME
)

# Esquema para leer el token del Header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Obtenemos la llave pública desde Keycloak
        public_key = "-----BEGIN PUBLIC KEY-----\n" + keycloak_openid.public_key() + "\n-----END PUBLIC KEY-----"
        
        # Validamos el token
        # Nota: verify_aud se pone en False si el token no trae el campo 'aud' exacto
        options = {"verify_signature": True, "verify_aud": False, "verify_exp": True}
        token_info = keycloak_openid.decode_token(token, key=public_key, options=options)
        return token_info
    except Exception as e:
        print(f"Error validando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/api/secure-data")
async def secure_endpoint(user: dict = Depends(get_current_user)):
    return {
        "message": f"Hola {user.get('preferred_username')}",
        "roles": user.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", []),
        "status": "success"
    }