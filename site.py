from model import Model

from flask import Flask, render_template, request, jsonify
from waitress import serve

app = Flask("__name__")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/prompt", methods=["POST"])
def prompt():
    data = request.get_json()
    question = data['message']
    output = model.quick_prompt(question)
    return jsonify({"answer" : output})

if __name__ == "__main__":
    print("Loading Model")
    database_folder = "historical_embeddings"
    model = Model(database_folder)
    print("Model loaded; Serving Site")
    serve(app, host="0.0.0.0", port=5000)
    