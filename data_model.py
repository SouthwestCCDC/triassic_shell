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


    @property
    def state(self):
        global dist_dict
        if dist_dict is not None:
            conn = get_db_conn()
            #print('setting zodb %d_state' % self.id)
            try:
                time_delta_seconds = 900
                start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta_seconds)
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=time_delta_seconds)
                node_last_update = datetime.datetime.strptime(dist_dict['%d_last_updated' % self.id], '%Y-%m-%d %H:%M:%S.%f')

                if not self.time_in_range(start_time, end_time, node_last_update):
                    dist_dict['%d_state' % self.id] = 0

                conn.root.fence_segments[self.id].state = dist_dict['%d_state' % self.id]
            except:
                #print('reconnecting')
                dist_dict_reconnect()

                time_delta_seconds = 900
                start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta_seconds)
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=time_delta_seconds)
                node_last_update = datetime.datetime.strptime(dist_dict['%d_last_updated' % self.id], '%Y-%m-%d %H:%M:%S.%f')

                if not self.time_in_range(start_time, end_time, node_last_update):
                    dist_dict['%d_state' % self.id] = 0

                conn.root.fence_segments[self.id].state = dist_dict['%d_state' % self.id]

            #print('commiting on state getter')
            transaction.commit()
            #print('closing on state getter')
            conn.close()

            #print(dist_dict['%d_last_updated' % self.id])
        else:
           time.sleep(.3)

        #print('returning from state getter')
        return self._state

    @state.setter
    def state(self, value):
        global dist_dict
        if dist_dict is not None:
            #print('getting %d_state' % self.id)
            try:
                dist_dict['%d_state' % self.id] = value
            except:
                dist_dict_reconnect()
                dist_dict['%d_state' % self.id] = value

            #print('%d_state set')

        else:
            time.sleep(.3)

        self._state = value
        self._p_changed = True
        #print('returning')


    @property
    def enabled(self):
        global dist_dict
        if dist_dict is not None:
            conn = get_db_conn()
            #print('syncing zodb %d_enabled to dist_dict %s' % (self.id, dist_dict['%d_enabled' % self.id]))
            try:
                conn.root.fence_segments[self.id].enabled = dist_dict['%d_enabled' % self.id]
            except:
                dist_dict_reconnect()
                conn.root.fence_segments[self.id].enabled = dist_dict['%d_enabled' % self.id]

            #print('zodb set')
            transaction.commit()
            #print('zodb commit')
            conn.close()
            #print('zodb close')
        else:
            time.sleep(.3)

        return self._enabled

    @enabled.setter
    def enabled(self, value):
        global dist_dict
        if dist_dict is not None:
            #print('setting dist_dict and zodb %d_enabled to %s' % (self.id, value))
            try:
                dist_dict['%d_enabled' % self.id] = value
            except:
                dist_dict_reconnect()
                dist_dict['%d_enabled' % self.id] = value

            #print('set complete')
        else:
            time.sleep(.3)

        self._enabled = value
        #print('_enabled set')
        self._p_changed = True
        #print('_p_changed set')

    def fence_status(self):
        #print('getting enabled')
        if not self.enabled:
            #print('enabled')
            return 'pwroff'

        #print('getting state')
        if self.state < 0.25:
            #print('state<.25')
            return 'failed'

        #print('getting state')
        if self.state < 1.0:
            #print('state<.5')
            return 'degrad'
        else:
            #print('ok')
            return 'ok'

    def resync(self):
        global dist_dict
        if dist_dict is not None:
            try:
                time_delta_seconds = 900
                start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta_seconds)
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=time_delta_seconds)
                node_last_update = datetime.datetime.strptime(dist_dict['%d_last_updated' % self.id], '%Y-%m-%d %H:%M:%S.%f')

                if not self.time_in_range(start_time, end_time, node_last_update):
                    dist_dict['%d_state' % self.id] = 0
                else:
                    dist_dict['%d_task_queued' % self.id] = 'df5ac'
                    time.sleep(5)
                    dist_dict['%d_state' % self.id] = 1.0
            except:
                dist_dict_reconnect()
                time_delta_seconds = 900
                start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_delta_seconds)
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=time_delta_seconds)
                node_last_update = datetime.datetime.strptime(dist_dict['%d_last_updated' % self.id], '%Y-%m-%d %H:%M:%S.%f')

                if not self.time_in_range(start_time, end_time, node_last_update):
                    dist_dict['%d_state' % self.id] = 0
                else:
                    dist_dict['%d_task_queued' % self.id] = 'df5ac'
                    time.sleep(5)
                    dist_dict['%d_state' % self.id] = 1.0

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
    for id in range(0x10000+10111, 0xfffff, 10111): # 97x2 elements I think
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
