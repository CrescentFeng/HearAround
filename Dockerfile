FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --prefer-binary -r /app/backend/requirements.txt

COPY backend /app/backend
COPY config /app/config
COPY dist /app/dist
COPY data/manifest.csv data/ATTRIBUTION.md /app/data/
COPY data/demo /app/data/demo
COPY eval/demo_baseline_metrics.json eval/holdout_metrics.json eval/stream_stress_metrics.json /app/eval/
COPY submission/PROJECT_FACTS.json /app/submission/PROJECT_FACTS.json

RUN useradd --create-home --uid 1000 hearound \
    && mkdir -p /app/.cache/tfhub \
    && chown -R hearound:hearound /app
USER hearound

EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '7860') + '/api/health', timeout=3)" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-7860} --proxy-headers --forwarded-allow-ips='*'"]
