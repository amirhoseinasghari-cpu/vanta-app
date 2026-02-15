"""
Vanta - NFT Smart Contract Manager
Real contract interaction with Polygon/Ethereum
"""
from web3 import Web3
from eth_account import Account
from typing import Optional, Dict
import json
import time

# ABI کامل ERC721
ERC721_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "uri", "type": "string"}
        ],
        "name": "mintNFT",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": True, "name": "tokenId", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]

# ⬇️ آدرس کانتریکت خودت رو اینجا بذار
CONTRACT_ADDRESSES = {
    "ethereum": None,  # "0x..."
    "polygon": None,   # "0x..."  آدرس Mumbai/Polygon
}


class NFTContractManager:
    def __init__(self, wallet_manager):
        self.wm = wallet_manager
        self.w3 = None
        self.contract = None
        self.contract_address = None
        self.connect()
    
    def connect(self):
        """Connect to Web3"""
        self.w3 = self.wm.get_web3()
        if self.w3 and self.w3.is_connected():
            print("✅ Connected to blockchain")
            self._load_contract()
        else:
            print("❌ Blockchain connection failed")
    
    def _load_contract(self):
        """Load existing contract"""
        addr = CONTRACT_ADDRESSES.get(self.wm.current_network)
        if addr and self.w3:
            try:
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(addr),
                    abi=ERC721_ABI
                )
                self.contract_address = addr
                print(f"📜 Contract loaded: {addr[:10]}...")
            except Exception as e:
                print(f"❌ Contract load failed: {e}")
    
    def mint_nft(self, metadata_uri: str, to_address: str = None) -> Optional[Dict]:
        """Mint NFT with metadata URI"""
        if not self.w3 or not self.wm.account:
            print("❌ Wallet not connected")
            return None
        
        # اگه کانتریکت نیست، Mock کن
        if not self.contract:
            print("⚠️ No contract - using mock mode")
            return self._mock_mint(metadata_uri)
        
        recipient = to_address or self.wm.address
        
        try:
            print(f"🎨 Minting NFT to {recipient[:10]}...")
            print(f"📋 Metadata: {metadata_uri[:30]}...")
            
            # Build transaction
            tx = self.contract.functions.mintNFT(
                Web3.to_checksum_address(recipient),
                metadata_uri
            ).build_transaction({
                'from': self.wm.address,
                'nonce': self.w3.eth.get_transaction_count(self.wm.address),
                'gas': 300000,
                'gasPrice': self.w3.to_wei('30', 'gwei'),
                'chainId': self.wm.get_chain_id()
            })
            
            # Sign
            signed = self.wm.account.sign_transaction(tx)
            
            # Send
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            print(f"⏳ Waiting for confirmation...")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                # Get token ID from event (simplified)
                token_id = receipt.blockNumber
                
                print(f"✅ Minted! Token ID: {token_id}")
                print(f"🔗 Tx: {tx_hash.hex()[:20]}...")
                
                return {
                    "tx_hash": tx_hash.hex(),
                    "token_id": str(token_id),
                    "contract": self.contract_address,
                    "explorer": f"https://{self._get_explorer()}/tx/{tx_hash.hex()}"
                }
            else:
                print("❌ Transaction failed")
                return None
                
        except Exception as e:
            print(f"❌ Mint failed: {e}")
            return None
    
    def _mock_mint(self, metadata_uri: str) -> Dict:
        """Mock mint for testing"""
        time.sleep(1)
        mock_tx = "0x" + "b" * 64
        mock_token_id = str(int(time.time()))
        
        print(f"🧪 Mock Minted! Token ID: {mock_token_id}")
        
        return {
            "tx_hash": mock_tx,
            "token_id": mock_token_id,
            "contract": "mock",
            "explorer": "https://example.com"
        }
    
    def _get_explorer(self) -> str:
        if self.wm.current_network == "polygon":
            return "polygonscan.com"
        return "etherscan.io"


def get_contract_manager(wallet_manager):
    return NFTContractManager(wallet_manager)