
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy OpenAPI spec into the image
COPY openapi/openapi.json /app/openapi.json

# Install tools needed to generate the client
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl default-jre \
  && rm -rf /var/lib/apt/lists/*

# Download OpenAPI Generator
RUN curl -L -o /tmp/openapi-generator-cli.jar \
  https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.6.0/openapi-generator-cli-7.6.0.jar

# Generate python client with package name = openapi_client (matches your imports)
RUN java -jar /tmp/openapi-generator-cli.jar generate \
  -i /app/openapi.json \
  -g python \
  -o /app/python-client \
  --additional-properties=packageName=openapi_client

# Install generated client into the environment
RUN pip install --no-cache-dir /app/python-client

# Now install the remaining deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]