# ── Build Stage ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Runtime Stage ───────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Security: non-root user
RUN addgroup --system devbrain && adduser --system --ingroup devbrain devbrain

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY . .
RUN chown -R devbrain:devbrain /app

USER devbrain

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
