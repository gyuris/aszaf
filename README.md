Ászáf
=====

[![Build Status](https://travis-ci.org/gyuris/aszaf.svg?branch=refactor-build)](https://travis-ci.org/gyuris/aszaf)

Magyar Keresztény OpenLyrics adatbázis

Az adatbázist azért hoztuk létre, hogy a ma használatos legismertebb keresztény 
dicsőítő, imádó, hitvalló és evangelizáló dalokat egy helyen meg lehessen találni 
és letölteni az OpenLP számára (http://openlp.org/) OpenLyrics formátumban 
(http://www.openlyrics.org/). Bár a későbbiekben más jellegű dalszövegek is 
bekerültek a gyűjteménybe, az továbbra is a keresztény liturgikus könnyűzenére koncentrál.
Noha a létrehozók katolikusak, az adatbázis nyitott más felekezet gyűjteményei előtt is, 
hiszen elég sok dalunk máris közös.

A gyűjtemény kiindulópontja a Szent András Evangelizációs Iskola OpenSong 
formátumú „Énekfüzet” adatbázisa volt. Nagy mennyiségű dalszöveget konvertált Riszterer Tamás (@triszterer) 
a „Diatár - Templomi énekvetítő program” (http://diatar.eu) adatbázisából. Köszönet 
Rieth Józsefnek, hogy hozzájárult az énektárak OpenLyrics formátumúvá 
konvertálásához és azok közzétételéhez.

Letöltési oldal: http://gyuris.github.io/aszaf

Ez a mű a [Creative Commons Nevezd meg! - Így add tovább! 4.0 Nemzetközi Licenc (CC BY-SA 4.0)](http://creativecommons.org/licenses/by-sa/4.0/)
feltételei szerint felhasználható, terjeszthető, módosítható.

Használat:

* Csomagolás: ``node util/build.js``
* Ellenőrzés: ``node util/validate.js``
