build-Widget6Function:
	pip install -r requirements.txt -t $(ARTIFACTS_DIR)/ --upgrade
	cp app.py $(ARTIFACTS_DIR)/
	cp run.sh $(ARTIFACTS_DIR)/
	cp requirements.txt $(ARTIFACTS_DIR)/
