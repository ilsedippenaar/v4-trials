import pathlib
import json
import re
import datetime
import math

from scipy import io

from flask import Flask, request, render_template
app = Flask(__name__)

class DataHandler:
    """Basically a stand-in read-only database thing"""
    def __init__(self, data_dir):
        self.data_dir = pathlib.Path(data_dir)
        self._cache = None

    @staticmethod
    def _load_raw(file):
        mat = io.loadmat(file)
        N = len(mat['num'])
        lfps = [lfp[0].reshape(-1) for lfp in mat['lfp']]
        spikes = [s[0].reshape(-1) for s in mat['spikes']]
        event_names = mat['events'].dtype.names
        events = {event_name: mat['events'][event_name][0][0].reshape(-1) for event_name in event_names}
        return [{'lfp': lfps[i],
               'spikes': spikes[i],
               'events': {name: events[name][i] for name in event_names if not math.isnan(events[name][i])}} for i in range(N)]

    @staticmethod
    def _raw_to_json(trial):
        lfp = [float(x) for x in trial['lfp'].round(2)]
        spikes = [[float(x) for x in unit.reshape(-1)] for unit in trial['spikes']]
        events = {k: float(v) for k,v in trial['events'].items()}
        return json.dumps({'lfp': lfp, 'spikes': spikes, 'events': events})

    def _get_filename(self, monkey_name: str, date: str):
        dates = self.get_dates(monkey_name)
        return dates[datetime.date.fromisoformat(date)]

    def _from_cache(self, monkey_name: str, date: str):
        params = (monkey_name, date)
        if not self._cache or self._cache[0] != params:
            self._cache = (params, self._load_raw(self._get_filename(*params)))
        return self._cache[1]

    def get_names(self):
        return ["Zorin", "Jaws"]

    def get_dates(self, monkey_name: str):
        files = sorted(self.data_dir.glob(f'*{monkey_name.lower()}.mat'))
        date_matches = [re.match(r'(\d+-\d+-\d+)', str(f.name)) for f in files]
        return {datetime.date.fromisoformat(d.group(0)): files[i]
                for i, d in enumerate(date_matches) if d}

    def get_idxs(self, monkey_name: str, date: str):
        return list(range(len(self._from_cache(monkey_name, date))))

    def get_trial(self, monkey_name: str, date: str, idx: int):
        return self._raw_to_json(self._from_cache(monkey_name, date)[idx])


data_handler = DataHandler('data')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/names')
def get_names():
    return json.dumps(data_handler.get_names())

@app.route('/dates')
def get_dates():
    name = request.args.get('name')
    return json.dumps([str(x) for x in data_handler.get_dates(name).keys()])

@app.route('/idxs')
def get_idxs():
    name, date = [request.args.get(x) for x in ['name', 'date']]
    return json.dumps(data_handler.get_idxs(name, date))

@app.route('/trial')
def get_trial():
    name, date, idx = [request.args.get(x)
                            for x in ['name', 'date', 'idx']]
    return data_handler.get_trial(name, date, int(idx))

if __name__ == '__main__':
    app.env = 'development'
    app.run(debug=True)
