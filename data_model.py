import json
import time
import datetime

import persistent
import ZODB, ZODB.FileStorage, transaction
import BTrees.OOBTree
from triassic_consensus.client import DistributedDict

db = None
db_path = None
dist_dict = None
config = None

with open('./triassic_shell.conf', 'r') as fp:
    config = json.load(fp)


class FenceSegment(persistent.Persistent):
    def __init__(self, id, dinosaur_name):
        self.id = id
        self.dinosaur = dinosaur_name

        # TODO: Changing the following need to set self._p_changed=True:

        global dist_dict

        if dist_dict is not None:
            try:
                if '%d_dino_name' % id in dist_dict:
                    self.dinosaur = dist_dict['%d_dino_name' % id]
                else:
                    dist_dict['%d_dino_name' % id] = dinosaur_name

                self._state = dist_dict['%d_state' % id]
                self._enabled = dist_dict['%d_enabled' % id]
            except:
                dist_dict_reconnect()

                if '%d_dino_name' % id in dist_dict:
                    self.dinosaur = dist_dict['%d_dino_name' % id]
                else:
                    dist_dict['%d_dino_name' % id] = dinosaur_name

                self._state = dist_dict['%d_state' % id]
                self._enabled = dist_dict['%d_enabled' % id]


    def get_dist_value(self, key):
        while True:
            try:
                return dist_dict[key]
                break
            except:
                dist_dict_reconnect()
                time.sleep(1)

    def set_dist_value(self, key, value):
        while True:
            try:
                dist_dict[key] = value
                break
            except:
                dist_dict_reconnect()
                time.sleep(1)

    @property
    def state(self):
        global dist_dict
        if dist_dict is not None:
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
            time.sleep(.3)

        return self._state

    @state.setter
    def state(self, value):
        global dist_dict
        if dist_dict is not None:
            self.set_dist_value('%d_state' % self.id, value)
        else:
            time.sleep(.3)

        self._state = value
        self._p_changed = True


    @property
    def enabled(self):
        global dist_dict
        if dist_dict is not None:
            conn = get_db_conn()

            conn.root.fence_segments[self.id].enabled = self.get_dist_value('%d_enabled' % self.id)

            transaction.commit()
            conn.close()
        else:
            time.sleep(.3)

        return self._enabled

    @enabled.setter
    def enabled(self, value):
        global dist_dict
        if dist_dict is not None:
            self.set_dist_value('%d_enabled' % self.id, value)
        else:
            time.sleep(.3)

        self._enabled = value
        self._p_changed = True

    def fence_status(self):
        if not self.enabled:
            return 'pwroff'

        if self.state < 0.25:
            return 'failed'
        elif self.state < 1.0:
            return 'degrad'
        else:
            return 'ok'

    def resync(self):
        global dist_dict
        if dist_dict is not None:
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

def dist_dict_reconnect():
    global dist_dict
    while True:
        for sensor in config['sensors']:
            try:
                dist_dict = DistributedDict(sensor['ip'], sensor['port'])
                break
            except:
                pass

        if dist_dict is not None:
            break
        else:
            time.sleep(1)

def init_db(filepath):
    global db_path
    global config
    global dist_dict

    if filepath:
        db_path = filepath

    conn = get_db_conn()

    if config['dist_dict_enabled'] == 'True':
        while True:
            for sensor in config['sensors']:
                try:
                    dist_dict = DistributedDict(sensor['ip'], sensor['port'])
                    break
                except:
                    pass

            if dist_dict is not None:
                break
            else:
                time.sleep(1)

    try:
        if conn.root.fence_segments:
            conn.close()
            return
    except AttributeError:
        pass

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
