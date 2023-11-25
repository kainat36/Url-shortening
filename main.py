# importing libraries and modules
import random
import string
from io import BytesIO
import qrcode
from flask import Flask, render_template, request, redirect, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy

# creating instance of flask and establishing sql connection
app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shorturls.db'
db = SQLAlchemy(app)


# making of the database model for the ShortenedURL table
class ShortenedURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_url = db.Column(db.String(10), unique=True, nullable=False)
    long_url = db.Column(db.String(200), nullable=False)


# Define your models before creating the app context
with app.app_context():
    db.create_all()


# Generating a short URL
def generate_short_url(length=5):
    """This function generates a short URL of a specified length (default is 5 characters) using a combination of
     uppercase letters, lowercase letters, and digits"""
    chars = string.ascii_letters + string.digits
    short_url = ''.join(random.choice(chars) for _ in range(length))
    return short_url


# defining routes for the index page
@app.route('/', methods=['GET', 'POST'])
def index():
    """ This function handles the index page where user enter long url and customize the short url. it checks weather
    if the input url already exist or not if exist then return short url already exist.If the user wants to customize
    the short URL, it checks if the custom code already exists in the database. If not, it generates a new short URL
     and adds it to the database. Finally, it renders the index.html template with the list of all URLs."""
    if request.method == 'POST':
        long_url = request.form['long_url']
        customize = request.form['customize']

        existing_entry = ShortenedURL.query.filter_by(long_url=long_url).first()

        if existing_entry:
            return 'URL Already Exist'

        if customize:
            url = ShortenedURL.query.filter_by(short_url=customize).first()
            if url:
                return 'Short code already exists'

        short_url = generate_short_url()
        while ShortenedURL.query.filter_by(short_url=short_url).first() is not None:
            short_url = generate_short_url()

        new_url_entry = ShortenedURL(short_url=short_url, long_url=long_url)
        db.session.add(new_url_entry)
        db.session.commit()

        return {
            'shortened_url': short_url,
            'link': request.url_root
        }

    urls = ShortenedURL.query.all()
    return render_template("index.html", urls=urls)

# Route to test a shortened URL
@app.route('/test-url/<short_url>')
def test_url(short_url):
    url_entry = ShortenedURL.query.filter_by(short_url=short_url).first()
    if url_entry:
        return 'Success'
    return 'Failure'

# Route to redirect to the original URL
@app.route('/<short_url>')
def redirect_url(short_url):
    url_entry = ShortenedURL.query.filter_by(short_url=short_url).first()
    if url_entry:
        return redirect(url_entry.long_url)
    else:
        return "URL not found", 404

# Route to delete a URL
@app.route('/delete/<int:url_id>', methods=['DELETE'])
def delete_url(url_id):
    """Delete a URL based on its ID."""
    url = ShortenedURL.query.get_or_404(url_id)
    db.session.delete(url)
    db.session.commit()
    return {'success': True}

# Route to list all URLs
@app.route('/list-urls')
def list_urls():
    """display all urls in table"""
    urls = ShortenedURL.query.all()
    return {
        'urls': [{'id': url.id, 'shortened_url': url.short_url, 'long_url': url.long_url} for url in urls]
    }


# Route to generate a QR code for a given short URL
@app.route('/generate-qr/<short_url>')
def generate_qr_code(short_url):
    url_entry = ShortenedURL.query.filter_by(short_url=short_url).first()
    if url_entry:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url_entry.long_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        response = make_response(send_file(img_io, mimetype='image/png'))
        return response
    else:
        return "URL not found", 404


if __name__ == '__main__':
    app.run(debug=True)
