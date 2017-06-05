'''
Created on Sep 17, 2014

@author: vieglais
'''

import logging
import urllib
import requests
from datetime import datetime

class PadList(object):
  def __init__(self, host="https://epad.dataone.org/pad/api/1.2.1/",
               apikey=None,
               indexer_url="http://localhost:9200/notes/note/",
               db_name='etherpad',
               db_user='etherpad',
               db_password=None):
    self.log = logging.getLogger(self.__class__.__name__)
    self.params = {'apikey': apikey}
    self.url = host
    self.pad_base_url = "https://epad.dataone.org/pad/p/"
    self.indexer_url=indexer_url
    self.db_name=db_name
    self.db_user=db_user
    self.db_password=db_password
    self.authors = {}


  def pads(self):
    res = requests.get(self.url + "listAllPads", params=self.params).json()
    return res['data']['padIDs']


  def padUrl(self, padId):
    url = self.pad_base_url + urllib.quote(padId,'')
    return url


  def getPadIdentifier(self, padId):
    return "EP:"+padId


  def getPadLastIndexDate(self, padId):
    doc_id = self.getPadIdentifier(padId)
    url = "{0}{1}?_source_include=date_index_updated".format(self.indexer_url, urllib.quote(doc_id))
    logging.debug(url)
    res = requests.get(url).json()
    if res['found']:
      dstr = res['_source']['date_index_updated'].split('.')[0]
      return datetime.strptime(dstr, '%Y-%m-%dT%H:%M:%S')
    return datetime.strptime("1970-01-01T00:00:01", '%Y-%m-%dT%H:%M:%S')


  def getAuthorName(self, authorId):
    if self.authors.has_key(authorId):
      return self.authors[authorId]
    params = self.params
    params['authorID'] = authorId
    res = requests.get(self.url + 'getAuthorName', params=params).json()
    author = res['data']
    self.authors[authorId] = author
    return author


  def padAuthors(self, padId):
    params = self.params
    params['padID'] = padId
    res = requests.get(self.url + 'listAuthorsOfPad', params=params).json()
    anames = []
    for author in res['data']['authorIDs']:
      aname = self.getAuthorName(author)
      if not aname is None:
        anames.append(aname)
    return anames


  def padLastEdited(self, padId):
    '''Returns a python datetime object indicating the last time the pad was 
    edited
    '''
    params = self.params
    params['padID'] = padId
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


  def getIndexEntry(self, padId):
    '''
    Returns an index entry dict 
    :param padId: 
    :return: 
    '''
    res = {}
    authors = self.padAuthors(padId)
    ptext = self.padText(padId)
    pad_url = self.padUrl(padId)
    d_created = self.padCreated(padId)
    d_modified = self.padLastEdited(padId)
    tnow = datetime.utcnow()
    res['identifier'] = self.getPadIdentifier(padId)
    res['title'] = padId
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
    res['title'] = padId
    res['body'] = ptext
    res['publisher'] = 'epad'
    return res



if __name__ == "__main__":
  k = "api key"
  PL = PadList(apikey=k)
  pads = PL.pads()
  for pad in pads:
    print pad
    #print PL.getPadInfo(pad)
    # authors = PL.padAuthors(pad)
    # for author in authors:
    #  print PL.getAuthorName(author)


