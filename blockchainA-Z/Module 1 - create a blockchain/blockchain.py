# Module 1 - Create a blockchain

import datetime
import hashlib
import json
from flask import Flask, jsonify

class Blockchain:
    def __init__(self) -> None:
        self.chain = []
        self.create_block(proof=1, previous_hash='0')
    
    def create_block(self, proof: int, previous_hash: str) -> dict:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'proof': proof,
            'previous_hash': previous_hash,
        }
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

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
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
    block = blockchain.create_block(proof=proof, previous_hash=previous_hash)
    response = {
        'msg': 'Congratulations on mining your block',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
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
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

# app.run('0.0.0.0', port = 5000)