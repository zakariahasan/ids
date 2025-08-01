# ─── Stage 1: build ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS build
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tshark libpcap-dev build-essential iproute2 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Stage 2: runtime ───────────────────────────────────────────────────────────
FROM python:3.11-slim
COPY --from=build /usr/local /usr/local

WORKDIR /app
COPY . .

ENV PYTHONUNBUFFERED=1 \
    TZ=UTC \
    FLASK_APP=ids.web.app:create_app \
    IDS_INTERFACE=eth0

EXPOSE 5000

# Main IDS sniffer entry‑point
CMD ["python", "ids/scripts/run_ids.py", "--interface", "eth0"]
