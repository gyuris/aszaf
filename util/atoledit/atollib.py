#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Attila Tóth's OpenLyrics Library
#
# dependencies:
#   openlyrics.py (included, http://code.google.com/p/openlyrics/source/browse/lib/python/openlyrics.py)
#   lxml (http://lxml.de/)
#   pandas (http://pandas.pydata.org/)
#   YAD (http://sourceforge.net/projects/yad-dialog/)

# TODO
# do not hard wire atoledit.py
# CBE fileds should remember their edited content and populate it on next window opening
# Shortcut to verse order and last added Title / Author / Verse
# Handle file names containing apostrophe ' (e.g. 131, Ó, Jah')

__version__ = u'2014.06.28'

import openlyrics as ol
import sys, subprocess, argparse, os, ConfigParser
from collections import defaultdict
from lxml import etree
from tempfile import mkstemp
from datetime import datetime
import pandas as pd

class SongInfo():
    def __init__(self, titleText=u'', authorName=u'', songbookEntry=u'', filePath=u'', mTime=u'', status=u''):
        self.titleText = titleText
        self.authorName = authorName
        self.songbookEntry = songbookEntry
        self.filePath = filePath
        self.mTime = mTime
        self.status = status

class Fields():
    def __init__(self):
        self.fieldContents = []
        self.resultKeys = []

    def appendFieldContentsAndResultKeys(self, fieldContent, resultKey):
        self.fieldContents.append(fieldContent)
        self.resultKeys.append(resultKey)

def getSchema(confFile=u'atollib.ini'):
    config = ConfigParser.ConfigParser()
    config.read(confFile)
    schema = config.get(u'Validation', u'schema')
    return schema

def getFieldLabel(label, fieldType=None):
    if not fieldType:
        return u'--field=%s' % (label)
    else:
        return u'--field=%s:%s' % (label, fieldType)

def getFieldText(text):
    if text is not None:
        #~ return '%s' % text.encode('utf8')
        return u'%s' % text
    else:
        return u''

def getLang(lang):
    if lang == u'hu':
        return u'!^hu!en'
    elif lang == u'en':
        return u'!hu!^en'
    else:
        return u'^!hu!en'

def getAuthorType(authorType):
    if authorType == u'words':
        return u'!^words!music!translation'
    elif authorType == u'music':
        return u'!words!^music!translation'
    elif authorType == u'translation':
        return u'!words!music!^translation'
    else:
        return u'^!words!music!translation'

def createNewSong():
    song = ol.Song()
    song.props.titles.append(ol.Title())
    song.props.authors.append(ol.Author())
    song.verses.append(ol.Verse())
    song.verses[0].lines.append(ol.Lines())
    song.verses[0].lines[0].lines.append(ol.Line(u''))
    song.props.songbooks.append(ol.Songbook())
    return song

def setMetaData(song):
    song.modifiedIn = u'atollib.py %s (openlyrics.py %s)' % (__version__, ol.__version__)
    return song

