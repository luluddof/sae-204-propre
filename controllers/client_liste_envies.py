#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g

from connexion_db import get_db

client_liste_envies = Blueprint('client_liste_envies', __name__,
                        template_folder='templates')


@client_liste_envies.route('/client/envie/add', methods=['get'])
def client_liste_envies_add():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.args.get('id_article')
    
    # Vérifier si l'article est déjà dans la liste d'envies
    sql_check = '''
    SELECT * FROM liste_envie 
    WHERE id_utilisateur = %s AND id_vetement = %s
    '''
    mycursor.execute(sql_check, (id_client, id_article))
    existe = mycursor.fetchone()
    
    if not existe:
        # Ajouter à la liste d'envies
        sql_insert = '''
        INSERT INTO liste_envie (id_vetement, id_utilisateur, date_update)
        VALUES (%s, %s, CURDATE())
        '''
        mycursor.execute(sql_insert, (id_article, id_client))
        get_db().commit()
        flash('Article ajouté à la liste des souhaits')
    
    return redirect('/client/article/show')

@client_liste_envies.route('/client/envie/delete', methods=['get'])
def client_liste_envies_delete():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.args.get('id_article')
    
    sql_delete = '''
    DELETE FROM liste_envie 
    WHERE id_utilisateur = %s AND id_vetement = %s
    '''
    mycursor.execute(sql_delete, (id_client, id_article))
    get_db().commit()
    flash('Article retiré de la liste des souhaits')
    
    return redirect('/client/envies/show')

@client_liste_envies.route('/client/envies/show', methods=['get'])
def client_liste_envies_show():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    
    # Récupération des articles de la liste d'envies
    sql_liste_envies = '''
    SELECT v.*, le.date_update 
    FROM vetement v
    JOIN liste_envie le ON v.id_vetement = le.id_vetement
    WHERE le.id_utilisateur = %s
    ORDER BY le.date_update DESC
    '''
    mycursor.execute(sql_liste_envies, (id_client,))
    articles_liste_envies = mycursor.fetchall()

    # Calcul du nombre d'articles dans la liste d'envies
    sql_count_wishlist = '''
    SELECT COUNT(*) as nb_articles
    FROM liste_envie
    WHERE id_utilisateur = %s
    '''
    mycursor.execute(sql_count_wishlist, (id_client,))
    nb_liste_envies = mycursor.fetchone()['nb_articles']

    # Calcul du nombre d'articles dans l'historique
    sql_count_historique = '''
    SELECT COUNT(*) as nb_articles
    FROM historique
    WHERE id_utilisateur = %s
    '''
    mycursor.execute(sql_count_historique, (id_client,))
    nb_liste_historique = mycursor.fetchone()['nb_articles']
    
    # Récupération de l'historique
    sql_historique = '''
    SELECT v.*, h.date_consultation 
    FROM vetement v
    JOIN historique h ON v.id_vetement = h.id_vetement
    WHERE h.id_utilisateur = %s
    ORDER BY h.date_consultation DESC
    LIMIT 6
    '''
    mycursor.execute(sql_historique, (id_client,))
    articles_historique = mycursor.fetchall()
    
    return render_template('client/liste_envies/liste_envies_show.html',
                         articles_liste_envies=articles_liste_envies,
                         articles_historique=articles_historique,
                         nb_liste_envies=nb_liste_envies,
                         nb_liste_historique=nb_liste_historique)



def client_historique_add(article_id, client_id):
    mycursor = get_db().cursor()
    client_id = session['id_user']
    # rechercher si l'article pour cet utilisateur est dans l'historique
    # si oui mettre
    sql ='''   '''
    mycursor.execute(sql, (article_id, client_id))
    historique_produit = mycursor.fetchall()
    sql ='''   '''
    mycursor.execute(sql, (client_id))
    historiques = mycursor.fetchall()


