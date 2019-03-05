import json
import time
import sys

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
        self._state = 1.0
        self._enabled = True

        global dist_dict

        if dist_dict is not None:
            dist_dict['%d_dino_name' % id] = dinosaur_name
            self._state = dist_dict['%d_state' % id]
            self._enabled = dist_dict['%d_enabled' % id]


    @property
    def state(self):
        global dist_dict
        if dist_dict is not None:
            conn = get_db_conn()
            #print('setting zodb %d_state' % self.id)
            conn.root.fence_segments[self.id].state = dist_dict['%d_state' % self.id]
            transaction.commit()
            conn.close()

            #print(dist_dict['%d_last_updated' % self.id])
        else:
           time.sleep(.3)

        return self._state

    @state.setter
    def state(self, value):
        global dist_dict
        if dist_dict is not None:
            #print('getting %d_state' % self.id)
            dist_dict['%d_state' % self.id] = value
        else:
            time.sleep(.3)

        self._state = value
        self._p_changed = True


    @property
    def enabled(self):
        global dist_dict
        if dist_dict is not None:
            conn = get_db_conn()
            #print('syncing zodb %d_enabled to dist_dict %s' % (self.id, dist_dict['%d_enabled' % self.id]))
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
            dist_dict['%d_enabled' % self.id] = value
            #print('set complete')
        else:
            time.sleep(.3)

        self._enabled = value
        #print('_enabled set')
        self._p_changed = True
        #print('_p_changed set')

    def reset_state(self):
        self.state = 1.0

    def fence_status(self):
        #print('getting enabled')
        if not self.enabled:
            #print('enabled')
            sys.stdout.flush()
            return 'pwroff'

        #print('getting state')
        if self.state < 0.25:
            #print('state<.25')
            return 'failed'

        #print('getting state')
        if self.state < 0.5:
            #print('state<.5')
            return 'degrad'
        else:
            #print('ok')
            return 'ok'

    def resync(self):
        global dist_dict
        if dist_dict is not None:
            dist_dict['%d_task_queued' % self.id] = 'df5ac'

def get_db_conn():
    global db

    if not db:
        db = ZODB.DB(db_path)
    conn = db.open()
    return conn

def init_db(filepath):
    global db_path
    global config
    global dist_dict

    if filepath:
        db_path = filepath

    conn = get_db_conn()

    if config['dist_dict_enabled'] == 'True':
        dist_dict = DistributedDict('129.244.246.192', 5255)

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
        else:
            dino_name = 'triceratops'

        dist_dict['%d_dino_name' % id] = dino_name

        conn.root.fence_segments[id] = FenceSegment(
            id,
            dino_name,
        )

    transaction.commit()
    conn.close()
