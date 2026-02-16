# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY fe/package*.json ./
RUN npm install
COPY fe/ .
RUN npm run build

# Stage 2: Build Backend and Runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# gcc and libpq-dev are often needed for psycopg2/asyncpg building if wheels aren't available,
# though asyncpg usually has binary wheels. keeping them minimal.
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY be/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY be/ .

# Copy frontend build
COPY --from=frontend-builder /app/dist ./dist

ENV HOST=0.0.0.0
ENV PORT=8080
ENV FRONTEND_DIST=/app/dist

# Expose the port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
