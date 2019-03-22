import sys
import logging
import socket
import argparse
import json
import os

import ZODB, transaction

import data_model

def degrade_step():
    data_model.load_from_disk()
    for id,node in data_model.fence_segments.items():
        if node.state < 1.0:
            node.state -= 0.067
    data_model.save_to_disk()

def main():
    parser = argparse.ArgumentParser(prog='triassic_scoring.py')
    parser.add_argument('-f', '--file', help="Path to the ZODB persistence file to use.")

    args = parser.parse_args()

    # Initialize the database, if needed.
    data_model.init_db(args.file if args.file else None)

    degrade_step()

if __name__ == "__main__":
    main()
