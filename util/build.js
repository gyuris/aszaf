/**
 * TELEPÍTÉS
 * sudo apt-get install npm p7zip-full
 * npm install xpath
 * npm install xmldom
 * npm install --save node-7z
 * npm install json2csv --save
 */

/**
 * Csomagok
 */
var fs       = require('fs');
var xpath    = require('xpath');
var dom      = require('xmldom').DOMParser;
var zip      = require('node-7z');
var json2csv = require('json2csv');

/**
 * Állandók
 */
const MASTER    = process.cwd() + '/master/'; // a mester könyvtár helye a util-hoz viszonyítva
const EXPORT    = process.cwd() + '/songbooks/'; // az export könyvtár helye a util-hoz viszonyítva
const ARCHIVE   = process.cwd(); // a végleges csomagolt fájlok helye
const PACKAGE   = EXPORT + 'Ászáf csomag/'
const NAMESPACE = 'http://openlyrics.info/namespace/2009/song';


/**
 * Feldolgozás
 */
// jegyzék
var index = { global : [], local : [] };
// munkamappa létrehozása
if (!fs.existsSync(EXPORT)){
    fs.mkdirSync(EXPORT);
};
if (!fs.existsSync(PACKAGE)){
    fs.mkdirSync(PACKAGE);
};
// olvassuk az összes fájlt a könyvtárból egyenként
var files = fs.readdirSync(MASTER);
for (var i in files) {
    // nem .xml fájl, pl. README.md
    if ( files[i].toLowerCase().substr(files[i].length - 4) != '.xml' ) {
        continue;
    };
    // kiolvassuk a fájl statisztikai adatait, hogy később az időbélyeget be tudjuk állítani
    var stat = fs.statSync(MASTER + files[i]);
    // megnyitjuk a fájlt
    var file = fs.readFileSync( MASTER + files[i], { encoding : 'UTF-8' });
    // kiírjuk a fájlt az Ászáf csomagba módosítás nélkül
    fs.writeFileSync(PACKAGE + files[i], file);
    // szinkronizáljuk az új fájl időbélyegét a régihez
    fs.utimesSync(PACKAGE + files[i], stat.atime, stat.mtime);
    // a tartalmát DOM-má alakítjuk
    var doc = new dom().parseFromString(file);
    // kiolvassuk a dal adatait
    var select = xpath.useNamespaces({"song": NAMESPACE});
    var nodes  = select('//song:songbook[@name]', doc);
    var data   = {
        title       : ( select('//song:title[@lang="hu"][1]/text()', doc).join() != '' ) ? select('//song:title[@lang="hu"][1]/text()', doc).join() : select('//song:title[1]/text()', doc).join(),
        alternate   : select('//song:title[@lang="hu"][2]/text()', doc).join(),
        original    : select('//song:title[@lang!="hu"][1]/text()', doc).join(),
        words       : select('//song:author[@type="words"]/text()', doc).join(', '),
        music       : select('//song:author[@type="music"]/text()', doc).join(', '),
        translation : select('//song:author[@type="translation"][@lang="hu"]/text()', doc).join(', '),
        copyright   : select('//song:copyright/text()', doc).join(),
        variant     : select('//song:variant/text()', doc).join(),
        songbooks   : []
    }
    // a dalban jegyzett minden gyűjteményre...
    for (j = 0; j < nodes.length; j++) {
        // kiolvassuk a gyűjtemények nevét és a dal számát
        data.songbook = select("@name", nodes[j])[0].value;
        data.entry    = select("@entry", nodes[j])[0].value;
        // ha még nincs a gyűjtemény nevével megegyező mappa, akkor létrehozzuk
        if (!fs.existsSync(EXPORT + data.songbook)){
            fs.mkdirSync(EXPORT + data.songbook);
        };
        // módosítjuk az XML-t
        if ( nodes.length > 1 ) { // ahol csak egy gyűjtemény van, nem kell változtatni semmit
            // lemásoljuk az XML struktúrát
            var copy = new dom().parseFromString(file);
            // töröljük a gyűjteményeket
            var songbooks = select('//song:songbooks', copy)[0];
            while (songbooks.firstChild) {
                songbooks.removeChild(songbooks.firstChild);
            }
            // az aktuálisat belerakjuk
            var clone = nodes[j].cloneNode();
            songbooks.appendChild(clone);
        };
        // kiírjuk a fájl tartalmát gyűjtmény nevével megyegező export mappába
        fs.writeFileSync(EXPORT + data.songbook + '/' + files[i], (nodes.length > 1) ? copy.toString() : file); 
        // szinkronizáljuk az új fájl időbélyegét a régihez
        fs.utimesSync(EXPORT + data.songbook + '/' + files[i], stat.atime, stat.mtime);
        // ha még nincs a gyűjtemény nevével megegyező jegyzék, akkor létrehozzuk
        if (index.local[data.songbook] == undefined) {
            index.local[data.songbook] = new Array();
        }
        // lokális jegyzék feltöltése adatokkal
        index.local[data.songbook].push({
            "Gyűjtemény" : data.songbook,
            "Sorszám" : data.entry,
            "Cím" : data.title,
            "Alternatív cím" : data.alternate,
            "Eredeti cím" : data.original,
            "Szöveg szerzői" : data.words,
            "Zene szerzői" : data.music,
            "Fordítók" : data.translation,
            "Variáns" : data.variant,
            "Copyright" : data.copyright,
            "Állomány" : files[i]
        });
        // globális jegyzékbe szánt többszörös gyűjtemény
        data.songbooks.push(data.songbook + " (" + data.entry + ")");
    };  
    // globális gyűjtemény feltöltése adatokkal
    index.global.push({
        "Cím" : data.title,
        "Alternatív cím" : data.alternate,
        "Eredeti cím" : data.original,
        "Szöveg szerzői" : data.words,
        "Zene szerzői" : data.music,
        "Fordítók" : data.translation,
        "Variáns" : data.variant,
        "Copyright" : data.copyright,
        "Gyűjtemény" : data.songbooks.join(', '),
        "Állomány" : files[i]
    });
};

