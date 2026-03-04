#!/bin/bash
# Script de despliegue para servidor-permanente

echo "🛑 Deteniendo contenedores actuales..."
docker compose down

echo "🏗️ Reconstruyendo Microservicio Python..."
docker compose build user_service

echo "🚀 Levantando infraestructura..."
docker compose up -d

echo "----------------------------------------"
echo "✅ Despliegue completado con éxito."
echo "🌍 Accede a: http://localhost"
echo "🔑 Keycloak en: http://localhost/auth"
echo "----------------------------------------"
