#!/bin/bash

echo "📦 Instalando monorepo..."

# Instalar librería común
echo "Installing common library..."
cd packages/common && poetry install && cd ../..

# Instalar aplicaciones
for app in apps/*; do
    echo "Installing $(basename $app)..."
    cd "$app" && poetry install && cd ../..
done

echo "✅ Instalación completada"