/**
 * Jegyzék kiírása
 */
// globális jegyzék
json2csv({ data: index.global, fields: [ "Cím", "Alternatív cím", "Eredeti cím", "Szöveg szerzői", "Zene szerzői", "Fordítók", "Variáns", "Copyright", "Gyűjtemény", "Állomány" ] }, function(err, csv) {
    if (err) console.log(err);
    fs.writeFileSync( PACKAGE + '/Tartalomjegyzék.csv', csv);
});
// lokális jegyzék
for (i in index.local) {
    json2csv({ data: index.local[i], fields: [ "Gyűjtemény", "Sorszám", "Cím", "Alternatív cím", "Eredeti cím", "Szöveg szerzői", "Zene szerzői", "Fordítók", "Variáns", "Copyright", "Állomány" ] }, function(err, csv) {
        if (err) console.log(err);
        fs.writeFileSync( EXPORT + i + '/Tartalomjegyzék.csv', csv);
    });
};

/**
 * Csomagolás
 */
// az aktuális futási könyvtárt megváltoztatjuk, hogy a zip csomagokban ne legyen benne a songbook mappa
process.chdir(EXPORT);
// listázzuk az összes export könyvtárat
var files = fs.readdirSync(process.cwd());
for (var i in files) {
    if ( !fs.lstatSync(files[i]).isDirectory() )  {
        continue;
    };
    // minden gyűjteménynek létrehozunk egy 7z csomagot
    var archive = new zip();
    // beolvasunk mindent xml fájlt és elmentjük a gyökérbe a gyűjtemény nevével
    archive.add( files[i] + '.7z', files[i], {
      wildcards: [ '*.xml', '*.csv' ]
    })
    .progress(function (files) {
    })
    .catch(function (err) {
        console.error(err);
    });
    console.log('Csomagolva: ' + files[i]);
};
