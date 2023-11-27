s'assurer que le def service_connection(key, mask) soit identique entre les deux

il faut permettre à service_connection du client à échanger le parametre keep_running afin de cesser la boucle lorsque l'on désire. Le serveur dans x-plane sera arrêté quand x-plane fermera

s'assurer de _SelServer.py et _SelClient.py puisse arrêter sans faire de traceback.

1-faire dans _SelServer.py "server_data" comme dans _Selclient.py concernant "client_data"
2-structurer le _SelServer.py comme le _Selclient.py avec un main() et des variable simpleNamespaces
3-Une fois fais... faire un KeyboardInterrupt de chaque côté... jusqu'à satisfaction
4-demander une fois seulement les updates à partir de la connexion2. quand le serveur le recoît la demande "command : ask_update", il part un thread pour vérifier les valeurs de x-plane avec ceux en tableaux du côté serveur à condition que "command : init" à été effectué