@client_liste_envies.route('/client/envies/up', methods=['get'])
@client_liste_envies.route('/client/envies/down', methods=['get'])
@client_liste_envies.route('/client/envies/last', methods=['get'])
@client_liste_envies.route('/client/envies/first', methods=['get'])
def client_liste_envies_article_move():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.args.get('id_article')
    action = request.args.get('action')
    
    # Récupérer la position actuelle de l'article
    sql_position = '''
    SELECT date_update
    FROM liste_envie
    WHERE id_utilisateur = %s AND id_vetement = %s
    '''
    mycursor.execute(sql_position, (id_client, id_article))
    current_date = mycursor.fetchone()['date_update']
    
    if action == 'up':
        # Trouver l'article juste au-dessus (date plus récente)
        sql_prev = '''
        SELECT id_vetement, date_update
        FROM liste_envie
        WHERE id_utilisateur = %s
        AND date_update > %s
        ORDER BY date_update ASC
        LIMIT 1
        '''
        mycursor.execute(sql_prev, (id_client, current_date))
        prev_article = mycursor.fetchone()
        
        if prev_article:
            # Échanger les dates
            sql_update = '''
            UPDATE liste_envie
            SET date_update = CASE
                WHEN id_vetement = %s THEN %s
                WHEN id_vetement = %s THEN %s
            END
            WHERE id_utilisateur = %s 
            AND id_vetement IN (%s, %s)
            '''
            mycursor.execute(sql_update, (
                id_article, prev_article['date_update'],
                prev_article['id_vetement'], current_date,
                id_client,
                id_article, prev_article['id_vetement']
            ))
            
    elif action == 'down':
        # Trouver l'article juste en-dessous (date moins récente)
        sql_next = '''
        SELECT id_vetement, date_update
        FROM liste_envie
        WHERE id_utilisateur = %s
        AND date_update < %s
        ORDER BY date_update DESC
        LIMIT 1
        '''
        mycursor.execute(sql_next, (id_client, current_date))
        next_article = mycursor.fetchone()
        
        if next_article:
            # Échanger les dates
            sql_update = '''
            UPDATE liste_envie
            SET date_update = CASE
                WHEN id_vetement = %s THEN %s
                WHEN id_vetement = %s THEN %s
            END
            WHERE id_utilisateur = %s 
            AND id_vetement IN (%s, %s)
            '''
            mycursor.execute(sql_update, (
                id_article, next_article['date_update'],
                next_article['id_vetement'], current_date,
                id_client,
                id_article, next_article['id_vetement']
            ))
            
    elif action == 'first':
        # Trouver l'article le plus récent
        sql_max = '''
        SELECT id_vetement, date_update
        FROM liste_envie
        WHERE id_utilisateur = %s
        ORDER BY date_update DESC
        LIMIT 1
        '''
        mycursor.execute(sql_max, (id_client,))
        max_article = mycursor.fetchone()
        
        if max_article and max_article['id_vetement'] != id_article:
            # Échanger les dates
            sql_update = '''
            UPDATE liste_envie
            SET date_update = CASE
                WHEN id_vetement = %s THEN %s
                WHEN id_vetement = %s THEN %s
            END
            WHERE id_utilisateur = %s 
            AND id_vetement IN (%s, %s)
            '''
            mycursor.execute(sql_update, (
                id_article, max_article['date_update'],
                max_article['id_vetement'], current_date,
                id_client,
                id_article, max_article['id_vetement']
            ))
        
    elif action == 'last':
        # Trouver l'article le plus ancien
        sql_min = '''
        SELECT id_vetement, date_update
        FROM liste_envie
        WHERE id_utilisateur = %s
        ORDER BY date_update ASC
        LIMIT 1
        '''
        mycursor.execute(sql_min, (id_client,))
        min_article = mycursor.fetchone()
        
        if min_article and min_article['id_vetement'] != id_article:
            # Échanger les dates
            sql_update = '''
            UPDATE liste_envie
            SET date_update = CASE
                WHEN id_vetement = %s THEN %s
                WHEN id_vetement = %s THEN %s
            END
            WHERE id_utilisateur = %s 
            AND id_vetement IN (%s, %s)
            '''
            mycursor.execute(sql_update, (
                id_article, min_article['date_update'],
                min_article['id_vetement'], current_date,
                id_client,
                id_article, min_article['id_vetement']
            ))
    
    get_db().commit()
    return redirect('/client/envies/show')

@client_liste_envies.route('/client/panier/add', methods=['POST'])
def client_panier_add():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    id_article = request.form.get('id_article')
    quantite = request.form.get('quantite', 1, type=int)

    # Ajouter au panier
    sql_panier = '''
    INSERT INTO ligne_panier (utilisateur_id, vetement_id, quantite, date_ajout)
    VALUES (%s, %s, %s, CURDATE())
    '''
    mycursor.execute(sql_panier, (id_client, id_article, quantite))

    # Retirer de la liste d'envies
    sql_delete_wishlist = '''
    DELETE FROM liste_envie 
    WHERE id_utilisateur = %s AND id_vetement = %s
    '''
    mycursor.execute(sql_delete_wishlist, (id_client, id_article))

    get_db().commit()
    flash('Article ajouté au panier et retiré de la liste des souhaits')
    return redirect('/client/article/show')
