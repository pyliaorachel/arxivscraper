import re
import os

from .utils import always_true, split_sent


def find_institutes(text):
    text = ' '.join(text.strip().split())

    institutes = []
    institute_titles = [r'University', r'Institute', r'College']
    for title in institute_titles:
        pattern = r'{.*}'
        in_brackets = re.findall(pattern, text)
        for in_bracket in in_brackets:
            pattern = r'[^a-zA-Z\s]([a-zA-Z\s]*' + title + r'[a-zA-Z\s]*)[^a-zA-Z\s]'
            institutes += re.findall(pattern, text)

    institutes = [clean_text(ins).lower() for ins in institutes]
    return institutes

def clean_text(text):
    def remove_pattern(pattern, text, clean, flags=0):
        # Cut on text too long, probably something wrong and unuseful
        if len(text) > 2000:
            return '', True

        r = re.search(pattern, text, flags)
        if text != '' and r:
            s, e = r.span()
            text = text[:s] + text[e:]
            # Recursively remove
            return remove_pattern(pattern, text, False, flags)
        return text, clean

    text = ' '.join(text.strip().split())
    text += '\n'
    clean = False
    while not clean:
        clean = True
        # Remove commands
        text, clean = remove_pattern(r'~?\\.*?{[^{]*?}[\s$]+', text, clean, re.MULTILINE)
        text, clean = remove_pattern(r'~?\\.*?\[[^\[]*?\][\s$]+', text, clean, re.MULTILINE)
        text, clean = remove_pattern(r'~?\\.*?[\s$]+', text, clean, re.MULTILINE)
        # Remove math
        text, clean = remove_pattern(r'\$\$.*?\$\$', text, clean, re.MULTILINE) # remove this first so the next one won't find $$
        text, clean = remove_pattern(r'\$.*?\$', text, clean, re.MULTILINE)
        # Remove brackets
        text, clean = remove_pattern(r'\[[^\[]*?\]', text, clean, re.MULTILINE)
        text, clean = remove_pattern(r'{[^{]*?}', text, clean, re.MULTILINE)
        # Remove comments
        text, clean = remove_pattern(r'%.*$', text, clean, re.MULTILINE)

    return text.strip()

def text_from_latex(fpath, classifications=None, meta=None, is_class=None, filter_text=always_true):
    """
    Extract from sections and subsections.
    Remove latex specific tokens.
    """
    if classifications is None:
        classifications = [lambda x: True] # return all text as one class
        is_class = [True]
    elif is_class is None:
        is_class = [True for i in range(len(classifications))]

    n_classes = len(classifications)
    text_lists = [[] for _ in range(n_classes)]
    if os.path.isfile(fpath):
        text_list = []
        institutes = []
        something_begins = 0
        is_main_file = False # has \documentclass
        text = ''
        with open(fpath, 'r', errors='ignore') as fin:
            for line in fin:
                # Flag a skip segment
                if '\begin' in line:
                    something_begins += 1
                # End a skip segment
                elif something_begins and '\end' in line:
                    something_begins -= 1
                # Read text in chunks of paragraphs
                elif something_begins == 0:
                    if line != '\n':
                        text += line
                    else:
                        is_main_file |= '\documentclass' in text

                        # Find institutes/universities
                        if is_main_file:
                            institutes += find_institutes(text)

                        cleaned_text = clean_text(text)
                        sents = split_sent(cleaned_text)
                        text_list += [sent for sent in sents if filter_text(sent)]
                        text = ''
        if text != '':
            cleaned_text = clean_text(text)
            sents = split_sent(cleaned_text)
            text_list += [sent for sent in sents if filter_text(sent)]
            text = ''
        
        # Classify the text
        for i, filt in enumerate(classifications):
            if is_class[i]:
                if filt((text_list, institutes, meta, is_main_file)):
                    text_lists[i] += text_list
                else:
                    is_class[i] = False

    return text_lists, is_class
