This is a [tou.tv](http://tou.tv) console application.

You may list episodes, get information on shows or download shows.

## Usage
    $ ./toutv-cli.py --help

## Example

### Searching
    $ ./toutv-cli.py search bourassa
    Query:
        bourassa
    Results:
        Episode:
            Les Cris de la baie James revendiquent leurs droits
    [...]

### Listing all shows
    $ ./toutv-cli.py list
    [...]
    1597224814 - Campus
    2157713779 - Physique ou chimie
    2166270270 - Pour ne pas les oublier
    [...]

### Listing all episodes from 'Physique ou chimie'
    $ ./toutv-cli.py list 2157713779
    Title:
        Physique ou chimie
    Episodes:
        2161200777 - Égoïsme raisonnable
        2172164238 - La vie en cadeau
        [...]

### Getting more info about a show
    $ ./toutv-cli.py info 2157713779 2161200777
    Title:
        Égoïsme raisonnable     (S01E09)
    Date aired:
        20111028
    Description
        Ruth hérite d’une grosse somme d’argent provenant de l’assurance-vie de ses parents. On découvre que
        Joy est victime de racket.

### Downloading an emission
    $ ./toutv-cli.py fetch -d ~/tou.tv --bitrate MAX 2157713779 2161200777
    Emission and episode:
            Physique ou chimie - Égoïsme raisonnable        (S01E09)
    Downloading 312 segments...
    [ ##                                                                 ] 2%

    $ ls ~/tou.tv/
    Physique ou chimie-Égoïsme raisonnable.ts

    $ mplayer ~/tou.tv/Physique\ ou\ chimie-Égoïsme\ raisonnable.ts

## In case of a problem
Try to delete the cache by removing the file named ".toutv\_cache" in the same directory where you run toutv-cli.py.
    $ rm .toutv_cache

## Dependencies:

- python 2.7
- [pycrypto](https://www.dlitz.net/software/pycrypto/)

## Bugs

Contact Benjamin Vanheuverzwijn <bvanheu@gmail.com>

## Thanks

Thanks to Marc-Etienne M. Leveille
Thanks to Simon Marchi <simark>
