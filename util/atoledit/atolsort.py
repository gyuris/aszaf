#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Attila Tóth's OpenLyrics batch sorting helper script
#
# dependencies:
#   atollib.py (included)
#   openlyrics.py (included, http://code.google.com/p/openlyrics/source/browse/lib/python/openlyrics.py)
#   pandas (http://pandas.pydata.org/)

__version__ = u'2014.06.28'

from atollib import *
import openlyrics as ol

def renumberSongs(zerosOn, songDir):
    songInfoDF = getSongInfoDF(songDir)
    for songIndex, songInfoS in songInfoDF.iterrows():
        filePath = songInfoS[u'Fájlnév']
        song = ol.Song(filePath)
        for songbook in song.props.songbooks:
            if songbook.name == u'Énekfüzet':
                entryInt = int(songbook.entry)
                if zerosOn:
                    songbook.entry = '%03d' % entryInt
                else:
                    songbook.entry = '%d' % entryInt
                song = setMetaData(song)
                song.write(filePath)

def main():
    parser = argparse.ArgumentParser(description=u'Modify songbook entry of all OpenLyrics files in a directory for easier sorting.')
    parser.add_argument(u'zeros', help=u'leading zeros: on|off')
    parser.add_argument(u'songDir', help=u'song directory')
    
    args = parser.parse_args()
    
    if unicode(args.zeros, encoding=sys.getfilesystemencoding()).lower() == 'on':
        zerosOn = True
    elif unicode(args.zeros, encoding=sys.getfilesystemencoding()).lower() == 'off':
        zerosOn = False
    else:
        raise Exception(u'Error! The first argument must be "on" or "off"!')
    songDir = unicode(args.songDir, encoding=sys.getfilesystemencoding())
    
    renumberSongs(zerosOn, songDir)
    
    return 0

if __name__ == '__main__':
    main()
