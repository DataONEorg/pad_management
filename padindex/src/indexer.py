'''
Python script that lists all:

* archived etherpads
* current etherpads
* hackmd pads

and adds the entries to the elasticsearch instance.
'''

import os
import sys
import logging
from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text
from elasticsearch_dsl.connections import connections
import nltk
import pickle
import urllib.request, urllib.parse, urllib.error
import requests
from datetime import datetime
import argparse
import yaml
from sshtunnel import SSHTunnelForwarder

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from txtutil import tagger
from epad_index import epadlist
from epad_index import archivelist
from epad_index import hpadlist


INDEX = 'notes.a'

EMPTY_CONTENT='''Welcome to Etherpad!

This pad text is synchronized as you type, so that everyone viewing this page sees the same text. This allows you to collaborate seamlessly on documents!

Get involved with Etherpad at http://etherpad.org'''

# These terms are fairly common across indexed documents and so aren't much
# help for discovery purposes. Any values listed here are ignored when 
# constructing the list of keywords for the indexed content with the tagger.
IGNORED_TAGS = ['dataone','http','https']


class Note(DocType):
  contributor = Keyword()
  creator = Keyword()
  date_modified = Date()
  date_index_updated = Date()
  description = Text()
  format = Keyword()
  identifier = Keyword()
  publisher = Keyword()
  source = Text()
  title = Keyword()
  keywords = Keyword()
  body = Text()
  lines = Integer()

  class Meta:
    index = INDEX

  def save(self, **kwargs):
    self.lines = len(self.body.split())
    return super(Note, self).save( **kwargs )


def getTagger(weightings='data/dict.pkl'):
  '''Return a tagger for auto generated tags / keywords
  '''
  stop_words = set(nltk.corpus.stopwords.words("english"))
  stop_words.update(IGNORED_TAGS)
  weights = pickle.load(open(weightings, 'rb'))
  doc_reader = tagger.Reader( stop_words=stop_words )
  doc_stemmer = tagger.Stemmer( nltk.SnowballStemmer("english") )
  doc_rater = tagger.Rater(weights)
  return tagger.Tagger(doc_reader, doc_stemmer, doc_rater)


def getPadLastIndexDate(indexed_id, indexer_url="http://localhost:9200/" + INDEX + "/note/"):
  url = "{0}{1}?_source_include=date_index_updated".format(indexer_url, urllib.parse.quote(indexed_id))
  logging.debug(url)
  res = requests.get(url).json()
  if res['found']:
    dstr = res['_source']['date_index_updated'].split('.')[0]
    return datetime.strptime(dstr, '%Y-%m-%dT%H:%M:%S')
  return datetime.strptime("1970-01-01T00:00:01", '%Y-%m-%dT%H:%M:%S')


def doIndexPads(pad_list,
                indexer_url="http://localhost:9200/" + INDEX + "/note/",
                reindex_all=False,
                ):
  Note.init()
  for pad in pad_list.getDocumentIDs():
    logging.info("Pad: %s", pad)
    dt_indexed = getPadLastIndexDate(pad_list.getIndexedId(pad), indexer_url=indexer_url)
    dt_modified = pad_list.padLastEdited(pad)
    if (dt_modified > dt_indexed) or reindex_all:
      pad_data = pad_list.getIndexEntry(pad)
      if len(pad_data['body']) > len(EMPTY_CONTENT)+10:
        logging.info("Indexing: %s", pad)
        epad_doc = Note(**pad_data)
        epad_doc.meta.id = pad_data['identifier']
        epad_doc.save()
      else:
        logging.info("Ignoring: %s", pad)



def indexHPads(indexer_url="http://localhost:9200/" + INDEX + "/note/",
               reindex_all=False,
               doc_tagger=None,
               delete_existing=False):
  Note.init()
  pad_list = hpadlist.HPadList(password="penchant-piddling-cod-sober-ablution", tagger=doc_tagger)
  doIndexPads(pad_list, indexer_url=indexer_url, reindex_all=reindex_all)



def indexEtherpads(api_key=None,
                   indexer_url="http://localhost:9200/" + INDEX + "/note/",
                   reindex_all=False,
                   doc_tagger = None,
                   delete_existing=False):
  Note.init()
  pad_list = epadlist.PadList(apikey=api_key,
                              tagger = doc_tagger)
  doIndexPads(pad_list, indexer_url=indexer_url, reindex_all=reindex_all)


def indexArchivedEtherpads(doc_tagger = None, 
                           delete_existing = False):
  Note.init()
  #archive_url = "/Users/vieglais/Projects/DataONE_61385/svn/documents/Projects/epads"
  #a_list = epad_index.ArchiveList(archive_url = archive_url, fakes=True)
  a_list = archivelist.ArchiveList(tagger=doc_tagger)
  for pad in a_list.pads():
    logging.info(pad)
    entry = a_list.getEntry( pad )
    if len(entry['body']) > len(EMPTY_CONTENT) + 10:
      adoc = Note(**entry)
      adoc.meta.id = entry['identifier']
      adoc.save()
    else:
      logging.info("Ignoring: %s", pad)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-l', '--log_level',
                      action='count',
                      default=0,
                      help='Set logging level, multiples for more detailed.')
  parser.add_argument('--config',
                      default=os.path.expanduser("~/.dataone/epads/epadindex.yaml"),
                      help="Path to configuration file")
  args = parser.parse_args()
  # Setup logging verbosity
  levels = [logging.WARNING, logging.INFO, logging.DEBUG]
  level = levels[min(len(levels) - 1, args.log_level)]
  logging.basicConfig(level=level,
                      format="%(asctime)s %(levelname)s %(message)s")
  config = {}
  with open(args.config, "r") as config_data:
    config = yaml.safe_load(config_data)
  epad_api_key = config["etherpad"]["key"]
  index_name = config["index"]["index"]
  logging.info("Creating tunnel to %s:%s", config["index"]["host"], str(config["index"]["port"]))
  with SSHTunnelForwarder(
      config["index"]["host"],
      remote_bind_addresses=[("127.0.0.1", config["index"]["port"]),("127.0.0.1", 5432),],
      ssh_private_key_password=config["index"]["key"],
      local_bind_addresses=[("127.0.0.1", config["index"]["port"]),("127.0.0.1", 5432),],
    ) as tunnel:
    logging.info("Local bind port = %s", str(tunnel.local_bind_ports))
    logging.info("Creating connection to index...")
    connections.create_connection(hosts=['localhost'])
    logging.info("Creating document tagger...")
    doc_tagger = getTagger()
    logging.info("Indexing etherpads...")
    indexEtherpads(api_key = epad_api_key,
                   indexer_url="http://localhost:9200/" + index_name + "/note/",
                   reindex_all=False,
                   doc_tagger=doc_tagger)
    indexHPads(indexer_url="http://localhost:9200/" + index_name + "/note/",
                   reindex_all=False,
                   doc_tagger=doc_tagger)

  #indexArchivedEtherpads(doc_tagger=doc_tagger)
  #indexHPads(indexer_url="http://localhost:9200/" + INDEX + "/note/",
  #           reindex_all=False,
  #           doc_tagger=doc_tagger)
