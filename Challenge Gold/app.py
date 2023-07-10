from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import re
import sqlite3
import matplotlib.pyplot as plt
import base64
from collections import Counter

app = Flask(__name__)

abusive = pd.read_csv('E:/Data/abusive.csv', encoding='utf-8')
new_kamusalay = pd.read_csv('E:/Data/new_kamusalay.csv', encoding='latin1')
new_kamus_alay = {}
for k, v in new_kamusalay.values:
    new_kamus_alay[k] = v
    
def count_abusive_words(text):
    abusive_words = abusive['ABUSIVE'].tolist()
    pattern = r'\b(?:{})\b'.format('|'.join(re.escape(word) for word in abusive_words))
    matches = re.findall(pattern, text)
    return len(matches)

def processing_text(input_text):
    # Decode the text using various encodings
    decoded_text = None
    encodings = ['utf-8', 'latin1']

    for encoding in encodings:
        try:
            decoded_text = input_text.encode(encoding).decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    # If decoding fails, return the input text as is
    if decoded_text is None:
        return input_text

    # Replace email addresses with 'EMAIL'
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', 'EMAIL', decoded_text)

    # Remove numbers
    text = re.sub(r'\d+', '', text)

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)

    # Replace phone numbers with 'NOMOR_TELEPON'
    text = re.sub(r"\b\d{4}\s?\d{4}\s?\d{4}\b", "NOMOR_TELEPON", text)

    # Remove the string "USER" or "user"
    text = text.replace("USER", "").replace("user", "")

    # Remove specific pattern "xf0x9fx98x84xf0x9fx98x84xf0x9fx98x84"
    text = text.replace("xf0x9fx98x84xf0x9fx98x84xf0x9fx98x84", "")

    # Remove other similar patterns like "xf0x9fx98x8f" or "xf0x9fx98x86xf0x9fx98x86"
    text = re.sub(r'x[0-9a-f]{2}', '', text)

    # Remove URLs
    text = remove_urls(text)

    # Remove specific pattern "xfxfxxxfxfxxxfxfxx"
    text = re.sub(r'xfxfxxxfxfxxxfxfxx', '', text)

    # Remove other similar patterns like "xfxfxx" or "xfxfxxxfxfxx"
    text = re.sub(r'x[0-9a-f]{2}', '', text)

    # Strip leading and trailing whitespace
    text = text.strip()

    # Remove Bahasa Alay
    text = remove_bahasa_alay(text)
    # Remove abusive words
    abusive_words = abusive['ABUSIVE'].tolist()
    pattern = r'\b(?:{})\b'.format('|'.join(re.escape(word) for word in abusive_words))
    clean_text = re.sub(pattern, '', text)

    return clean_text

def remove_bahasa_alay(input_text):
    words = input_text.split()
    cleaned_words = []

    for word in words:
        cleaned_word = new_kamus_alay.get(word, word)
        cleaned_words.append(cleaned_word)

    return ' '.join(cleaned_words)

def count_abusive_words(text):
    abusive_words = abusive['ABUSIVE'].tolist()
    pattern = r'\b(?:{})\b'.format('|'.join(re.escape(word) for word in abusive_words))
    matches = re.findall(pattern, text)
    return len(matches)


def remove_urls(input_text):
    # Remove URLs from the text
    return re.sub(r'http\S+|www\S+', '', input_text)

def create_table():
    # Placeholder function for creating a database table
    pass

def insert_to_table(value_1, value_2):
    # Placeholder function for inserting values into the database table
    pass

def read_table(target_index=None, target_keywords=None):
    # Placeholder function for reading data from the database table
    pass

