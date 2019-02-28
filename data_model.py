import persistent
import ZODB, ZODB.FileStorage, transaction
import BTrees.OOBTree

class FenceSegment(persistent.Persistent):
    def __init__(self, id, dinosaur_name):
        pass
        self.id = id
        self.dinosaur = dinosaur_name
        # TODO: Changing the following need to set self._p_changed=True:
        self._state = 1.0
        self._enabled = True

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self._p_changed = True

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        self._p_changed = True

    def reset_state(self):
        self.state = 1.0

    def fence_status(self):
        if not self.enabled:
            return 'pwr_off'
        if self.state < 0.5:
            return 'degraded'
        elif self.state < 0.25:
            return 'failed'
        else:
            return 'ok'

db = None

def get_db_conn():
    global db
    if not db:
        db = ZODB.DB(None)
    # conn = db.open_then_close_db_when_connection_closes()
    conn = db.open()
    return conn


def init_db():
    conn = get_db_conn()
    conn.root.fence_segments = BTrees.OOBTree.BTree()
    for id in range(0x10000+10111, 0xfffff, 10111): # 97 elements
        if id % 5 == 0:
            dino_name = 'velociraptor'
        elif id % 4 == 0:
            dino_name = 'tyrannosaurus'
        else:
            dino_name = 'triceratops'
        conn.root.fence_segments[id] = FenceSegment(
            id,
            dino_name,
        )
    transaction.commit()
    conn.close()
