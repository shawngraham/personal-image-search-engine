from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import os
import subprocess
import json
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/images/'
app.config['STATIC_IMAGES_FOLDER'] = 'static/images/'
app.secret_key = 'supersecretkey'  # Needed to use flash

# Ensure the necessary folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_IMAGES_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No files part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        for file in files:
            if file.filename == '':
                flash('No selected file')
                continue  # Continue to the next file

            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            # Copy the file to the static/images folder for web access
            static_path = os.path.join(app.config['STATIC_IMAGES_FOLDER'], filename)
            shutil.copy(upload_path, static_path)

        return redirect(url_for('index'))  # Redirect to the home page after successful upload
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/embed')
def embed():
    # Run the embedding script here
    command = "llm embed-multi photos --files uploads/images/ '*.jpg' --binary -m clip"
    output = run_command(command)
    return render_template('console.html', output=output)

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    command = f"llm similar photos -c \"{query}\""
    output = run_command(command)
    results = parse_output(output)
    return render_template('results.html', results=results, output=output)

@app.route('/visually-similar-upload', methods=['POST'])
def visually_similar_upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Copy the file to the static/images folder for web access
        static_path = os.path.join(app.config['STATIC_IMAGES_FOLDER'], filename)
        shutil.copy(upload_path, static_path)
        
        # Process the uploaded file to find similar images
        command = f"llm similar photos -i \"{upload_path}\" --binary"
        output = run_command(command)
        results = parse_output(output)
        return render_template('results.html', results=results, output=output)

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()
    return output + error

def parse_output(output):
    lines = output.split('\n')
    json_lines = [line for line in lines if line.startswith('{\"id\":')]
    results = []
    for json_line in json_lines[:3]:
        try:
            result = json.loads(json_line)
            results.append(result)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
    return results

if __name__ == '__main__':
    app.run(debug=True)