from flask import Flask, render_template, request, jsonify
import os
from mismatcher import findMissMatchPercentage
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    file = request.files['file']
    if file.filename == '':
        return jsonify({'result': 'No file selected.'})
    if file and file.filename.endswith('.jpg'):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Process the file here
        result = str(findMissMatchPercentage(os.path.join(app.config['UPLOAD_FOLDER'], filename)))
        return jsonify({'result':result})
    else:
        return jsonify({'result': 'Invalid file format. Only JPG files are allowed.'})

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'inputfiles'
    app.run(debug=True)