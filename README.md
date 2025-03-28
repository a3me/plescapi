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