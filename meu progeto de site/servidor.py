from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login_success')
def login_success():
    return render_template('login_success.html')

@app.route('/save', methods=['POST'])
def save():
    data = request.json['logData']
    with open('log.txt', 'a') as file:
        file.write(data)
    return '', 204

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)

