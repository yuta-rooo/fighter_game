# Pixel Fighter v5.3 server-only Docker image
# The pygame client is a desktop app and should be run on each player's PC.
# This container runs only the authoritative TCP game server.

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GAME_MODE=online \
    CPU_DIFFICULTY=normal \
    INTERNAL_PORT=5000

WORKDIR /app

COPY server.py cpu_controller.py docker_entrypoint.py ./

EXPOSE 5000

CMD ["python", "docker_entrypoint.py"]
