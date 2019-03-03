"""\
Provides a python package to get data of academic papers
posted at arXiv.org in a specific date range and category.

Collected data:

        Title,
        ID,
        Authors,
        Abstract,
        Subcategories,
        DOI,
        Created (date),
        Updated (date)
"""

import sys
try:
    from setuptools import setup
except ImportError:
    sys.exit("""Error: Setuptools is required for installation.
 -> http://pypi.python.org/pypi/setuptools""")

setup(
    name = "paperscraper",
    version = "0.0.1",
    description = "Get paper text data of specific language users",
    author = "Mahdi Sadjadi, Peiyu Liao",
    author_email = "pyliao@stanford.edu",
    url = "https://github.com/pyliaorachel/paperscraper",
    keywords = ["arxiv", "scraper", "api", "citation"],
    license = "MIT",
    install_requires=[
        'marisa-trie',
        'BeautifulSoup4',
        'pdftotext'
    ],
    classifiers = [
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Text Processing :: Markup :: LaTeX",
        ],
)
