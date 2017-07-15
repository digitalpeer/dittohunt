#!/usr/bin/python
#
# Ditto Hunt
#
# Copyright (c) 2017 Joshua Henderson <digitalpeer@digitalpeer.com>
#
# SPDX-License-Identifier: GPL-3.0
import os
import sys
from hashlib import md5
from pprint import pprint
from collections import defaultdict

def _md5(file_path, block_size=1024 * 1024):
    m = md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(block_size)
            if not chunk:
                break
            m.update(chunk)
    return m.digest()

def find_duplicates(path, status_callback=None):

    # TODO: make sure path exists
    # TODO: add option to exclude zero length files

    # first find files by equal size
    sizes = defaultdict(list)
    for root, dirs, filenames in os.walk(str(path)):
        for filename in filenames:
            path = os.path.join(root, filename)
            try:
                # This can result in FileNotFoundError, for example, when there
                # is a bad symlink.  Just ignore this specific error.
                sizes[os.path.getsize(path)].append(path)
            except FileNotFoundError as e:
                pass
    sizes = [x for x in sizes.values() if len(x) > 1]

    # now compare hashes of equal size files
    files = defaultdict(list)
    for paths in sizes:
        for path in paths:
            if status_callback is not None:
                status_callback(path)
            key = _md5(path)
            files[key].append(path)
    files = [x for x in files.values() if len(x) > 1]
    return files

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: finddups.py PATH")
        sys.exit()

    path = sys.argv[1]
    files = find_duplicates(path)

    for dups in files:
        print("\n\n---")
        pprint(dups)
        print("---")

    print("\n%s files have duplicates\n" % len(files))
