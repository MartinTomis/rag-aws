## TO DO:

- Search - should be hybrid - vector and keyword/BM25 - DONE
- Parsing of different documents - DONE
- Batch processing
- Similarity threshold - DONE - in function
- metadata - Name in the file, name of the file, topics
- metadata filtering and Faceted search (or faceted navigation) provides users with filterable categories (facets) to refine search results interactively.
### logging and correlation ID - middleware.
```
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```
```
app.add_middleware(CorrelationIdMiddleware)
```
```
import logging

logger = logging.getLogger("app")

def log_with_correlation_id(request, msg):
    logger.info(f"[{request.state.correlation_id}] {msg}")
```

```

from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```


### database migrations and schema management
```
client.schema.update_property("Document", {
  "name": "document_name",
  "dataType": ["text"]
})
```
- Deployment



This needs to be loaded first.

import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")





4. Use __name__ == "__main__" or FastAPI startup event
If you have init code (like init_schema()), do not run it directly at import-time — do this:

python
Copy
Edit
def init():
    init_schema()

if __name__ == "__main__":
    init()
Or in FastAPI:

python
Copy
Edit
@app.on_event("startup")
def on_startup():
    init_schema()

# Set Region
aws configure set region eu-central-1
# Authenticate (if needed)
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 161015140575.dkr.ecr.eu-central-1.amazonaws.com

docker build -t rag-aws-container:first .
# Tag image
docker tag rag-aws-container:first 161015140575.dkr.ecr.eu-central-1.amazonaws.com/rag-registry-v1

# Push image
docker push 161015140575.dkr.ecr.eu-central-1.amazonaws.com/rag-registry-v1

# Register the tasks
aws ecs register-task-definition --cli-input-json file://deployment/weaviate-task.json
aws ecs register-task-definition --cli-input-json file://deployment/rag-task.json

# Update service
aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service rag-app-service \
  --task-definition rag-task

aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service weaviate-service \
  --task-definition weaviate-task

# Force new deployment
aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service rag-app-service \
  --force-new-deployment

aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service weaviate-service \
  --force-new-deployment





aws configure set region eu-central-1

aws ecs create-cluster --cluster-name rag-ecs-cluster-1

aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://deployment/ecs-trust-policy.json


aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonSSMManagedInstanceCore


aws ecs register-task-definition --cli-input-json file://deployment/weaviate-task.json
aws ecs register-task-definition --cli-input-json file://deployment/rag-task.json

aws ec2 describe-vpcs
aws ec2 describe-subnets
aws ec2 describe-security-groups

# Replace subnet-xxxx and sg-yyyy with actual IDs

aws ec2 describe-subnets \
  --query "Subnets[*].{ID:SubnetId,AZ:AvailabilityZone,Default:DefaultForAz}" \
  --output table

aws ec2 describe-vpcs --query "Vpcs[*].{ID:VpcId,CIDR:CidrBlock}" --output table


aws ec2 create-security-group \
  --group-name rag-sg \
  --description "Security group for RAG ECS Fargate" \
  --vpc-id vpc-d2c139bb

aws ec2 authorize-security-group-ingress \
  --group-id sg-09c634a7064f19396 \
  --protocol tcp \
  --port 8080 \
  --source-group sg-09c634a7064f19396

aws ec2 authorize-security-group-ingress \
  --group-id sg-09c634a7064f19396 \
  --protocol tcp \
  --port 50051 \
  --source-group sg-09c634a7064f19396

aws ec2 authorize-security-group-ingress \
  --group-id sg-09c634a7064f19396 \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0



aws ecs create-service \
  --cluster rag-ecs-cluster-1 \
  --service-name weaviate-service \
  --task-definition weaviate-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={subnets=["subnet-93e22ffa"],securityGroups=["sg-09c634a7064f19396"],assignPublicIp="ENABLED"}'

aws ecs create-service \
  --cluster rag-ecs-cluster-1 \
  --service-name rag-app-service \
  --task-definition rag-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={subnets=["subnet-93e22ffa"],securityGroups=["sg-09c634a7064f19396"],assignPublicIp="ENABLED"}'

aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service rag-app-service \
  --task-definition arn:aws:ecs:eu-central-1:161015140575:task-definition/rag-task:10 \
  --enable-execute-command \
  --force-new-deployment




curl http://ec2-18-153-79-61.eu-central-1.compute.amazonaws.com:8000/health

http://ec2-3-79-63-33.eu-central-1.compute.amazonaws.com:8000/docs
http://ec2-18-153-79-61.eu-central-1.compute.amazonaws.com:8000/docs

aws ec2 describe-security-groups --group-ids sg-09c634a7064f19396

aws ec2 authorize-security-group-ingress \
  --group-id sg-09c634a7064f19396 \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0



  aws ecs describe-tasks \
  --cluster rag-ecs-cluster-1 \
  --tasks <your-task-id>




### Test v RAG
aws ecs execute-command \
  --cluster rag-ecs-cluster-1 \
  --task 1f597abf946f47cb9cc3ac5ebb95e7ca \
  --container rag-aws-container \
  --command "/bin/sh" \
  --interactive


python3 -c "import requests; r = requests.get('http://weaviate.myapp.local:8080/v1'); print(r.status_code, r.text)"

### Test v Weaviate
aws ecs execute-command \
  --cluster rag-ecs-cluster-1 \
  --task f30005e5cd08410998357f5af0bed909 \
  --container weaviate \
  --command "/bin/sh" \
  --interactive

python3 -c "import requests; print(requests.get('http://localhost:8080/v1').json())"



aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service rag-app-service \
  --force-new-deployment

aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service your-service-name \
  --force-new-deployment



curl http://weaviate.myapp.local:8080/v1

## model refresh

## Enabling ECS EXEC pro weaviate

### First task revision with new role - in console, add as Task Role the ecsTaskExecutionRole
### Deploy the revision to service 
aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service weaviate-service \
  --task-definition weaviate-task:5 \
  --enable-execute-command \
  --force-new-deployment


aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service weaviate-service \
  --enable-execute-command

aws ecs update-service \
  --cluster rag-ecs-cluster-1 \
  --service weaviate-service \
  --force-new-deployment

aws ecs execute-command \
  --cluster rag-ecs-cluster-1 \
  --task 2278e76fa55e483ea981e58affd474d7 \
  --container weaviate \
  --command "/bin/sh" \
  --interactive


  aws ecs list-tasks \
  --cluster rag-ecs-cluster-1 \
  --service-name weaviate-service


  aws ecs describe-tasks \
  --cluster rag-ecs-cluster-1 \
  --tasks c04ad13cf0f94ce78d1666bb316eec39

c04ad13cf0f94ce78d1666bb316eec39




Qs:
- In container definition under task definition, I see "Port name": weaviate-8080-tcp, "Host Port:Container Port": weaviate-8080-tcp and protocol tcp
- When I do getent hosts weaviate.myapp.local, I get 172.31.24.88    weaviate.myapp.local. But I get error after : python3 -c "import requests; r = requests.get('http://weaviate.myapp.local:8080/v1'); print(r.status_code)"
- When defining the inbound rules, how should I define security group of my rag as the source? Should I use private IP?

docker system prune -a