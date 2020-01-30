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

layer:
	rm -rf $(CUR_DIR)/$(LAYER_DIR) -v !('requirements.txt')
	find $(CUR_DIR)/$(LAYER_DIR) -type f -not -name 'requirements.txt'-delete
	mkdir -p $(LAYER_DIR)
	docker run --rm -v $(CUR_DIR):/foo -w /foo lambci/lambda:build-python3.7 \
		pwd && ls -als && pip install -r $(LAYER_DIR)/requirements.txt --no-deps -t $(LAYER_DIR) && ls -als $(LAYER_DIR)

express-deploy:
	cdk deploy "*"