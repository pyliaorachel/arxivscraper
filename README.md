# PaperScraper

An paper scraper to retrieve text data of specific language users from some source.

## Usage

Use `pip` (or `pip3` for python3) to install dependencies:

```bash
$ pip install -r requirements.txt
```

## Examples

### Without filtering

Let's import `paperscraper` and create a scraper to fetch all preprints
in condensed matter physics category
from 27 May 2017 until 29 May 2017 (for other categories, see below)
from [arXiv.org](https://arxiv.org/):

```python
from paperscraper.scraper import Scraper
scraper = Scraper(category='physics:cond-mat', date_from='2017-05-27', date_until='2017-05-29')
```

Once we built an instance of the scraper, we can start the scraping:

```python
scraper.scrape_text('arxiv', save_to='test.txt', log_to='test.log')
```

The scraper scrapes at an interval of 10 days.
For each interval, the metadata is first fetched,
and the papers that pass the filters and are written by the target language users
are further scraped for their text data.

The status is printed out:

```
fetching data from  2017-05-27  to  2017-05-29 ...
http://export.arxiv.org/oai2?verb=ListRecords&from=2017-05-27&until=2017-05-29&metadataPrefix=arXiv&set=physics:cond-mat
fetching up to  1000 records...
Fetching meta is completed in 4.4 seconds.
Total number of records 38
https://arxiv.org/e-print/1503.04690
...
https://arxiv.org/e-print/1705.09598
Fetching text is completed in 106.7 seconds.
File counts: 29, sentence counts: 7393
```

The text is saved to `test.txt`. The ids of all scraped papers and selected papers are logged to `test.log`.

### With filtering

To have more control over the output, you could supply a dictionary to filter out the results. As an example, let's collect all preprints related to machine learning. This subcategory (`stat.ML`) is part of the statistics (`stat`) category. In addition, we want those preprints that word `learning` appears in their abstract.

```python
from paperscraper.scraper import Scraper
scraper = Scraper(category='stat', date_from='2017-08-01', date_until='2017-08-10', t=10, filters={'categories':['stat.ml'],'abstract':['learning']})
scraper.scrape_text('arxiv', save_to='test.txt', log_to='test.log')
```

> In addition to `categories` and `abstract`, other available keys for `filters` are: `authors` and `title`.

### With classification

We can pass in custom classification filters to classify the papers and text.

To do so, we define a list of filters that takes in a tuple `(text_list, institutes, meta)`
of the paper and returns a boolean indicating whether it belongs to the class.

The following example shows how to classify the papers into two classes,
one with the number of institutes smaller than 2, another with those greater than 2.

```python
from paperscraper.scraper import Scraper
classifications = [
  lambda x: len(x[1]) <= 2,
  lambda x: len(x[1]) > 2
]
scraper = Scraper(
  category='physics:cond-mat', date_from='2017-05-27', date_until='2017-05-29',
  classifications=classifications)
scraper.scrape_text('arxiv', save_to=['class1.txt', 'class2.txt'], log_to='test.log')
```

## Supported Sites

- [arXiv.org](https://arxiv.org/)

## Categories

Here is a list of all categories available on ArXiv. For a complete list of subcategories, see [categories.md](categories.md).

| Category | Code |
| --- | --- |
| Computer Science | `cs` |
| Economics | `econ` |
| Electrical Engineering and Systems Science | `eess` |
| Mathematics | `math` |
| Physics | `physics` |
| Astrophysics | `physics:astro-ph` |
| Condensed Matter | `physics:cond-mat` |
| General Relativity and Quantum Cosmology | `physics:gr-qc` |
| High Energy Physics - Experiment | `physics:hep-ex` |
| High Energy Physics - Lattice | `physics:hep-lat` |
| High Energy Physics - Phenomenology | `physics:hep-ph` |
| High Energy Physics - Theory | `physics:hep-th` |
| Mathematical Physics | `physics:math-ph` |
| Nonlinear Sciences | `physics:nlin` |
| Nuclear Experiment | `physics:nucl-ex` |
| Nuclear Theory | `physics:nucl-th` |
| Physics (Other) | `physics:physics` |
| Quantum Physics | `physics:quant-ph` |
| Quantitative Biology | `q-bio` |
| Quantitative Finance | `q-fin` |
| Statistics | `stat` |

## Credits

The project is built upon [arxivscraper](http://doi.org/10.5281/zenodo.889853) by Mahdi Sadjadi, which scrapes meta data from arXiv.
