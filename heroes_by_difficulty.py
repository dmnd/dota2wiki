#! /usr/bin/env python

import logging

from pyquery import PyQuery as pq
import nltk.data
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')


hostname = "http://www.dota2wiki.com"


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def get_next(el, tag):
    while el.next():
        el = el.next()
        if el[0].tag == tag:
            return el
    return None


def get_hero_urls():
    heroes = "/wiki/Heroes"
    d = pq(url="%s%s" % (hostname, heroes))
    ids = ["#Strength_Heroes", "#Agility_Heroes", "#Intelligence_Heroes"]
    tables = [get_next(d(id).parent("h3"), 'table') for id in ids]
    hrefs = [href for href in [table.find("td > div > a").map(lambda i, a: (d(a).text(), a.attrib["href"])) for table in tables]]
    return dict([item for sublist in hrefs for item in sublist if item[0]])


def scrape_hero(url):
    difficulty = ""
    recommendation = ""

    d = pq(url="%s%s" % (hostname, url))
    text = d(".mw-content-ltr > p").text()
    sentences = tokenizer.tokenize(text)

    # find the sentence with recommended and players
    import re
    recommendation = ""
    meaning = None
    for s in sentences:
        match = re.search(r"(not )?recommended for (.*) players", s)
        if match:
            recommendation = s
            meaning = match.group(2).lower()
            break

    if meaning:
        new = "new" in meaning
        intermediate = "intermediate" in meaning
        advanced = "advanced" in meaning

        if new and not intermediate:
            difficulty = 0
        elif new and intermediate:
            difficulty = 1
        elif intermediate and not advanced:
            difficulty = 2
        elif intermediate and advanced:
            difficulty = 3
        elif not intermediate and advanced:
            difficulty = 4
        elif "experienced" in meaning:
            difficulty = 5

        if difficulty == "":
            logging.error("invalid meaning %s for url %s" % (meaning, url))
        else:
            logging.info("Finished %s" % url)
    return difficulty, recommendation

import StringIO


def table_to_wiki(table, urls):
    buffer = StringIO.StringIO()
    buffer.write("""
{| class="wikitable sortable"
|-
! Hero !! Difficulty !! Recommendation
""")

    for name, difficulty, rec in table:
        buffer.write("""|-
| [[%s]] || %s || %s
""" % (name, difficulty, rec))

    buffer.write("|}")
    return buffer.getvalue()

setup_logger()
urls = get_hero_urls()
table = [(name,) + scrape_hero(url) for name, url in urls.iteritems()]
table.sort(key=lambda x: x[1])
wiki = table_to_wiki(table, urls)
print wiki
