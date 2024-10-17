from config import app
from flask import render_template

@app.route('/')
def index():
    return render_template('home/index.html')


@app.errorhandler(429)
def rate_limit_exceeded(e):
    return render_template('Errors/Error Handling.html'), 429


if __name__ == '__main__':
    app.run()