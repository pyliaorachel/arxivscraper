"""
A python program to retreive recrods from ArXiv.org in given
categories and specific date range.

Author: Mahdi Sadjadi (sadjadi.seyedmahdi[AT]gmail[DOT]com).
"""
from __future__ import print_function
import xml.etree.ElementTree as ET
import datetime
import time
import sys
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from socket import error as SocketError

import marisa_trie
from bs4 import BeautifulSoup

from .record import Record
from .utils.const import OAI, ARXIV, META_BASE, E_PRINT_BASE, TAR, GOOGLE_SCHOLAR_BASE
from .utils.utils import get_date_chunks, is_chinese, always_true, always_false
from .utils.file_utils import save_tar, untar, save_text, save_classified_text, extract_text, download_pdf


class Scraper(object):
    """
    A class to hold info about attributes of scraping,
    such as date range, categories, and number of returned
    records. If `from` is not provided, the first day of
    the current month will be used. If `until` is not provided,
    the current day will be used.

    Paramters
    ---------
    category: str
        The category of scraped records
    data_from: str
        starting date in format 'YYYY-MM-DD'. Updated eprints are included even if
        they were created outside of the given date range. Default: first day of current month.
    date_until: str
        final date in format 'YYYY-MM-DD'. Updated eprints are included even if
        they were created outside of the given date range. Default: today.
    t: int
        Waiting time between subsequent calls to API, triggred by Error 503.
    filter: dictionary
        A dictionary where keys are used to limit the saved results. Possible keys:
        subcats, author, title, abstract. See the example, below.
    content_type: str
        The content type of the data to scrape, as specified in response header 'Content-Type'.
    text_file_exts: list
        A list of file extensions to consider as text file for text extraction.
    max_sent: int
        Maximum number of sentences to scrape
    """

    def __init__(self,
        category='', date_from=None, date_until=None, t=30,
        filters={}, content_type=TAR, text_file_exts=['tex'], max_sent=100,
        classifications=None, filter_text=always_true
    ):
        self.cat = str(category)
        self.t = t
        self.content_type = content_type
        self.text_file_exts = text_file_exts
        self.max_sent = max_sent
        self.filter_text = filter_text

        if classifications is None:
            classifications = [always_true] # All in one class
        self.classifications = classifications

        DateToday = datetime.date.today()
        if date_from is None:
            self.f = str(DateToday.replace(day=1))
        else:
            self.f = date_from
        if date_until is None:
            self.u = str(DateToday)
        else:
            self.u = date_until

        self.filters = filters
        if not self.filters:
            self.append_all = True
        else:
            self.append_all = False
            self.keys = filters.keys()
            for k, v in self.filters.items():
                self.filters[k] = marisa_trie.Trie(v)

    @property
    def n_classes(self):
        return len(self.classifications)

    def set_classifications(self, classifications):
        self.classifications = classifications

    def arxiv_meta_url(self, f, u, cat):
        return '{}from={}&until={}&metadataPrefix=arXiv&set={}'.format(META_BASE, f, u, cat)

    def arxiv_eprint_url(self, id):
        return '{}{}'.format(E_PRINT_BASE, id)

    def google_scholar_req(self, query, page):
        params = dict(q=str(query), start=str(page*10))
        query = urlencode([(k, v.encode('utf-8')) for k, v in params.items()])
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        return Request(GOOGLE_SCHOLAR_BASE + '?' + query, headers=headers)

    def scrape_arxiv_meta(self, category=None, date_from=None, date_until=None):
        category = self.cat if category is None else category
        date_from = self.f if date_from is None else date_from
        date_until = self.u if date_until is None else date_until

        t0 = time.time()
        url = self.arxiv_meta_url(date_from, date_until, category)
        print(url)
        ds = []
        k = 1
        while True:
            print('fetching up to ', 1000 * k, 'records...')
            try:
                response = urlopen(url)
            except HTTPError as e:
                if e.code == 503:
                    to = int(e.hdrs.get('retry-after', 30))
                    print('Got 503. Retrying after {} seconds.'.format(self.t))
                    time.sleep(self.t)
                    continue
                else:
                    raise
            k += 1
            xml = response.read()
            root = ET.fromstring(xml)
            records = root.findall(OAI + 'ListRecords/' + OAI + 'record')
            for record in records:
                meta = record.find(OAI + 'metadata').find(ARXIV + 'arXiv')
                record = Record(meta).output()
                if self.append_all:
                    ds.append(record)
                else:
                    save_record = False
                    for key in self.keys:
                        for word in self.filters[key]:
                            if word.lower() in record[key]:
                                save_record = True

                    if save_record:
                        ds.append(record)

            try:
                token = root.find(OAI + 'ListRecords').find(OAI + 'resumptionToken')
            except:
                return []
            if token is None or token.text is None:
                break
            else:
                url = META_BASE + 'resumptionToken=%s' % token.text

        t1 = time.time()
        print('Fetching meta is completed in {0:.1f} seconds.'.format(t1 - t0))
        print('Total number of records {:d}'.format(len(ds)))
        return ds
    
    def scrape_meta(self, site, *args, **kwargs):
        if site == 'arxiv':
            self.scrape_arxiv_meta(*args, **kwargs)
        else:
            print('site \'{}\' not supported'.format(site))

    def scrape_arxiv_text(self, save_to, log_to, append=False, day_intv=10):
        # Handle the save filepaths
        if self.n_classes > 1 and len(save_to) != self.n_classes:
            print('save_to should be a list of {}(number of classes) filepaths'.format(self.n_classes))
            return
        elif self.n_classes == 1: # ensures we have a list of paths
            if type(save_to) != list:
                save_to = [save_to]

        # Empty the save files
        if not append:
            for path in save_to:
                with open(path, 'w'): pass
            with open(log_to, 'w'): pass

        # Main
        t0 = time.time()

        file_cnt = 0
        sent_cnts = [0] * self.n_classes
        extracted_file_id_list = [[] for _ in range(self.n_classes)]
        scraped_file_ids = []
        date_chunks = get_date_chunks(self.f, self.u, intv=day_intv)
        classifications = self.classifications[:] # make a copy so we can modify later
        termination_reached = [False] * self.n_classes
        for start, end in date_chunks:
            print('fetching data from ', start, ' to ', end, '...')

            meta_records = self.scrape_arxiv_meta(date_from=start, date_until=end)
            r = 0
            while r < len(meta_records):
                meta_record = meta_records[r]
                url = self.arxiv_eprint_url(meta_record['id'])
                scraped_file_ids.append(meta_record['id'])
                print(url)

                # Fetch
                try:
                    response = urlopen(url)
                except HTTPError as e:
                    if e.code == 503:
                        to = int(e.hdrs.get('retry-after', 30))
                        print('Got {}. Retrying after {} seconds.'.format(e.code, self.t))
                        time.sleep(self.t)
                        continue
                    else:
                        print(e)
                        r += 1 # avoid redoing, may never succeed
                        continue
                except SocketError as e:
                    if e.errno == 104:
                        print('Got {}. Retrying after {} seconds.'.format(e.errno, self.t))
                        time.sleep(self.t)
                        continue
                    else:
                        print(e)
                        r += 1 # avoid redoing, may never succeed
                        continue
                except Exception as e:
                    print(e)
                    r += 1 # avoid redoing, may never succeed
                    continue

                # Check content type
                if response.getheader('Content-Type') == self.content_type:
                    # Decompress, extract, and save
                    try:
                        bin = response.read()
                    except Exception as e:
                        print(e)
                        r += 1 # avoid redoing, may never succeed
                        continue

                    tar_file = save_tar(bin)                                    # save to temp file
                    output_dir = untar(tar_file, exts=self.text_file_exts)      # decompress temp file
                    if output_dir:
                        text_lists = extract_text(output_dir, exts=self.text_file_exts, classifications=classifications, meta=meta_record)
                        save_classified_text(text_lists, save_to=save_to, append=True)

                        file_cnt += 1
                        for i in range(len(text_lists)):
                            sent_cnts[i] += len(text_lists[i])
                        for i, text_list in enumerate(text_lists):
                            if len(text_list) > 0:
                                extracted_file_id_list[i].append(meta_record['id'])

                for i, sent_cnt in enumerate(sent_cnts):
                    if not termination_reached[i] and sent_cnt >= self.max_sent:
                        print('Max number of sentences reached for class {} with {} sentences.'.format(i, sent_cnt))
                        classifications[i] = always_false
                        termination_reached[i] = True

                if all(termination_reached):
                    break
                r += 1

            file_ids = ['Scraped'] + scraped_file_ids
            for i, extracted_file_ids in enumerate(extracted_file_id_list):
                file_ids += ['Extracted - class {}'.format(i)]
                file_ids += extracted_file_ids
            save_text(file_ids, save_to=log_to, append=True)
            extracted_file_id_list = [[] for _ in range(self.n_classes)]
            scraped_file_ids = []

            if all(termination_reached):
                break

        return sent_cnts

    def scrape_google_scholar(self, save_to, log_to, queries, append=False):
        # Empty the save files
        if not append:
            with open(save_to, 'w'): pass
            with open(log_to, 'w'): pass

        # Main
        t0 = time.time()

        file_cnt = 0
        sent_cnt = 0
        extracted_file_ids = []
        scraped_file_ids = []
        for query in queries:
            print('fetching data for query', query, '...')

            for p in range(100):
                req = self.google_scholar_req(query, p)
                print(req.get_full_url())

                # Fetch
                try:
                    response = urlopen(req)
                except SocketError as e:
                    if e.errno == 104:
                        print('Got {}. Retrying after {} seconds.'.format(e.errno, self.t))
                        time.sleep(self.t)
                        continue
                    else:
                        print(e)
                        continue
                except Exception as e:
                    print(e)
                    continue

                page = BeautifulSoup(response, 'html.parser')
                scraped_file_ids.append('{}:{}'.format(query, p))

                # Go through each link
                pdf_divs = page.find_all('div', attrs={'class': 'gs_or_ggsm'})
                for pdf_div in pdf_divs:
                    pdf_a = pdf_div.findChild('a' , recursive=False) # pdf link should be the first child
                    download_link = pdf_a.get('href')
                    print('download', download_link)

                    pdf_file = download_pdf(download_link)                      # save to temp file
                    if pdf_file:
                        text_lists = extract_text(pdf_file, exts=['pdf'], filter_text=self.filter_text)
                        save_text(text_lists[0], save_to=save_to, append=True)

                        file_cnt += 1
                        sent_cnt += len(text_lists[0])
                        extracted_file_ids.append('{}:{}:{}'.format(query, p, download_link))

                if sent_cnt >= self.max_sent:
                    break

            file_ids = ['Scraped'] + scraped_file_ids + ['Extracted'] + extracted_file_ids
            save_text(file_ids, save_to=log_to, append=True)
            extracted_file_ids = []
            scraped_file_ids = []

            if sent_cnt >= self.max_sent:
                break

        t1 = time.time()
        print('Fetching text is completed in {0:.1f} seconds.'.format(t1 - t0))
        print('File counts: {:d}, sentence counts: {}'.format(file_cnt, sent_cnt))

        return sent_cnt
    
    def scrape_text(self, site, *args, **kwargs):
        if site == 'arxiv':
            return self.scrape_arxiv_text(*args, **kwargs)
        elif site == 'google-scholar':
            return self.scrape_google_scholar(*args, **kwargs)
        else:
            print('site \'{}\' not supported'.format(site))
