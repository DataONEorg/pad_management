from flask import render_template, request
from app import app
from elasticsearch_dsl import Search, Q
from datetime import datetime
import bleach
import json

LOGOS = {'epad':{'img':'<span title="Etherpad" class="logo_etherpad">EP</span>',
                     'short':'EP',
                     'descr':'Etherpad documents'},
         'hpad':{'img':'<span title="Hackpad" class="logo_hackpad">HP</span>',
                   'short':'HP',
                   'descr':'Hackpad documents',
                   },
         'archive_epad':{'img':'<span title="Archived Etherpad" class="logo_etherpad_archive">EA</span>',
                             'short':'EA',
                             'descr':'Archived etherpad documents',
                             },
         }

DEFAULT_ORDER = {'_score':{'order':'desc'}}


def sourceShortToName(short):
  '''returns the index key for a source entry in the LOGOS dictionary
  '''
  short = short.upper().strip()
  for entry in LOGOS.keys():
    if LOGOS[entry]['short'] == short:
      return entry
  return None


@app.template_filter('formatDateStr')
def formatDateStr_filter(ds, dformat='%Y-%m-%d'):
  if ds is None:
    return ''
  if ds == '':
    return ''
  dstr = ds.split('.')[0]
  dt = datetime.strptime(dstr, '%Y-%m-%dT%H:%M:%S')
  return dt.strftime(dformat)


@app.template_filter('logoify')
def publisherLogo_filter(pub):
  if pub is None:
    return ''
  if pub == '':
    return ''
  try:
    return LOGOS[pub.lower()]['img']
  except:
    pass
  return pub


@app.template_filter('unique')
def unique_filter(alist):
  used = set()
  unique = [x for x in alist if x.lower() not in used and (used.add(x.lower()) or True)]
  return unique


@app.template_filter('sanitize')
def sanitize_filter(txt):
  return bleach.clean(txt.strip(), tags=['em'])


@app.template_filter('score')
def score_filter(v, maxv):
  n = int(5*(v/maxv))
  return "*" * n


@app.template_filter('source_selection')
def source_listing_filter(selection):
  pass


@app.route('/exists')
def padExists():
  '''
  Does specified name refer to existing etherpad, archive, or hackpad?

  Check the index for ID
  :return:
  '''
  pass


def makeOrder(qo, is_empty_query=False):
  if qo is None:
    qo = ''
  qo = qo.lower()
  qparts = qo.split(':')
  qf = qparts[0]
  if qf not in ['_score', 'date_modified', 'publisher', 'lines']:
    if is_empty_query:
      qf = 'date_modified'
    else:
      qf = '_score'
  try:
    ad = qparts[1]
    if ad not in ['a', 'd', 'asc', 'desc']:
      raise ValueError()
    if ad == 'a':
      ad = 'asc'
    elif ad == 'd':
      ad = 'desc'
  except:
    ad = 'desc'
  order = {qf:{'order':ad}}
  return order


@app.route('/')
@app.route('/index')
def index():
  #The query string for selecting documents
  qbody = request.args.get('qb', '')
  if qbody is None:
    qbody = ''
  #Field to order on
  qordering = request.args.get('o', '')
  qorder = makeOrder(qordering, is_empty_query=(len(qbody)==0))
  #qsource_tags = request.args.get('p','EP').split(',')
  #The types of source to show
  qsource_tags = request.args.getlist('p')
  qsources=[]
  for tag in qsource_tags:
    name = sourceShortToName(tag)
    if not name is None:
      qsources.append(name)
  if len(qsources) == 0:
    qsources.append('epad')
  show_help = False
  if qbody == 'help':
    show_help = True
  s = Search(using=app.es_client, index=app.config['DOC_INDEX'])\
      .source(include=['publisher', 'id', 'title', 'date_modified', 'lines', 'source', 'contributor'])
  if len(qsources) > 0:
    s = s.filter('terms', publisher=qsources)

  if len(qbody) > 1:
    s = s.query({'simple_query_string': {'query': qbody,
                                         'fields':['body^5', '_all'],
                                         'default_operator': 'and'}})
    s = s.highlight('body', fragment_size=200)
  s = s.sort(qorder)

  print(json.dumps(s.to_dict(), indent=2))
  response = s.execute()
  nhits = response.hits.total
  max_score = response.hits.max_score
  epad_selected = "epad" in qsources
  hpad_selected = "hpad" in qsources
  arch_selected = "archive_epad" in qsources
  return render_template('index.html',
                         nhits=nhits,
                         max_score=max_score,
                         rows=s[0:nhits],
                         qbody=qbody,
                         show_help=show_help,
                         epad_selected=epad_selected,
                         hpad_selected=hpad_selected,
                         arch_selected=arch_selected)
