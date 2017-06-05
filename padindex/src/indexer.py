'''
Python script that lists all:

* archived etherpads
* current etherpads
* hackmd pads

and adds the entries to the elasticsearch instance.


'''

import logging
import epad_index
from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text
from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=['localhost'])

INDEX = 'notes.a'

EMPTY_CONTENT='''Welcome to Etherpad!

This pad text is synchronized as you type, so that everyone viewing this page sees the same text. This allows you to collaborate seamlessly on documents!

Get involved with Etherpad at http://etherpad.org'''

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


def indexEtherpads(api_key=None,
                   indexer_url="http://localhost:9200/" + INDEX + "/note/",
                   reindex_all=False):
  Note.init()
  pad_list = epad_index.PadList(apikey=api_key, indexer_url=indexer_url)
  for pad in pad_list.pads():
    logging.info("Pad: %s", pad)
    dt_indexed = pad_list.getPadLastIndexDate(pad)
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


def indexArchivedEtherpads():
  Note.init()
  #archive_url = "/Users/vieglais/Projects/DataONE_61385/svn/documents/Projects/epads"
  #a_list = epad_index.ArchiveList(archive_url = archive_url, fakes=True)
  a_list = epad_index.ArchiveList()
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
  logging.basicConfig(level=logging.INFO)
  api_key = 'dd907d7179952f3d811e04c593ac83b4e6a3d7a897edd0fb703d72bfa2b8fbe0'
  #indexArchivedEtherpads()
  indexEtherpads(api_key = api_key,
                 indexer_url="http://localhost:9200/" + INDEX + "/note/",
                 reindex_all=True)
