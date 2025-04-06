#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, abort, flash, session

from connexion_db import get_db

client_article = Blueprint('client_article', __name__,
                        template_folder='templates')

@client_article.route('/client/index')
@client_article.route('/client/article/show')              # remplace /client
def client_article_show():                                 # remplace client_index
    mycursor = get_db().cursor()
    id_client = session['id_user']

    # Récupérer la liste des souhaits de l'utilisateur
    sql_liste_envies = '''
    SELECT id_vetement 
    FROM liste_envie 
    WHERE id_utilisateur = %s
    '''
    mycursor.execute(sql_liste_envies, (id_client,))
    liste_envies = [item['id_vetement'] for item in mycursor.fetchall()]

    # Récupération des articles avec leur stock actuel
    sql = '''
    SELECT vetement.id_vetement, vetement.nom_vetement, vetement.prix_vetement, 
           vetement.photo, vetement.description, vetement.matiere, vetement.stock,
           type_vetement.libelle_type_vetement, type_vetement.id_type_vetement, 
           taille.libelle_taille
    FROM vetement
    LEFT JOIN type_vetement ON vetement.type_vetement_id = type_vetement.id_type_vetement
    LEFT JOIN taille ON vetement.taille_id = taille.id_taille
    '''
    
    list_param = []
    
    # Application des filtres depuis la session
    if 'filter_word' in session and session['filter_word']:
        sql += " WHERE vetement.nom_vetement LIKE %s"
        list_param.append(f"%{session['filter_word']}%")
    elif 'filter_types' in session and session['filter_types']:
        sql += " WHERE type_vetement.id_type_vetement IN ({})".format(','.join(['%s'] * len(session['filter_types'])))
        list_param.extend(session['filter_types'])
    elif 'filter_prix_min' in session and session['filter_prix_min']:
        sql += " WHERE vetement.prix_vetement >= %s"
        list_param.append(session['filter_prix_min'])
    elif 'filter_prix_max' in session and session['filter_prix_max']:
        sql += " WHERE vetement.prix_vetement <= %s"
        list_param.append(session['filter_prix_max'])
    
    # Ajouter un ORDER BY pour trier les articles
    sql += " ORDER BY vetement.nom_vetement ASC"
    
    mycursor.execute(sql, tuple(list_param))
    articles = mycursor.fetchall()

    # Récupération des types de vêtements pour le formulaire de filtre
    sql_types = '''SELECT id_type_vetement, libelle_type_vetement FROM type_vetement'''
    mycursor.execute(sql_types)
    types_vetement = mycursor.fetchall()

    # Récupération du panier de l'utilisateur avec le stock actuel
    sql_panier = '''
    SELECT ligne_panier.vetement_id, ligne_panier.quantite, 
           vetement.nom_vetement, vetement.prix_vetement, vetement.photo, vetement.stock
    FROM ligne_panier
    JOIN vetement ON ligne_panier.vetement_id = vetement.id_vetement
    WHERE ligne_panier.utilisateur_id = %s
    ORDER BY ligne_panier.date_ajout DESC
    '''
    mycursor.execute(sql_panier, (id_client,))
    articles_panier = mycursor.fetchall()

    # Calcul du prix total du panier
    if len(articles_panier) >= 1:
        sql_prix_total = '''
        SELECT SUM(ligne_panier.quantite * vetement.prix_vetement) as prix_total
        FROM ligne_panier
        JOIN vetement ON ligne_panier.vetement_id = vetement.id_vetement
        WHERE ligne_panier.utilisateur_id = %s
        '''
        mycursor.execute(sql_prix_total, (id_client,))
        prix_total = mycursor.fetchone()['prix_total']
    else:
        prix_total = None
        
    return render_template('client/boutique/panier_article.html',
                           articles=articles,
                           articles_panier=articles_panier,
                           prix_total=prix_total,
                           items_filtre=types_vetement,
                           liste_envies=liste_envies)

@client_article.route('/client/panier/filtre', methods=['POST'])
def client_article_filtre():
    # Récupération des paramètres du formulaire
    filter_word = request.form.get('filter_word', '')
    filter_types = request.form.getlist('filter_types')
    filter_prix_min = request.form.get('filter_prix_min', '')
    filter_prix_max = request.form.get('filter_prix_max', '')
    
    # Stockage des filtres dans la session
    session['filter_word'] = filter_word
    session['filter_types'] = filter_types
    session['filter_prix_min'] = filter_prix_min
    session['filter_prix_max'] = filter_prix_max
    
    return redirect('/client/article/show')

