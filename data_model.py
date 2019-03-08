import json
import time
import datetime
import os

import persistent
import ZODB, ZODB.FileStorage, transaction
import BTrees.OOBTree
from triassic_consensus.client import DistributedDict

db = None
db_path = None
consensus_dist_dict = None
consensus_config = None
current_dist_dict_sensor_index = None

DELAY_SLEEP = 0.15

class FenceSegment(persistent.Persistent):
    def __init__(self, id, dinosaur_name):
        self.id = id
        self.dinosaur = dinosaur_name
        global consensus_dist_dict
        self._state = 1.0
        self._enabled = True

        # If we're not using the distributed dict, then we're done.
        # Otherwise, do some initialization...

        if consensus_dist_dict is not None:
            print('init %x' % self.id)
            try:
                if '%d_dino_name' % id in consensus_dist_dict:
                    self.dinosaur = consensus_dist_dict['%d_dino_name' % id]
                else:
                    consensus_dist_dict['%d_dino_name' % id] = dinosaur_name

                self._state = consensus_dist_dict['%d_state' % id]
                self._enabled = consensus_dist_dict['%d_enabled' % id]
            except:
                dist_dict_reconnect()

                if '%d_dino_name' % id in consensus_dist_dict:
                    self.dinosaur = consensus_dist_dict['%d_dino_name' % id]
                else:
                    consensus_dist_dict['%d_dino_name' % id] = dinosaur_name

                self._state = consensus_dist_dict['%d_state' % id]
                self._enabled = consensus_dist_dict['%d_enabled' % id]


    def get_dist_value(self, key):
        while True:
            try:
                return consensus_dist_dict[key]
            except:
                dist_dict_reconnect()

    def set_dist_value(self, key, value):
        while True:
            try:
                consensus_dist_dict[key] = value
                break
            except:
                dist_dict_reconnect()

    @property
    def state(self):
        if consensus_dist_dict is not None:
            conn = get_db_conn()

            time_delta_seconds = 900
            start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta_seconds)
            end_time = datetime.datetime.now() + datetime.timedelta(seconds=time_delta_seconds)

            node_last_update = datetime.datetime.strptime(self.get_dist_value('%d_last_updated' % self.id), '%Y-%m-%d %H:%M:%S.%f')

            if not self.time_in_range(start_time, end_time, node_last_update):
                self.set_dist_value('%d_state' % self.id, 0)

            conn.root.fence_segments[self.id].state = self.get_dist_value('%d_state' % self.id)

            transaction.commit()
            conn.close()
        else:
            time.sleep(DELAY_SLEEP)

        return self._state

    @state.setter
    def state(self, value):
        if consensus_dist_dict is not None:
            self.set_dist_value('%d_state' % self.id, value)
        else:
            time.sleep(DELAY_SLEEP)

        self._state = value
        self._p_changed = True


    @property
    def enabled(self):
        if consensus_dist_dict is not None:
            conn = get_db_conn()
            self._enabled = self.get_dist_value('%d_enabled' % self.id)
            transaction.commit()
            conn.close()
        else:
            time.sleep(DELAY_SLEEP)

        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if consensus_dist_dict is not None:
            self.set_dist_value('%d_enabled' % self.id, value)
        else:
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
        if consensus_dist_dict is not None:
            time_delta_seconds = 900
            start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta_seconds)
            end_time = datetime.datetime.now() + datetime.timedelta(seconds=time_delta_seconds)
            node_last_update = datetime.datetime.strptime(self.get_dist_value('%d_last_updated' % self.id),
                                                          '%Y-%m-%d %H:%M:%S.%f')

            if not self.time_in_range(start_time, end_time, node_last_update):
                self.set_dist_value('%d_state' % self.id, 0)
            else:
                self.set_dist_value('%d_task_queued' % self.id, 'df5ac')
                time.sleep(5)
                self.set_dist_value('%d_state' % self.id, 1.0)

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

def consensus_config_from_file(filename):
    with open(filename) as f:
        conf = json.load(f)
    return conf

def dist_dict_reconnect():
    global consensus_dist_dict
    global current_dist_dict_sensor_index

    while True:
        count = 0
        for sensor in consensus_config['sensors']:
            if count == (len(consensus_config['sensors']) - 1):
                current_dist_dict_sensor_index = 0

            if count > current_dist_dict_sensor_index:
                try:
                    current_dist_dict_sensor_index = count
                    print('reconnecting to %s:%d' % (sensor['ip'], sensor['port']))
                    consensus_dist_dict = DistributedDict(sensor['ip'], sensor['port'])
                    break
                except:
                    pass

            count += 1

        if consensus_dist_dict is not None:
            break
        else:
            time.sleep(.25)

def load_consensus_dist_dict():
    global consensus_dist_dict
    global current_dist_dict_sensor_index

    if consensus_config['dist_dict_enabled'] == 'True':
        while True:
            count = 0
            for id in range(len(consensus_config['sensors'])):
                sensor = consensus_config['sensors'][id]
                print('Loading sensor %d' % id)
                try:
                    current_dist_dict_sensor_index = count
                    consensus_dist_dict = DistributedDict(sensor['ip'], sensor['port'])
                    break
                except:
                    pass
                count += 1

            if consensus_dist_dict is not None:
                break
            else:
                time.sleep(.25)

def init_db(filepath):
    global db_path
    global consensus_config

    if filepath:
        db_path = filepath

    conn = get_db_conn()

    # If we're using the consensus protocol, it's time to load the
    #  configuration for that subsystem.
    if consensus_config:
        load_consensus_dist_dict()

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
