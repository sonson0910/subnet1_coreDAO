#!/usr/bin/env python3
"""
Test connection between miner and validator
"""
import requests
import time

def test_connections():
    """Test if miner and validator can communicate"""
    print("🔍 TESTING MINER-VALIDATOR CONNECTION")
    print("=" * 50)
    
    # Test ports
    ports_to_test = [
        (8001, "Validator 1"),
        (8002, "Validator 2"), 
        (8101, "Miner 1"),
        (8102, "Miner 1 old port"),
    ]
    
    for port, name in ports_to_test:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            print(f"✅ {name} (port {port}): {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {name} (port {port}): Connection refused")
        except requests.exceptions.Timeout:
            print(f"⏰ {name} (port {port}): Timeout")
        except Exception as e:
            print(f"💥 {name} (port {port}): {e}")
    
    # Test validator submit endpoint
    print(f"\n🔍 Testing validator submit endpoints...")
    for port in [8001, 8002]:
        try:
            # Test with fake data to see response
            test_data = {
                "task_id": "test_task",
                "miner_uid": "test_miner",
                "result_data": {
                    "output_description": "test_base64_string",
                    "processing_time_ms": 1000
                }
            }
            
            response = requests.post(
                f"http://localhost:{port}/v1/miner/submit_result",
                json=test_data,
                timeout=5
            )
            print(f"✅ Validator (port {port}) submit endpoint: {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Validator (port {port}) submit endpoint: Connection refused")
        except Exception as e:
            print(f"💥 Validator (port {port}) submit endpoint: {e}")
    
    # Test if miner can reach validator
    print(f"\n🤖 Testing if miner can submit to validator...")
    
    # This simulates what miner does
    problematic_data = {
        "task_id": "test_slot_task",
        "miner_uid": "test_miner_uid",
        "result_data": {
            "output_description": "Slot-basedconsensustaskforslot1708",  # The problematic string!
            "processing_time_ms": 1000,
            "miner_uid": "test_uid",
            "model_id": "test_model"
        }
    }
    
    try:
        response = requests.post(
            f"http://localhost:8001/v1/miner/submit_result",
            json=problematic_data,
            timeout=5
        )
        print(f"🎯 Submitted problematic data: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
    except Exception as e:
        print(f"💥 Failed to submit problematic data: {e}")

if __name__ == "__main__":
    test_connections()