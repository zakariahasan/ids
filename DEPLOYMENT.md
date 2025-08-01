# Deployment Guide – IDS Containerisation

This guide explains how to build, run, and publish the IDS container images.

## 1  Single‑container workflow

```bash
docker build -t ids:latest .
docker run --cap-add=NET_RAW -p 5000:5000 ids:latest
```

Use `--network host` on Linux for full packet visibility.

## 2  docker‑compose workflow

```bash
docker compose up --build   # build and start IDS + Postgres
docker compose logs -f ids   # follow IDS service logs
docker compose down -v       # stop and clean volumes
```

Edit `docker-compose.yml` to match your interface or DB credentials.

## 3  Publishing to a registry

### Docker Hub

```bash
docker tag ids:latest <your‑dockerhub‑user>/ids:0.1.0
docker push <your‑dockerhub‑user>/ids:0.1.0
```

### GitHub Container Registry

```bash
docker tag ids:latest ghcr.io/<org>/ids:0.1.0
echo $PAT | docker login ghcr.io -u <username> --password-stdin
docker push ghcr.io/<org>/ids:0.1.0
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Permission denied` opening pcap | Missing NET_RAW | Run with `--cap-add=NET_RAW` |
| No packets captured | Isolated network namespace | Use `network_mode: host` or mirror traffic |
| High CPU | Unfiltered capture loop | Add BPF filters or batch processing |

Happy shipping!
