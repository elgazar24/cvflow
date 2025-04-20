from flask import Blueprint
from .route_names import *



routes = Blueprint('routes', __name__)


class RoutePath:

    _home_dir = f'/{templates_home_dir_name}'
    home_index = f'{_home_dir}/{home_index_file_name}'
    home_style = f'{static_css_dir_name}{_home_dir}/{home_style_file_name}'
    home_script = f'{static_js_dir_name}{_home_dir}/{home_script_file_name}'


    _auth_dir = f'/{templates_auth_dir_name}'
    login_index = f'{_auth_dir}/{login_index_file_name}'
    login_style = f'{static_css_dir_name}{_auth_dir}/{login_style_file_name}'
    login_script = f'{static_js_dir_name}{_auth_dir}/{login_script_file_name}'

    register_index = f'{_auth_dir}/{register_index_file_name}'
    register_style = f'{static_css_dir_name}{_auth_dir}/{register_style_file_name}'
    register_script = f'{static_js_dir_name}{_auth_dir}/{register_script_file_name}'

    forgot_password_index = f'{_auth_dir}/{forgot_password_index_file_name}'
    forgot_password_style = f'{static_css_dir_name}{_auth_dir}/{forgot_password_style_file_name}'
    forgot_password_script = f'{static_js_dir_name}{_auth_dir}/{forgot_password_script_file_name}'


    _dashboard_dir = f'/{templates_dashboard_dir_name}'
    dashboard_index = f'{_dashboard_dir}/{dashboard_index_file_name}'
    dashboard_style = f'{static_css_dir_name}{_dashboard_dir}/{dashboard_style_file_name}'
    dashboard_script = f'{static_js_dir_name}{_dashboard_dir}/{dashboard_script_file_name}'


    _errors_dir = f'/{templates_errors_dir_name}'
    errors_404_index = f'{_errors_dir}/{errors_404_index_file_name}'
    errors_404_style = f'{static_css_dir_name}{_errors_dir}/{errors_404_style_file_name}'
    errors_404_script = f'{static_js_dir_name}{_errors_dir}/{errors_404_script_file_name}'

    errors_500_index = f'{_errors_dir}/{errors_500_index_file_name}'
    errors_500_style = f'{static_css_dir_name}{_errors_dir}/{errors_500_style_file_name}'
    errors_500_script = f'{static_js_dir_name}{_errors_dir}/{errors_500_script_file_name}'


    _base_dir = f'/{templates_base_dir_name}'
    base_index = f'{_base_dir}/{base_index_file_name}'
    base_style = f'{static_css_dir_name}{_base_dir}/{base_style_file_name}'
    base_script = f'{static_js_dir_name}{_base_dir}/{base_script_file_name}'


    _images_dir = f'/{static_images_dir_name}'
    author_photos_dir = f'{_images_dir}/{static_images_author_photos_dir_name}'
    author_photo = f'{author_photos_dir}/{author_photo_file_name}'

    logo = f'{_images_dir}/'


    _favicon_dir = f'/{static_images_favicon_dir_name}'
    favicon = f'{_images_dir}{_favicon_dir}/{favicon_file_name}'
    android_chrome_192x192 = f'{_images_dir}{_favicon_dir}/{android_chrome_192x192_file_name}'
    android_chrome_512x512 = f'{_images_dir}{_favicon_dir}/{android_chrome_512x512_file_name}'
    site_webmanifest = f'{_images_dir}{_favicon_dir}/{site_webmanifest_file_name}'
    favicon_16x16 = f'{_images_dir}{_favicon_dir}/{favicon_16x16_file_name}'
    favicon_32x32 = f'{_images_dir}{_favicon_dir}/{favicon_32x32_file_name}'
    apple_touch_icon = f'{_images_dir}{_favicon_dir}/{apple_touch_icon_file_name}'


    



