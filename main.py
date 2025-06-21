from flask import Flask , render_template, session , request , redirect

import string

import pymongo

from werkzeug.utils import secure_filename

from datetime import datetime

from bson.objectid import ObjectId  

import os



app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # Cache les fichiers statiques pendant 1 an
app.secret_key = "cookies"


mongo = pymongo.MongoClient("mongodb+srv://NiSeLeY:atelier1234@cluster0.gw1ai.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo.bdd.games.create_index([("Titre", "text")])


@app.route("/")
def acceuil() :
    mes_annonces = mongo.bdd.annonce
    annonces = mes_annonces.find({})
    mes_jeux = mongo.bdd.games  # Assurez-vous que "games" est le nom de votre collection
    games = list(mes_jeux.find())
    print(games)  # Récupère tous les jeux sous forme de liste
    if"utilisateur" in session : 
        mes_utilisateurs = mongo.bdd.utilisateurs
        utilisateur = mes_utilisateurs.find_one({"pseudo" : session["utilisateur"]})
        print(utilisateur)
        return render_template("index.html" , utilisateur = utilisateur , annonces = annonces, games = games)
    else : 
        return render_template("index.html" , annonces = annonces , games=games)



@app.route("/profil")
def profil() :
    mes_utilisateurs = mongo.bdd.utilisateurs
    utilisateur = mes_utilisateurs.find_one({"pseudo" : session["utilisateur"]})
    return render_template("profil.html" , utilisateur = utilisateur)


@app.route("/profil/edit" , methods = ["GET" , "POST"])
def modifier_profil() :
    if request.method == "GET" : 
        mes_utilisateurs = mongo.bdd.utilisateurs
        utilisateur = mes_utilisateurs.find_one({"pseudo" : session["utilisateur"]})
        return render_template("edit_profil.html" , utilisateur = utilisateur)
    else:
        # 1 : on recupere les informations  entreees dans les boites (input)
        admin_code = request.form.get("input_admin", "")
        role = "admin" if admin_code == "10102011" else "user"

        pseudo_entre = request.form["input_pseudo"]
        mdp_entre = request.form["input_mdp"]
        image = request.files["input_avatar"]
        age_entre = request.form["input_age"]
        nationalite_entre = request.form["input_nationalite"]
        if nationalite_entre == "" : 
            nationalite_entre == "unspecified"
        elif age_entre == "" : 
            age_entre == "unspecified"
        #2 : on gere tous les cas d'erreur 
        mes_utilisateurs = mongo.bdd.utilisateurs
        utilisateur = mes_utilisateurs.find_one({"pseudo" : pseudo_entre})
        
        if utilisateur and pseudo_entre != session["utilisateur"]:
            return render_template("edit_profil.html" , erreur = "The user already exists")
        elif pseudo_entre == "" : 
            return render_template("edit_profil.html" , erreur = "Please enter a username")
        elif len(mdp_entre) < 6 : 
            return render_template("edit_profil.html" , erreur = "Password must be at least 6 characters long")
        elif not image :
            return render_template("register.html", erreur = "Veuillez choisir une image")
        # si le fichier n'a pas de nom
        elif image.filename == "" :
            return render_template("register.html", erreur = "Veuillez choisir une image")
      
        else :    
        

            nom_image = secure_filename(image.filename)  # Sécurise le nom du fichier 
            image.save("static/upload/" + nom_image)  # Enregistre l'image dans le dossier static/upload")
        
        #3 : on cree le compte utilisateur
            resultat = mes_utilisateurs.update_one(
            {"pseudo": session["utilisateur"]},  # Critère de recherche
            {
                "$set": {
                    "pseudo": pseudo_entre,
                    "mdp": mdp_entre,
                    "avatar" : "../static/upload/" + nom_image,  # Chemin vers l'image
                    "age": age_entre,
                    "nationalite": nationalite_entre,
                    "role": role
                }
            }
        )
        if resultat.modified_count > 0:
            session["utilisateur"] = pseudo_entre

        # 6 : Retourner un message ou rediriger
        return redirect("/profil")


@app.route("/admin_games")
def admin_games() :
    mes_utilisateurs = mongo.bdd.utilisateurs
    utilisateur = mes_utilisateurs.find_one({"pseudo" : session["utilisateur"]})
    mes_jeux = mongo.bdd.games
    jeux = mes_jeux.find({})
    return render_template("admin/admin_games.html" , jeux =list(jeux) )

@app.route("/delete/<id>")
def admin_jeux_delete(id):
    mes_jeux = mongo.bdd.games
    mes_jeux.delete_one({"_id" : ObjectId(id)})
    return redirect("/admin_games")

@app.route("/look/<id>")
def look(id):
    mes_jeux = mongo.bdd.games
    jeux = mes_jeux.find_one({"_id" : ObjectId(id)})
    return render_template("admin/look.html", jeux=jeux  )



@app.route("/register" , methods = ["GET" , "POST"])
def register() :
    if request.method == "GET" : 
        return render_template("register.html")
    else:
        # 1 : on recupere les informations  entreees dans les boites (input)
        admin_code = request.form.get("input_admin", "")
        role = "admin" if admin_code == "10102011" else "user"
        pseudo_entre = request.form["input_pseudo"]
        mdp_entre = request.form["input_mdp"]
        image = request.files["input_avatar"]
        age_entre = request.form["input_age"]
        nationalite_entre = request.form["input_nationalite"]
        if nationalite_entre == "" : 
            nationalite_entre == "unspecified"
        elif age_entre == "" : 
            age_entre == "unspecified"
        #2 : on gere tous les cas d'erreur 
        mes_utilisateurs = mongo.bdd.utilisateurs
        utilisateur = mes_utilisateurs.find_one({"pseudo" : pseudo_entre})
        if utilisateur :
            return render_template("register.html" , erreur = "l'utilisateur existe déjà")
        elif pseudo_entre == "" : 
            return render_template("register.html" , erreur = "Mettez un pseudo")
        elif len(mdp_entre) < 6 : 
            return render_template("register.html" , erreur = "Le mot de passe doit faire au moins 6 caractères")
        # si aucun fichier n'est présent
        elif not image :
            return render_template("register.html", erreur = "Veuillez choisir une image")
        # si le fichier n'a pas de nom
        elif image.filename == "" :
            return render_template("register.html", erreur = "Veuillez choisir une image")
        else : 

            nom_image = secure_filename(image.filename)  # Sécurise le nom du fichier 
            image.save("static/upload/" + nom_image)  # Enregistre l'image dans le dossier static/upload")

        #3 : on cree le compte utilisateur
            mes_utilisateurs.insert_one({
                "pseudo" : pseudo_entre,
                "mdp" : mdp_entre,
                "avatar" : "../static/upload/" + nom_image,  # Chemin vers l'image
                "age" : age_entre,
                "nationalite" : nationalite_entre,
                "role" : role
                

            })
            session["utilisateur"] = pseudo_entre
            return redirect("/")

# exemple de requete find


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("search", "").lower()
    mes_jeux = mongo.bdd.games
    mes_utilisateurs = mongo.bdd.utilisateurs
    utilisateur = mes_utilisateurs.find_one({"pseudo" : session["utilisateur"]})
   

    if query:
        # Utilisation de $regex pour une recherche floue
        results = list(mes_jeux.find({"Titre": {"$regex": f".*{query}.*", "$options": "i"}}))
        print(f"Results found: {results}")
    else:
        results = []
        print("No query provided or no results found.")

    return render_template("search_results.html", games=results, utilisateur =utilisateur) 




@app.route("/modifier/<id>", methods = ["GET", "POST"])
def modifierjeux(id) :
    # On récupère le personnage à afficher / modifier
    mes_jeux = mongo.bdd.games
    jeux = mes_jeux.find_one({"_id" : ObjectId(id)})
    # Si la requête est un GET, on affiche simplement la page
    if request.method == "GET" :
        return render_template("admin/modifier_perso.html",
                                   jeux = jeux)
    # Si la requête est un POST, il faut appliquer la modification
    else :
        print("a")
        # 1 : on récupère les informations entrées dans les boîtes (inputs)
        nom_entre = request.form["input_nom"]
        description_entre = request.form["input_description"]
        image = request.files["input_fichier"]
        link_entre = request.form["input_lien"]
        print("b")
        # 2 : on gère tous les cas d'erreur
        game = mongo.bdd.games
        if nom_entre == "" :
            return render_template("admin/modifier_perso.html", erreur = "Veuillez rentrer un nom de personnage")
        elif description_entre == "" :
            return render_template("admin/modifier_perso.html", erreur = "Veuillez rentrer une description")
        elif link_entre == "" : 
            return render_template("admin/modifier_perso.html", erreur = "Veuillez rentrer un lien")
        else :
            print("c")
            
# S'il y a une image, on met à jour les champs nom, descr. et image
            if image :
                # On ajoute l'image à nos images
                nom_image = secure_filename(image.filename)
                image.save(os.path.join("static/upload/",image.filename))
                print("d")
                # On màj le perso sur la BDD
                mes_jeux.update_one(
                    {"_id":ObjectId(id)},
                    {"$set":{
                        "Titre" : nom_entre,
                        "Image" : "../static/upload/"+nom_image,
                        "Description" : description_entre,
                        "Link" : link_entre
                    }}
                )
                print("e")
            # Si pas d'image, on met à jour uniquement le nom et la description
            else :
                # on màj le perso (sans l'image)
                mes_jeux.update_one(
                    {"_id":ObjectId(id)},
                    {"$set": {
                        "Titre" : nom_entre,
                        "Description" : description_entre,
                        "Link" : link_entre
                    }}
                )
                print("f")
            # on redirige vers la page d'admin
            return redirect("/admin_games")



# exemple de requete find_one 
@app.route("/profil/delete", methods=["POST"])
def supprimer_profil():
    if "utilisateur" in session:
        mes_utilisateurs = mongo.bdd.utilisateurs
        # Supprime l'utilisateur basé sur le pseudo dans la session
        resultat = mes_utilisateurs.delete_one({"pseudo": session["utilisateur"]})
        if resultat.deleted_count > 0:
            print(f"Utilisateur {session['utilisateur']} supprimé avec succès.")
            session.clear()  # Supprime la session après suppression de l'utilisateur
            return redirect("/")
        else:
            print(f"Aucun utilisateur trouvé avec le pseudo {session['utilisateur']}.")
            return redirect("/profil")  # Redirige vers le profil si la suppression échoue
    else:
        print("Aucun utilisateur connecté.")
        return redirect("/login")  # Redirige vers la page de connexion si non connecté


@app.route("/filter", methods=["GET"])
def filter_games():
    game_type = request.args.get("type", "").lower()  # Récupère le type sélectionné
    mes_jeux = mongo.bdd.games  # Collection MongoDB contenant les jeux
    
   
    # Vérifiez si un type a été sélectionné
    if game_type:
        # Filtrer les jeux par type
        filtered_games = list(mes_jeux.find({"type": {"$regex": f"^{game_type}$", "$options": "i"}}))
        print(f"Filtered games: {filtered_games}")  # Debug : Affiche les jeux filtrés
    else:
        filtered_games = []
        print("No type provided or no games found.")  # Debug : Aucun type sélectionné

    return render_template("filter_results.html", games=filtered_games, game_type=game_type)


@app.route("/login" , methods = ["GET" , "POST"])
def login() :
    if request.method == "GET" : 
        return render_template("login.html")
    
    pseudo_entre = request.form["input_pseudo"]
    mdp_entre = request.form["input_mdp"]

    mes_utilisateurs = mongo.bdd.utilisateurs
    utilisateur = mes_utilisateurs.find_one({"pseudo" : pseudo_entre})
    

    if not utilisateur : 
        return render_template("login.html" , erreur = "The user does not exist or the password is incorrect")
    elif mdp_entre != utilisateur["mdp"] : 
        return render_template("login.html" , erreur = "The user does not exist or the password is incorrect" )
    else :
        session["utilisateur"] = pseudo_entre
        return redirect("/")

@app.route("/infos")
def infos() :
    return "ici on mettra toutes les infos"

@app.route("/nouvelle-annonce" , methods = ["GET","POST"])
def nouvelleannonce():
    if request.method == "GET" :
        mes_utilisateurs = mongo.bdd.utilisateurs
        utilisateur = mes_utilisateurs.find_one({"pseudo" : session["utilisateur"]})
    
        return render_template("newpost.html")
    else:
        # 1 : on recupere les informations  entreees dans les boites (input)
        print("1")
        titre_entre = request.form["input_titre"]
        description_entre = request.form["input_description"]
        image_entre = request.form["input_image"]
        
        if image_entre == "" : 
            image_entre = "https://images.a-qui-s.fr/image/upload/v1725461325/BLOG/Capture_d_e%CC%81cran_2024-09-04_a%CC%80_16.47.08.png"
        #2 : on gere tous les cas d'erreur 
        print("2")
        mes_utilisateurs = mongo.bdd.utilisateurs
        utilisateur = mes_utilisateurs.find_one({"pseudo" :session["utilisateur"]})
        if titre_entre == "" : 
            return render_template("newpost.html" , erreur = "Please enter a title")
        elif len(description_entre) < 10 : 
            return render_template("newpost" , erreur = "Description must be at least 6 characters long")
        else :    

        #3 : on cree le compte utilisateur
            print("3")
            mes_annonces = mongo.bdd.annonce 
            mes_annonces.insert_one({
                "titre" : titre_entre,
                "description" : description_entre,
                "image" : image_entre,
                "auteur" : utilisateur["pseudo"],
                "date" : datetime.now()
            })
            print("4")
            return redirect("/")


    
        
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")




if __name__ == "__main__":
    app.run("0.0.0.0", 81, debug=True)