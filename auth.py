from flask import Blueprint, render_template, redirect, url_for, flash , request
from forms import ForgotPasswordForm
from extensions import db
from werkzeug.security import generate_password_hash , check_password_hash
import secrets
from datetime import datetime, timedelta
from flask_mail import Message
from extensions import mail
from flask_login import login_user ,logout_user ,current_user ,login_required
from forms import RegistrationForm, LoginForm
from routes.route_path import RoutePath
import db_access



auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():

        user = db_access.get_user_by_email(form.email.data)
        if user:
            flash('Email address already exists', 'error')
            return render_template( RoutePath.register_index, form=form)
        
        user = db_access.get_user_by_username(form.username.data)
        if user:
            flash('Username already exists', 'error')
            return render_template( RoutePath.register_index, form=form)
        

        
        user = db_access.create_user(form.username.data, form.email.data, form.password.data)

        if not user:
            flash('Error creating user', 'error')
            return render_template( RoutePath.register_index, form=form)
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.signin'))
    
    elif form.errors:
        # Flush First Error
        if form.errors.popitem()[1][0] == 'Field must be between 4 and 20 characters long.':
            flash('Username must be between 4 and 20 characters long', 'error')
        else :
            flash(form.errors.popitem()[1][0], 'error')
        
        return render_template( RoutePath.register_index, form=form)

    else:
        return render_template( RoutePath.register_index, form=form)


from urllib.parse import urlparse, urljoin
def is_safe_url(target):
    """Check if the target URL is safe (internal)."""
    if not target or target == None:
        return False
    
    # Handle relative URLs (like /dashboard)
    if target.startswith(('/', './', '../')):
        return True
    
    # Handle full URLs
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@auth.route('/signin', methods=['GET', 'POST'])
def signin():

    signin_request = request

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db_access.get_user_by_email(form.email.data)
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)

            next_page = signin_request.args.get('next')
            
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('index'))
            
        flash('Invalid email or password', 'error')
    
    return render_template(RoutePath.login_index, form=form)


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = db_access.get_user_by_email(form.email.data)
        
        if user:
            # Generate reset token (expires in 1 hour)
            reset_token = secrets.token_urlsafe(32)
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send email (requires Flask-Mail setup)
            reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
            
            msg = Message(
                "Password Reset Request - CVFlow",
                sender="noreply@cvflow.live",
                recipients=[user.email]
            )
            
            msg.body = f"""
            To reset your password, visit the following link:
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you didn't request a password reset, please ignore this email.
            """
            
            try:
                mail.send(msg)
                flash('Password reset link sent to your email', 'success')
            except Exception as e:
                flash('Failed to send email. Please try again later.', 'danger')
        else:
            flash('If this email exists in our system, you will receive a reset link', 'success')
        
        return redirect(url_for('auth.forgot_password'))
    
    return render_template( RoutePath.forgot_password_index , form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index')) 