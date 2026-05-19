FROM python:3.12-slim
WORKDIR /app

# Build arguments for collectstatic
ARG SECRET_KEY=dummy-key-for-build
ARG DEBUG=False

ENV SECRET_KEY=$SECRET_KEY
ENV DEBUG=$DEBUG

# Install system dependencies for build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "xjhs_pis.wsgi:application", "--bind", "0.0.0.0:8000"]
