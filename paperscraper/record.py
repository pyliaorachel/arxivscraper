from .utils.const import ARXIV


class Record(object):
    """
    A class to hold a single record from ArXiv
    Each records contains the following properties:

    object should be of xml.etree.ElementTree.Element.
    """

    def __init__(self, xml_record):
        """if not isinstance(object,ET.Element):
        raise TypeError("")"""
        self.xml = xml_record
        self.id = self._get_text(ARXIV, 'id')
        self.url = 'https://arxiv.org/abs/' + self.id
        self.title = self._get_text(ARXIV, 'title')
        self.abstract = self._get_text(ARXIV, 'abstract')
        self.cats = self._get_text(ARXIV, 'categories')
        self.created = self._get_text(ARXIV, 'created')
        self.updated = self._get_text(ARXIV, 'updated')
        self.doi = self._get_text(ARXIV, 'doi')
        self.authors = self._get_authors()

    def _get_text(self, namespace, tag):
        """Extracts text from an xml field"""
        try:
            return self.xml.find(namespace + tag).text.strip().lower().replace('\n', ' ')
        except:
            return ''

    def _get_authors(self):
        authors = self.xml.findall(ARXIV + 'authors/' + ARXIV + 'author')
        authors = [author.find(ARXIV + 'keyname').text.lower() for author in authors]
        return authors

    def output(self):
        d = {'title': self.title,
         'id': self.id,
         'abstract': self.abstract,
         'categories': self.cats,
         'doi': self.doi,
         'created': self.created,
         'updated': self.updated,
         'authors': self.authors,
         'url': self.url}
        return d