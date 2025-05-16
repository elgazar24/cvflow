
from flask import Blueprint
from flask import render_template
from routes.route_path import RoutePath



about = Blueprint('about', __name__)



@about.route('/about')
def about_index():
    breadcrumbs = [
        {"title": "About", "url": "/about"},
    ]
    return render_template( RoutePath.about_index , breadcrumbs=breadcrumbs)
