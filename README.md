[![Build Status](https://travis-ci.org/bvanheu/pytoutv.svg?branch=master)](https://travis-ci.org/bvanheu/pytoutv)

(Voir [`README.fr.md`](README.fr.md) pour une version française.)

***pytoutv*** is a [TOU.TV](http://tou.tv/) client library written in
Python 3.

This repository also holds a command line interface.

pytoutv, thanks to TOU.TV's public API (see
[`toutv/config.py`](toutv/config.py) for public URLs), is able to
retrieve lists of emissions (shows) and episodes, get emissions and episodes
informations and fetch any video file publicly distributed by the TOU.TV
service. Informations, including video files, downloaded using pytoutv are
for personal use only and should not be redistributed unless otherwise
authorized by TOU.TV owners.

The pytoutv project is not affiliated, connected or associated with the Canadian
Broadcasting Corporation or CBFT-DT. The Canadian Broadcasting Corporation or
CBFT-DT do not sponsor, approve of, or endorse pytoutv.

_Note_: although this is pytoutv 2, there's no such thing as pytoutv 1. This
project was previously known as _Tou.tv-console-application_ and targeted
at Python 2. Its refactoring and renaming to pytoutv led to its version 2.
The CLI remains mostly compatible with the previous version.


Dependencies
============

pytoutv needs:

  * Python 3.3+, with:
    * [PyCrypto](https://www.dlitz.net/software/pycrypto/)
      ([available on PyPI](https://pypi.python.org/pypi/pycrypto))
    * [Requests](http://python-requests.org/)
      ([available on PyPI](https://pypi.python.org/pypi/requests))
    * [setuptools](https://pythonhosted.org/setuptools/)
      ([available on PyPI](https://pypi.python.org/pypi/setuptools))

Optional dependencies:

  * termcolor
    ([available on PyPI](https://pypi.python.org/pypi/termcolor)):
    colors in terminal (CLI)
  * [PyQt4](http://www.riverbankcomputing.com/software/pyqt/download):
    Qt interface

pytoutv is known to work on Ubuntu, Debian, Fedora, Arch Linux
and Mac OS X.


Installing
==========

There are several ways to install pytoutv, the easiest being using pip.

Please note that you need Python 3.3+ whatever the method you choose.


Install dependencies
--------------------

The pip and `setup.py` install methods will automatically install Python
dependencies for you. However, it might be a better idea to have them
installed using your package manager if you have any.

On Debian and Ubuntu, here's how it's done:

    $ sudo aptitude install python3-crypto python3-requests python3-setuptools

On Fedora:

    $ sudo yum install python3-crypto python3-requests python3-setuptools

On Arch Linux:

    $ sudo pacman -Sy python-crypto python-requests python-setuptools


Using pip
---------

Make sure you have [pip](http://www.pip-installer.org/en/latest/) and
[setuptools](https://pypi.python.org/pypi/setuptools). Your favorite
distribution should provide a way to get both.

Then install pytoutv using pip:

    $ sudo pip install pytoutv


### Ubuntu and Debian

On Debian and Ubuntu, pip uses the Python 2 dependencies by default.
To fix this, you can download the Python 3 version of pip:

    $ sudo aptitude install python3-pip

You can then run the installation using this package:

    $ sudo pip3 install pytoutv


### Fedora

On Fedora, pip uses the Python 2 dependencies by default.
To fix this, you can download the Python 3 version of pip:

    $ sudo yum install python3-pip

You can then run the installation using this package:

    $ sudo python3-pip install pytoutv


### Mac OS X

First, make sure you have the latest version of Python installed.
Apple provides their own build of Python 2.7, but you'll need
3.3 or more for pytoutv.

You can download the latest build for your version of Mac OS X
on here: https://www.python.org/download/

To check if it has installed correctly, simply run 'python3.X'
(where X is the subversion, like '3.4').

If you have the Python prompt with the correct version stated,
you're ready for the next step!

Exit the Python prompt (if not back to your usual terminal)
and run:

    $ sudo pip3 install pytoutv

Now, have fun!


PLEASE NOTE:
It seems the autoinstall script doesn't add pytoutv's path
to the global paths file.
Add "/Library/Frameworks/Python.framework/Versions/3.4/bin"
to "/etc/paths/" and you should be in business!


Using setup.py
--------------

As long as you have [setuptools](https://pypi.python.org/pypi/setuptools),
you may install pytoutv directly using its `setup.py` script:

  1. Clone the repo:

        $ git clone https://github.com/bvanheu/pytoutv && cd pytoutv

  2. Run the setup script:

        $ sudo ./setup.py install

On Debian, Ubuntu and Fedora, you might need to specify you want to use Python 3
to run the program:

    $ sudo python3 ./setup.py install


Library
=======

Package documentation is not available yet.


CLI
===

Four commands are available using the command line interface tool,
which, after installing, is simply named `toutv`:

  * `list`: lists emissions (shows) and episodes of a given emission
  * `info`: outputs informations about an emission or an episode
  * `fetch`: fetches (downloads) a complete episode or all episodes of
    a given emission
  * `search`: searches amongst emissions and episodes

Additionnal features are available, like fetching or getting infos
using a TOU.TV URL, or a caching mechanism which accelerates
requests. Use

    $ toutv <command> -h

to get a detailed list of options for command `<command>`.


Proxy
-----

Please note `toutv` honors the `HTTP_PROXY` and `HTTPS_PROXY` environment
variables, which should contain the full URLs of HTTP(S) proxies to use, including
the scheme (`http://`, `https://`).


Examples
--------

Here are a few CLI usage examples.

### Login to the extra section of Tou.tv

     $ toutv login <USERNAME>
     Password: <PASSWORD>
     Login successful
     Token: c3458d85-6094-4030-9454-114380b2dec0

### Listing all emissions

    $ toutv list
    2416249839: 2030, Le Big Bang démographique
    2424965959: 26 lettres
    1735242576: 30 vies
    2415880603: Ainsi soient-ils
    2284422575: Air de famille (Un)
    2424965905: Alain Bashung faisons envie
    2424966134: Alfred Hitchcock : Agent secret
    2424966154: Alfred Hitchcock : Aventure malgache
    ...


### Listing episodes of a given emission

    $ toutv list 'physique ou chimie'
    Physique ou chimie:

      * 2160477711: S01E01 Des choses à faire avant de mourir
      * 2160477623: S01E02 Agir ou laisser faire
      * 2160483636: S01E03 Uniquement sexuel
      * 2160483351: S01E04 Dommages collatéraux
      * 2160490365: S01E05 Une victoire très curieuse
      * 2160490718: S01E06 Il en faut du courage
      * 2160497332: S01E07 Aller de l’avant
      * 2160497534: S01E08 Le prix de la liberté
      * 2161200777: S01E09 Égoïsme raisonnable
      * 2161201111: S01E10 Réactions en chaîne
      ...


### Getting informations about an emission

    $ toutv info 'physique ou chimie'
    Physique ou chimie  [Unknown country]

    Blanche, Irène, Jonathan et Rock, professeurs au Collège Zurbarán à Madrid, sont
    censés servir de guides à leurs étudiants, alors qu'eux-mêmes ont une vie
    compliquée. Ils découvriront assez rapidement qu'enseigner est la meilleure
    façon d'apprendre la vie. Entre amours, amitiés, trahisons et déceptions, la
    série espagnole Physique ou chimie met de l’avant les hauts et les bas que
    vivent les élèves et les professeurs.


    Infos:

      * Tags: jeunesse, rogers


### Getting information about an episode using its URL

    $ toutv info -u http://ici.tou.tv/serie-noire/S01E08
    Série noire
    Épisode 8  [S01E08]

    Ébranlés par les récentes découvertes, Denis et Patrick tentent d’en savoir
    davantage sur l’identité de la mystérieuse femme corpulente. Charlène et Judith
    les aideront-elles à éclaircir cette nouvelle piste? Victimes d’un kidnapping,
    Denis et Patrick découvrent, au péril de leur vie, les motivations étonnantes de
    l’organisation criminelle de Bruno.


    Infos:

      * Air date: 2014-03-03
      * Available bitrates:
        * 461 kbps
        * 561 kbps
        * 925 kbps
        * 1324 kbps

### Fetching an episode

    $ toutv fetch Enquete S2014E11
    Enquête.S2014E11.La.guerre.d...    28.8 MiB    24/260 [##-----------------]   9%


### Fetching an episode at maximum available video quality

    $ toutv fetch -q MAX 'série noire' s01e05
    Série.noire.S01E05.Épisode.5...    63.7 MiB    38/260 [###----------------]  14%


### Fetching all episodes of a given emission at average quality

    $ toutv fetch 'en audition avec simon'
    En.audition.avec.Simon.S01E01...    16.5 MiB   15/15 [####################] 100%
    En.audition.avec.Simon.S03E47...    24.9 MiB   23/23 [####################] 100%
    En.audition.avec.Simon.S01E17...     9.9 MiB    9/27 [#######-------------]  33%
    ...


### Searching for episodes and emissions

    $ toutv search politique
    Effective query: politique

    Episode: Loi 101 : Le malaise de René Lévesque (1re partie)  [1481687502]

      * Air date: 2010-04-27
      * Emission ID: 1480980995

      En 1976, le Parti québécois remporte pour la première fois les élections sur
      la promesse d’être un bon gouvernement. Sans avoir mis la question de la
      langue au cœur du débat électoral, René Lévesque avait promis de revoir la loi
      22. Il confie ce mandat à Camille Laurin.


    Episode: Loi 101 : le combat de Camille Laurin (2e partie)  [1485812723]

      * Air date: 2010-05-04
      * Emission ID: 1480980995

      La loi 101 sera, pour Camille Laurin, le combat de sa vie. Il s’entoure
      d’abord des meilleurs esprits de son temps pour rédiger la Charte de la langue
      française. René Lévesque lui demande d’aller convaincre la population
      québécoise. Il affronte alors la colère de la communauté anglaise. À force de
      ruse et de détermination, Camille Laurin dépose finalement le projet de loi
      qui transformera le paysage linguistique du Québec.


    Episode: Sommet des Amériques et Sommet des peuples  [1498400939]

      * Air date: 2010-05-18
      * Emission ID: 1480980995

      En 2001, un sommet parallèle s’organise dans la basse-ville de Québec pour
      répliquer aux négociations officielles d’un traité de libre-échange des trois
      Amériques. Le Sommet des peuples accueille 2000 représentants syndicaux, des
      organismes sociaux et féministes, d’ici et d’ailleurs en Amérique. Cinquante
      mille personnes sortent dans la rue pour s’opposer pacifiquement. D’autres
      manifestants préfèrent affronter la police.


    Episode: L'humour politique II : Les années 70  [1573008143]

      * Air date: 2010-08-17
      * Emission ID: 1480980995

      Les années 70 sont fertiles en bouleversements. C’est l’ère des imitateurs, de
      la montée du féminisme et le début de l’humour au féminin. Invités : Jean-Guy
      Moreau, Claude Landré et Clémence DesRochers.

    ...


Bugs
====

pytoutv is known to work as of the date of the last repo commit. Should you encounter
any problem, please [create an issue](https://github.com/bvanheu/pytoutv/issues/new)
and give details about your situation and what's not working as expected.


Contributing
============

To contribute to any part of this project, send us a GitHub pull request. Make sure
your Python code follows [PEP-8](http://legacy.python.org/dev/peps/pep-0008/),
except for long lines that cannot be broken (e.g. long strings).


Python workflow
---------------

The best way to develop pytoutv locally without installing it globally is to
create a [virtualenv](http://www.virtualenv.org/en/latest/). If you don't
have virtualenv, get it now (most distributions provide it as a package).

  1. In the root of the repo, create the virtualenv:

        $ virtualenv virt

  2. Activate the virtualenv:

        $ . ./virt/bin/activate

  3. Use the `develop` command of `setup.py`:

        $ ./setup.py develop

     The first time this executes, if you don't have any of the dependencies,
     they will be downloaded and installed (locally, in `virt`).

After step 3, you may execute `toutv` (which now resolves to the local version
of the command). You may as well launch ipython and import `toutv` modules;
the local modules will be imported.


Semantic versioning
-------------------

pytoutv follows [semantic versioning](http://semver.org/). If you submit a bugfix
patch, we'll bump the patch version. If you submit a new feature, we'll bump the
minor version. No version 3 of pytoutv is planned.


Contributors
============

Special thanks to:

  * [Benjamin Vanheuverzwijn](https://github.com/bvanheu)
  * Alexandre Vézina
  * [Alexis Dorais-Joncas](https://github.com/balexis)
  * [Israel Halle](https://github.com/isra17)
  * [Marc-Etienne M. Leveillé](https://github.com/marc-etienne)
  * [Simon Marchi](https://github.com/simark)
  * [Simon Carpentier](https://github.com/scarpentier)
  * [Philippe Proulx](https://github.com/eepp)
