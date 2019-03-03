import pdftotext

from .utils import split_sent, always_true


def text_from_pdf(fpath, filter_text=always_true):
    text_list = []
    with open(fpath, 'rb') as fin:
        try:
            pdf = pdftotext.PDF(fin)
        except Exception as e:
            print(e)
            return [text_list]

    for page in pdf:
        text = ''.join(page.split())
        text_list += [sent for sent in split_sent(text) if filter_text(sent)]

    return [text_list]