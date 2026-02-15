"""
Vanta - IPFS Manager
Upload images to IPFS via NFT.Storage (real)
"""
import requests
import json
from pathlib import Path
from typing import Optional, Dict

class IPFSManager:
    def __init__(self):
        self.nft_storage_url = "https://api.nft.storage/upload"
        # ⬇️ API KEY خودت رو اینجا بذار از nft.storage
        self.nft_storage_key = "eyJhbGciOiJIUzI1NiIs..."  # توکن خودت
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """Upload image to IPFS, return CID"""
        if not Path(image_path).exists():
            print(f"❌ File not found: {image_path}")
            return None
        
        if not self.nft_storage_key or self.nft_storage_key == "eyJhbGciOiJIUzI1NiIs...":
            print("⚠️ No API key - using mock mode")
            return self._mock_upload(image_path)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.nft_storage_key}",
                "Accept": "application/json"
            }
            
            with open(image_path, 'rb') as f:
                response = requests.post(
                    self.nft_storage_url,
                    headers=headers,
                    data=f,
                    timeout=60
                )
            
            if response.status_code == 200:
                cid = response.json()['value']['cid']
                print(f"✅ Uploaded to NFT.Storage: {cid}")
                return f"ipfs://{cid}"
            else:
                print(f"❌ NFT.Storage error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None
    
    def _mock_upload(self, image_path: str) -> str:
        """Mock upload for testing"""
        import hashlib
        fake_cid = hashlib.md5(image_path.encode()).hexdigest()[:16]
        print(f"🧪 Mock IPFS CID: {fake_cid}")
        return f"ipfs://{fake_cid}"
    
    def create_metadata(self, name: str, description: str, image_uri: str, 
                       attributes: list = None) -> Dict:
        """Create NFT metadata JSON"""
        metadata = {
            "name": name,
            "description": description,
            "image": image_uri,
            "external_url": "https://vanta.app",
            "attributes": attributes or []
        }
        return metadata
    
    def upload_metadata(self, metadata: Dict) -> Optional[str]:
        """Upload metadata JSON to IPFS"""
        if not self.nft_storage_key or self.nft_storage_key == "eyJhbGciOiJIUzI1NiIs...":
            import hashlib
            fake_cid = hashlib.md5(json.dumps(metadata).encode()).hexdigest()[:16]
            return f"ipfs://{fake_cid}"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.nft_storage_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.nft_storage_url,
                headers=headers,
                json=metadata,
                timeout=30
            )
            
            if response.status_code == 200:
                cid = response.json()['value']['cid']
                print(f"✅ Metadata uploaded: {cid}")
                return f"ipfs://{cid}"
            else:
                print(f"❌ Metadata upload error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Metadata upload failed: {e}")
            return None


# Singleton
ipfs_manager = IPFSManager()