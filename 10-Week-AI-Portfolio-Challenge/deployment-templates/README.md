# Deployment Templates
*Production-Ready Deployment Configurations*

## Overview
This directory contains deployment templates and configurations for getting your AI projects into production quickly and professionally.

## Deployment Options by Project Type

### Web Applications (Streamlit/FastAPI)
- **Platforms**: Streamlit Cloud, Heroku, Railway, Render
- **Use Cases**: Dashboards, APIs, interactive demos
- **Benefits**: Easy deployment, custom domains, SSL

### Machine Learning APIs
- **Platforms**: AWS Lambda, Google Cloud Run, Azure Functions
- **Use Cases**: Model inference endpoints, microservices
- **Benefits**: Serverless scaling, pay-per-use, high availability

### Mobile Applications
- **Platforms**: App Store, Google Play, TestFlight
- **Use Cases**: Edge AI, mobile inference, user apps
- **Benefits**: Direct user access, offline capability, native performance

### Docker Containerization
- **Platforms**: Docker Hub, AWS ECR, Google Container Registry
- **Use Cases**: Consistent deployment, scalable services
- **Benefits**: Environment consistency, easy scaling, cloud portability

## Template Structure

```
deployment-templates/
├── web-apps/
│   ├── streamlit/
│   ├── fastapi/
│   └── react/
├── apis/
│   ├── serverless/
│   ├── microservices/
│   └── ml-inference/
├── mobile/
│   ├── react-native/
│   ├── flutter/
│   └── tensorflow-lite/
├── containers/
│   ├── dockerfile-templates/
│   ├── docker-compose/
│   └── kubernetes/
├── cloud-platforms/
│   ├── aws/
│   ├── gcp/
│   ├── azure/
│   └── heroku/
└── ci-cd/
    ├── github-actions/
    ├── gitlab-ci/
    └── jenkins/
```

## Quick Start Deployment Guides

### 1. Streamlit App Deployment

#### Streamlit Cloud (Free)
```bash
# 1. Push your code to GitHub
git add .
git commit -m "Add Streamlit app"
git push origin main

# 2. Connect to Streamlit Cloud
# Visit: https://share.streamlit.io
# Connect GitHub repository
# Auto-deploy on push
```

#### Requirements Template
```txt
streamlit==1.28.0
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
plotly==5.15.0
```

### 2. FastAPI Deployment

#### Railway (Recommended)
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and deploy
railway login
railway init
railway up
```

#### Dockerfile Template
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. React App Deployment

#### Netlify (Free)
```bash
# 1. Build your app
npm run build

# 2. Deploy via drag-and-drop
# Visit: https://app.netlify.com/drop
# Drag build folder to deploy
```

#### Vercel (Recommended for Next.js)
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
vercel
```

## Platform-Specific Configurations

### AWS Deployment

#### Lambda Function Template
```python
import json
import boto3
import pickle
import numpy as np

def lambda_handler(event, context):
    # Load model from S3
    s3 = boto3.client('s3')
    model_obj = s3.get_object(Bucket='your-bucket', Key='model.pkl')
    model = pickle.loads(model_obj['Body'].read())
    
    # Get input data
    data = json.loads(event['body'])
    features = np.array(data['features']).reshape(1, -1)
    
    # Make prediction
    prediction = model.predict(features)[0]
    
    return {
        'statusCode': 200,
        'body': json.dumps({'prediction': float(prediction)})
    }
```

#### requirements.txt for Lambda
```txt
numpy==1.24.3
scikit-learn==1.3.0
boto3==1.28.25
```

### Google Cloud Platform

#### Cloud Run Deployment
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/ml-api', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/ml-api']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'ml-api', '--image', 'gcr.io/$PROJECT_ID/ml-api', 
           '--platform', 'managed', '--region', 'us-central1']
```

### Azure Deployment

#### Azure Functions Template
```python
import azure.functions as func
import json
import pickle
import numpy as np

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Load model
        with open('model.pkl', 'rb') as f:
            model = pickle.load(f)
        
        # Get input
        req_body = req.get_json()
        features = np.array(req_body['features']).reshape(1, -1)
        
        # Predict
        prediction = model.predict(features)[0]
        
        return func.HttpResponse(
            json.dumps({'prediction': float(prediction)}),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=400
        )
```

## CI/CD Pipeline Templates

### GitHub Actions

#### Python ML Model Deployment
```yaml
name: Deploy ML Model
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/
      - name: Train model
        run: |
          python train_model.py
      - name: Deploy to production
        run: |
          # Add deployment commands
```

### Docker Compose for Development

```yaml
version: '3.8'
services:
  ml-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MODEL_PATH=/app/models/model.pkl
    volumes:
      - ./models:/app/models
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: mldb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Environment Configuration

### Production Environment Variables
```bash
# .env.production
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379
MODEL_PATH=/app/models/
API_KEY=your-api-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
```

### Development Environment Variables
```bash
# .env.development
DATABASE_URL=sqlite:///./dev.db
REDIS_URL=redis://localhost:6379
MODEL_PATH=./models/
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Security Best Practices

### API Security
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

app = FastAPI()
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

@app.post("/predict")
async def predict(data: dict, user=Depends(verify_token)):
    # Your prediction logic here
    pass
```

### HTTPS Configuration
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Logging

### Application Monitoring
```python
import logging
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_LATENCY.observe(process_time)
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response
```

This comprehensive deployment template collection ensures your AI projects can be deployed professionally and scale with your career growth.