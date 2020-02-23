CUR_DIR = $(CURDIR)
LAYER_DIR=aws_callouts_cdk/layer
AMAZON_CONNECT_INSTANCE_ARN=""
AMAZON_CONNECT_CONTACT_FLOW_ARN=""
AMAZON_CONNECT_PHONE_NUMBER=""

init:
	python3 -m venv .env
	. .env/bin/activate && \
	pip install -r requirements.txt

init-ps1:
	python -m venv .env
	.env/Scripts/Activate.ps1
	pip install -r requirements.txt

python-layer:
	docker run --rm -v $(CUR_DIR):/foo -w /foo lambci/lambda:build-python3.7 \
		pip install -r $(LAYER_DIR)/python/requirements.txt --no-deps -t $(LAYER_DIR)/python

nodejs-layer:
	cd $(LAYER_DIR)/nodejs && \
	npm install