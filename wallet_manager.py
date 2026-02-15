"""
Vanta - Wallet Manager (Optimized)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional, Dict, Callable
from dataclasses import dataclass

from eth_account import Account
from eth_account.signers.local import LocalAccount

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


Account.enable_unaudited_hdwallet_features()


@dataclass
class NetworkConfig:
    name: str
    rpc_url: str
    chain_id: int
    symbol: str
    explorer: str


NETWORKS = {
    "ethereum": NetworkConfig(
        "Ethereum",
        "https://eth.llamarpc.com",
        1,
        "ETH",
        "etherscan.io"
    ),
    "polygon": NetworkConfig(
        "Polygon",
        "https://polygon-rpc.com",
        137,
        "MATIC",
        "polygonscan.com"
    ),
    "mumbai": NetworkConfig(
        "Mumbai Testnet",
        "https://rpc-mumbai.maticvigil.com",
        80001,
        "MATIC",
        "mumbai.polygonscan.com"
    ),
}


class WalletError(Exception):
    """Wallet operation error"""
    pass


class WalletManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._account: Optional[LocalAccount] = None
        self._current_network = "polygon"
        self._web3: Optional[Web3] = None
        self._listeners: list[Callable] = []
        
        self._wallet_file = Path("vanta_wallet.json")
        self._load_or_create()
        self._connect_web3()
        self._initialized = True
    
    def add_listener(self, callback: Callable):
        """Add state change listener"""
        self._listeners.append(callback)
    
    def _notify(self):
        """Notify all listeners"""
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                print(f"Listener error: {e}")
    
    def _load_or_create(self) -> None:
        """Load existing wallet or create new one"""
        if self._wallet_file.exists():
            try:
                data = json.loads(self._wallet_file.read_text(encoding="utf-8"))
                pk = data.get("private_key")
                if pk:
                    self._account = Account.from_key(pk)
                    print(f"✅ Wallet loaded: {self.address[:12]}...")
                    return
            except Exception as e:
                print(f"⚠️ Wallet load error: {e}")
        
        # Create new
        self._account = Account.create()
        self._save()
        print(f"🆕 New wallet: {self.address[:12]}...")
    
    def _save(self) -> None:
        """Persist wallet securely"""
        if self._account:
            data = {
                "private_key": self._account.key.hex(),
                "address": self.address,
                "created_at": str(Path().stat().st_ctime)
            }
            # Set restrictive permissions (Unix)
            self._wallet_file.write_text(json.dumps(data), encoding="utf-8")
            try:
                os.chmod(self._wallet_file, 0o600)
            except:
                pass  # Windows doesn't support Unix permissions
    
    def _connect_web3(self) -> None:
        """Connect to blockchain"""
        if not WEB3_AVAILABLE:
            print("⚠️ Web3 not installed")
            return
        
        try:
            config = NETWORKS[self._current_network]
            self._web3 = Web3(Web3.HTTPProvider(config.rpc_url, request_kwargs={'timeout': 10}))
            
            if self._web3.is_connected():
                print(f"✅ Connected to {config.name}")
            else:
                print(f"⚠️ Connection failed to {config.name}")
                self._web3 = None
        except Exception as e:
            print(f"❌ Web3 error: {e}")
            self._web3 = None
    
    @property
    def address(self) -> str:
        return self._account.address if self._account else ""
    
    @property
    def account(self) -> Optional[LocalAccount]:
        return self._account
    
    @property
    def is_connected(self) -> bool:
        return self._web3 is not None and self._web3.is_connected()
    
    @property
    def current_network(self) -> str:
        return self._current_network
    
    def get_network_config(self) -> NetworkConfig:
        return NETWORKS[self._current_network]
    
    def set_network(self, network: str) -> bool:
        """Switch network with validation"""
        if network not in NETWORKS:
            print(f"❌ Unknown network: {network}")
            return False
        
        old_network = self._current_network
        self._current_network = network
        self._connect_web3()
        
        if self.is_connected or network == old_network:
            self._notify()
            print(f"🌐 Switched to {NETWORKS[network].name}")
            return True
        
        # Revert on failure
        self._current_network = old_network
        self._connect_web3()
        return False
    
    def get_balance(self) -> float:
        """Get balance in native token"""
        if not self.is_connected or not self._account:
            return 0.0
        
        try:
            balance_wei = self._web3.eth.get_balance(self.address)
            return float(self._web3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            print(f"Balance error: {e}")
            return 0.0
    
    def get_web3(self) -> Optional[Web3]:
        """Get Web3 instance (may be None)"""
        if not self.is_connected:
            self._connect_web3()
        return self._web3
    
    def get_transaction_count(self) -> int:
        """Get nonce for transactions"""
        if not self.is_connected:
            return 0
        try:
            return self._web3.eth.get_transaction_count(self.address)
        except:
            return 0
    
    def sign_transaction(self, tx_dict: dict) -> Optional[bytes]:
        """Sign transaction with private key"""
        if not self._account:
            return None
        
        try:
            signed = self._account.sign_transaction(tx_dict)
            return signed.rawTransaction
        except Exception as e:
            print(f"Signing error: {e}")
            return None
    
    def send_transaction(self, signed_tx: bytes) -> Optional[str]:
        """Send signed transaction"""
        if not self.is_connected or not signed_tx:
            return None
        
        try:
            tx_hash = self._web3.eth.send_raw_transaction(signed_tx)
            return tx_hash.hex()
        except Exception as e:
            print(f"Send error: {e}")
            return None
    
    def wait_for_receipt(self, tx_hash: str, timeout: int = 120):
        """Wait for transaction confirmation"""
        if not self.is_connected:
            return None
        
        try:
            return self._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        except Exception as e:
            print(f"Wait error: {e}")
            return None
    
    def get_short_address(self, chars: int = 6) -> str:
        """Get truncated address"""
        addr = self.address
        if len(addr) <= chars * 2 + 4:
            return addr
        return f"{addr[:2+chars]}...{addr[-chars:]}"
    
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address"""
        if not WEB3_AVAILABLE:
            return address.startswith("0x") and len(address) == 42
        
        try:
            return self._web3.is_address(address)
        except:
            return False


# Global instance
wallet_manager = WalletManager()