import json

config = {}

start_port = 5254
end_port = 5350

current_port = start_port

config['dist_dict_enabled'] = 'True'
config['sensors'] = []
while current_port <= end_port:
    node_conf = {}
    node_conf['ip'] = '129.244.246.192'
    node_conf['port'] = current_port

    config['sensors'].append(node_conf)

    current_port += 1

with open('triassic_shell.conf', 'w') as fp:
    json.dump(config, fp)
