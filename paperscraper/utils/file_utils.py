import gzip
import tarfile
from io import BytesIO
import os
import shutil

from .latex_utils import text_from_latex


def save_tar(bin, output_file='/tmp/temp.tar.gz'):
    try:
        compressed_f = BytesIO()
        compressed_f.write(bin)
        compressed_f.seek(0)

        decompressed_f = gzip.GzipFile(fileobj=compressed_f, mode='rb')
        with open(output_file, 'wb') as fout:
            fout.write(decompressed_f.read())
        return output_file
    except Exception as e:
        print(e)
        return False

def untar(fpath, output_dir='/tmp/temp', exist_ok=True, exts=['']):
    def select_members(members): # check extension
        for tarinfo in members:
            if has_ext(tarinfo.name, exts=exts):
                yield tarinfo

    if fpath and fpath.endswith('tar.gz') and os.path.isfile(fpath): # check file valid
        # Clean directory
        shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        # Try unzip
        try:
            with tarfile.open(fpath) as tar:
                tar.extractall(members=select_members(tar), path=output_dir)

        except Exception as e:
            print(e)
            return False

        return output_dir
    return False

def has_ext(fname, exts):
    return any([fname.endswith('.{}'.format(ext)) for ext in exts])

def save_text(text_list, save_to, append=False):
    mode = 'w' if not append else 'a'
    with open(save_to, mode) as fout:
        for line in text_list:
            print(line, file=fout)

def save_classified_text(text_lists, save_to, append=False):
    for text_list, save_path in zip(text_lists, save_to):
        save_text(text_list, save_path, append=append)

def extract_text_from_file(fpath, classifications=None, meta=None, is_class=None):
    if classifications is None:
        classifications = [lambda x: True] # return all text as one class
        is_class = [True]
    elif is_class is None:
        is_class = [True for i in range(len(classifications))]

    n_classes = len(classifications)
    text_lists = [[] for _ in range(n_classes)]
    if os.path.isfile(fpath):
        if fpath.endswith('tex'):
            text_lists, is_class = text_from_latex(fpath, classifications=classifications, meta=meta, is_class=is_class)
    return text_lists, is_class

def extract_text(path, exts=[''], classifications=None, meta=None):
    if classifications is None:
        classifications = [lambda x: True] # return all text as one class

    n_classes = len(classifications)
    text_lists = [[] for _ in range(n_classes)]
    is_class = [True for i in range(n_classes)]

    # Extract from files in directory if path is directory
    if os.path.isdir(path):
        for dpath, dnames, fnames in os.walk(path):
            for fname in fnames:
                if has_ext(fname, exts=exts):
                    fpath = os.path.join(dpath, fname)
                    this_text_lists, is_class = extract_text_from_file(fpath, classifications=classifications, meta=meta, is_class=is_class)

                    # If documents does not pass any classification, return nothing
                    if not any(is_class):
                        return []

                    for i in range(n_classes):
                        text_lists[i] += this_text_lists[i]
    # Else extract from file
    elif os.path.isfile(path):
        if has_ext(path, exts=exts):
            text_lists, is_class = extract_text_from_file(path, classifications=classifications, meta=meta, is_class=is_class)
    # Not valid path
    else:
        return False

    # Remove text of invalid classes
    for i, c in enumerate(is_class):
        if not c:
            text_lists[i] = []
    return text_lists