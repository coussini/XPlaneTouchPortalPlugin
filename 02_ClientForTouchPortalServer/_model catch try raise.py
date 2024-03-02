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
    print(f"Traitement d'une erreur de plugin: {e}")

try:
    plugin.json_error_method()
except plugin.CustomErrorJson as e:
    print(f"Traitement d'une erreur JSON: {e}")

try:
    plugin.xplane_error_method()
except plugin.CustomErrorXPlane as e:
    print(f"Traitement d'une erreur XPlane: {e}")

# Vous pouvez également gérer plusieurs exceptions dans un seul bloc try-except
try:
    # Appel d'une méthode qui pourrait lever n'importe laquelle des exceptions personnalisées
    # Pour cet exemple, remplacez `method_name` par le nom de la méthode que vous souhaitez tester
    plugin.plugin_error_method()  # Changez cette ligne pour tester les autres méthodes
except (plugin.CustomErrorPlugin, plugin.CustomErrorJson, plugin.CustomErrorXPlane) as e:
    print(f"Traitement d'une erreur (plugin, json, ou xplane): {e}")
