FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.lock.txt pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.lock.txt && pip install --no-cache-dir --no-deps . \
    && useradd --uid 10001 --create-home app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "ai_platform.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-config", "/app/src/ai_platform/logging.json"]
