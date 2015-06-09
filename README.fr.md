(See [`README.md`](README.md) for an English version.)

***pytoutv*** est une librairie écrite en Python 3 qui implémente un client
pour [TOU.TV](http://tou.tv/).

Ce dépôt contient aussi une interface en ligne de commande.

pytoutv, grâce à l'API publique de TOU.TV (voir
[`toutv/config.py`](toutv/config.py) pour les URL publiques), est en
mesure de récupérer les listes d'émissions et d'épisodes, obtenir des
informations sur des émissions ou des épisodes ou télécharger n'importe quel
fichier vidéo distribué publiquement par le service TOU.TV. Les informations
téléchargées, incluant les fichiers vidéo, sont destinées à un usage personnel
et ne devraient pas être redistribuées, à moins d'une autorisation préalable
fournie par les propriétaires de TOU.TV.

Le projet pytoutv n'est pas affilié, connecté ou associé à la Société Radio-Canada
ou à CBFT-DT. La Société Radio-Canada ou CBFT-DT ne parrainent pas, n'approuvent
pas ou n'endossent pas le projet pytoutv.

_Note_ : bien qu'on parle de pytoutv 2, il n'existe pas de version 1 de
pytoutv. Ce projet était auparavant connu sous le nom
_Tou.tv-console-application_ et ciblait Python 2. Son réusinage et son
changement de nom vers pytoutv a mené à sa version 2. L'interface en ligne
de commande demeure assez compatible avec la version précédente.


Dépendances
============