@client_article.route('/client/panier/filtre/suppr', methods=['POST'])
def client_article_filtre_suppr():
    # Suppression des filtres de la session
    if 'filter_word' in session:
        session.pop('filter_word')
    if 'filter_types' in session:
        session.pop('filter_types')
    if 'filter_prix_min' in session:
        session.pop('filter_prix_min')
    if 'filter_prix_max' in session:
        session.pop('filter_prix_max')
    
    return redirect('/client/article/show')

@client_article.route('/client/panier/add', methods=['POST'])
def client_panier_add():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article')
    quantite = request.form.get('quantite', 1, type=int)

    # Vérifier si l'article est déjà dans le panier
    sql_check = '''
    SELECT quantite FROM ligne_panier 
    WHERE utilisateur_id = %s AND vetement_id = %s
    '''
    mycursor.execute(sql_check, (id_client, id_article))
    article_in_panier = mycursor.fetchone()

    if article_in_panier:
        # Mettre à jour la quantité
        sql_update = '''
        UPDATE ligne_panier SET quantite = quantite + %s
        WHERE utilisateur_id = %s AND vetement_id = %s
        '''
        mycursor.execute(sql_update, (quantite, id_client, id_article))
    else:
        # Ajouter l'article au panier
        sql_insert = '''
        INSERT INTO ligne_panier (utilisateur_id, vetement_id, quantite, date_ajout)
        VALUES (%s, %s, %s, CURDATE())
        '''
        mycursor.execute(sql_insert, (id_client, id_article, quantite))

    # Supprimer de la liste d'envies si présent
    sql_delete_wishlist = '''
    DELETE FROM liste_envie 
    WHERE id_utilisateur = %s AND id_vetement = %s
    '''
    mycursor.execute(sql_delete_wishlist, (id_client, id_article))

    get_db().commit()
    flash('Article ajouté au panier')
    return redirect('/client/article/show')

@client_article.route('/client/panier/delete', methods=['POST'])
def client_panier_delete():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_vetement = request.form.get('id_article', None)
    
    if id_vetement is None:
        flash('Erreur lors de la suppression de l\'article')
        return redirect('/client/article/show')
    
    # Vérifier la quantité actuelle
    sql_check = '''
    SELECT quantite FROM ligne_panier 
    WHERE utilisateur_id = %s AND vetement_id = %s
    '''
    mycursor.execute(sql_check, (id_client, id_vetement))
    article = mycursor.fetchone()
    
    if article and article['quantite'] > 1:
        # Diminuer la quantité
        sql_update = '''
        UPDATE ligne_panier SET quantite = quantite - 1
        WHERE utilisateur_id = %s AND vetement_id = %s
        '''
        mycursor.execute(sql_update, (id_client, id_vetement))
    else:
        # Supprimer l'article du panier
        sql_delete = '''
        DELETE FROM ligne_panier 
        WHERE utilisateur_id = %s AND vetement_id = %s
        '''
        mycursor.execute(sql_delete, (id_client, id_vetement))
    
    get_db().commit()
    flash('Article mis à jour dans le panier')
    return redirect('/client/article/show')

@client_article.route('/client/panier/delete/line', methods=['POST'])
def client_panier_delete_line():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_vetement = request.form.get('id_article', None)
    
    if id_vetement is None:
        flash('Erreur lors de la suppression de la ligne')
        return redirect('/client/article/show')
    
    # Supprimer la ligne du panier
    sql_delete = '''
    DELETE FROM ligne_panier 
    WHERE utilisateur_id = %s AND vetement_id = %s
    '''
    mycursor.execute(sql_delete, (id_client, id_vetement))
    
    get_db().commit()
    flash('Ligne supprimée du panier')
    return redirect('/client/article/show')

@client_article.route('/client/panier/vider', methods=['POST'])
def client_panier_vider():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    
    # Vider le panier
    sql_delete = '''
    DELETE FROM ligne_panier 
    WHERE utilisateur_id = %s
    '''
    mycursor.execute(sql_delete, (id_client,))
    
    get_db().commit()
    flash('Panier vidé avec succès')
    return redirect('/client/article/show')

