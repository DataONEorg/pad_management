# Indexing Etherpad Documents

This tool runs on the etherpad server and populates an
[elasticsearch](https://www.elastic.co/products/elasticsearch) index
with pad contents and associated metadata.

Index entries are structured like:


| Field               | Description |
----------------------|------------------------|
| contributor         | Name(s) of contributors to the document (if available) |
| creator             | Name(s) of document creator (if available) |
| date_created        | DateTime that the document was created |
| date_modified       | DateTime that the document was last modified |
| date_index_updated  | DateTime that the index entry was last updated |
| description         | Description if provided otherwise slug of first 100 words of text |
| format              | html, text, markdown |
| identifier          | url |
| publisher           | Origin of content: epad, hackpad, archive |
| source              | url |
| title               | Document title if available |
| keywords            | keywords if available |
| body                | Document text |


