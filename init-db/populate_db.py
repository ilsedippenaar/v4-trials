import pathlib
import json
import re
import datetime
import math
import subprocess as sp

import psycopg2
import psycopg2.extras
from scipy import io


def get_names():
    return ["Zorin", "Jaws"]


def get_dates(data_dir: pathlib.Path, monkey_name: str):
    files = sorted(data_dir.glob(f'*{monkey_name.lower()}.mat'))
    date_matches = [re.match(r'\d+-\d+-\d+', str(f.name)) for f in files]
    return {datetime.date.fromisoformat(d.group()): files[i]
            for i, d in enumerate(date_matches) if d}


def load_trials(file: pathlib.Path):
    print("Loading...")
    mat = io.loadmat(str(file))

    print("Parsing...")
    N = len(mat['num'])
    indices = mat['num'].reshape(-1)
    shapecoh = mat['shapecoh'].reshape(-1)
    results = [str(r[0][0]) for r in mat['result']]

    lfps = [lfp[0].reshape(-1) for lfp in mat['lfp']]
    lfps = [[float(x) for x in lfp] for lfp in lfps]

    spikes = [s[0].reshape(-1) for s in mat['spikes']]
    spikes = [[[float(x) for x in unit.reshape(-1)] for unit in trial] for trial in spikes]

    events = {name: mat['events'][name][0,0].reshape(-1) for name in mat['events'].dtype.names}
    # switch to [trial{event}] instead of {event[trial]}
    events = [{name: float(events[name][i]) for name in events.keys()} for i in range(N)]
    # eliminate nans
    events = [{k: v for k,v in events[i].items() if not math.isnan(v)} for i in range(N)]

    return [{
            'index': int(indices[i]),
            'result': results[i],
            'shapecoh':  None if math.isnan(shapecoh[i]) else float(shapecoh[i]),
            'lfp': lfps[i],
            'spikes': spikes[i],
            'events': events[i]} for i in range(N)]


def create_db(curr):
    # this is an idempotent op
    curr.execute('''
        DROP TABLE IF EXISTS trials;
        DROP TYPE IF EXISTS outcome;
        CREATE TYPE outcome AS ENUM ('true_positive', 'false_positive', 'false_negative', 'true_negative', 'failed');
        CREATE TABLE IF NOT EXISTS trials (
            name TEXT NOT NULL,
            date DATE NOT NULL,
            index INTEGER NOT NULL,
            result outcome,
            shapecoh REAL,
            lfp REAL[],
            spikes JSONB,
            events JSONB,
            PRIMARY KEY(name, date, index)
        );
        ''')


def insert_trials(curr, name, date, trial_data):
    # note: this is slower than building the string manually, but it is safer
    print("Inserting...")
    for trial in trial_data:
        trial['name'] = name
        trial['date'] = date
        trial['spikes'] = psycopg2.extras.Json(trial['spikes'])
        trial['events'] = psycopg2.extras.Json(trial['events'])
        curr.execute('''
          INSERT INTO trials VALUES
          (%(name)s,%(date)s,%(index)s,%(result)s,%(shapecoh)s,%(lfp)s,%(spikes)s,%(events)s);
          ''', trial)


if __name__ == '__main__':
    data_dir = pathlib.Path('/raw')
    with psycopg2.connect(dbname="postgres", user='postgres', host='db') as conn, conn.cursor() as curr:
        create_db(curr)
        conn.commit()

        names = get_names()
        for name in names:
            dates = get_dates(data_dir, name)
            for date, file in dates.items():
                print(f"Inserting data from {date}...")
                insert_trials(curr, name, date, load_trials(file))
        conn.commit()