def editSongByYad(song=None, fileName=u''):
    if song is None:
        song = createNewSong()
    
    # fixed dialog parameters
    # if the window grows bigger, than the screen, add these options:
        #~ u'--maximized',
        #~ u'--scroll',
    dBase = (u'yad',
        u'--form',
        u'--title=Ének szerkesztése',
        u'--width 1000',
        u'--maximized',
        u'--scroll',
        u'--center',
        u'--window-icon=gtk-edit',
        u'--button=Cí_m hozzáadása:2',
        u'--button=_Szerző hozzáadása:4',
        u'--button=_Versszak hozzáadása:8',
        u'--button=gtk-cancel:1',
        u'--button=gtk-ok:0',
        u'--buttons-layout=spread',
        u'--columns=3')
    
    # prepare variable dialog parameters
    titleTexts = []
    titleTextLabels = []
    titleLangs = []
    titleLangLabels = []
    authorNames = []
    authorNameLabels = []
    authorLangs = []
    authorLangLabels = []
    authorTypes = []
    authorTypeLabels = []
    verses = []
    verseLabels = []
    verseNames = []
    verseNameLabels = []
    for i, title in enumerate(song.props.titles, start=1):
        titleTexts.append(title.text)
        titleTextLabels.append(u'%d. cím' % i)
        titleLangs.append(title.lang)
        titleLangLabels.append(u'%d. c. nyelve' % i)
    for j, author in enumerate(song.props.authors, start=1):
        authorNames.append(author.name)
        authorNameLabels.append(u'%d. szerző' % j)
        authorLangs.append(author.lang)
        authorLangLabels.append(u'%d. sz. nyelve' % j)
        authorTypes.append(author.type)
        authorTypeLabels.append(u'%d. sz. típusa' % j)
    for k, verse in enumerate(song.verses, start=1):
        verses.append(verse.lines[0].__unicode__())
        verseLabels.append(u'%d. versszak' % k)
        verseNames.append(verse.name)
        verseNameLabels.append(u'%d. v. azon.' % k)
    
    # prepare field labels
    fieldLabels = []
    for titleTextLabel in titleTextLabels:
        fieldLabels.append(getFieldLabel(titleTextLabel))
    for authorNameLabel in authorNameLabels:
        fieldLabels.append(getFieldLabel(authorNameLabel))
    fieldLabels.append(getFieldLabel(u'Szövegvariáns'))
    fieldLabels.append(getFieldLabel(u'Énekfüzet'))
    for i in range(len(song.verses)):
        fieldLabels.append(getFieldLabel(u' ', u'LBL'))
    for titleLangLabel in titleLangLabels:
        fieldLabels.append(getFieldLabel(titleLangLabel, u'CBE'))
    for authorLangLabel in authorLangLabels:
        fieldLabels.append(getFieldLabel(authorLangLabel, u'CBE'))
    fieldLabels.append(getFieldLabel(u'Copyright'))
    fieldLabels.append(getFieldLabel(u'Sorszám'))
    for verseNameLabel in verseNameLabels:
        fieldLabels.append(getFieldLabel(verseNameLabel))
    for i in range(len(song.props.titles)):
        fieldLabels.append(getFieldLabel(u' ', u'LBL'))
    for authorTypeLabel in authorTypeLabels:
        fieldLabels.append(getFieldLabel(authorTypeLabel, u'CB'))
    fieldLabels.append(getFieldLabel(u'Fájlnév'))
    fieldLabels.append(getFieldLabel(u'Versszaksorrend'))
    for verseLabel in verseLabels:
        fieldLabels.append(getFieldLabel(verseLabel, u'TXT'))
    
    # prepare field contents and keys for evaluating results
    fields = Fields()
    for titleText in titleTexts:
        fields.appendFieldContentsAndResultKeys(getFieldText(titleText), u'titleText')
    for authorName in authorNames:
        fields.appendFieldContentsAndResultKeys(getFieldText(authorName), u'authorName')
    fields.appendFieldContentsAndResultKeys(getFieldText(song.props.variant), u'variant')
    fields.appendFieldContentsAndResultKeys(getFieldText(song.props.songbooks[0].name), u'songbookName')
    for i in range(len(song.verses)):
        fields.appendFieldContentsAndResultKeys(u'', u'junk')
    for titleLang in titleLangs:
        fields.appendFieldContentsAndResultKeys(getLang(getFieldText(titleLang)), u'titleLang')
    for authorLang in authorLangs:
        fields.appendFieldContentsAndResultKeys(getLang(getFieldText(authorLang)), u'authorLang')
    fields.appendFieldContentsAndResultKeys(getFieldText(song.props.copyright), u'copyright')
    fields.appendFieldContentsAndResultKeys(getFieldText(song.props.songbooks[0].entry), u'songbookEntry')
    for verseName in verseNames:
        fields.appendFieldContentsAndResultKeys(getFieldText(verseName), u'verseName')
    for i in range(len(song.props.titles)):
        fields.appendFieldContentsAndResultKeys(u'', u'junk')
    for authorType in authorTypes:
        fields.appendFieldContentsAndResultKeys(getAuthorType(getFieldText(authorType)), u'authorType')
    fields.appendFieldContentsAndResultKeys(fileName, u'fileName')
    fields.appendFieldContentsAndResultKeys(getFieldText(u' '.join(song.props.verse_order)), u'verse_order')
    for verse in verses:
        fields.appendFieldContentsAndResultKeys(getFieldText(verse), u'verse')
    
    # show the dialog, get results
    yadCommandParts = dBase + tuple(fieldLabels) + tuple(fields.fieldContents)
    results = None
    try:
        p = subprocess.Popen(yadCommandParts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = p.communicate()
        results = unicode(stdoutdata, encoding=sys.getfilesystemencoding())
        returncode = p.returncode
    except subprocess.CalledProcessError as e:
        returncode = e.returncode
    
    return song, fields, returncode, results

def updateSong(song, fields, results):
    resultsD = defaultdict(list)
    resultsL = zip(fields.resultKeys, results.split(u'|'))
    for resultKey, result in resultsL:
        resultsD[resultKey].append(result)
        #~ print u'"%s"' % resultKey, u'"%s"' % result
    for i, titleText, titleLang in zip(range(len(resultsD[u'titleText'])), resultsD[u'titleText'], resultsD[u'titleLang']):
        song.props.titles[i].text = titleText
        song.props.titles[i].lang = titleLang
    for i, authorName, authorLang, authorType in zip(range(len(resultsD[u'authorName'])), resultsD[u'authorName'], resultsD[u'authorLang'], resultsD[u'authorType']):
        song.props.authors[i].name = authorName
        song.props.authors[i].lang = authorLang
        song.props.authors[i].type = authorType
    for i, verseName, verse in zip(range(len(resultsD[u'verseName'])), resultsD[u'verseName'], resultsD[u'verse']):
        lines = ol.Lines()
        for j, line in enumerate(verse.split(u'\\n')):
            lines.lines.append(ol.Line(line))
        song.verses[i].lines[0] = lines
        song.verses[i].name = verseName
    song.props.variant = resultsD[u'variant'][0]
    song.props.songbooks[0].name = resultsD[u'songbookName'][0]
    song.props.copyright = resultsD[u'copyright'][0]
    song.props.songbooks[0].entry = resultsD[u'songbookEntry'][0]
    song.props.verse_order = resultsD[u'verse_order'][0].split(u' ')
    fileName = resultsD[u'fileName'][0]
    
    return song, fileName

def processResults(song, fields, returncode, results, fileName):
    if returncode in [0, 2, 4, 8]: # apply modifications, update song object
        song, fileName = updateSong(song, fields, results)
    
    return song, fileName, returncode

def editSong(song=None, fileName=u'', songDir=u''):
    while True:
        song, fields, returncode, results = editSongByYad(song, fileName)
        #~ print returncode, type(song)
        song, fileName, returncode = processResults(song, fields, returncode, results, fileName)
        
        # exit code pedendent actions
        if returncode == 0: # OK
            # check for empty file name
            if fileName == u'':
                subprocess.call([u'yad', u'--title=Üres fájlnév', u'--center', u'--window-icon=gtk-dialog-error', u'--image=gtk-dialog-error', u'--button=gtk-ok', u'--text=Üres fájlnév! Kérlek javítsd!'])
                continue
            # check verse order
            if not isVerseOrderOK(song): # verse order is NOT OK, offer chance to correct it
                corrVerseOrder = subprocess.call([u'yad', u'--title=Hibás versszaksorrend', u'--center', u'--window-icon=gtk-dialog-warning', u'--image=gtk-dialog-warning', u'--text=Hibás a versszaksorrend! Javítod?'])
                if corrVerseOrder == 0: # OK, edit the song again
                    continue
                else: # do not correct it
                    pass
            
            # write temporary output file
            # Using tempfile.mkstemp correctly
            # http://www.logilab.org/17873
            tmpfd, tmpfPath = mkstemp(suffix=u'.xml', dir=songDir)
            song = setMetaData(song)
            song.write(tmpfPath)
            
            # validate temporary output file
            try:
                validateXML(tmpfPath, getSchema())
            except: # validation NOT OK
                exctype, value = sys.exc_info()[:2]
                excMsg = u'%s: %s' % (unicode(exctype), value)
                
                # display info, offer chance to correct the song
                corrInvalid = subprocess.call([u'yad', u'--title=Invalid XML fájl', u'--center', u'--window-icon=gtk-dialog-warning', u'--image=gtk-dialog-warning', u'--no-markup', u'--text=Invalid XML fájl:\n%s\n\n%s\n\nJavítod?' % (tmpfPath, excMsg)])
                if corrInvalid == 0: # OK, edit the song again
                    continue
                else: # do not correct it
                    pass
            finally:
                # remove temporary output file
                os.close(tmpfd)
                os.remove(tmpfPath)
            
            # write output file
            #~ song = setMetaData(song)
            song.write(os.path.join(songDir, fileName))
        elif returncode in [1, 252]: # Cancel OR Esc/Windows closed
            # do not update song object, do not write output file
            pass
        elif returncode == 2: # Add title
            song.props.titles.append(ol.Title())
        elif returncode == 4: # Add author
            song.props.authors.append(ol.Author())
        elif returncode == 8: # Add verse
            song.verses.append(ol.Verse())
            song.verses[-1].lines.append(ol.Lines())
            song.verses[-1].lines[0].lines.append(ol.Line(u''))
        else:
            raise Exception(u'Error! Unknown exit code: %d. See YAD documentation (man yad) for details!' % returncode)
        
        # finish editing on OK, Cancel, or Esc/Windows closed
        if returncode not in [2, 4, 8]:
            break
    
    return song, fileName, songDir

def isVerseOrderOK(song):
    voNames = set(song.props.verse_order)
    verseNames = set([verse.name for verse in song.verses])
    return voNames == verseNames

def validateXML(xml_file, relaxng_file):
    relaxng_doc = etree.parse(relaxng_file)
    xml_doc = etree.parse(xml_file)
    relaxng = etree.RelaxNG(relaxng_doc)
    relaxng.assertValid(xml_doc)

def check(filePath, interactive=False):
    songDir, fileName = os.path.split(filePath)
    status = 0
    # validate file
    try:
        validateXML(filePath, getSchema())
    except: # validation NOT OK
        status += 1
        if interactive:
            exctype, value = sys.exc_info()[:2]
            excMsg = u'%s: %s' % (unicode(exctype), value)
            
            # display info, offer chance to correct the song
            corrInvalid = subprocess.call([u'yad', u'--title=Invalid XML fájl', u'--center', u'--window-icon=gtk-dialog-warning', u'--image=gtk-dialog-warning', u'--no-markup', u'--text=Invalid XML fájl!\n\n%s\n\nJavítod?' % excMsg])
            if corrInvalid == 0: # OK, edit the song
                song = ol.Song(filePath)
                song, fileName, songDir = editSong(song, fileName, songDir)
            else: # do not correct it
                pass
    
    # check verse order
    song = ol.Song(filePath)
    if not isVerseOrderOK(song): # verse order is NOT OK
        status += 2
        if interactive: # offer chance to correct it
            corrVerseOrder = subprocess.call([u'yad', u'--title=Hibás versszaksorrend', u'--center', u'--window-icon=gtk-dialog-warning', u'--image=gtk-dialog-warning', u'--text=Hibás a versszaksorrend! Javítod?'])
            if corrVerseOrder == 0: # OK, edit the song
                song = ol.Song(filePath)
                song, fileName, songDir = editSong(song, fileName, songDir)
            else: # do not correct it
                pass
    
    return status

def getFilesInfo(songDir):
    items = os.listdir(songDir)
    xmlFiles = []
    for item in items:
        itemPath = os.path.join(songDir, item)
        if os.path.isfile(itemPath): # select files
            fRoot, fExt = os.path.splitext(itemPath)
            if fExt == u'.xml': # select files with .xml extension
                mTime = unicode(datetime.fromtimestamp(os.stat(itemPath).st_mtime).strftime(u'%Y.%m.%d %H:%M:%S'))
                songInfo = SongInfo(filePath=itemPath, mTime=mTime)
                xmlFiles.append(songInfo)
    
    return xmlFiles

#~ def getSongInfo(item, songInfo=None):
def getSongInfo(songInfo):
    #~ #if isinstance(item, str) or isinstance(item, unicode):
    #~ if isinstance(item, unicode):
        #~ song = ol.Song(item)
    #~ else:
        #~ song = item
    #~ 
    #~ if songInfo is None:
        #~ songInfo = SongInfo()
    
    song = ol.Song(songInfo.filePath)
    
    # first title
    if len(song.props.titles) > 0:
        songInfo.titleText = unicode(song.props.titles[0].text)
    else:
        songInfo.titleText = u''
    
    # first author
    if len(song.props.authors) > 0:
        songInfo.authorName = unicode(song.props.authors[0].name)
    else:
        songInfo.authorName = u''
    
    # first songbook entry
    if len(song.props.songbooks) > 0:
        songInfo.songbookEntry = unicode(song.props.songbooks[0].entry)
    else:
        songInfo.songbookEntry = u''
    
    # status
    songInfo.status = unicode(check(songInfo.filePath))
    
    return songInfo

def getSongInfoDF(songDir, cacheUsagePermitted=True):
    xmlFiles = getFilesInfo(songDir)
    for i, songInfo in enumerate(xmlFiles):
        useCache = False
        if cacheUsagePermitted: # cache usage permitted
            cachedSongInfoDF = readCache(songDir)
            if cachedSongInfoDF is not None: # cache exists
                cachedSongInfoDFFiltered = cachedSongInfoDF[cachedSongInfoDF[u'Fájlnév']==songInfo.filePath]
                if len(cachedSongInfoDFFiltered.index) == 1: # file found in cache
                    cachedSongInfoS = cachedSongInfoDFFiltered.iloc[0]
                    if cachedSongInfoS[u'Utolsó módosítás'] == songInfo.mTime: # file was not modified since caching
                        useCache = True
        if useCache:
            songInfo.titleText = cachedSongInfoS[u'Cím']
            songInfo.authorName = cachedSongInfoS[u'Szerző']
            songInfo.songbookEntry = cachedSongInfoS[u'Sorszám']
            songInfo.status = cachedSongInfoS[u'Státusz']
            xmlFiles[i] = songInfo
            #~ print u'from cache:', songInfo.filePath
        else:
            xmlFiles[i] = getSongInfo(songInfo)
            #~ print u'from XML:', xmlFiles[i].filePath
        
    songInfoDF = pd.DataFrame()
    for songInfo in xmlFiles:
        # convert SongInfo object to a pandas Series object
        songInfoS = pd.Series([songInfo.songbookEntry, \
                    songInfo.titleText, \
                    songInfo.authorName, \
                    u'\\\\\\\\', \
                    songInfo.filePath, \
                    u'\\\\\\\\', \
                    songInfo.mTime, \
                    songInfo.status], \
                    index=[u'Sorszám', \
                    u'Cím', \
                    u'Szerző', \
                    u'Separator1', \
                    u'Fájlnév', \
                    u'Separator2', \
                    u'Utolsó módosítás', \
                    u'Státusz'])

        # append song info data to the DataFrame object
        songInfoDF = songInfoDF.append(songInfoS, ignore_index=True)
    
    # sort by titleText, than by mTime
    songInfoDF = songInfoDF.sort_index(by=[u'Cím', u'Utolsó módosítás'])
    
    return songInfoDF

def getCacheFilePath(songDir, cacheFileName=u'.atollib.cache.csv'):
    return os.path.join(songDir, cacheFileName)

def writeCache(songInfoDF, songDir, cacheFileName=u'.atollib.cache.csv'):
    cacheFileName = getCacheFilePath(songDir, cacheFileName)
    songInfoDF.to_csv(cacheFileName, index=False, encoding='utf-8')

def readCache(songDir, cacheFileName=u'.atollib.cache.csv'):
    cacheFileName = getCacheFilePath(songDir, cacheFileName)
    if os.path.isfile(cacheFileName):
        songInfoDF = pd.read_csv(cacheFileName, dtype=unicode, na_values=[], keep_default_na=False, encoding='utf-8')
    else:
        songInfoDF = None
    
    return songInfoDF

def getDialogFieldContents(songInfoDF):
    dialogFieldContents = []
    columns = [u'Sorszám', \
            u'Cím', \
            u'Szerző', \
            u'Separator1', \
            u'Fájlnév', \
            u'Separator2', \
            u'Utolsó módosítás', \
            u'Státusz']
    for songIndex, songInfoS in songInfoDF.iterrows():
        for column in columns:
            if column == u'Fájlnév':
                songPath, songFileName = os.path.split(songInfoS[column])
                dialogFieldContents.append(songFileName)
            else:
                dialogFieldContents.append(songInfoS[column])
    
    return dialogFieldContents

def editDirByYad(dialogFieldContents, songDir, xmlCount):
    # fixed dialog parameters
    # if the window grows bigger, than the screen, add these options:
        #~ u'--maximized',
        #~ u'--scroll',
    dBase = (u'yad',
        u'--list',
        u'--title=%s (%d) - Éneklista' % (songDir, xmlCount),
        u'--width 1000',
        u'--maximized',
        u'--scroll',
        u'--center',
        u'--window-icon=gtk-dnd-multiple',
        u'--button=gtk-edit:2',
        u'--button=gtk-new:4',
        u'--button=gtk-delete:8',
        u'--button=gtk-refresh:16',
        u'--button=gtk-close:0',
        u'--buttons-layout=spread',
        #~ u'--dclick-action=./editselected.sh "%%s" %s' % songDir,
        # shell: echo "$1" | sed -r 's/[^\]+\\\\'"'"' '"'"'//' | sed -r 's/'"'"' '"'"'\\\\.+//' > t.txt
        #~ u"""--dclick-action=/bin/sh -c "echo %s | sed -r 's/[^\]+\\\\\\\\\\\\\\\\ //' | sed -r 's/ \\\\\\\\\\\\\\\\.+//' > v.txt\"""",
        u"--dclick-action=python2 -c \"import os, subprocess; subprocess.call(['./atoledit.py', os.path.join('{0}', %s.split('\\\\\\\\')[1])])\"".format(songDir),
        u'--column=Sorszám',
        u'--column=Cím',
        u'--column=Szerző',
        u'--column=Separator1:HD',
        u'--column=Fájlnév',
        u'--column=Separator2:HD',
        u'--column=Utolsó módosítás',
        u'--column=Státusz',
        u'--search-column=2')
    
    # show the dialog, get results
    yadCommandParts = dBase
    results = None
    try:
        p = subprocess.Popen(yadCommandParts, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = p.communicate(input=u'\n'.join(dialogFieldContents).encode(sys.getfilesystemencoding()))
        results = unicode(stdoutdata, encoding=sys.getfilesystemencoding())
        returncode = p.returncode
    except subprocess.CalledProcessError as e:
        returncode = e.returncode
    
    return returncode, results

def getSongFileName(yadOutput):
    outParts = yadOutput.split(u'|\\\\\\\\|')
    if len(outParts) > 1:
        return outParts[1]
    else:
        return u''

def editDir(songDir):
    while True:
        songInfoDF = getSongInfoDF(songDir)
        writeCache(songInfoDF, songDir)
        dialogFieldContents = getDialogFieldContents(songInfoDF)
        xmlCount = len(songInfoDF.index)
        returncode, results = editDirByYad(dialogFieldContents, songDir, xmlCount)
        #~ print returncode
        fileName = getSongFileName(results)
        songPath = os.path.join(songDir, fileName)
        
        if fileName: # a song has been selected
            if returncode == 2: # Edit song
                song = ol.Song(songPath)
                song, fileName, songDir = editSong(song, fileName, songDir)
            elif returncode == 8: # Delete song
                os.remove(songPath)
        else: # no song has been selected
            if returncode in [0, 252]: # Close OR Esc/Windows closed
                pass
            elif returncode == 2: # Edit song
                pass # can not edit, if no song has been selected
            elif returncode == 4: # New song
                song, fileName, songDir = editSong(songDir=songDir)
            elif returncode == 8: # Delete song
                pass # can not delete, if no song has been selected
            elif returncode == 16: # Refresh song list
                pass # song list will be refreshed in the new iteration
            else:
                raise Exception(u'Error! Unknown exit code: %d. See YAD documentation (man yad) for details!' % returncode)
        
        # finish editing on Close or Esc/Windows closed
        if returncode not in [2, 4, 8, 16]:
            break
    
    return returncode, results

def main():
    
    return 0

if __name__ == '__main__':
    main()
