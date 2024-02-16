from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
import requests


app = Flask(__name__)

# Set the secret key for the session
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Database connection parameters
dbname = "postgres"
user = "postgres"
password = "Itv4312"
host = "localhost"  # or your host if it's different
port = "5432"  # or your port if it's different



# Function to execute SQL query and return results
def execute_query(query, data=None):
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cur = conn.cursor()
    if data:
        cur.execute(query, data)
    else:
        cur.execute(query)
    if cur.description:
        results = cur.fetchall()
    else:
        results = None
    conn.commit()
    cur.close()
    conn.close()
    return results

@app.route('/')
def index():
    return render_template('index.html')

# Function to authenticate user
def authenticate_user(email, password):
    query = "SELECT * FROM users WHERE email = %s AND password = %s"
    data = (email, password)
    result = execute_query(query, data)
    return len(result) > 0

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    if authenticate_user(email, password):
        session['user_email'] = email  # Store the user's email in the session
        return redirect(url_for('search'))
    else:
        return "Invalid email or password"


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        # Insert the user data into the database
        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        data = (name, email, password)
        execute_query(query, data)
        return "Signup successful! Please <a href='/'>login</a>."
    return render_template('signup.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        # Build SQL query to search for books matching the query
        search_query = (
            "SELECT * FROM books WHERE "
            "isbn ILIKE '%{query}%' OR "
            "title ILIKE '%{query}%' OR "
            "author ILIKE '%{query}%'"
        ).format(query=query)
        results = execute_query(search_query)
        if results:
            return render_template('search_results.html', results=results)  # Pass results to the template
        else:
            return "No results found."
    return render_template('search.html')


@app.route('/book/<isbn>', methods=['GET'])
def book_details(isbn):
    # Fetch book details from the database using the ISBN
    query = "SELECT * FROM books WHERE isbn = '{}';".format(isbn)
    book_details = execute_query(query)
    
    if book_details:
        # Get the email of the logged-in user from the session
        user_email = session.get('user_email')  # Change 'user_email' to match your session variable

        # Fetch reviews and ratings for the book
        review_query = "SELECT review, rating FROM book_reviews WHERE isbn = '{}';".format(isbn)
        reviews = execute_query(review_query)
        
        # Fetch book data from Google Books API
        google_books_url = "https://www.googleapis.com/books/v1/volumes"
        params = {"q": "isbn:{}".format(isbn)}
        response = requests.get(google_books_url, params=params)
        book_data = response.json()["items"][0]["volumeInfo"]
        
        # Extract average rating and number of ratings from book data
        average_rating = book_data.get("averageRating")
        ratings_count = book_data.get("ratingsCount")
        
        # Render template with book details, user email, average rating, and ratings count
        return render_template('book_details.html', book=book_details[0], user_email=user_email, reviews=reviews, 
                               average_rating=average_rating, ratings_count=ratings_count)
    else:
        return "Book not found"

    
@app.route('/save_review/<isbn>', methods=['POST'])
def save_review(isbn):
    email = request.form['email']  # Assuming you have a form field for the user's email
    review = request.form['review']
    rating = int(request.form['rating'])  # Assuming you have a form field for the rating

    try:
        # Check if the user has already reviewed the book
        query = "SELECT * FROM book_reviews WHERE email = %s AND isbn = %s"
        data = (email, isbn)
        existing_review = execute_query(query, data)
        if existing_review:
            return "You have already reviewed this book."

        # Insert the new review into the book_reviews table
        insert_query = "INSERT INTO book_reviews (email, isbn, review, rating) VALUES (%s, %s, %s, %s)"
        insert_data = (email, isbn, review, rating)
        execute_query(insert_query, insert_data)

        return redirect(url_for('book_details', isbn=isbn))  # Redirect to the book details page after saving the review
    except psycopg2.Error as e:
        error_message = "An error occurred while saving the review: {}".format(str(e))
        return error_message

@app.route('/logout')
def logout():
    # Clear the session or any other logout logic
    # For example, you can clear the user session like this:
    # session.clear()
    return redirect(url_for('index'))  # Redirect to the index page after logout


@app.route('/api/<isbn>')
def get_book_info(isbn):
    # Make a request to the Google Books API
    response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
    if response.status_code == 200:
        # Parse the JSON response
        book_data = response.json()
        if 'items' in book_data:
            book_info = book_data['items'][0]['volumeInfo']
            # Extract necessary fields from the response
            title = book_info.get('title')
            author = ', '.join(book_info.get('authors', []))
            published_date = book_info.get('publishedDate')
            isbn_10 = book_info['industryIdentifiers'][0]['identifier'] if book_info.get('industryIdentifiers') else None
            isbn_13 = book_info['industryIdentifiers'][1]['identifier'] if book_info.get('industryIdentifiers') else None
            review_count = book_info.get('ratingsCount')
            average_rating = book_info.get('averageRating')
            # Construct JSON response
            json_response = {
                "title": title,
                "author": author,
                "publishedDate": published_date,
                "ISBN_10": isbn_10,
                "ISBN_13": isbn_13,
                "reviewCount": review_count,
                "averageRating": average_rating 
            }
            return jsonify(json_response)  # Return JSON response
    # If book not found or error occurred, return appropriate response
    return jsonify({"404 error": "Book not found or error occurred"}), 404



if __name__ == '__main__':
    app.run(debug=True)

