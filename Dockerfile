FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY configs/ configs/
COPY src/ src/
COPY apps/ apps/
COPY models/ models/
COPY docs/json/ docs/json/
COPY data/raw/ data/raw/

EXPOSE 8000 8501 8502

# One image, three commands (see docker-compose.yml):
#   api:          uvicorn src.api.main:app --host 0.0.0.0 --port 8000
#   predict-app:  streamlit run apps/predict_app/app.py --server.port 8501
#   dashboard:    streamlit run apps/dashboard/app.py --server.port 8502
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
