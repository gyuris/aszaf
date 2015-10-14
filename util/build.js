/*
TELEPÍTÉS
sudo apt-get install npm
npm install xpath
npm install xmldom
*/

// csomagok
var fs      = require('fs');
var xpath   = require('xpath');
var dom     = require('xmldom').DOMParser;

// állandók
const MASTER    = '../master/'; // a mester könyvtár helye a util-hoz viszonyítva
const EXPORT = '../songbooks/'; // az export könyvtár helye a util-hoz viszonyítva

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
    var select = xpath.useNamespaces({"song": "http://openlyrics.info/namespace/2009/song"});
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
        // kiírjuka  fájl tartalmát gyűjtmény nevével megyegező export mappába
        fs.writeFileSync(EXPORT + name + '/' + files[i], data); 
        // szinkronizáljuk az új fájl időbélyegét a régihez
        fs.utimesSync(EXPORT + name + '/' + files[i], stat.atime, stat.mtime);
        // log
        console.log(EXPORT + name + '/' + files[i] + ' -> ' + name + ': ' + entry);
    }
}
