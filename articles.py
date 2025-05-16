from flask import Blueprint 
from flask import jsonify
from flask import render_template
from routes.route_path import RoutePath
import db_access



articles = Blueprint('articles', __name__)



@articles.route('/articles')
def  articles_index():
    breadcrumbs = [
        {"title": "Articles", "url": "/articles"},
    ]
    return render_template(RoutePath.articles_index , breadcrumbs=breadcrumbs)

