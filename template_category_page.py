#!/usr/bin/env python
import re
import sys
import requests
from jinja2 import Environment, PackageLoader, Template
import boto3
import StringIO

sourceTitle = sys.argv[1]

#get the rendered text from the given categories page using the
#render parameter of index.php

baseURL = u'http://192.168.1.14/wiki/index.php'
parameters = {'action':'render',
              'title':sourceTitle}

r = requests.get(baseURL,params=parameters)

articleText = r.text

#replace all the wikilinks for existing articles
#e.g. "http://192.168.1.14/wiki/index.php/Article" -> "Article.html"
extantLink = re.compile(r'http://192.168.1.14/wiki/index.php/([^"]+)')
newArticleText = extantLink.sub(r'/\1.html',articleText)

#get the page title and rendered categories
#using the MediaWiki api

sourceTitle = sys.argv[1]

baseURL = u'http://192.168.1.14/wiki/api.php'
parameters = {'action':'parse',
              'page':sourceTitle,
              'prop':'categorieshtml',
              'disablepp':'true',
              'disableeditsection':'true',
              'format':'json'}

r = requests.get(baseURL,params=parameters)

parsedPage = r.json()

#extract the information we want from the json dictionary
articleTitle = parsedPage[u'parse'][u'title']
if u'categorieshtml' in parsedPage[u'parse']:
    categories = parsedPage[u'parse'][u'categorieshtml'][u'*']
else:
    categories = u''

#replace all the wikilinks for the categories
catLink = re.compile(r'/wiki/index.php/([^"]+)')
cleanCategories = catLink.sub(r'/\1.html',categories)

#now take the newArticle text from the first section and the title and the
#cleaned Categories HTML for the second part and combine it into one page
#using Jinja2

env = Environment(loader=PackageLoader('template_page','templates'))

template = env.get_template('category_template.html')

finalPage = template.render(articleTitle = articleTitle,
                            articleText = newArticleText,
                            categories = cleanCategories)

#if a second parameter was passed at the command line, use this for the file name
#otherwise, build a file name by replacing spaces with underlines
if len(sys.argv) == 3:
    fileName = sys.argv[2] + u'.html'
else:
    fileName = sourceTitle.replace(' ','_') + u'.html'

outfile = StringIO.StringIO(finalPage.encode('utf-8'))

#write the file to S3
s3 = boto3.resource('s3')
s3.Bucket('www.fracturedfairfax.com').put_object(Key=fileName,
                                                 Body=outfile,
                                                 ContentType='text/html',
                                                 ACL='public-read')
outfile.close()