import re
import os


def find_institutes(text):
    text = ' '.join(text.strip().split())

    institutes = []
    institute_titles = [r'University', r'Institute', r'College']
    for title in institute_titles:
        pattern = r'{([^{,]*?' + title + r'.*?)[,}]'
        institutes += re.findall(pattern, text) # {...title..., or {...title...}
        pattern = r',([^{,]*?' + title + r'.*?)[,}]'
        institutes += re.findall(pattern, text) # ,...title..., or ,...title...}

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
        text, clean = remove_pattern(r'~?\\.*?{.*?}[\s$]+', text, clean, re.MULTILINE)
        text, clean = remove_pattern(r'~?\\.*?\[.*?\][\s$]+', text, clean, re.MULTILINE)
        text, clean = remove_pattern(r'~?\\.*?[\s$]+', text, clean, re.MULTILINE)
        # Remove math
        text, clean = remove_pattern(r'\$\$.*?\$\$', text, clean, re.MULTILINE) # remove this first so the next one won't find $$
        text, clean = remove_pattern(r'\$.*?\$', text, clean, re.MULTILINE)
        # Remove brackets
        text, clean = remove_pattern(r'\[.*?\]', text, clean, re.MULTILINE)
        text, clean = remove_pattern(r'{.*?}', text, clean, re.MULTILINE)
        # Remove comments
        text, clean = remove_pattern(r'%.*$', text, clean, re.MULTILINE)

    return text.strip()

def text_from_latex(fpath, classifications=None, meta=None):
    """
    Extract from sections and subsections.
    Remove latex specific tokens.
    """
    if classifications is None:
        classifications = [lambda x: True] # return all text as one class

    text_lists = [[] for _ in range(len(classifications))]
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
                        if cleaned_text != '':
                            text_list.append(cleaned_text)
                        text = ''
        if text != '':
            cleaned_text = clean_text(text)
            if cleaned_text != '':
                text_list.append(cleaned_text)
        
        # Classify the text
        for i, filt in enumerate(classifications):
            if filt((text_list, institutes, meta)):
                text_lists[i] += text_list

    return text_lists