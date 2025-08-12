#!/usr/bin/env python3
"""
Deep Transaction Analysis
"""""

import asyncio
import httpx

async def analyze_transaction():
    tx_hash  =  "0x3ef8d61a31c267484b8eeb7abde3261a4a70761983bcbd717e1723d4c8eae353"
    original_miner  =  "0xd2c53003a54fb09e1ee900842fb1572101ca8bcbffb16005054a90199bc00f6d"
    
    print("🔍 DEEP TRANSACTION ANALYSIS")
    print(" = "*60)
    
    try:
        async with httpx.AsyncClient() as client:
            # Get transaction details
            response  =  await client.get(f"https://fullnode.testnet.aptoslabs.com/v1/transactions/by_hash/{tx_hash}")
            data  =  response.json()
            
            print(f"✅ SUCCESS: {data.get('success', False)}")
            print(f"📍 HASH: {data.get('hash', 'unknown')}")
            print(f"🏛️ SENDER: {data.get('sender', 'unknown')}")
            print(f"🏷️ VERSION: {data.get('version', 'unknown')}")
            print()
            
            # Analyze arguments
            print("📝 ARGUMENTS:")
            args  =  data.get('payload', {}).get('arguments', [])
            for i, arg in enumerate(args):
                print(f"  {i}: {arg}")
                if arg == original_miner:
                    print(f"     🎯 *** MATCHES ORIGINAL MINER ADDRESS! ***")
            print()
            
            # Analyze changes
            print("🔄 CHANGES:")
            changes  =  data.get('changes', [])
            for i, change in enumerate(changes):
                if i < 10:  # Show first 10:
                    addr  =  change.get('address', 'N/A')
                    change_type  =  change.get('type', 'unknown')
                    print(f"  {i}: {change_type} - {addr}")
                    
                    if addr == original_miner:
                        print(f"     🎯 *** CHANGE TO ORIGINAL MINER! ***")
                        print(f"     Data: {change.get('data', {})}")
            print()
            
            # Analyze events  
            print("🎉 EVENTS:")
            events  =  data.get('events', [])
            for i, event in enumerate(events):
                event_type  =  event.get('type', 'unknown')
                print(f"  {i}: {event_type}")
                
                if 'data' in event:
                    event_data  =  event['data']
                    print(f"     Data: {event_data}")
                    
                    # Check if store address relates to our miner:
                    if 'store' in event_data:
                        store_addr  =  event_data['store']
                        print(f"     Store: {store_addr}")
            print()
            
            # Check current account state
            print("🔍 CURRENT ACCOUNT STATE:")
            
            # Check account resources
            acc_response  =  await client.get(f"https://fullnode.testnet.aptoslabs.com/v1/accounts/{original_miner}/resources")
            if acc_response.status_code == 200:
                resources  =  acc_response.json()
                print(f"   Resources count: {len(resources)}")
                
                for resource in resources:
                    resource_type  =  resource.get('type', 'unknown')
                    print(f"   - {resource_type}")
                    
                    if 'coin' in resource_type.lower():
                        coin_data  =  resource.get('data', {})
                        if 'coin' in coin_data:
                            value  =  coin_data['coin'].get('value', '0')
                            apt_value  =  int(value) / 100_000_000
                            print(f"     💰 Balance: {apt_value} APT ({value} octas)")
            else:
                print(f"   ❌ Could not get resources: {acc_response.status_code}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_transaction()) 