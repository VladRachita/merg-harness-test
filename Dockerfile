# Image for both the harness runner and the bundled demo backend.
FROM python:3.12-slim

# ffmpeg/ffprobe are needed by the media generator and the media validation step
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# default: run the suites against the configured target
ENTRYPOINT ["python", "-m", "sentinel.cli"]
CMD ["run", "--target", "reference-secure", "--suite", "all"]
