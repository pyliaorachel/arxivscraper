import gzip
import tarfile
from io import BytesIO
import os


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
        os.makedirs(output_dir, exist_ok=exist_ok)
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
    return any([fname.endswith(ext) for ext in exts])

def save_text(text_list, save_to, append=False):
    mode = 'w' if not append else 'a'
    with open(save_to, mode) as fout:
        for line in text_list:
            print(line, file=fout)

def extract_text_from_file(fpath):
    text_list = []
    if os.path.isfile(fpath):
        with open(fpath, 'r') as fin:
            text_list.append('a ')
    return text_list

def extract_text(path, exts=['']):
    text_list = []

    # Extract from files in directory if path is directory
    if os.path.isdir(path):
        for dpath, dnames, fnames in os.walk(path):
            for fname in fnames:
                if has_ext(fname, exts=exts):
                    fpath = os.path.join(dpath, fname)
                    text_list += extract_text_from_file(fpath)
    # Else extract from file
    elif os.path.isfile(path):
        if has_ext(path, exts=exts):
            text_list += extract_text_from_file(path)
    # Not valid path
    else:
        return False
    return text_list