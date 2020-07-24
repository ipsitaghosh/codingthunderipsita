from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/about')
def ipsita():
    name="Ipsita Ghosh"
    return render_template('about.html', name1=name)

app.run(debug=True)