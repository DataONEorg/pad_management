'''
Flask application implementing where.
'''

from flask import Flask
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.config.from_object('config')
app.es_client = Elasticsearch()

from app import views
