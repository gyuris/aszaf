/*
TELEPÍTÉS
sudo apt-get install npm p7zip-full
npm install xpath
npm install xmldom
npm install --save node-7z
*/

// csomagok
var fs      = require('fs');
var xpath   = require('xpath');
var dom     = require('xmldom').DOMParser;
var zip      = require('node-7z');

// állandók
const MASTER    = '../master/'; // a mester könyvtár helye a util-hoz viszonyítva
const EXPORT    = '../songbooks/'; // az export könyvtár helye a util-hoz viszonyítva
const NAMESPACE = 'http://openlyrics.info/namespace/2009/song'

// olvassuk az összes fájlt a könyvtárból egyenként
var files = fs.readdirSync(MASTER);
for (var i in files) {
    // kiolvassuk a fájl statisztikai adatait, hogy később az időbélyeget be tudjuk állítani
    var stat = fs.statSync(MASTER + files[i]);
    // megnyitjuk a fájlt
    var data = fs.readFileSync( MASTER + files[i], { encoding : 'UTF-8' });
    // a tartalmát DOM-má alakítjuk
    var doc = new dom().parseFromString(data);
    // kiolvassuk a gyűjteményeket
    var select = xpath.useNamespaces({"song": NAMESPACE});
    var nodes  = select('//song:songbook[@name]', doc);
    // minden gyűjteményre 
    for (j = 0; j < nodes.length; j++) {
        // kiolvassuk a gyűjtemények nevét és a dal számát
        var name  = select("@name", nodes[j])[0].value;
        var entry = select("@entry", nodes[j])[0].value;
        // ha még nincs a gyűjtemény nevével megegyező mappa, akkor létrehozzuk
        if (!fs.existsSync(EXPORT + name)){
            fs.mkdirSync(EXPORT + name);
        }
        // módosítjuk az XML-t
        if ( nodes.length > 1 ) { // ahol csak egy gyűjtemény van, nem kell változtatni semmit
            // lemásoljuk az XML struktúrát
            var copy = new dom().parseFromString(data);
            // töröljük a gyűjteményeket
            var songbooks = select('//song:songbooks', copy)[0];
            while (songbooks.firstChild) {
                songbooks.removeChild(songbooks.firstChild);
            }
            // az aktuálisat belerakjuk
            var clone = nodes[j].cloneNode();
            songbooks.appendChild(clone);
        }
        // kiírjuka  fájl tartalmát gyűjtmény nevével megyegező export mappába
        fs.writeFileSync(EXPORT + name + '/' + files[i], (nodes.length > 1) ? copy.toString() : data); 
        // szinkronizáljuk az új fájl időbélyegét a régihez
        fs.utimesSync(EXPORT + name + '/' + files[i], stat.atime, stat.mtime);
        // log
        //console.log(EXPORT + name + '/' + files[i] + ' -> ' + name + ': ' + entry);
    }
}
// Csomagolás: listázzuk az össze export könyvtárat
var files = fs.readdirSync(EXPORT);
for (var i in files) {
    // minden gyűjteménynek létrehozunk egy 7z csomagot
    var archive = new zip();
    // beolvasunk mindent xml fájlt és elmentjük a gyökérbe a gyűjtemény nevével
    archive.add( '../' + files[i] + '.7z', EXPORT + files[i] + '/*.xml')
    .progress(function (files) {
      console.log( 'Zipped -> %s', files);
    })
    .catch(function (err) {
        console.error(err);
    });
};
