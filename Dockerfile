FROM python:3.11-slim

WORKDIR /app

# Install TimeTree exporter + Flask web server
RUN pip install --no-cache-dir timetree-exporter==0.6.1 Flask==3.0.0

# Copy app
COPY app.py .

# Default envs (can be overridden in Hostinger)
ENV OUTPUT_FILE=/app/timetree.ics
ENV PORT=8000
ENV SYNC_INTERVAL_MINUTES=15

EXPOSE 8000

CMD ["python", "app.py"]
