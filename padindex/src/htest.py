import logging
from epad_index import hpadlist
import pprint

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  lister = hpadlist.HPadList(password="put password here")
  ids = lister.getDocumentIDs()
  for id in ids:
    print(id)
    info = lister.getIndexEntry(id)
    if len(info["body"]) > 5:
      print(pprint.pformat(info, indent=2))
