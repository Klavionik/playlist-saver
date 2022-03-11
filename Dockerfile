FROM python:3.10.2-alpine
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/app
COPY requirements.txt .
RUN python -m venv venv && source venv/bin/activate
RUN apk add --no-cache gcc libffi-dev musl-dev
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8030", "--factory", "main:create_app"]

