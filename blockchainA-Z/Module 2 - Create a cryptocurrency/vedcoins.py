# Module 1 - Create a blockchain

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    def __init__(self) -> None:
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()
    
    def create_block(self, proof: int, previous_hash: str) -> dict:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }
        self.transactions = [] # emptying the transactions once they are part of the block
        self.chain.append(block)
        return block
    
    def get_previous_block(self) -> dict:
        return self.chain[-1]
    
    def proof_of_work(self,previous_proof):
        new_proof = 1
        check_proof = False
        # run the loop until you find new_proof(nonce)
        while check_proof is False:
            # ideally hash will be caculated using the nonce and the block's data
            # right now we are calculating using previous proof and the new proof
            # to avoid symmetry new_proof + prev_proof = prev_proof + new_proof
            # we use the formula new_proof**2 - previous_proof**2
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof +=1
        return new_proof

    def hash(self, block: dict) -> str:
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self) -> bool:
        chain = self.chain
        previous_block = chain[0]
        block_index = 1
        
        # looping through the chain
        while block_index < len(chain):

            # 1. checking the previous_hash value in current block is right
            current_block = chain[block_index]
            if current_block['previous_hash'] != self.hash(previous_block):
                return False
            
            # 2. check whether the hash of current block is valid or not
            previous_proof = previous_block['proof']
            current_proof = current_block['proof']
            hash_operation = hashlib.sha256(str(current_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            
            previous_block = current_block
            block_index += 1
        return True 
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })

        # we return index of the new block that will be mined in the future
        # and will contain this transaction
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for nodes in network:
            response = requests.get(f'http://{nodes}/get_chain')
            if response.status_code == 200:
                # get the length and the chain
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        else:
            return False


app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# generate random node address for port 5000
# remove hyphens from the generated string
node_address = str(uuid4()).replace('-', '')
blockchain = Blockchain()

@app.route('/healthz',methods = ['GET'])
def healthz():
    return "Ok", 200

@app.route('/mine_block',methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof=previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # adding transactions
    # sender is this node, receiver is miner, amount is 1
    blockchain.add_transaction(sender=node_address, receiver='Vedant', amount = 1)
    block = blockchain.create_block(proof=proof, previous_hash=previous_hash)
    response = {
        'msg': 'Congratulations on mining your block',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200


@app.route('/is_valid', methods=['GET'])
def is_valid():
    if blockchain.is_chain_valid():
        message ='Chain valid'
    else:
        message='Chain Invalid'
    response = {
            'message': message
        }
    return response, 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']

    # checking if transactions keys are present in incoming json
    if not all (key in json for key in transaction_keys):
        return 'Some elements are missing', 400
    
    # this transaction is going to be added to the (last block + 1)th block in the chain
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {
        'message': f'This transaction will be added to the block {index}'
    }
    return jsonify(response), 201 

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes:
        for node in nodes:
            blockchain.add_node(node)
        response = {
            'message': 'New Nodes are connected',
            'total_nodes': list(blockchain.nodes)
        }
        return jsonify(response), 201
    else:
        return 'No Nodes', 400

@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    if blockchain.replace_chain():
        message = 'Chain is successfully replaced'
    else:
        message='Chain is already the largest'
    response = {
            'message': message,
            'chain': blockchain.chain
        }
    return response, 200

app.run('0.0.0.0', port = 5000)