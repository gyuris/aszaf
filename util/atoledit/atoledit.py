#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Attila Tóth's OpenLyrics Editor
#
# dependencies:
#   atollib.py (included)
#   openlyrics.py (included, http://code.google.com/p/openlyrics/source/browse/lib/python/openlyrics.py)
#   lxml (http://lxml.de/)
#   pandas (http://pandas.pydata.org/)
#   YAD (http://sourceforge.net/projects/yad-dialog/)

# TODO
# schema as argument with default value
# configurable sort order

__version__ = u'2014.06.28'

from atollib import *
import openlyrics as ol

def main():
    parser = argparse.ArgumentParser(description=u'Edit OpenLyrics file(s).')
    parser.add_argument(u'target', help=u'OpenLyrics XML file or a directory')
    parser.add_argument(u'-c', u'--check', action=u'store_true', help=u'Check file instead of editing it')
    #~ parser.add_argument(u'-s', u'--schema', help=u'RelaxNG XML schema')
    
    args = parser.parse_args()
    
    if os.path.isfile(args.target):
        filePath = unicode(args.target, encoding=sys.getfilesystemencoding())
        songDir, fileName = os.path.split(filePath)
        if args.check:
            check(filePath, interactive=True)
        else:
            song = ol.Song(filePath)
            song, fileName, songDir = editSong(song, fileName, songDir)
    elif os.path.isdir(args.target):
        songDir = unicode(args.target, encoding=sys.getfilesystemencoding())
        returncode, results = editDir(songDir)
    else:
        raise Exception(u'Error! %s is not a file or a directory' % args.target)
    return 0

if __name__ == '__main__':
    main()
