import persistent
import ZODB, ZODB.FileStorage, transaction
import BTrees.OOBTree

class FenceSegment(persistent.Persistent):
    def __init__(self, id, dinosaur_name):
        pass
        self.id = id
        self.dinosaur = dinosaur_name
        self.state = 1.0
        self.enabled = True

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

def init_db(root):
    root.fence_segments = BTrees.OOBTree.BTree()
    for id in range(0x10000+10111, 0xfffff, 10111): # 97 elements
        if id % 5 == 0:
            dino_name = 'velociraptor'
        elif id % 4 == 0:
            dino_name = 'tyrannosaurus'
        else:
            dino_name = 'triceratops'
        root.fence_segments[id] = FenceSegment(
            id,
            dino_name,
        )

def get_data_root():
    connection = ZODB.connection(None)
    root = connection.root
    # TODO: if not working:
    init_db(root)
    return root