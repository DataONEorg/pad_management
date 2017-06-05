'''
Listing of the archived pads

https://epad.dataone.org/archive/content/?F=2&P=*.txt
'''
import os
import logging
import requests
from lxml import etree
from datetime import datetime
import time
import codecs

FAKE_TAGS = ['python','lemur','cantelope','wasabi']

class ArchiveList(object):
  '''
  
  '''
  def __init__(self, archive_url="https://epad.dataone.org/archive/content/", fakes=False):
    self._L = logging.getLogger(self.__class__.__name__)
    self.archive_url = archive_url
    self.pad_info = []
    self.fakes = fakes
    self.loadDocuments()


  def getIdentifier(self, docid):
    return "EA:" + docid


  def loadDocumentsFS(self):
    '''
0	tm_year	(for example, 1993)
1	tm_mon	range [1, 12]
2	tm_mday	range [1, 31]
3	tm_hour	range [0, 23]
4	tm_min	range [0, 59]
5	tm_sec	range [0, 61]; see (2) in strftime() description
6	tm_wday	range [0, 6], Monday is 0
7	tm_yday	range [1, 366]
8	tm_isdst	0, 1 or -1; see below    

datetime(year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]])
    :return: 
    '''
    self.pad_info = []
    tnow = datetime.utcnow()
    src_dirs = [self.archive_url, ]
    extra_files = src_dirs[:]
    i = 0
    for extra_dir in src_dirs:
      for dirname, dirs, files in os.walk(extra_dir):
        for fname in files:
          filename = os.path.join(dirname, fname)
          if os.path.isfile(filename):
            if filename.lower().endswith(".txt"):
              url = "file://" + filename
              title = fname
              stats = os.stat(filename)
              dmod = time.gmtime(stats.st_ctime)
              date_modified = datetime(dmod[0], dmod[1], dmod[2], dmod[3], dmod[4], dmod[5])
              entry = {}
              entry['identifier'] = self.getIdentifier(title)
              entry['title'] = title
              entry['source'] = url
              if self.fakes:
                entry['publisher'] = FAKE_TAGS[i]
                i += 1
                if i >= len(FAKE_TAGS):
                  i = 0
              else:
                entry['publisher'] = 'archive_epad'
              entry['format'] = 'text/plain'
              entry['date_modified'] = date_modified
              entry['date_index_updated'] = tnow
              self.pad_info.append(entry)
              self._L.debug('%s', str(entry))


  def loadDocumentsHTTP(self):
    self.pad_info = []
    doc = requests.get(self.archive_url + "?F=2&P=*.txt")
    tree = etree.HTML(doc.text)
    rows = tree.xpath("//table[1]/tr")[3:]
    tnow = datetime.utcnow()
    for row in rows:
      if len(row.xpath("td")) > 3:
        url = self.archive_url + row.xpath("td[2]/a/@href")[0].strip()
        title = row.xpath("td[2]/a")[0].text.strip()
        date_modified = row.xpath("td[3]")[0].text.strip()

        entry = {}
        entry['identifier'] = self.getIdentifier(title)
        entry['title'] = title
        entry['source'] = url
        entry['publisher'] = 'archive_epad'
        entry['format'] = 'text/plain'
        entry['date_modified'] = datetime.strptime(date_modified,'%Y-%m-%d %H:%M')
        entry['date_index_updated'] = tnow
        self.pad_info.append(entry)


  def loadDocuments(self):
    if self.archive_url.lower().startswith('http'):
      self.loadDocumentsHTTP()
    else:
      self.loadDocumentsFS()


  def getEntry(self, docid):
    e = {}
    for r in self.pad_info:
      if docid == r['identifier']:
        e = r
        break
    doc = ''
    if self.archive_url.lower().startswith('http'):
      doc = requests.get(e['source']).text
    else:
      fname = os.path.join(self.archive_url, e['title'])
      doc = codecs.open(fname, 'r', encoding='utf-8').read()
    e['body'] = doc
    e['description'] = doc[:500]
    return e


  def pads(self):
    res = []
    for r in self.pad_info:
      res.append(r['identifier'])
    return res


if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  archive_url = "/Users/vieglais/Projects/DataONE_61385/svn/documents/Projects/epads"
  archive = ArchiveList(archive_url = archive_url, fakes=True)
  for pad in archive.pads():
    print archive.getEntry(pad)['publisher']


