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
    
    return redirect('/client/envies/show')

@client_liste_envies.route('/client/envies/show', methods=['get'])
def client_liste_envies_show():
    mycursor = get_db().cursor()
    id_client = session['id_user']
    
    sql_liste_envies = '''
    SELECT v.*, le.date_update 
    FROM vetement v
    JOIN liste_envie le ON v.id_vetement = le.id_vetement
    WHERE le.id_utilisateur = %s
    ORDER BY le.date_update DESC
    '''
    mycursor.execute(sql_liste_envies, (id_client,))
    articles_liste_envies = mycursor.fetchall()
    
    sql_historique = '''
    SELECT v.*, h.date_consultation 
    FROM vetement v
    JOIN historique h ON v.id_vetement = h.id_vetement
    WHERE h.id_utilisateur = %s
    ORDER BY h.date_consultation DESC
    '''
    mycursor.execute(sql_historique, (id_client,))
    articles_historique = mycursor.fetchall()
    
    return render_template('client/liste_envies/liste_envies_show.html',
                         articles_liste_envies=articles_liste_envies,
                         articles_historique=articles_historique)



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
  
    return redirect('/client/envies/show')
