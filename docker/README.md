# toutv in a Docker container
It's just a Docker image for https://github.com/bvanheu/pytoutv

## How to use
Very similarly to the pytoutv client, except you don't have to install python3 nor pip3 nor toutv scripts and their dependencies, everything is provided in this image.

Here are a few examples on how to use this image , [list of commmands is provided on pytoutv Github repo](https://github.com/bvanheu/pytoutv) : 

```
$ docker run -t anthonydahanne/toutv
usage: toutv [-h] [-n] [-v] [-V] {list,info,search,fetch,clean,login} ...
toutv: error: argument command: invalid choice: '' (choose from 'list', 'info', 'search', 'fetch', 'clean', 'login')

```

```
$ docker run -t anthonydahanne/toutv -V
toutv v3.0.2
```

```
$ docker run anthonydahanne/toutv info INFOMAN
Infoman  [Canada]
ID: 1362844950

C'est la première émission de la saison et on vous parle après tout le monde de
la campagne électorale. Au menu, un résumé de ce qui s'est passé depuis son
déclenchement le 23 août et un segment de tweets méchants en compagnie de
quelques politiciens. Aussi au programme, le premier Miss Candidat Provincial
avec MC Gilles et son urne du succès et Chantal Lamarre nous offre, au lieu du
traditionnel Bingo, le jeu Débat des chefs pour agrémenter la suite de votre
soirée.

Infos:

  * Network: CBFT
```  

Also, you can mount a local directory to the /media volume; in other words, you can download files to your host filesystem :

```
$ docker run -t -v /Users/anthony/Downloads/:/media/  anthonydahanne/toutv fetch -q MAX INFOMAN S19E01
Infoman.S19E01.Épisode.01.qMAX.ts    25.7 MiB     9/127 [#####-----------------------------------------------------------]   7%
```
