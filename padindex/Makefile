.PHONY=help
help::
	@echo "Install virtualenv and dependencies first (see README)"
	@echo ""
	@echo "Then run:"
	@echo "make index #(re)create Elasticsearch index"
	@echo "make backend #Run backend service on http://localhost:5000"
	@echo "make frontend #Run frontend service on http://localhost:8000"
	@echo
	@echo "After performing the above, point your browser to http://localhost:8000"

.PHONY=frontend
frontend::
	(cd frontend && python -m http.server)

.PHONY=backend
backend::
	python runbackend.py

.PHONY=index
index::
	#curl -X DELETE http://localhost:9200/notes; echo;
	#curl -X PUT http://localhost:9200/pads -d @mapping.json; echo
