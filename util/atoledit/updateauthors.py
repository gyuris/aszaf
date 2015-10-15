#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# usage: updateauthors.py <OpenLyrics XML file> <output directory>
#
# Duplicates authors which do not have type associated with. The first
# copy will have the type 'words', the second one will have the type 'music'.
#
# dependencies:
#   openlyrics.py (included, http://code.google.com/p/openlyrics/source/browse/lib/python/openlyrics.py)

__version__ = u'2014.12.18'

import sys, os, copy
import openlyrics as ol

def main():
    filePath = sys.argv[1]
    outDir = sys.argv[2]
    song = ol.Song(filePath)
    authorsUpdated = []
    for author in song.props.authors:
        if not author.type:
            author.type = 'words'
            authorsUpdated.append(author)
            author2 = copy.deepcopy(author)
            author2.type = 'music'
            authorsUpdated.append(author2)
        else:
            authorsUpdated.append(author)
    song.props.authors = authorsUpdated
    song.modifiedIn = u'openlyrics.py %s' % (ol.__version__)
    songDir, fileName = os.path.split(filePath)
    outPath = os.path.join(outDir, fileName)
    song.write(outPath)
    return 0

if __name__ == '__main__':
    main()

