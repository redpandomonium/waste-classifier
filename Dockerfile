FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    WASTE_DATA_DIR=/data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY waste_classifier ./waste_classifier
COPY dashboard ./dashboard
COPY eda ./eda
COPY models ./models

EXPOSE 8501
CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
