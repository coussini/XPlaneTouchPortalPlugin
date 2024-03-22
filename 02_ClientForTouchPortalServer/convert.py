import json

# Chemin vers votre fichier JSON
chemin_fichier_json = "C:/Users/couss/OneDrive/Bureau/XPlaneTouchPortalPlugin/02_ClientForTouchPortalServer/default.json"


# Ouvrir le fichier JSON pour lecture
with open(chemin_fichier_json, 'r') as fichier:
    donnees = json.load(fichier)

# Fonction pour ajouter un nouvel élément juste après un élément spécifique dans un dictionnaire
def ajouter_apres(dictionnaire, apres_cle, nouvelle_cle, nouvelle_valeur):
    # Convertir le dictionnaire en une liste de tuples (cle, valeur)
    items = list(dictionnaire.items())
    # Trouver l'index de la clé après laquelle on veut ajouter le nouvel élément
    index = next((i for i, item in enumerate(items) if item[0] == apres_cle), None)
    # Si la clé a été trouvée, insérer le nouvel élément juste après
    if index is not None:
        items.insert(index + 1, (nouvelle_cle, nouvelle_valeur))
    # Retourner le dictionnaire mis à jour
    return dict(items)

# Parcourir chaque élément dans 'datarefs' et ajouter "format": "" après "dataref"
for item in donnees['datarefs']:
    # Utiliser la fonction pour ajouter "format": "" juste après "dataref"
    nouvel_item = ajouter_apres(item, 'dataref', 'format', '')
    # Mettre à jour l'élément dans 'datarefs'
    item.update(nouvel_item)

# Réécrire le fichier JSON avec les modifications
with open(chemin_fichier_json, 'w') as fichier:
    json.dump(donnees, fichier, indent=4)  # 'indent=4' pour un formatage plus lisible

print("Le fichier JSON a été mis à jour avec succès.")