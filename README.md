# 🔐 SecureGateway

<div align="center">

![Keycloak](https://img.shields.io/badge/Keycloak-22.0-4D4D4D?style=for-the-badge&logo=keycloak&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-Alpine-009639?style=for-the-badge&logo=nginx&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Plataforma de autenticación empresarial con Keycloak, JWT y gateway Nginx.**  
Un único punto de entrada para frontend, backend y proveedor de identidad.

[Arquitectura](#️-arquitectura) · [Instalación](#-instalación) · [Flujo de autenticación](#-flujo-de-autenticación) · [API](#-api-reference)

</div>

---

## 📌 Descripción

**SecureGateway** es una plataforma de autenticación y autorización lista para producción. Integra Keycloak como proveedor de identidad central (IdP), un backend FastAPI que valida tokens JWT con clave pública RSA, y un gateway Nginx que actúa como único punto de entrada para todos los servicios.

> Demuestra cómo implementar autenticación SSO real en una arquitectura de microservicios, sin depender de servicios de terceros — todo self-hosted con Docker Compose.

---

## 🏗️ Arquitectura

```
                        ┌─────────────────────┐
                        │     Cliente Web      │
                        │  (Keycloak.js / SPA) │
                        └──────────┬──────────┘
                                   │ HTTP :80
                        ┌──────────▼──────────┐
                        │    Gateway Nginx     │
                        │   (Reverse Proxy)    │
                        └──┬──────────────┬───┘
                           │              │
             ┌─────────────▼──┐    ┌──────▼──────────────┐
             │   /auth/*      │    │      /api/*          │
             │                │    │                      │
             │  Keycloak 22   │    │  FastAPI Backend     │
             │  (IdP / SSO)   │    │  (JWT Validation)    │
             └────────┬───────┘    └──────────────────────┘
                      │
             ┌────────▼───────┐
             │   PostgreSQL   │
             │ (Keycloak DB)  │
             └────────────────┘
```

---

## ✨ Características principales

| Feature | Descripción |
|---|---|
| 🔑 **SSO con Keycloak** | Proveedor de identidad self-hosted con soporte OIDC / OAuth2 |
| 🛡️ **Validación JWT con clave RSA** | El backend obtiene la clave pública de Keycloak y valida tokens sin estado compartido |
| 🚪 **Gateway centralizado** | Nginx enruta `/auth/`, `/api/` y el frontend desde un único puerto |
| 🔄 **PKCE Flow** | Flujo de autorización seguro sin client_secret en el navegador |
| 🐳 **100% Dockerizado** | Un solo `docker compose up` levanta toda la plataforma |
| 📦 **Persistencia de sesiones** | PostgreSQL como backend de Keycloak para datos durables |

---

## 🔄 Flujo de autenticación

```
Browser          Nginx          Keycloak         FastAPI
   │                │               │                │
   │── GET / ──────►│               │                │
   │◄── index.html ─│               │                │
   │                │               │                │
   │── Keycloak.js init() ─────────►│                │
   │◄── redirect login page ────────│                │
   │                │               │                │
   │── POST credentials ───────────►│                │
   │◄── JWT access_token ───────────│                │
   │                │               │                │
   │── GET /api/secure-data ────────────────────────►│
   │   Authorization: Bearer <JWT>  │                │
   │                │               │                │
   │                │               │◄── public_key()│
   │                │               │── RSA key ─────►
   │                │               │                │── jwt.decode()
   │◄── 200 { user data } ──────────────────────────│
```

---

## 🗂️ Estructura del proyecto

```
securegate/
├── docker-compose.yml           # Orquestación de todos los servicios
├── nginx.conf                   # Configuración del gateway y proxy inverso
├── deploy.sh                    # Script de despliegue automatizado
├── backend/
│   ├── main.py                  # FastAPI: endpoint protegido + validación JWT
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── index.html               # SPA con Keycloak.js (PKCE flow)
└── keycloak_config/
    └── realm-export.json        # Realm preconfigurado (import automático)
```

---

## 🚀 Instalación

### Prerrequisitos

- Docker 24+ y Docker Compose v2

### Despliegue con Docker

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/securegate.git
cd securegate

# 2. Levantar toda la plataforma
docker compose up -d

# 3. Esperar a que Keycloak importe el realm (~30 segundos)
docker compose logs -f keycloak | grep "Listening on"
```

Los servicios estarán disponibles en:

| Servicio | URL |
|---|---|
| Frontend | `http://localhost` |
| Keycloak Admin | `http://localhost/auth` → admin / admin |
| API Backend | `http://localhost/api/secure-data` |

### Redespliegue tras cambios en el backend

```bash
./deploy.sh
```

---

## ⚙️ Configuración de Keycloak

El realm `myrealm` se importa automáticamente al iniciar. Incluye:

| Parámetro | Valor |
|---|---|
| Realm | `myrealm` |
| Client (frontend) | `my-frontend-client` (público, PKCE) |
| Client (backend) | `my-backend-client` (confidencial) |
| Usuario de prueba | `testuser` / `testpassword` |

Para acceder al panel de administración: `http://localhost/auth` → `admin` / `admin`

---

## 📡 API Reference

### `GET /api/secure-data`

Endpoint protegido. Requiere token JWT válido emitido por Keycloak.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200 OK`:**
```json
{
  "message": "Bienvenido testuser",
  "status": "success",
  "email": "testuser@example.com"
}
```

**Response `401 Unauthorized`:**
```json
{
  "detail": "Token inválido: Signature verification failed"
}
```

---

## ⚙️ Variables de entorno

```env
# Keycloak
KC_DB=postgres
KC_DB_URL=jdbc:postgresql://postgres_db:5432/keycloak_db
KC_DB_USERNAME=admin
KC_DB_PASSWORD=password123
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Backend FastAPI
KEYCLOAK_ISSUER=http://keycloak_server:8080/auth/realms/myrealm

# Base de datos
POSTGRES_DB=keycloak_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=password123
```

> ⚠️ En producción, usa secretos gestionados (Docker Secrets, Vault, etc.) y nunca expongas credenciales en el repositorio.

---

## 🛠️ Stack tecnológico

- **[Keycloak 22](https://www.keycloak.org/)** — Identity Provider con soporte OIDC, OAuth2 y SAML
- **[FastAPI](https://fastapi.tiangolo.com/)** — Backend asíncrono con validación JWT
- **[python-keycloak](https://python-keycloak.readthedocs.io/)** — Cliente oficial para integración con Keycloak
- **[python-jose](https://python-jose.readthedocs.io/)** — Decodificación y verificación de tokens JWT (RS256)
- **[Nginx](https://nginx.org/)** — Gateway y reverse proxy
- **[PostgreSQL 15](https://www.postgresql.org/)** — Persistencia para Keycloak
- **[Docker Compose](https://docs.docker.com/compose/)** — Orquestación de servicios

---

## 📄 Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para más información.

---

<div align="center">

Hecho con ☕ y Python · [⬆ Volver arriba](#-securegate)

</div>
