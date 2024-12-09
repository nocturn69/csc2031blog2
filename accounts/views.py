from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from accounts.forms import RegistrationForm, LoginForm
from config import User, db, limiter
from flask_limiter.util import get_remote_address
import pyotp, io, base64
import qrcode
accounts_bp = Blueprint('accounts', __name__, template_folder='templates')


  # Library for generating MFA keys

@accounts_bp.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', category="danger")
            return render_template('accounts/registration.html', form=form)

        mfa_key = pyotp.random_base32()  # Generate MFA key
        new_user = User(
            email=form.email.data,
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            phone=form.phone.data,
            password=form.password.data,
            mfa_key=mfa_key
        )

        db.session.add(new_user)
        db.session.commit()

        # Generate the QR code URI
        totp = pyotp.TOTP(mfa_key)
        qr_code_uri = totp.provisioning_uri(form.email.data, issuer_name="YourAppName")

        flash('Account Created. Please set up MFA.', category='success')
        return redirect(url_for('accounts.mfa_setup', mfa_key=mfa_key, qr_code_uri=qr_code_uri))

    return render_template('accounts/registration.html', form=form)


@accounts_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()

    if 'attempts' not in session:
        session['attempts'] = 3

    if session['attempts'] <= 0:
        flash('Account locked. Please unlock your account to try again.', category='danger')
        return redirect(url_for('accounts.locked'))

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or user.password != form.password.data:
            session['attempts'] -= 1
            flash(f'Invalid email or password. Attempts remaining: {session["attempts"]}', category='danger')
            return redirect(url_for('accounts.login'))


        # Verify MFA PIN
        mfa_pin = form.pin.data  # Assume form includes MFA PIN field
        if not user.verifypin(mfa_pin):
            session['attempts'] -= 1
            flash(f'Invalid MFA PIN. Attempts remaining: {session["attempts"]}', category='danger')
            return redirect(url_for('accounts.login'))

        # Mark MFA as enabled upon first successful authentication
        if not user.mfa_enabled:
            user.mfa_enabled = True
            db.session.commit()

        session['attempts'] = 3
        flash('Successfully logged in!', category='success')
        return redirect(url_for('accounts.account'))

    return render_template('accounts/login.html', form=form)


@accounts_bp.route('/account')
def account():
    return render_template('accounts/account.html')


@accounts_bp.route('/mfa_setup')
def mfa_setup():
    mfa_key = request.args.get('mfa_key')
    qr_code_uri = request.args.get('qr_code_uri')

    # Generate QR code
    qr_img = qrcode.make(qr_code_uri)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)
    qr_code_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template('accounts/mfa_setup.html', mfa_key=mfa_key, qr_code_data=qr_code_data)
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

