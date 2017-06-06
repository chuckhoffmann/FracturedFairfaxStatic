#!/usr/bin/env python
import re
import sys
from jinja2 import Environment, PackageLoader, Template
import requests
import boto3
import StringIO
import logging

def make_request_parameters(source_title):
    parameters = {'action':'parse',
                  'page':source_title,
                  'prop':'text|categorieshtml',
                  'disablelimitreport':'true',
                  'disableeditsection':'true',
                  'format':'json'}
    return parameters

def get_article_json(source_title):
    """Get the title and text of an article and return it as a json object"""
    baseURL = u'http://192.168.1.14/wiki/api.php'
    parameters = make_request_parameters(source_title)

    r = requests.get(baseURL,params=parameters)

    #error if the request returned no data

    return r.json()

def replace_wiki_links(article_text):
    """Replace all wiki links, converting them from
    # "/wiki/index.php/Article" -> "/Article.html" or
    # "/wiki/index.php?title=Article&action=edit&redlink=1"""
    wiki_link = re.compile('\/wiki\/index\.php'                     #literal
                           '(?:\/|\?title=)'
                           '([a-zA-Z0-9%\.:_\-(),]+)'
                           '(?:&amp;action=edit&amp;redlink=1)?')

    extant_link = re.compile('wiki\/index\.php\/'
                             '([^"]+)') #regex for existing wiki articles
    #regex for nonexistent wiki articles
    nonexistent_link = re.compile('<a href="\/wiki\/index\.php\?[^>]+>'
                                  '([^<]+)'
                                  '<\/a>') #regex for nonexisting wiki articles

    #replace existing article links
    #replace nonexisting article links (redlinks)
    el_replaced = extant_link.sub(r'\1.html', article_text)
    cat = nonexistent_link.sub(r'\1', el_replaced)

    cleaned_article_text = wiki_link.sub(r'/\1.html', article_text)

    #return cleaned_article_text
    return cat

def replace_category_links(category_text):
    #remove the link to the "Special:Categories" page
    special_page_link = re.compile('<a href="\/wiki\/index\.php\/Special:Categories" title="Special:Categories">(Category|Categories)<\/a>')
    category_despecial, dummy = special_page_link.subn(r'\1', category_text)
    #replace all the wikilinks for the categories
    catLink = re.compile(r'/wiki/index.php/([^"]+)')
    cleaned_categories, replacements = catLink.subn(r'/\1.html',category_despecial)

    #if no replacements were made, return an empty string so that
    #when page is assembled there won't be a categories section at all
    if replacements == 0:
        cleaned_categories = u''

    return cleaned_categories

def remove_hidden_categories(category_text):
    # clean out the hidden categories div, if it exists
    if "mw-hidden" in category_text:
        hiddenCats = re.compile(r'<div id="mw-hidden-catlinks.+?</div>')
        cleaned_categories = hiddenCats.sub(r'', category_text)
    else:
        cleaned_categories = category_text

    return cleaned_categories

def make_final_page(article_title, article_text, categories ):
    #make a Fractured Fairfax page using a Jinja2 template

    #set up the Jinja2 environment
    env = Environment(loader=PackageLoader('template_page','templates'))

    #template located at ./templates/
    template = env.get_template('article_template.html')

    final_page = template.render(articleTitle = article_title,
                                articleText = article_text,
                                categories = categories)
    return final_page

def main():
    #Build an article page using a template

    if len(sys.argv) > 1:
        source_title = sys.argv[1]
        #source_title = source_title.strip()
    else:
        sys.exit('You must specify the article name.')

    parsed_page = get_article_json(source_title)

    #check for error in returned json dictionary
    if u'error' in parsed_page:
        sys.stdout.write('Error in parsed page:\n')
        for k, v in parsed_page[u'error'].items():
            sys.stdout.write("*%s - %s\n" % (k, v))
        sys.exit('Error in parsed page.')

    #extract the title and article text from the json dictionary
    article_title = parsed_page[u'parse'][u'title']
    article_text = parsed_page[u'parse'][u'text'][u'*']

    clean_article_text = replace_wiki_links(article_text)

    #check for the existence of categorieshtml in the json
    #dictionary, and if they exist, clean the wiki links
    if u'categorieshtml' in parsed_page[u'parse']:
        categories = parsed_page[u'parse'][u'categorieshtml'][u'*']
        cleanCategories = replace_category_links(remove_hidden_categories(categories))
    else:
        cleanCategories = u''

    final_page = make_final_page(article_title, clean_article_text, cleanCategories)

    #sys.stdout.write(finalPage.encode('utf-8'))

    #if a second parameter was passed at the command line, use this for the file name
    #otherwise, build a file name by replacing spaces with underlines
    if len(sys.argv) == 3:
        fileName = sys.argv[2] + '.html'
    else:
        fileName = source_title.replace(' ','_') + '.html'

    #write the page to a file on disk
    #outFile = open(fileName,'w')
    #outFile.write(finalPage.encode('utf-8'))
    #outFile.close()

    outfile = StringIO.StringIO(final_page.encode('utf-8'))

    #write the file to S3
    s3 = boto3.resource('s3')
    s3.Bucket('www.fracturedfairfax.com').put_object(Key=fileName,
                                                     Body=outfile,
                                                     ContentType='text/html',
                                                     ACL='public-read')

    outfile.close()

if __name__ == "__main__":
    main()