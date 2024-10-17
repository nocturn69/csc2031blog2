from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from accounts.forms import RegistrationForm, LoginForm
from config import User, db
accounts_bp = Blueprint('accounts', __name__, template_folder='templates')


@accounts_bp.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()

    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', category="danger")
            return render_template('accounts/registration.html', form=form)

        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        )

        db.session.add(new_user)
        db.session.commit()

        flash('Account Created', category='success')
        return redirect(url_for('accounts.login'))

    return render_template('accounts/registration.html', form=form)


@accounts_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if 'attempts' not in session:
        session['attempts'] = 3  # Start with 3 attempts

        # Check if attempts have run out and prevent login if so
    if session['attempts'] <= 0:
        flash('Account locked. Please unlock your account to try again.', category='danger')
        return redirect(url_for('accounts.locked'))  # Redirect to the locked page

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or user.password != form.password.data:
            session['attempts'] -= 1  # Reduce attempts
            flash(f'Invalid email or password. Attempts remaining: {session["attempts"]}', category='danger')
            return redirect(url_for('accounts.login'))  # Reload login form

        # Successful login - Reset attempts and redirect
        session['attempts'] = 3  # Reset attempts on successful login
        flash('You have successfully logged in!', category='success')
        return redirect(url_for('accounts.account'))

    return render_template('accounts/login.html', form=form)

@accounts_bp.route('/account')
def account():
    return render_template('accounts/account.html')

@accounts_bp.route('/LOCKEDACC')
def locked():
    """Page shown when the account is locked."""
    return render_template('accounts/LOCKEDACC.html')

@accounts_bp.route('/unlock', methods=['POST'])
def unlock():
    """Unlock the account and reset attempts."""
    session['attempts'] = 3  # Reset attempts
    flash('Your account has been unlocked. You can try logging in again.', category='info')
    return redirect(url_for('accounts.login'))

