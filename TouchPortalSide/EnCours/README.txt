s'assurer que le def service_connection(key, mask) soit identique entre les deux

il faut permettre à service_connection du client à échanger le parametre keep_running afin de cesser la boucle lorsque l'on désire. Le serveur dans x-plane sera arrêté quand x-plane fermera

s'assurer de _SelServer.py et _SelClient.py puisse arrêter sans faire de traceback.

1-faire dans _SelServer.py "server_data" comme dans _Selclient.py concernant "client_data"
2-structurer le _SelServer.py comme le _Selclient.py avec un main() et des variable simpleNamespaces
3-Une fois fais... faire un KeyboardInterrupt de chaque côté... jusqu'à satisfaction