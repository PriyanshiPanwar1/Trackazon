import os
import time
import json
import requests
import pygame
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, render_template, request, flash, redirect, url_for, session, current_app
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # Automatically manage driver version
from models import User, PriceHistory

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key
app.config['DATABASE'] = 'price_tracker.db'  # Path to your SQLite database

# Load settings from the JSON file
def load_settings():
    with open('settings.json', 'r') as file:
        return json.load(file)

# Initialize sound for notifications
def init_sound(sound_path):
    pygame.mixer.init()
    pygame.mixer.music.load(sound_path)

# Send Telegram notification
def send_telegram_notification(chat_id, bot_token, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    requests.post(url, data=data)

# Check price function using Selenium
def checking_price(url, budget):
    options = Options()
    options.headless = True  # Run headless browser
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        time.sleep(2)  # Wait for page to load

        # Extract product title
        product_title_element = driver.find_element('id', 'productTitle')
        product_title = product_title_element.text.strip()

        # Extract product price
        product_price_element = driver.find_element('xpath', '//span[contains(@class, "a-price-whole")]')
        product_price = product_price_element.text.strip().replace(',', '')  # Clean price string

        # Clean and convert price to integer
        if not product_price:
            flash("Could not extract a valid price.")
            return None
        
        product_price = int(product_price)

        # Check if the price is below the budget
        should_buy = product_price < budget
        return {
            'title': product_title,
            'price': product_price,
            'should_buy': should_buy
        }

    except Exception as e:
        flash(f"Error fetching the product: {e}")
        return None
    finally:
        driver.quit()  # Close the browser

# Update price history for a specific product
def update_price_history(product_name, current_price):
    PriceHistory.add_price_history(product_name, current_price)  # Save price to DB

# Plot price history graph
def plot_price_history(product_name):
    history = PriceHistory.get_price_history(product_name)
    if not history:
        return  # No history to plot

    df = pd.DataFrame(history, columns=['id', 'product_name', 'price', 'timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['price'], marker='o')
    plt.title('Price History')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid()
    plt.tight_layout()

    # Save the plot
    plt.savefig('static/price_history.png')
    plt.close()

# Initialize the database
def init_db():
    with app.app_context():  # Create application context
        User.create_table()
        PriceHistory.create_table()

init_db()  # Call the init_db function directly

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    settings = load_settings()
    chat_id = settings['chat_id']
    bot_token = settings['bot_token']

    if request.method == 'POST':
        url = request.form['url']
        budget = float(request.form['budget'])

        # Check price and update history
        result = checking_price(url, budget)
        if result is None:
            return redirect(url_for('form'))  # Redirect if there's an error

        product_name = result['title']  # Get the product name from the result

        # Update the price history for the product
        update_price_history(product_name, result['price'])

        # Plotting price history
        plot_price_history(product_name)

        # Display results and notify if price drops below budget
        flash(f"Product Name: {result['title']}")
        flash(f"Price: ₹{result['price']}")
        flash(f"Should Buy: {'Yes' if result['should_buy'] else 'No'}")

        if result['should_buy']:
            pygame.mixer.music.play()
            send_telegram_notification(chat_id, bot_token, f"Price Alert! You can buy {result['title']} for ₹{result['price']}.")

        return render_template('form.html', result=result)  # Pass the actual result to the template

    return render_template('form.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/track')
def track():
    return render_template('track.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Logic to handle the message (e.g., send an email, save to database, etc.)
        flash('Message sent successfully!')
        return redirect(url_for('contact'))  # Redirect after POST to avoid form re-submission
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.get_user(username)
        if user and user[2] == password:  # Check if password matches
            session['username'] = username
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.add_user(username, password):
            flash('Registration successful! You can now log in.')
            return redirect(url_for('login'))
        else:
            flash('Username already exists. Please choose a different one.')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    # Check if user is logged in and set the username
    username = session.get('username', 'Guest')
    
    # Retrieve and display price history here if needed
    return render_template('dashboard.html', username=username)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Handle form submission here
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # You would add your user update logic here
        # For example, update the session or the database with the new data

        flash('Settings updated successfully!', 'success')  # Flash message for feedback
        return redirect(url_for('settings'))  # Redirect to the same page to show changes

    return render_template('settings.html')  # Render the settings page

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('index'))

if __name__ == '__main__':
    settings = load_settings()
    init_sound(settings["remind-sound-path"])  # Initialize sound notification
    app.run(debug=True)
