from flask import Flask, render_template, request, jsonify
import os, json
from mismatcher import findMissMatchPercentage
import base64
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
uri = "mongodb+srv://urpreetam:mongo12345@idcontainer.5ecdmsl.mongodb.net/?retryWrites=true&w=majority"
app = Flask(__name__)

client = MongoClient(uri, server_api=ServerApi('1'))
db = client['images']
image_collection = db['user_inputs']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    file = request.files['file']
    # If file name is empty then return no file selected
    if file.filename == '':
        return jsonify({'result': 'No file selected.'})

    # Inserted images
    allowed_extensions = {'jpg', 'jpeg', 'png'}
    if file and file.filename.lower().rsplit('.', 1)[1] in allowed_extensions:
        filename = file.filename
        image_path = os.path.join("uploaded_images", filename)
        with open(image_path, "wb") as f:
            f.write(file.read())

        output = findMissMatchPercentage(image_path)

        image_data = base64.b64encode(file.read()).decode('utf-8')

        # Store the image in MongoDB
        objectID = image_collection.insert_one({'image': image_data, 'filename': filename, 'output': output})

        # Store image data and filename in uploads.jsonl
        data = {
            'objectID': str(objectID.inserted_id),
            'filename': filename,
            'output': output
        }
        with open("artifacts/uploads.jsonl", "a") as f:
            f.write(json.dumps(data) + "\n")

        return jsonify({'result': {'msg': 'Image uploaded successfully.', 'output': str(output)}})
    else:
        return jsonify({'result': 'Invalid file format. Only JPG, JPEG, and PNG files are allowed.'})


if __name__ == '__main__':
    app.run(debug=True)