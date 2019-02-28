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
PYTHON3 = sys.version_info[0] == 3
if PYTHON3:
    from urllib.parse import urlencode
    from urllib.request import urlopen
    from urllib.error import HTTPError
else:
    from urllib import urlencode
    from urllib2 import HTTPError, urlopen

from .record import Record
from .const import OAI, ARXIV, META_BASE, E_PRINT_BASE, TAR
from .utils.utils import get_date_chunks
from .utils.file_utils import save_tar, untar, save_text, extract_text


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
    """

    def __init__(self, category, date_from=None, date_until=None, t=30, filters={}, content_type=TAR, text_file_exts=['']):
        self.cat = str(category)
        self.t = t
        self.content_type = content_type
        self.text_file_exts = text_file_exts

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

    def meta_url(self, f, u, cat):
        return '{}from={}&until={}&metadataPrefix=arXiv&set={}'.format(META_BASE, f, u, cat)

    def eprint_url(self, id):
        return '{}{}'.format(E_PRINT_BASE, id)

    def scrape_arxiv_meta(self, category=None, date_from=None, date_until=None):
        category = self.cat if category is None else category
        date_from = self.f if date_from is None else date_from
        date_until = self.u if date_until is None else date_until

        t0 = time.time()
        url = self.meta_url(date_from, date_until, category)
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
                    print('Got 503. Retrying after {0:d} seconds.'.format(self.t))
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
        if not append:
            # Empty the files
            with open(save_to, 'w'): pass
            with open(log_to, 'w'): pass

        t0 = time.time()

        file_cnt = 0
        sent_cnt = 0
        extracted_file_ids = []
        scraped_file_ids = []
        date_chunks = get_date_chunks(self.f, self.u, intv=day_intv)
        for start, end in date_chunks:
            print('fetching data from ', start, ' to ', end, '...')

            meta_records = self.scrape_arxiv_meta(date_from=start, date_until=end)
            for meta_record in meta_records:
                url = self.eprint_url(meta_record['id'])
                scraped_file_ids.append(meta_record['id'])
                print(url)

                # Fetch
                try:
                    response = urlopen(url)
                except HTTPError as e:
                    if e.code == 503:
                        to = int(e.hdrs.get('retry-after', 30))
                        print('Got 503. Retrying fter {0:d} seconds.'.format(self.t))
                        time.sleep(self.t)
                        continue
                    else:
                        raise

                # Check content type
                if response.getheader('Content-Type') == self.content_type:
                    # Decompress, extract, and save
                    tar_file = save_tar(response.read())                        # save to temp file
                    output_dir = untar(tar_file, exts=self.text_file_exts)      # decompress temp file
                    if output_dir:
                        text_list = extract_text(output_dir, exts=self.text_file_exts)
                        save_text(text_list, save_to=save_to, append=True)

                        file_cnt += 1
                        sent_cnt += len(text_list)
                        extracted_file_ids.append(meta_record['id'])

        t1 = time.time()
        print('Fetching text is completed in {0:.1f} seconds.'.format(t1 - t0))
        print('File counts: {:d}, sentence counts: {:d}'.format(file_cnt, sent_cnt))

        file_ids = ['Scraped'] + scraped_file_ids + ['Extracted'] + extracted_file_ids
        save_text(file_ids, save_to=log_to, append=True)
    
    def scrape_text(self, site, *args, **kwargs):
        if site == 'arxiv':
            self.scrape_arxiv_text(*args, **kwargs)
        else:
            print('site \'{}\' not supported'.format(site))