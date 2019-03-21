import sys
import logging
import socket
import argparse
import json
import os

import data_model

from flask import Flask

app = Flask(__name__)
app.secret_key = 'NpaguVKgv<;f;i(:T>3tn~dsOue5Vy)'

@app.route('/fence/<string:dinosaur>/<int:percent>/')
def exhibit_contained(dinosaur,percent):
    if dinosaur not in ['velociraptor', 'tyrannosaurus', 'guaibasaurus', 'triceratops', 'all']:
        return 'error'

    all_exhibits = set()
    fence_sections = {}
    conn = data_model.get_db_conn()
    for id,node in conn.root.fence_segments.items():
        all_exhibits.add(node.dinosaur)
        fence_sections[id] = node
    conn.close()

    number_up = 0
    total_number = 0

    for section in fence_sections.values():
        if dinosaur == 'all' or section.dinosaur == dinosaur:
            total_number += 1
            if section.state >= 0.3:
                number_up += 1

    percent_up = int(100 * (float(number_up)/float(total_number)))

    if percent_up >= percent:
        return 'up'
    else:
        return 'down'

def main():
    parser = argparse.ArgumentParser(prog='triassic_scoring.py')
    parser.add_argument('-f', '--file', help="Path to the ZODB persistence file to use.")
    parser.add_argument('-a', '--address', default='0.0.0.0', dest='host')
    parser.add_argument('-p', '--port', default='5000', dest='port')

    args = parser.parse_args()

    # Initialize the database, if needed.
    data_model.init_db(args.file if args.file else None)

    app.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()