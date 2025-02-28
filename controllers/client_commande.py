#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g
from datetime import datetime
from connexion_db import get_db

client_commande = Blueprint('client_commande', __name__,
                        template_folder='templates')


# validation de la commande : partie 2 -- vue pour choisir les adresses (livraision et facturation)
@client_commande.route('/client/commande/valide', methods=['POST'])
def client_commande_valide():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    sql = ''' selection des articles d'un panier 
    '''
    articles_panier = []
    if len(articles_panier) >= 1:
        sql = ''' calcul du prix total du panier '''
        prix_total = None
    else:
        prix_total = None
    # etape 2 : selection des adresses
    return render_template('client/boutique/panier_validation_adresses.html'
                           #, adresses=adresses
                           , articles_panier=articles_panier
                           , prix_total= prix_total
                           , validation=1
                           #, id_adresse_fav=id_adresse_fav
                           )


@client_commande.route('/client/commande/add', methods=['POST'])
def client_commande_add():
    mycursor = get_db().cursor()

    # choix de(s) (l')adresse(s)

    id_client = session['id_user']
    sql = ''' selection du contenu du panier de l'utilisateur '''
    items_ligne_panier = []
    # if items_ligne_panier is None or len(items_ligne_panier) < 1:
    #     flash(u'Pas d\'articles dans le ligne_panier', 'alert-warning')
    #     return redirect('/client/article/show')
                                           # https://pynative.com/python-mysql-transaction-management-using-commit-rollback/
    #a = datetime.strptime('my date', "%b %d %Y %H:%M")

    sql = ''' creation de la commande '''

    sql = '''SELECT last_insert_id() as last_insert_id'''
    # numéro de la dernière commande
    for item in items_ligne_panier:
        sql = ''' suppression d'une ligne de panier '''
        sql = "  ajout d'une ligne de commande'"

    get_db().commit()
    flash(u'Commande ajoutée','alert-success')
    return redirect('/client/article/show')




@client_commande.route('/client/commande/show', methods=['get','post'])
def client_commande_show():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    sql = '''SELECT commande.id_commande, commande.date_achat, etat.libelle AS etat, 
                    SUM(ligne_commande.prix * ligne_commande.quantite) AS prix_total,
                    SUM(ligne_commande.quantite) AS nbr_articles
             FROM commande 
             JOIN ligne_commande ON commande.id_commande = ligne_commande.commande_id 
             JOIN etat ON commande.etat_id = etat.id_etat
             WHERE commande.utilisateur_id = %s 
             GROUP BY commande.id_commande, commande.date_achat, etat.libelle
             ORDER BY commande.date_achat DESC'''
    mycursor.execute(sql, (id_client,))
    commandes = mycursor.fetchall()

    articles_commande = None
    id_commande = request.args.get('id_commande', None)
    prix_total_commande = None
    nbr_articles_commande = None
    
    if id_commande != None:
        print(id_commande)
        sql = '''SELECT ligne_commande.quantite, ligne_commande.prix, vetement.nom_vetement AS nom, 
                      vetement.photo AS image, ligne_commande.prix * ligne_commande.quantite AS prix_ligne
                 FROM ligne_commande 
                 JOIN vetement ON ligne_commande.vetement_id = vetement.id_vetement 
                 WHERE ligne_commande.commande_id = %s'''
        mycursor.execute(sql, (id_commande,))
        articles_commande = mycursor.fetchall()

        # Calcul du prix total et du nombre d'articles de la commande sélectionnée
        sql = '''SELECT SUM(ligne_commande.prix * ligne_commande.quantite) AS prix_total,
                        SUM(ligne_commande.quantite) AS nbr_articles
                 FROM ligne_commande 
                 WHERE ligne_commande.commande_id = %s'''
        mycursor.execute(sql, (id_commande,))
        result = mycursor.fetchone()
        prix_total_commande = result['prix_total']
        nbr_articles_commande = result['nbr_articles']
        
    # Traitement pour changer l'état de la commande
    if request.method == 'POST' and request.form.get('id_commande') and request.form.get('etat_id'):
        id_commande_update = request.form.get('id_commande')
        nouvel_etat_id = request.form.get('etat_id')
        sql = '''UPDATE commande SET etat_id = %s WHERE id_commande = %s'''
        mycursor.execute(sql, (nouvel_etat_id, id_commande_update))
        get_db().commit()
        flash(u'État de la commande mis à jour', 'alert-success')
        return redirect('/client/commande/show')

    # Récupération des états possibles
    sql = '''SELECT id_etat, libelle FROM etat ORDER BY id_etat'''
    mycursor.execute(sql)
    etats = mycursor.fetchall()

    return render_template('client/commandes/show.html'
                           , commandes=commandes
                           , articles_commande=articles_commande
                           , id_commande_selected=id_commande
                           , prix_total_commande=prix_total_commande
                           , nbr_articles_commande=nbr_articles_commande
                           , etats=etats
                           )

