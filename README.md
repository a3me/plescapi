# plescapi

pleść api 

## requirements

python 3.13.2
docker 

## installation

python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

## build and run

docker build -t plescapi .
docker run -p 8000:8000 plescapi

## update requirements
pip freeze > requirements.txt

## deploy 

gcloud auth configure-docker
docker tag plescapi gcr.io/YOUR_PROJECT_ID/plescapi
docker push gcr.io/YOUR_PROJECT_ID/plescapi
gcloud container clusters create plesc-cluster --num-nodes=2
kubectl create deployment plescapi --image=gcr.io/YOUR_PROJECT_ID/plescapi
kubectl expose deployment plescapi --type=LoadBalancer --port=80 --target-port=8000