/**
 * TELEPÍTÉS
 * sudo apt install xmllint
 * mkdir node_modules
 * npm install git+ssh://git@github.com:kripken/xml.js.git
 * npm install console.table
 * FUTTATÁS
 * node util/validate.js
 */

/**
 * Csomagok
 */

'use strict';

const fs         = require('fs');
const xmllint    = require('xmllint');
const cTable     = require('console.table');
const folders    = [
  './master/',
  './other/Cserkészek daloskönyve/',
  './other/Gyerekdalok/',
  './other/Sárga könyv (akkordos)/',
  './other/Taize-i énekek/',
  './other/A Hit Hangjai/',
  './other/Baptista Énekanyagok/',
  './other/Gyülekezeti Énekeskönyv/',
  './classical/Adventi és karácsonyi/',
  './classical/Dicsérjétek az Urat!/',
  './classical/Éneklő Egyház/',
  './classical/Erdélyi gyűjtemény/',
  './classical/Graduale Hungaricum/',
  './classical/Harmatozzatok, egek!/',
  './classical/Imák és válaszok/',
  './classical/Latin imák/',
  './classical/Ordinárium/',
  './classical/Szentkúti énekek/',
  './classical/Szentségimádás/',
  './classical/Szent Vagy, Uram!/',
  './classical/Ujjongj az úrnak! - népdalzsoltárok/',
  './classical/Zsolozsma/',
  './classical/Zsoltár - páratlan hétköznap/',
  './classical/Zsoltár - páros hétköznap/',
  './classical/Zsoltár - ünnepek/',
  './classical/Zsoltár - vasárnapok/'
];
const schema   = fs.readFileSync('./util/openlyrics-0.8.rng').toString();
var   report   = [];

/**
 * Feldolgozás
 */
function validateFolder(sPath) {
  // olvassuk az összes fájlt a könyvtárból egyenként
  var files = fs.readdirSync(sPath);
  var count = 0;
  for (var i in files) {
    // nem .xml fájl, pl. README.md
    if (files[i].toLowerCase().substr(files[i].length - 4) != '.xml') {
      continue;
    }
    // ellenőrzés a fájlt
    var sLog = "Validating... ";
    var oError = xmllint.validateXML({
      xml: fs.readFileSync(sPath + files[i], { encoding : 'UTF-8' }).toString(),
      format: 'rng',
      schema: schema
    }).errors;
    if ( oError == null ) {
      sLog += "OK"
    }
    else {
      sLog += "INVALID\n"
      sLog += oError.join("\n");
      count++;
    }
    process.stdout.write(sLog + ' ' + sPath + files[i] );
  }
  if (count > 0) {
    process.stdout.write("\nINVALID: " + count + "/" + i);
  }
  report.push( { name : sPath.substring(2, sPath.length-1), total: i, valid: i-count, invalid: count });
}

folders.forEach(function(item) {
  validateFolder(item);
});
console.log("\n**************************************************************************************");
console.table(report);
