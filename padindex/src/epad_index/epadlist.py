
import logging
import urllib.request, urllib.parse, urllib.error
import requests
from datetime import datetime
from . import doclist

class PadList(doclist.DocList):
  def __init__(self, host="https://epad.dataone.org/pad/api/1.2.1/",
               apikey=None,
               db_name='etherpad',
               db_user='etherpad',
               db_password=None,
               tagger=None):
    super().__init__(tagger=tagger)
    self._indexer_id_prefix = "EP:"
    self.params['apikey'] = apikey
    self.url = host
    self.pad_base_url = "https://epad.dataone.org/pad/p/"
    self.db_name = db_name
    self.db_user = db_user
    self.db_password = db_password


  def getDocumentIDs(self):
    res = requests.get(self.url + "listAllPads", params=self.params).json()
    return res['data']['padIDs']


  def padUrl(self, pad_id):
    url = self.pad_base_url + urllib.parse.quote(pad_id, '')
    return url


  def getAuthorName(self, author_id):
    if author_id in self.authors:
      return self.authors[author_id]
    params = self.params
    params['authorID'] = author_id
    res = requests.get(self.url + 'getAuthorName', params=params).json()
    author = res['data']
    self.authors[author_id] = author
    return author


  def padAuthors(self, pad_id):
    params = self.params
    params['padID'] = pad_id
    res = requests.get(self.url + 'listAuthorsOfPad', params=params).json()
    anames = []
    for author in res['data']['authorIDs']:
      aname = self.getAuthorName(author)
      if not aname is None:
        anames.append(aname)
    return anames


  def padLastEdited(self, pad_id):
    '''Returns a python datetime object indicating the last time the pad was
    edited
    '''
    params = self.params
    params['padID'] = pad_id
    res = requests.get(self.url + 'getLastEdited', params=params).json()
    tmod = datetime.fromtimestamp(res['data']['lastEdited'] / 1000.0)
    return tmod


  def padCreated(self, padId):
    '''
    Date created can be retrieved from the database by getting revision 0 of the PADID

      select store.value from store where store.key='pad:PADID:revs:0';

    Returns a json object with a field "timestamp" which is the timestamp of revision 0 of the pad.

    :param padId:
    :return:
    '''
    return None


  def padText(self, padId):
    params = self.params
    params['padID'] = padId
    res = requests.get(self.url + 'getText', params=params).json()
    return res['data']['text']


  def getPadInfo(self, padId):
    res = {}
    res['text'] = self.padText(padId)
    res['lastEdited'] = self.padLastEdited(padId)
    res['authors'] = self.padAuthors(padId)
    return res


  def getIndexEntry(self, pad_id):
    '''
    Returns an index entry dict

    Dict of:
      {'identifier': '',       #unique id for document
       'title': '',            #title of document
       'contributor': [],      #list of authors of document
       'creator': '',          #the creator, usually the first author
       'description': '',      #description, using the first 500 chars of document
       'date_created': None,   #datetime that document was created
       'date_modified': None,  #datetime the document was modified
       'date_index_updated': datetime.utcnow(),
       'format': 'text/plain',
       'source': '',           #URL of source document, the pad URL
       'body': '',             #Text of the document
       'publisher': '',        #
       'keywords': []
      }

    :param padId:
    :return:
    '''
    res = {}
    authors = self.padAuthors(pad_id)
    ptext = self.padText(pad_id)
    pad_url = self.padUrl(pad_id)
    d_created = self.padCreated(pad_id)
    d_modified = self.padLastEdited(pad_id)
    tnow = datetime.utcnow()
    res['identifier'] = self.getIndexedId(pad_id)
    res['title'] = pad_id
    res['contributor'] = authors
    if len(authors) > 0:
      res['creator'] = authors[0]
    else:
      res['creator'] = 'anonymous'
    res['description'] = ptext[:500]
    res['date_created'] = d_created
    res['date_modified'] = d_modified
    res['date_index_updated'] = tnow
    res['format'] = 'text/plain'
    res['source'] = pad_url
    res['body'] = ptext
    res['publisher'] = 'epad'
    if self.tagger is not None:
      key_words = self.tagger(ptext, self.max_key_words)
      kwl = []
      for kw in key_words:
        kwl.append(kw.string)
      res['keywords'] = kwl
    return res


if __name__ == "__main__":
  k = "api key"
  PL = PadList(apikey=k)
  pads = PL.getDocumentIDs()
  for pad in pads:
    print((str(pad)))
    # print PL.getPadInfo(pad)
    # authors = PL.padAuthors(pad)
    # for author in authors:
    #  print PL.getAuthorName(author)