pytoutv requiert :

  * Python 3.3+, avec :
    * [PyCrypto](https://www.dlitz.net/software/pycrypto/)
      ([disponible sur PyPI](https://pypi.python.org/pypi/pycrypto))
    * [Requests](http://python-requests.org/)
      ([disponible sur PyPI](https://pypi.python.org/pypi/requests))
    * [setuptools](https://pythonhosted.org/setuptools/)
      ([disponible sur PyPI](https://pypi.python.org/pypi/setuptools))

Dépendances facultatives :

  * termcolor
    ([disponible sur PyPI](https://pypi.python.org/pypi/termcolor)):
    couleurs dans le terminal (CLI)
  * [PyQt4](http://www.riverbankcomputing.com/software/pyqt/download):
    interface Qt

pytoutv est réputé fonctionner sur Ubuntu, Debian, Fedora, Arch Linux et Mac OS X.


Installation
============

Il existe plusieurs méthodes pour installer pytoutv, la plus facile étant en
passant par l'outil pip.

Veuillez noter que Python 3.3+ est requis peu importe la méthode utilisée.


Installation des dépendances
----------------------------

Les méthodes d'installation avec pip et `setup.py` vont automatiquement installer
les dépendances Python pour vous. Ceci dit, il peut être préférable de les
installer avec le gestionnaire de paquetages de votre distribution :

Sur Debian et Ubuntu, voici comment faire :

    $ sudo aptitude install python3-crypto python3-requests python3-setuptools

Sur Fedora:

    $ sudo yum install python3-crypto python3-requests python3-setuptools

Sur Arch Linux :

    $ sudo pacman -Sy python-crypto python-requests python-setuptools


Avec pip
--------

Assurez-vous d'avoir [pip](http://www.pip-installer.org/en/latest/) et
[setuptools](https://pypi.python.org/pypi/setuptools). Votre distribution
favorite devrait fournir une façon d'obtenir ces paquetages.

Installez ensuite pytoutv à l'aide de pip :

    $ sudo pip install pytoutv


### Ubuntu et Debian

Sur Debian et Ubuntu, pip utilise par défaut les dépendances en Python 2.
Pour régler ce problème, vous pouvez télécharger la version Python 3 de pip :

    $ sudo aptitude install python3-pip

Par la suite, il ne suffit que de lancer l'installation avec ce paquet:

    $ sudo pip3 install pytoutv


### Fedora

Sur Fedora, pip utilise par défaut les dépendances en Python 2.
Pour régler ce problème, vous pouvez télécharger la version Python 3 de pip :

    $ sudo yum install python3-pip

Par la suite, il ne suffit que de lancer l'installation avec ce paquet:

    $ sudo python3-pip install pytoutv


### Mac OS X

Apple fournissent leur propre version de Python 2.7, pré-installé avec
le système d'exploitation. C'est bien, mais nous avons besoin de 3.3
minimum.

Rendez-vous sur https://www.python.org/download/ pour télécharger
la dernière version de Python compatible avec votre système.

Installez-le et ouvrez votre terminal. Si l'exécution de "python3.X"
(X étant la sous-version installée, comme 3.3 ou 3.4) vous
ouvre le mode de commande de Python 3.3+, tout est correct.

Quittez Python et exécutez:

"sudo pip3 install pytoutv"

Si tout se passe bien, vous devriez ensuite pouvoir l'exécuter!


À NOTER:
Il semble que le script d'installation ne place pas de chemin global.
Ajoutez: "/Library/Frameworks/Python.framework/Versions/3.4/bin" à
"/etc/paths".


Avec setup.py
-------------

Tant que vous avez [setuptools](https://pypi.python.org/pypi/setuptools),
vous pouvez installer pytoutv directement en utilisant son script `setup.py` :

  1. Clonez le dépôt :

        $ git clone https://github.com/bvanheu/pytoutv && cd pytoutv

  2. Lancez le script d'installation :

        $ sudo ./setup.py install

Sur Debian, Ubuntu et Fedora, vous devrez surement spécifier que vous souhaitez
utiliser Python 3 pour faire rouler le programme :

    $ sudo python3 ./setup.py install


Librairie
=========

La documentation de la librairie n'est pas encore disponible.


Ligne de commande
=================

Quatre commandes sont disponibles en utilisant l'outil en ligne de commande
qui, après installation, se nomme simplement `toutv` :

  * `list` : liste les émissions et épisodes d'une émission donnée
  * `info` : écrit les informations d'une émission ou d'un épisode
  * `fetch` : télécharge un épisode ou tous les épisodes d'une émission donnée
  * `search` : recherche parmi les émissions et épisodes

D'autres fonctionnalités dont disponibles, tels que le téléchargement ou
l'obtention d'informations en utilisant une URL TOU.TV, ou encore un mécanisme
de cache qui permet d'accélérer les requêtes. Utilisez

    $ toutv <commande> -h

afin d'obtenir une liste détaillée des options pour la commande `<commande>`.


Proxy
-----

Veuillez noter que `toutv` honore les variables d'environnement `HTTP_PROXY` et
`HTTPS_PROXY`, qui devraient contenir les URL complètes des proxies à utiliser,
incluant le schéma (`http://`, `https://`).


Exemples
--------

Voici quelques exemples d'utilisation de l'interface en ligne de commande.

### Se connecter à la section extra de Tou.tv

    $ toutv login <USERNAME>
    Password: <PASSWORD>
    Login successful
    Token: c3458d85-6094-4030-9454-114380b2dec0

### Liste de toutes les émissions

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


### Liste des épisodes d'une émission donnée

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


### Informations d'une émission

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


### Informations d'un épisode en utilisant son URL TOU.TV

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


### Téléchargement d'un épisode

    $ toutv fetch Enquete S2014E11
    Enquête.S2014E11.La.guerre.d...    28.8 MiB    24/260 [##-----------------]   9%


### Téléchargement d'un épisode avec la meilleure qualité vidéo disponible

    $ toutv fetch -q MAX 'série noire' s01e05
    Série.noire.S01E05.Épisode.5...    63.7 MiB    38/260 [###----------------]  14%


### Téléchargement de tous les épisodes d'une émission donnée avec une qualité moyenne

    $ toutv fetch 'en audition avec simon'
    En.audition.avec.Simon.S01E01...    16.5 MiB   15/15 [####################] 100%
    En.audition.avec.Simon.S03E47...    24.9 MiB   23/23 [####################] 100%
    En.audition.avec.Simon.S01E17...     9.9 MiB    9/27 [#######-------------]  33%
    ...


### Recherche d'émissions et d'épisodes

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

Bogues
======

pytoutv est réputé fonctionner en date du dernier _commit_ de ce dépôt. Si vous
rencontrez un bogue quelconque, nous vous saurons gré de
[créer un problème](https://github.com/bvanheu/pytoutv/issues/new) et de
fournir le plus de détails possibles à propos de votre situation, en plus de
spécifier ce qui ne fonctionne pas tel que prévu.


Contribuer
==========

Afin de contribuer à n'importe quelle composante de ce projet, envoyez-nous un
_pull request_ GitHub. Assurez-vous que votre code Python suive
[PEP-8](http://legacy.python.org/dev/peps/pep-0008/), sauf pour de très
longues lignes qui ne peuvent pas être cassées (longues chaines, par exemple).


Flux de travail avec Python
---------------------------

La meilleure façon de développer pytoutv localement sans avoir à l'installer
globalement est de créer un
[virtualenv](http://www.virtualenv.org/en/latest/). Si vous n'avez pas
virtualenv, procurez-vous le (la plupart des distributions le fournissent en
tant que paquetage).

  1. Dans la racine du dépôt, créez le virtualenv :

        $ virtualenv virt

  2. Activez le virtualenv :

        $ . ./virt/bin/activate

  3. Utilisez la commande `develop` du script `setup.py` :

        $ ./setup.py develop

     La première fois que ceci s'exécute, si vous n'avez pas toutes les
     dépendances du projet, elles seront téléchargées et installées (localement,
     dans `virt`).

Suite à l'étape 3, vous pouvez exécuter `toutv` (qui pointe maintenant vers la
version locale de la commande). Vous pouvez aussi lancer ipython et importer
des modules de `toutv`; les versions locales seront importées.


Versionnage sémantique
----------------------

pytoutv suit un [versionnage sémantique](http://semver.org/). Si vous soumettez
un simple correctif, nous incrémenterons la version de _patch_. Si vous soumettez
une nouvelle fonctionnalité, nous incrémenterons la version mineure. Aucune version
3 de pytoutv n'est prévu pour l'instant.


Contributeurs
=============

Nous tenons à remercier spécialement :

  * [Benjamin Vanheuverzwijn](https://github.com/bvanheu)
  * Alexandre Vézina
  * [Alexis Dorais-Joncas](https://github.com/balexis)
  * [Israel Halle](https://github.com/isra17)
  * [Marc-Etienne M. Leveillé](https://github.com/marc-etienne)
  * [Simon Marchi](https://github.com/simark)
  * [Simon Carpentier](https://github.com/scarpentier)
  * [Philippe Proulx](https://github.com/eepp)
