import json

import persistent
import ZODB, ZODB.FileStorage, transaction
import BTrees.OOBTree
from triassic_consensus.client import DistributedDict


class FenceSegment(persistent.Persistent):
    def __init__(self, id, dinosaur_name):
        self.id = id
        self.dinosaur = dinosaur_name

        global dist_dict
        self.dist_dict = dist_dict

        # TODO: Changing the following need to set self._p_changed=True:
        self._state = 1.0
        self._enabled = True

        if self.dist_dict is not None:
            self.dist_dict['%d_dino_name' % id] = dinosaur_name
            self.dist_dict['%d_state' % id] = self._state
            self.dist_dict['%d_enabled' % id] = self._enabled

    @property
    def state(self):
        # if self.dist_dict is not None:
        #     self._state = self.dist_dict['%d_state' % self.id]

        return self._state

    @state.setter
    def state(self, value):
        if self.dist_dict is not None:
            self.dist_dict['%d_state' % self.id] = value

        self._state = value
        self._p_changed = True


    @property
    def enabled(self):
        # if self.dist_dict is not None:
        #     self._enabled = self.dist_dict['%d_enabled' % self.id]

        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if self.dist_dict is not None:
            self.dist_dict['%d_enabled' % self.id] = value

        self._enabled = value
        self._p_changed = True

    def reset_state(self):
        self.state = 1.0

    def fence_status(self):
        if not self.enabled:
            return 'pwroff'
        if self.state < 0.25:
            return 'failed'
        elif self.state < 0.5:
            return 'degrad'
        else:
            return 'ok'

db = None
db_path = None
dist_dict = None
config = None

with open('./triassic_shell.conf', 'r') as fp:
    config = json.load(fp)

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