def create_table():
    conn = sqlite3.connect('tweet_data.db')
    c = conn.cursor()

    # Create the tweets table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS tweets
                 (TweetIndex INTEGER PRIMARY KEY AUTOINCREMENT,
                 Previous_text TEXT,
                 Cleaned_text TEXT,
                 Keywords TEXT)''')

    conn.commit()
    conn.close()

def insert_to_table(previous_text, cleaned_text):
    conn = sqlite3.connect('tweet_data.db')
    c = conn.cursor()

    # Encode the text to UTF-8
    previous_text = previous_text.encode('utf-8')
    cleaned_text = cleaned_text.encode('utf-8')
 

    # Insert the data into the tweets table
    c.execute("INSERT INTO tweets (Previous_text, Cleaned_text) VALUES (?, ?)",
              (previous_text, cleaned_text))

    conn.commit()
    conn.close()

def read_table(target_index=None, target_keywords=None):
    conn = sqlite3.connect('tweet_data.db')
    c = conn.cursor()

    if target_index:
        # Query the database based on the provided index
        c.execute("SELECT Previous_text, Cleaned_text FROM tweets WHERE TweetIndex = ?", (target_index,))
    elif target_keywords:
        # Query the database based on the provided keyword
        target_keywords = '%' + target_keywords + '%'
        c.execute("SELECT Previous_text, Cleaned_text FROM tweets WHERE Keywords LIKE ?", (target_keywords,))
    else:
        # Read all rows from the tweets table
        c.execute("SELECT Previous_text, Cleaned_text FROM tweets")

    result = c.fetchall()

    conn.close()

    return result

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        go_to_page = request.form.get('inputText')
        if go_to_page == "1":
            return redirect(url_for('input_text_processing'))
        elif go_to_page == "2":
            return redirect(url_for('input_file_processing'))
        elif go_to_page == "3":
            return redirect(url_for('read_database'))
    else:
        return render_template('index.html')

@app.route('/input-text-processing', methods=['GET', 'POST'])
def input_text_processing():
    if request.method == 'POST':
        previous_text = request.form['inputText']
        cleaned_text = processing_text(previous_text)
        json_response = {
            'previous_text': previous_text,
            'cleaned_text': cleaned_text
        }
        return jsonify(json_response)

    return render_template('input_text_processing.html')

@app.route('/input-file-processing', methods=['GET', 'POST'])
def input_file_processing():
    if request.method == 'POST':
        input_file = request.files['inputFile']
        df = pd.read_csv(input_file, encoding='latin1')
        if "Tweet" in df.columns:
            list_of_tweets = df['Tweet']
            list_of_cleaned_tweets = df['Tweet'].apply(processing_text)
            list_of_abusive_words_count = list_of_tweets.apply(count_abusive_words)

            create_table()
            for previous_text, cleaned_text in zip(list_of_tweets, list_of_cleaned_tweets):
                insert_to_table(previous_text, cleaned_text)

            # Generate histogram of abusive words count
            plt.hist(list_of_abusive_words_count, bins=10, alpha=0.5)
            plt.xlabel('Abusive Words Count')
            plt.ylabel('Frequency')
            plt.title('Histogram of Abusive Words Count')
            plt.grid(True)
            plt.savefig('histogram.png')
            plt.close()
            # Read the abusive words from the CSV file
            abusive_words = pd.read_csv('E:/Data/abusive.csv')['ABUSIVE'].tolist()

            # Count top abusive words from uncleaned tweets
            all_abusive_words = ' '.join(list_of_tweets)
            abusive_words_count = Counter(word for word in all_abusive_words.split() if word in abusive_words)
            top_abusive_words = abusive_words_count.most_common(10)
            # Visualize top abusive words
            word_labels, word_counts = zip(*top_abusive_words)
            plt.bar(word_labels, word_counts)
            plt.xlabel('Abusive Words')
            plt.ylabel('Count')
            plt.title('Top 10 Abusive Words')
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.savefig('top_abusive_words.png')
            plt.close()

            # Convert the histogram and top abusive words images to base64
            with open('histogram.png', 'rb') as histogram_file:
                encoded_histogram = base64.b64encode(histogram_file.read()).decode('utf-8')

            with open('top_abusive_words.png', 'rb') as top_abusive_words_file:
                encoded_top_abusive_words = base64.b64encode(top_abusive_words_file.read()).decode('utf-8')

            json_response = {
                'list_of_tweets': list_of_tweets.tolist(),
                'list_of_cleaned_tweets': list_of_cleaned_tweets.tolist(),
                'list_of_abusive_words_count': list_of_abusive_words_count.tolist(),
                'histogram_image': encoded_histogram,
                'top_abusive_words_image': encoded_top_abusive_words,
                'top_abusive_words': top_abusive_words
            }
            return jsonify(json_response)
        else:
            json_response = {
                'error_warning': "No column 'Tweet' found in the uploaded file"
            }
            return jsonify(json_response)
    else:
        return render_template('input_file_processing.html')
    
@app.route('/read-database', methods=['GET', 'POST'])
def read_database():
    if request.method == "POST":
        showed_index = request.form.get('inputIndex')
        showed_keywords = request.form.get('inputKeywords')

        if showed_index:
            conn = sqlite3.connect('tweet_data.db')
            c = conn.cursor()

            c.execute("SELECT Previous_text, Cleaned_text FROM tweets WHERE TweetIndex = ?", (showed_index,))
            result = c.fetchone()

            conn.close()

            if result:
                previous_text = result[0]
                cleaned_text = result[1]
                return render_template("read_database.html", index=showed_index, previous_text=previous_text, cleaned_text=cleaned_text)
            else:
                return render_template("read_database.html", error_warning="No data found for the provided index")

        elif showed_keywords:
            conn = sqlite3.connect('tweet_data.db')
            c = conn.cursor()

            c.execute("SELECT Previous_text, Cleaned_text FROM tweets WHERE Keywords LIKE ?", ('%' + showed_keywords + '%',))
            results = c.fetchall()

            conn.close()

            if results:
                decoded_results = [(result[0].decode('latin1'), result[1].decode('latin1')) for result in results]
                return render_template("read_database.html", showed_keywords=showed_keywords, results=decoded_results)
            else:
                return render_template("read_database.html", error_warning="No data found for the provided keywords")
    
    else:
        results = []  # Define an empty list for results
        return render_template("read_database.html", error_warning="Index or Keywords is None")

if __name__ == '__main__':
    app.run(debug=True)