'''
Gathering content from HackPads for indexing

Getting a list of HPad documents requires contacting the PSQL
database. Connection info is at:

  /usr/local/etherpad/hackmd/config.json

The query

  select id,shortid,alias,title, from "Notes";

User names can be found in the Users table, in the profile field which contains a json structure.



hackpad=> \dt
             List of relations
 Schema |   Name    | Type  |     Owner
--------+-----------+-------+---------------
 public | Authors   | table | hackpad_owner
 public | Notes     | table | hackpad_owner
 public | Revisions | table | hackpad_owner
 public | Sessions  | table | hackpad_owner
 public | Temps     | table | hackpad_owner
 public | Users     | table | hackpad_owner
(6 rows)

hackpad=> \d "Notes"
                       Table "public.Notes"
      Column      |           Type           |     Modifiers
------------------+--------------------------+--------------------
 id               | uuid                     | not null
 shortid          | character varying(255)   | not null
 alias            | character varying(255)   |
 permission       | "enum_Notes_permission"  |
 viewcount        | integer                  | not null default 0
 title            | text                     |
 content          | text                     |
 authorship       | text                     |
 lastchangeAt     | timestamp with time zone |
 savedAt          | timestamp with time zone |
 createdAt        | timestamp with time zone | not null
 updatedAt        | timestamp with time zone | not null
 deletedAt        | timestamp with time zone |
 ownerId          | uuid                     |
 lastchangeuserId | uuid                     |
Indexes:
    "Notes_pkey" PRIMARY KEY, btree (id)
    "Notes_alias_key" UNIQUE CONSTRAINT, btree (alias)
    "Notes_shortid_key" UNIQUE CONSTRAINT, btree (shortid)

                Table "public.Users"
    Column    |           Type           | Modifiers
--------------+--------------------------+-----------
 id           | uuid                     | not null
 profileid    | character varying(255)   |
 profile      | text                     |
 history      | text                     |
 accessToken  | character varying(255)   |
 refreshToken | character varying(255)   |
 email        | text                     |
 password     | text                     |
 createdAt    | timestamp with time zone | not null
 updatedAt    | timestamp with time zone | not null
Indexes:
    "Users_pkey" PRIMARY KEY, btree (id)
    "Users_profileid_key" UNIQUE CONSTRAINT, btree (profileid)


select authorship from "Notes" limit 10;

                                  authorship
-------------------------------------------------------------------------------


 []



 [["d59f55fe-b527-4396-aa1a-dbdc314cd8da",0,5141,1506515540895,1506515540895]]
 []


select profile from "Users" where id='d59f55fe-b527-4396-aa1a-dbdc314cd8da';

 {"id":"605409","displayName":"Dave Vieglais","username":"datadavev", ...


The request:

  https://hpad.dataone.org/shortid/download

will redirect to a URL which provides access to the markdown content of the note.


'''

import logging
import urllib
import requests
from datetime import datetime
import psycopg2
from . import doclist
import json
import pprint

class HPadList(doclist.DocList):
  def __init__(self,
               tagger=None,
               dbname="hackpad",
               user="hackpad_owner",
               host="localhost",
               password=""):
    super().__init__(tagger=tagger)
    self._indexer_id_prefix = "HP:"
    cnstr = "dbname='{}' user='{}' host='{}' password='{}'".format(dbname, user, host, password)
    self.conn = psycopg2.connect(cnstr)

  def getDocumentIDs(self):
    '''
    Get a list of document IDs that can be used for accessing documents.

    SELECT shortid FROM "Notes";
    :return: array of IDs
    '''
    res = []
    csr = self.conn.cursor()
    sql = "SELECT shortid FROM \"Notes\";"
    csr.execute(sql)
    rows = csr.fetchall()
    for row in rows:
      res.append(row[0])
    return res


  def getUserInfo(self, csr, user_id):
    sql = "SELECT profile FROM \"Users\" WHERE id=%s;"
    csr.execute(sql, (user_id, ))
    row = csr.fetchone()
    entry = json.loads(row[0])
    res = entry["displayName"]
    if res is None:
      #logging.debug(pprint.pformat(entry, indent=2))
      res = entry["username"]
    return res


  def padAuthors(self, pad_id):
    csr = self.conn.cursor()
    sql = "SELECT \"ownerId\", \"authorship\" FROM \"Notes\" WHERE shortid=%s;"
    csr.execute(sql, (pad_id, ))
    rows = csr.fetchall()
    authors = []
    for row in rows:
      if row[0] is not None:
        authors.append(row[0])
        if row[1] is not None:
          entries = json.loads(row[1])
          for entry in entries:
            if entry[0] not in authors:
              authors.append(entry[0])
    names = []
    for author in authors:
      names.append(self.getUserInfo(csr, author))
    return names


  def padText(self, pad_id):
    url = 'https://hpad.dataone.org/{}/download'.format(pad_id)
    res = requests.get(url).text
    return res


  def padUrl(self, pad_id):
    return 'https://hpad.dataone.org/{}'.format(pad_id)


  def padCreated(self, pad_id):
    csr = self.conn.cursor()
    sql = "SELECT \"createdAt\" FROM \"Notes\" WHERE shortid=%s;"
    csr.execute(sql, (pad_id, ))
    row = csr.fetchone()
    c = row[0]
    cdate = datetime(c.year, c.month, c.day, c.hour, c.minute, c.second)
    return cdate


  def padLastEdited(self, pad_id):
    csr = self.conn.cursor()
    sql = "SELECT \"updatedAt\" FROM \"Notes\" WHERE shortid=%s;"
    csr.execute(sql, (pad_id, ))
    row = csr.fetchone()
    c = row[0]
    cdate = datetime(c.year, c.month, c.day, c.hour, c.minute, c.second)
    return cdate


  def padTitle(self, pad_id):
    csr = self.conn.cursor()
    sql = "SELECT \"title\" FROM \"Notes\" WHERE shortid=%s;"
    csr.execute(sql, (pad_id, ))
    row = csr.fetchone()
    return row[0]


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
    res['title'] = self.padTitle(pad_id)
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
    res['publisher'] = 'hpad'
    if self.tagger is not None:
      key_words = self.tagger(ptext, self.max_key_words)
      kwl = []
      for kw in key_words:
        kwl.append(kw.string)
      res['keywords'] = kwl
    return res




if __name__ == '__main__':
  lister = HPadList(password="penchant-piddling-cod-sober-ablution")
  ids = lister.getDocumentIDs()
  for id in ids:
    print(id)