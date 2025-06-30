"""
Client utilities for Aptos interactions.
Re-exports from official Aptos SDK with additional utility classes.
"""

from aptos_sdk.async_client import RestClient
import httpx
import logging

logger = logging.getLogger(__name__)

class FaucetClient:
    """Client for requesting test tokens from Aptos testnet/devnet faucets."""
    
    def __init__(self, base_url="https://faucet.testnet.aptoslabs.com"):
        """
        Initialize faucet client.
        
        Args:
            base_url: Faucet base URL (testnet or devnet)
        """
        self.base_url = base_url.rstrip("/")
        
    async def fund_account(self, address, amount=100_000_000):
        """
        Request test tokens from faucet.
        
        Args:
            address: Target account address (as string or AccountAddress)
            amount: Amount in octas (default 1 APT = 100_000_000 octas)
            
        Returns:
            Dict containing faucet response
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                endpoint = f"{self.base_url}/mint"
                
                # Handle different address types
                if hasattr(address, 'hex'):
                    address_str = address.hex()
                elif hasattr(address, '__str__'):
                    address_str = str(address)
                else:
                    address_str = address
                    
                # Ensure 0x prefix
                if not address_str.startswith('0x'):
                    address_str = f"0x{address_str}"
                
                payload = {
                    "amount": amount,
                    "address": address_str
                }
                
                logger.info(f"Requesting {amount} octas for {address_str} from {endpoint}")
                
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Faucet request successful: {result}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Faucet HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Faucet request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Faucet request failed: {e}")
            raise Exception(f"Faucet unavailable: {e}")

# Re-export common classes
__all__ = ['RestClient', 'FaucetClient'] 