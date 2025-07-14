# Deployment guide
## Summary

Implementation of Retrieval-Augmented Generation with:
- Weaviate DB as a knowledge base with sentence-transformer embeddings
- OpenAI gpt-4 LLM for response generation
- API supporting filtering based on metadata - topics
- deletion based on chunk ID as well as file name, e.g. "file.pdf"
- draft logic for feeding a list of topics (via weaviate_data/topics_list.txt), extending the list of topics by topics defined by users and assigning those topics to newly ingested documents automatically, i.e. tagging the documents.
- Logging and metrics collection with Prometheus

### API is here:
- http://ragaws-ragal-ckh1lbsks6ez-1296194638.eu-central-1.elb.amazonaws.com/docs#/
- API documentation - http://ragaws-ragal-ckh1lbsks6ez-1296194638.eu-central-1.elb.amazonaws.com/redoc

## High-level solution architecture

![alt text](https://github.com/MartinTomis/rag-aws/blob/main/architecture.jpg)

## Code structure
<pre> 

src
├── api
│   ├── __init__.py
│   ├── documents.py                # GET/documents and GET/documents/{id}
│   ├── ingest.py                   # POST/ingest
│   ├── models.py                   # pydantic models
│   ├── query.py                    # POST/query
│   └── routes.py
├── main.py                         # FastAPI initialization and endpoints
├── processing                      
│   ├── chunking.py                 # Chunking helper functions
│   ├── embedding.py                # Embeds text for vector DB
│   ├── file_parsing.py             # Converts PDF, TXT and JSON into text
│   ├── nltk_data
│   │   └── tokenizers
│   │       └── punkt
│   │           ├── PY3
│   │           │   └── english.pickle
│   │           ├── README
│   │           └── english.pickle
│   └── rag.py                      # RAG-logic 
└── storage
    └── vector_db.py                # Initialization and CRUD


 </pre>


## Deployment with CDK
In your projects:
```
git clone https://github.com/MartinTomis/rag-aws.git

cd rag-aws
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

In rag-aws/deployment/cdk/app.py, modify AWS account and region.

Then

```
cd deployment/cdk/
cdk synth
```
If everything goes smoothly, then:

```
cdk deploy
```

Then open via browser - it is the DNS of the application load balancer:
http://<rag-alb-dns-name>/docs



### Trouble Shooting
```
cdk bootstrap aws://<ACCOUNT>/<REGION>
```

If the issues persist, try
```
rm -rf cdk.out 
```
and delete CDKToolkit from cloud formation and a corresponsing S3 bucket (starting with "cdk").

If something fails, ensure that the CloudFormation stack is deleted from console and also run 
```
cdk destroy RagAwsStack
```

If everything fails, you can run manually

