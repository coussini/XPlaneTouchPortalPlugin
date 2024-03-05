# X-Plane Touch Portal Plugin

![XPlaneTouchPortalPlugin](https://github.com/coussini/XPlaneTouchPortalPlugin/assets/5262785/206080e9-4070-4172-a2d0-d7085f8a83dd)

## Instruction concernant la création du fichier datarefs.json à l'aide de l'outil

- Utilisez l'outil...

- Les datarefs doivent être unique dans le fichier dataref.json

## Instruction pour démarrage un fois ce plugin installé

- Démarrer X-Plane 12

- S'assurer qu'il y a le message dans x-plane "serveur pour touch portal actif"

- Démarrer Touch Portal

- Vous devriez voir sur votre page que les boutons ou les commandes sont les même que du côté X-Plane

## Instruction pour télécharger des pack de boutons utiles pour Touch Portal X-Plane

- Expliquer comment télécharger et intégrer des boutons pour X-Plane pour Touch-Portal

Un dataref doit-être utilisé qU'une fois dans le fichier datarefs.jspn

## Boutons connected sur la page Touch Portal

- Mettre un bouton avec couleur rouge ou vert pour connexion (connected)

## Les boutons se compotent annormalement

- Il faut faire Setings / General - Clean Data

## À faire

- Créer un pack d'icône pour Toliss A320 Essential et pour Default

- Peut-on diminuer le nombre de byte en receive par des time.spleep() ?

- Créer un default.json avec un page modèle

- Ne pas oublier de créer une procédure ou programme pour mettre en place un json sous Misc

- Créer une page default pour xplane comme modèle

- Important: Spécifier la version python à utiliser (minimum 3.0)

## Overview

- Explain to the XplaneTouchPortalPLugin user wich requierement are important to have (python, TouchPortal...)

- The states are use to store informations for x-plane DataRef. 

- Thats

- You can create your states into the "Datarefs.json"" file (already exist and contains an example) that you can use it.

- These are information for each states. 
  
  - id = Always beginning with "XplanePlugin.". You can take the description to complet the id. Do not put any spaces in it. 
  
  - desc = Description of the aircraft panel button.
  
  - group = Where you find the button in instruments panel. 
  
  - type = int or float. value = default value (usually 0). 
  
  - dataref = The full name of the dataref (including the index number if required). For an exemple "AirbusFBW/APUMaster" or  "AirbusFBW/OHPLightSwitches[2]"  where 2 is the index inside the variable AirbusFBW/OHPLightSwitches.
  
  - comment = Information allowing the panel's creator in Touch Portal to understand the values and wich corresponding

---

## Features

## IMPORTANT

Si un bouton ne réagit pas, il faut regarder s'il y a aucune information d'état disponible (à ce moment là il faut choisir une variable dans la liste pour cette ligne). S'il n'y a pas de variable (un blanc), il faut choisir la variable. Si un bouton ne réagit pas correctement à force de répéter des changement, il faut peut-être allez dans les paramètres sous Touch Portal, Puis Général,  puis Nettoyer les données.Il vaut mieux peut-être, si cela ne fonctionne pas, détruire ce bouton et en refaire un nouveaux pour que le référenciel de Touch Portal se refasse correctement (un bug sans doute)

Quand on ajoute une variable dans le fichier json, il faut redémarer touch portal afin que les nouveaux éléments inscrits puissent être utilisable

Attention utiliser le fichier Setup.JPG afin de permettre à l'utilisateur d'entrer le path de X-Plane

PEUT-ETRE

```python
pip install python-socketio
pip install python-socketio[client]
pip install eventlet
```

##### STEP POUR LA COMPRÉHENSION DES DONNÉES

For example, it is a good idea to familiarize yourself with the dataref values corresponding to the buttons you want to use in Touch Portal. You can use the DatarefTool (see the html link in the folder to understand DataRefTool. You can also rely on the example file Datarefs.json (a simple text editor can allow you to see its content) in order to clearly identify your needs

1. id = An unique id for Touch Portal Usage

2. desc = This description can be use when a page builder use:
   
   1. Logic : If Statement (Advanced)
   
   2. Xplane - Dataref: Set Named Variable Value
