import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from urllib.parse import urlparse
import sys

class Blockchain:

    def __init__(self):
        self.chain = []
        self.mempool = []
        self.nodes = set()
        self.create_block(proof = 1, previous_hash = '0')
        
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.mempool}
        self.mempool = []
        self.chain.append(block)
        if self.replace_chain():
            raise Exception('Houston, we have a bigger chain')   
        return block
    
    
    def create_transaction(self, sender, receiver, amount, timestamp):
        should_broadcast = False
        if not timestamp:
            timestamp = str(datetime.datetime.now())
            should_broadcast = True
        transaction = {'timestamp': timestamp,
                 'sender': sender,
                 'receiver': receiver,
                 'amount': amount}
        self.mempool.append(transaction)
        if should_broadcast:
            self.broadcast_transaction(transaction)
        return self.get_previous_block()['index'] + 1
    
    def create_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    def replace_chain(self):
        longest_chain = None
        max_length = len(self.chain)
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain != None:
            self.chain = longest_chain
            return True
        return False
    
    def broadcast_transaction(self, transaction):
        result = True
        for node in self.nodes:
            response = requests.post(f'http://{node}/chain/transaction', json = transaction)
            if response.status_code != 201:
                result = False
        return result
    
app = Flask(__name__)

blockchain = Blockchain()

@app.route('/chain/block', methods = ['PUT'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    proof = blockchain.proof_of_work(previous_block['proof'])
    try:
        block = blockchain.create_block(proof, blockchain.hash(previous_block))
    except Exception as e:
        return str(e), 409
    response = {'block': block}
    return jsonify(response), 200
 
@app.route('/chain', methods = ['GET'])
def get_chain():
    response = { 'chain': blockchain.chain,
                'length': len(blockchain.chain)
            }
    return jsonify(response), 200
 
@app.route('/chain/is_valid', methods = ['GET'])
def is_valid():
    return jsonify(blockchain.is_chain_valid(blockchain.chain)), 200

@app.route('/chain/transaction', methods = ['POST'])
def post_transaction():
    transaction_keys = ['sender', 'receiver', 'amount']
    json = request.get_json()
    print("JSON: " + str(json))
    if not all (key in json for key in transaction_keys):
        return 'Houston, we have a problem', 400
    sender = json['sender']
    receiver = json['receiver']
    amount = json['amount']
    timestamp = json['timestamp'] if 'timestamp' in json else ''
    return jsonify(blockchain.create_transaction(sender, receiver, amount, timestamp)), 201

@app.route('/chain/nodes', methods = ['POST'])
def post_node():
    node_keys = ['nodes']
    json = request.get_json()
    if not all (key in json for key in node_keys):
        return 'Houston, we have a problem', 400
    nodes = json['nodes']
    for node in nodes:
        blockchain.create_node(node)
    return jsonify(len(blockchain.nodes)), 201
        
@app.route('/chain', methods = ['PUT'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'Chain replaced',
                    'chain': blockchain.chain
                }    
    else: 
        response = {'message': 'Chain was not replaced',
                'chain': blockchain.chain
            }
    return jsonify(response), 200

app.run(port=sys.argv[1])