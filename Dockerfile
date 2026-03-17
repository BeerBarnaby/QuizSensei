FROM python:3.12-slim AS builder

WORKDIR /build

# Install system packages needed to compile certain Python wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker layer caching.
COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="QuizSensei Team"
LABEL app="quizsensei-api"
LABEL version="0.1.0"

# Install runtime system packages for OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-tha \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY app/ ./app/

# Uploads directory – will be volume-mounted in production
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Use exec form for proper signal handling (SIGTERM on container stop)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
