FROM alpine/git:2.47.2 AS source
ARG XIAOZHI_SERVER_COMMIT=6afc54a17def47578a4b3efc4680873689d3168b
RUN git clone https://github.com/xinnan-tech/xiaozhi-esp32-server.git /src \
 && git -C /src checkout --detach "$XIAOZHI_SERVER_COMMIT"
COPY custom-providers/xiaozhi-patches/never-idle.patch /tmp/never-idle.patch
RUN git -C /src apply --check /tmp/never-idle.patch \
 && git -C /src apply /tmp/never-idle.patch \
 && test "$(git -C /src rev-parse HEAD)" = "$XIAOZHI_SERVER_COMMIT"

COPY custom-providers/xiaozhi-patches/secure-transport.patch /tmp/secure-transport.patch
RUN git -C /src apply --check /tmp/secure-transport.patch \
 && git -C /src apply /tmp/secure-transport.patch

FROM python:3.11.10-slim-bookworm
ARG XIAOZHI_SERVER_COMMIT=6afc54a17def47578a4b3efc4680873689d3168b
LABEL org.opencontainers.image.revision=$XIAOZHI_SERVER_COMMIT
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libopus0 libsndfile1 \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/xiaozhi-esp32-server
COPY --from=source /src/main/xiaozhi-server/requirements.txt /tmp/upstream-requirements.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
      torch==2.2.2 torchaudio==2.2.2 \
 && pip install --no-cache-dir -r /tmp/upstream-requirements.txt \
 && pip install --no-cache-dir faster-whisper==1.2.1 piper-tts==1.3.0 scipy==1.15.3
COPY --from=source /src/main/xiaozhi-server /opt/xiaozhi-esp32-server
CMD ["python", "app.py"]