@client_article.route('/client/article/details/<int:id_article>')
def client_article_details(id_article):
    mycursor = get_db().cursor()
    id_client = session['id_user']
    
    # Récupération des détails de l'article
    sql = '''
    SELECT v.*, tv.libelle_type_vetement, t.libelle_taille
    FROM vetement v
    LEFT JOIN type_vetement tv ON v.type_vetement_id = tv.id_type_vetement
    LEFT JOIN taille t ON v.taille_id = t.id_taille
    WHERE v.id_vetement = %s
    '''
    mycursor.execute(sql, (id_article,))
    article = mycursor.fetchone()
    
    if not article:
        flash('Article non trouvé')
        return redirect('/client/article/show')
    
    # Récupération du nombre d'autres clients ayant l'article dans leur wishlist
    sql_wishlist_count = '''
    SELECT COUNT(*) as nb_autres_clients
    FROM liste_envie
    WHERE id_vetement = %s AND id_utilisateur != %s
    '''
    mycursor.execute(sql_wishlist_count, (id_article, id_client))
    wishlist_count = mycursor.fetchone()
    
    # Récupération du nombre d'autres articles de la même catégorie dans la wishlist
    sql_same_category_wishlist = '''
    SELECT COUNT(*) as nb_autres_articles_meme_categorie
    FROM liste_envie le
    JOIN vetement v ON le.id_vetement = v.id_vetement
    WHERE le.id_utilisateur = %s 
    AND v.type_vetement_id = %s 
    AND v.id_vetement != %s
    '''
    mycursor.execute(sql_same_category_wishlist, (id_client, article['type_vetement_id'], id_article))
    same_category_wishlist = mycursor.fetchone()
    
    # Récupération du nombre de commandes pour cet article
    sql_commandes = '''
    SELECT COUNT(*) as nb_commandes_article
    FROM ligne_commande lc
    JOIN commande c ON lc.commande_id = c.id_commande
    WHERE lc.vetement_id = %s AND c.utilisateur_id = %s
    '''
    mycursor.execute(sql_commandes, (id_article, id_client))
    commandes_articles = mycursor.fetchone()
    
    # Vérifier si l'article est déjà dans l'historique
    sql_check_historique = '''
    SELECT COUNT(*) as count
    FROM historique
    WHERE id_vetement = %s AND id_utilisateur = %s
    '''
    mycursor.execute(sql_check_historique, (id_article, id_client))
    historique_exists = mycursor.fetchone()['count'] > 0
    
    # Gestion de l'historique
    if not historique_exists:
        # Compter le nombre d'articles dans l'historique
        sql_count_historique = '''
        SELECT COUNT(*) as count
        FROM historique
        WHERE id_utilisateur = %s
        '''
        mycursor.execute(sql_count_historique, (id_client,))
        count = mycursor.fetchone()['count']
        
        if count >= 6:
            # Supprimer l'article le plus ancien
            sql_delete_oldest = '''
            DELETE FROM historique
            WHERE id_utilisateur = %s
            ORDER BY date_consultation ASC
            LIMIT 1
            '''
            mycursor.execute(sql_delete_oldest, (id_client,))
        
        # Ajouter le nouvel article à l'historique
        sql_add_historique = '''
        INSERT INTO historique (id_vetement, id_utilisateur, date_consultation)
        VALUES (%s, %s, NOW())
        '''
        mycursor.execute(sql_add_historique, (id_article, id_client))
        get_db().commit()
    
    # Récupération de l'historique des consultations
    sql_historique = '''
    SELECT v.*, h.date_consultation, tv.libelle_type_vetement, t.libelle_taille
    FROM historique h
    JOIN vetement v ON h.id_vetement = v.id_vetement
    LEFT JOIN type_vetement tv ON v.type_vetement_id = tv.id_type_vetement
    LEFT JOIN taille t ON v.taille_id = t.id_taille
    WHERE h.id_utilisateur = %s
    ORDER BY h.date_consultation DESC
    '''
    mycursor.execute(sql_historique, (id_client,))
    historique = mycursor.fetchall()
    
    return render_template('client/article_info/article_details.html',
                         article=article,
                         commandes_articles=commandes_articles,
                         same_category_wishlist=same_category_wishlist,
                         wishlist_count=wishlist_count,
                         historique=historique)
