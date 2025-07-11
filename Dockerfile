# Base stage: build dependencies
FROM python:3.11-slim AS builder

# Set environment variables for Hugging Face cache
ENV TRANSFORMERS_CACHE=/tmp/transformers \
    HF_HOME=/tmp/huggingface \
    HF_DATASETS_CACHE=/tmp/hf_datasets

WORKDIR /src
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /src
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# After downloading:
RUN mkdir -p /src/models && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2').save('/src/models/all-MiniLM-L6-v2')"


# Add app source code
COPY . .

# Security best practices
#RUN adduser --disabled-password --no-create-home appuser
#USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
