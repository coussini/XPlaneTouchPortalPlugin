transformer _SelEchoClientForXplane.py comme multiconn-client.py

utiliser multiconn-server3.py comme serveur

s'assurer que le def service_connection(key, mask) soit identique entre les deux
il faut permettre à service_connection du client à échanger le parametre keep_running afin de cesser la boucle lorsque l'on désire. Le serveur dans x-plane sera arrêté quand x-plane fermera


faire comme l'object selectors_server dans _SelServer.py pour éviter les global