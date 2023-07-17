FROM python:3.10.2-alpine
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/app
COPY requirements.txt .
RUN apk add --no-cache gcc libffi-dev musl-dev
RUN pip install -r requirements.txt
COPY . .
