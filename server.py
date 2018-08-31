import functools

import psycopg2
from flask import Flask, request, render_template, jsonify
app = Flask(__name__)


def uses_db(f):
    # for functions that want a cursor
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        with psycopg2.connect(dbname='v4_trials', user='postgres') as conn, \
             conn.cursor() as curr:
            return f(curr, *args, **kwargs)
        return None
    return wrapped


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/names')
@uses_db
def get_names(curr):
    curr.execute('SELECT DISTINCT name FROM trials;')
    rows = [row[0] for row in curr.fetchall()]
    print(rows)
    rows = list(sorted(rows, key=lambda name: 0 if name == 'Zorin' else 1))
    return jsonify(rows)


@app.route('/dates')
@uses_db
def get_dates(curr):
    name = request.args.get('name')
    # this is sanitized
    curr.execute('''SELECT DISTINCT date FROM trials
                    WHERE LOWER(name) = LOWER(%s)
                    ORDER BY date;''', (name,))
    return jsonify([row[0] for row in curr.fetchall()])


@app.route('/idxs')
@uses_db
def get_idxs(curr):
    name, date = [request.args.get(x) for x in ['name', 'date']]
    curr.execute('''SELECT index FROM trials
                    WHERE LOWER(name) = LOWER(%s) AND date = %s
                    ORDER BY index;''', (name, date))
    return jsonify([row[0] for row in curr.fetchall()])


@app.route('/trial')
@uses_db
def get_trial(curr):
    name, date, idx = [request.args.get(x)
                            for x in ['name', 'date', 'idx']]
    curr.execute('''SELECT lfp, spikes, events FROM trials
                    WHERE LOWER(name) = LOWER(%s) AND date = %s AND index = %s;''',
                 (name, date, idx))
    row = curr.fetchone()
    return jsonify({'lfp': row[0], 'spikes': row[1], 'events': row[2]})


if __name__ == '__main__':
    app.env = 'development'
    app.run(debug=True)
