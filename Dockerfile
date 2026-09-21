FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 1000 catalogwatch \
    && mkdir -p /app/out /app/state \
    && chown -R catalogwatch:catalogwatch /app
USER catalogwatch

ENTRYPOINT ["catalogwatch"]
CMD ["doctor"]
