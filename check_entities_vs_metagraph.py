#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Add moderntensor path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "moderntensor_aptos"))

from mt_core.metagraph.core_metagraph_adapter import CoreMetagraphClient

def load_entities():
    """Load all entities from JSON files"""
    entities_dir = Path(__file__).parent / "entities"
    entities = {}
    
    for json_file in entities_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            entity = json.load(f)
            entities[json_file.stem] = entity
    
    return entities

def check_entities_on_metagraph():
    """Check if entities are registered on metagraph"""
    print("🔍 CHECKING ENTITIES vs METAGRAPH")
    print("=" * 60)
    
    # Load entities from files
    entities = load_entities()
    print(f"📄 Loaded {len(entities)} entities from files:")
    
    for name, entity in entities.items():
        print(f"   {name}: {entity['address']} ({entity['type']})")
    
    # Get metagraph data
    print(f"\n🌐 Getting metagraph data from blockchain...")
    try:
        client = CoreMetagraphClient()
        
        # Get registered addresses
        registered_miners = client.get_all_miners()
        registered_validators = client.get_all_validators()
        
        print(f"📊 Found on blockchain:")
        print(f"   Miners: {len(registered_miners)}")
        print(f"   Validators: {len(registered_validators)}")
        
        print(f"\n🔍 DETAILED COMPARISON:")
        print("=" * 60)
        
        # Check each entity
        for name, entity in entities.items():
            address = entity['address']
            entity_type = entity['type']
            
            print(f"\n🎯 {name.upper()} ({entity_type})")
            print(f"   Address: {address}")
            print(f"   Private Key: {entity['private_key'][:16]}...")
            print(f"   Expected Endpoint: {entity.get('api_endpoint', 'N/A')}")
            
            # Check if registered
            is_registered = False
            actual_endpoint = None
            
            if entity_type == 'miner':
                if address in registered_miners:
                    is_registered = True
                    # Get detailed info
                    try:
                        miner_info = client.get_miner_info(address)
                        actual_endpoint = miner_info.get('api_endpoint', 'N/A')
                        status = miner_info.get('status', 'Unknown')
                        stake = miner_info.get('stake', 0)
                        print(f"   ✅ REGISTERED as MINER")
                        print(f"   📡 Actual Endpoint: {actual_endpoint}")
                        print(f"   💰 Stake: {stake} CORE")
                        print(f"   🔄 Status: {status}")
                    except Exception as e:
                        print(f"   ✅ REGISTERED but error getting details: {e}")
                else:
                    print(f"   ❌ NOT REGISTERED")
            
            elif entity_type == 'validator':
                if address in registered_validators:
                    is_registered = True
                    # Get detailed info
                    try:
                        validator_info = client.get_validator_info(address)
                        actual_endpoint = validator_info.get('api_endpoint', 'N/A')
                        status = validator_info.get('status', 'Unknown')
                        stake = validator_info.get('stake', 0)
                        print(f"   ✅ REGISTERED as VALIDATOR")
                        print(f"   📡 Actual Endpoint: {actual_endpoint}")
                        print(f"   💰 Stake: {stake} CORE")
                        print(f"   🔄 Status: {status}")
                    except Exception as e:
                        print(f"   ✅ REGISTERED but error getting details: {e}")
                else:
                    print(f"   ❌ NOT REGISTERED")
            
            # Check endpoint match
            if is_registered and actual_endpoint:
                expected_endpoint = entity.get('api_endpoint', '')
                if actual_endpoint == expected_endpoint:
                    print(f"   ✅ Endpoint MATCHES")
                else:
                    print(f"   ⚠️ Endpoint MISMATCH:")
                    print(f"      Expected: {expected_endpoint}")
                    print(f"      Actual:   {actual_endpoint}")
        
        # Summary
        registered_count = 0
        for name, entity in entities.items():
            if entity['type'] == 'miner' and entity['address'] in registered_miners:
                registered_count += 1
            elif entity['type'] == 'validator' and entity['address'] in registered_validators:
                registered_count += 1
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total entities in files: {len(entities)}")
        print(f"   Already registered: {registered_count}")
        print(f"   Need to register: {len(entities) - registered_count}")
        
        if registered_count == 0:
            print(f"\n🚀 NEXT STEP: Register all entities")
            print(f"   Run: python register_entities_from_files.py")
        elif registered_count < len(entities):
            print(f"\n⚠️ NEXT STEP: Register remaining {len(entities) - registered_count} entities")
        else:
            print(f"\n✅ ALL ENTITIES ALREADY REGISTERED!")
            
    except Exception as e:
        print(f"❌ Error connecting to metagraph: {e}")

if __name__ == "__main__":
    check_entities_on_metagraph()
