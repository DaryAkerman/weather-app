FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY /static/ /app/static
COPY /templates/ /app/templates
COPY app.py /app/
EXPOSE 5000
CMD ["python", "app.py"]
