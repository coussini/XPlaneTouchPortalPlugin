# model catch try raise

class XPlanePlugin:

    class CustomErrorPlugin(Exception):
        def __init__(self, message):
             super().__init__(message)

    class CustomErrorJson(Exception):
        def __init__(self, message):
            super().__init__(message)

    class CustomErrorXPlane(Exception):
        def __init__(self, message):
            super().__init__(message)

    def __init__(self):
        pass

    def plugin_error_method(self):
        # Simulons une condition d'erreur pour lever CustomErrorPlugin
        raise self.CustomErrorPlugin("Erreur dans la méthode plugin_error_method")

    def json_error_method(self):
        # Simulons une condition d'erreur pour lever CustomErrorJson
        raise self.CustomErrorJson("Erreur dans la méthode json_error_method")

    def xplane_error_method(self):
        # Simulons une condition d'erreur pour lever CustomErrorXPlane
        raise self.CustomErrorXPlane("Erreur dans la méthode xplane_error_method")

# Création d'une instance de la classe XPlanePlugin
plugin = XPlanePlugin()

# Tentative d'exécution des méthodes et gestion des exceptions levées
try:
    plugin.plugin_error_method()
except plugin.CustomErrorPlugin as e:
    print(f"ERROR -> TOUCH PORTAL XPLANE PLUGIN -> {e}") # e = message
    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '1') # Plugin error

try:
    plugin.json_error_method()
except plugin.CustomErrorJson as e:
    print(f"ERROR -> CUSTOMIZED JSON -> {e}")
    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '3') # Json error


try:
    plugin.xplane_error_method()
except plugin.CustomErrorXPlane as e:
    print(f"ERROR -> X-PLANE SERVER COMMUNICATION -> {e}")
    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '5') # X-Plane communication error

# Vous pouvez également gérer plusieurs exceptions dans un seul bloc try-except
try:
    # Appel d'une méthode qui pourrait lever n'importe laquelle des exceptions personnalisées
    # Pour cet exemple, remplacez `method_name` par le nom de la méthode que vous souhaitez tester
    plugin.plugin_error_method()  # Changez cette ligne pour tester les autres méthodes
except (plugin.CustomErrorPlugin, plugin.CustomErrorJson, plugin.CustomErrorXPlane) as e:
    print(f"Traitement d'une erreur (plugin, json, ou xplane): {e}")
    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '1') # Plugin error


##############################################################################
##############################################################################

import threading
import queue

class XPlanePlugin:

    def __init__(self):
        self.error_queue = queue.Queue()

    def xplane_client_thread_for_communication_with_xplane_server(self):
        try:
            # Code susceptible de lever une exception
            raise self.CustomErrorXPlaneThread("Erreur simulée dans le thread.")
        except Exception as e:
            self.error_queue.put(e)

    def second_thread(self):
        thread = threading.Thread(target=self.xplane_client_thread_for_communication_with_xplane_server)
        thread.start()
        thread.join()

        # Vérification et gestion des exceptions levées dans le thread secondaire
        try:
            error = self.error_queue.get_nowait()  # Essaie de récupérer une exception
        except queue.Empty:
            # Aucune exception levée dans le thread secondaire
            pass
        else:
            # Gestion de l'exception ici
            raise self.CustomErrorXPlane(f"Erreur provenant du thread: {error}")
# Exemple d'utilisation
plugin = XPlanePlugin()

try:
    plugin.second_thread()
except:
    except app.CustomErrorXPlane as e:
    print("Erreur capturée :", e)