#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Attila Tóth's OpenLyrics batch update script
#
# dependencies:
#   atollib.py (included)
#   openlyrics.py (included, http://code.google.com/p/openlyrics/source/browse/lib/python/openlyrics.py)
#   pandas (http://pandas.pydata.org/)

__version__ = u'2014.06.28'

from atollib import *
import openlyrics as ol
import pandas as pd
import shutil

def getSongDataDF(songDataTablePath):
    songDataDF = pd.read_csv(songDataTablePath, sep='\t', dtype=unicode, na_values=[], keep_default_na=False, encoding='utf-8')
    return songDataDF

def getOutFileName(songDataS):
    titleText = songDataS[u'Kezdő sor'].strip()
    authorName = songDataS[u'Szöveg szerzői'].strip()
    translatorName = songDataS[u'Fordítók'].strip()
    variant = songDataS[u'Szövegvariáns'].strip()
    
    fileNameParts = [titleText]
    if authorName or translatorName or variant:
        fileNameParts.append(u' (')
        for additionalInfo in (authorName, translatorName, variant):
            if additionalInfo:
                fileNameParts.append(additionalInfo)
                fileNameParts.append(u', ')
        fileNameParts.pop() # remove trailing u', '
        fileNameParts.append(u')')
    fileNameParts.append(u'.xml')
    
    fileName = ''.join(fileNameParts)
    
    # remove avoidable characters
    for avidableChar in [u'/', u'\\', u':']:
        fileName = fileName.replace(avidableChar, u'')
    
    # strip whitespace
    #~ fileName = fileName.strip()
    
    return fileName

def splitOrigTitleText(origTitleText):
    origTitleTextParts = origTitleText.split(u' [')
    origTitle = origTitleTextParts[0]
    if len(origTitleTextParts) > 1:
        keyline = origTitleTextParts[1].strip(u']')
    else:
        keyline = u''
    
    return origTitle, keyline

def updateSong(song, songDataS):
    # get raw song data
    songbookEntry = songDataS[u'#'].strip()
    titleText = songDataS[u'Kezdő sor'].strip()
    altTitleText = songDataS[u'Alternatív cím'].strip()
    textType = songDataS[u'Típus'].strip()
    authorName1 = songDataS[u'Szöveg szerzői'].strip()
    authorName2 = songDataS[u'Zene szerzői'].strip()
    origTitleText = songDataS[u'Eredeti cím'].strip()
    translatorName = songDataS[u'Fordítók'].strip()
    variant = songDataS[u'Szövegvariáns'].strip()
    songCopyright = songDataS[u'Kiadó / Copyright'].strip()
    
    # update song object
    # titles
    song.props.titles = [] # delete possibly existing title information
    song.props.titles.append(ol.Title(text=titleText, lang=u'hu')) # (first) title is assumed to be Hungarian
    if altTitleText:
        song.props.titles.append(ol.Title(text=altTitleText, lang=u'hu')) # alternative (second) title is assumed to be Hungarian
    if origTitleText:
        origTitle, keyline = splitOrigTitleText(origTitleText)
        song.props.titles.append(ol.Title(text=origTitle)) # do not assume language of the original title
    
    # authors
    # for now, do not split author fields
    # this probably should be corrected later
    song.props.authors = [] # delete possibly existing author information
    separateAuthors = False
    if authorName1 and authorName2:
        separateAuthors = True
    if separateAuthors:
        song.props.authors.append(ol.Author(name=authorName1, type_=u'words'))
        song.props.authors.append(ol.Author(name=authorName2, type_=u'music'))
    elif authorName1:
        song.props.authors.append(ol.Author(name=authorName1))
    elif authorName2:
        song.props.authors.append(ol.Author(name=authorName2, type_=u'music'))
    if translatorName:
        song.props.authors.append(ol.Author(name=translatorName, type_=u'translation', lang=u'hu')) # assume Hungarian translation
    
    # variant
    if variant:
        song.props.variant = variant
    else: # delete possibly existing variant information
        song.props.variant = u''
    
    # copyright
    if songCopyright:
        song.props.copyright = songCopyright
    else: # delete possibly existing copyright information
        song.props.copyright = u''
    
    # songbook
    song.props.songbooks = [] # delete possibly existing songbook information
    song.props.songbooks.append(ol.Songbook(name=u'Énekfüzet', entry=songbookEntry))
    
    return song
    
def updateSongs(args):
    inDirPath = unicode(args.inDir, encoding=sys.getfilesystemencoding())
    outDirPath = unicode(args.outDir, encoding=sys.getfilesystemencoding())
    newSongDataTablePath = unicode(args.songTable, encoding=sys.getfilesystemencoding())
    
    if not os.path.isdir(outDirPath):
        os.mkdir(outDirPath)
    
    inSongInfoDF = getSongInfoDF(inDirPath)
    newSongDataDF = getSongDataDF(newSongDataTablePath)
    
    for newSongDataIndex, newSongDataS in newSongDataDF.iterrows():
        songbookEntry = newSongDataS[u'#']
        outFileName = getOutFileName(newSongDataS)
        outFilePath = os.path.join(outDirPath, outFileName)
        if songbookEntry: # skip songs without songbookEntry
            print songbookEntry # process indicator
            if len(inSongInfoDF[inSongInfoDF[u'Sorszám']==songbookEntry].index) > 0: # input file exists
                inFilePath = inSongInfoDF[inSongInfoDF[u'Sorszám']==songbookEntry].iloc[0][u'Fájlnév']
                shutil.copy2(inFilePath, outFilePath)
                song = ol.Song(outFilePath)
            else: # input file doesn't exist, create new file
                song = ol.Song()
            updateSong(song, newSongDataS)
            song = setMetaData(song)
            song.write(outFilePath)

def main():
    parser = argparse.ArgumentParser(description=u'Update and/or create OpenLyrics files based on tabular song data.')
    parser.add_argument(u'inDir', help=u'input directory')
    parser.add_argument(u'outDir', help=u'output directory')
    parser.add_argument(u'songTable', help=u'table of new song data')
    
    args = parser.parse_args()
    
    updateSongs(args)
    
    return 0

if __name__ == '__main__':
    main()
