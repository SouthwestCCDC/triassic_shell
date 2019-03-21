import json
import time
import datetime
import os

import persistent
import ZODB, ZODB.FileStorage, transaction
import BTrees.OOBTree

db = None
db_path = None

DELAY_SLEEP = 0.95

class FenceSegment(persistent.Persistent):
    def __init__(self, id, dinosaur_name):
        self.id = id
        self.dinosaur = dinosaur_name
        global consensus_dist_dict
        self._state = 1.0
        self._enabled = True

    @property
    def state(self):
        time.sleep(DELAY_SLEEP)
        return self._state

    @state.setter
    def state(self, value):
        time.sleep(DELAY_SLEEP)
        self._state = value
        self._p_changed = True

    @property
    def enabled(self):
        time.sleep(DELAY_SLEEP)
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        time.sleep(DELAY_SLEEP)

        self._enabled = value
        self._p_changed = True

    def fence_status(self):
        if self.state == 0.0:
            return 'unreach'
        
        if not self.enabled:
            return 'pwroff'

        if self.state < 0.25:
            return 'fail'
        elif self.state < 1.0:
            return 'degrad'
        else:
            return 'ok'

    def resync(self):
        pass

    def time_in_range(self, start, end, x):
        """Return true if x is in the range [start, end]"""
        if start <= x <= end:
            return True
        else:
            return False

def get_db_conn():
    global db

    if not db:
        db = ZODB.DB(db_path)
    conn = db.open()
    return conn

def init_db(filepath):
    global db_path

    if filepath:
        db_path = filepath

    conn = get_db_conn()

    # Now, try loading our ZODB version of the data source. If
    #  conn.root.fence_segments exists, then it's already been
    #  initialized, and there's nothing to do. But, if conn.root
    #  doesn't have a fence_segments attribute, then we need
    #  to initialize that data.
    try:
        if conn.root.fence_segments:
            conn.close()
            return
    except AttributeError:
        pass


    # conn.root has no attribute fence_segments, so we need to
    #  create it, and load up all the dinosaurs.
    conn.root.fence_segments = BTrees.OOBTree.BTree()
    for id in range(0x10000+10111, 0xfffff, 10111): # 97 elements
        if id % 5 == 0:
            dino_name = 'velociraptor'
        elif id % 4 == 0:
            dino_name = 'tyrannosaurus'
        elif id % 3 == 0:
            dino_name = 'guaibasaurus'
        else:
            dino_name = 'triceratops'

        # TODO: What is the purpose of this?
        while True:
            try:
                conn.root.fence_segments[id] = FenceSegment(
                    id,
                    dino_name,
                )
                break
            except:
                time.sleep(1)

    transaction.commit()
    conn.close()
