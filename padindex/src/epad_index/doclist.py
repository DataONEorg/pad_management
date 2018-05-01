'''
Created on Sep 17, 2014

@author: vieglais
'''

import logging
from datetime import datetime


class DocList(object):

  def __init__(self, tagger=None):
    self.L = logging.getLogger(self.__class__.__name__)
    self.params = {}
    self.authors = {}
    self.max_key_words = 10
    self._indexer_id_prefix = ''
    self.tagger = tagger

  def getDocumentIDs(self):
    '''
    Returns a list of identifiers that can be used to retrieve details
    about individual pads.

    Override this method in derived classes.

    :return: []
    '''
    return []


  def getIndexedId(self, pad_id):
    '''
    Returns the identifier of the pad in the indexer. e.g.:

      "EP:" + pad_id

    :param pad_id:
    :return:
    '''
    return self._indexer_id_prefix + pad_id


  def padLastEdited(self, pad_id):
    return None


  def getIndexEntry(self, pad_id):
    entry = {'identifier': pad_id,    #unique id for document
       'title': '',                   #title of document
       'contributor': [],             #list of authors of document
       'creator': '',                 #the creator, usually the first author
       'description': '',             #description, using the first 500 chars of document
       'date_created': None,          #datetime that document was created
       'date_modified': None,         #datetime the document was modified
       'date_index_updated': datetime.utcnow(),
       'format': 'text/plain',
       'source': '',                  #URL of source document, the pad URL
       'body': '',                    #Text of the document
       'publisher': '',               #
       'keywords': [],
        }

    return entry


  def getDocumentMetadata(self, pad_id):
    meta = {'id': pad_id,
            'date_created':'',
            'date_modified':'',
            'authors':[],
            'title':'',
            'publisher':'',
            'url':''
            }
    return meta


  def getDocumentContent(self, id):
    return ""





