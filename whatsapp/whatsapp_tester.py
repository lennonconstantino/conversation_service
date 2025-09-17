"""
Script to test the WhatsApp server
"""
import requests
import time

SERVER_URL = "http://localhost:5001"
TEST_PHONE = "+5511999999999"

class WhatsAppServerTester:
    def __init__(self, base_url=SERVER_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_server_health(self):
        """Test if server is responding"""
        try:
            response = self.session.get(f"{self.base_url}/admin/stats", timeout=5)
            if response.status_code == 200:
                print("Server responding normally")
                return True
            else:
                print(f"Server responded with status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("Server not running or not accessible")
            return False
        except Exception as e:
            print(f"Error testing server: {e}")
            return False
    
    def test_webhook_verification(self):
        """Test webhook verification (simulating WhatsApp)"""
        params = {
            'hub.mode': 'subscribe',
            'hub.verify_token': 'test_token_123',
            'hub.challenge': 'test_challenge_123'
        }
        
        try:
            response = self.session.get(f"{self.base_url}/webhook", params=params)
            
            if response.status_code == 200:
                print("Webhook verified successfully")
                return True
            else:
                print(f"Webhook verification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error in webhook test: {e}")
            return False
    
    def simulate_text_message(self, phone=TEST_PHONE, message="Hi, I need help!"):
        """Simulate receiving text message via webhook"""
        webhook_payload = {
            "entry": [{
                "id": "entry_id",
                "changes": [{
                    # Adicione a linha abaixo
                    "field": "messages", 
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": "123456789"
                        },
                        "messages": [{
                            "from": phone,
                            "id": f"msg_{int(time.time())}",
                            "timestamp": str(int(time.time())),
                            "type": "text",
                            "text": {
                                "body": message
                            }
                        }]
                    }
                }]
            }]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/webhook",
                json=webhook_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print("Text message processed successfully")
                return True
            else:
                print(f"Error processing message: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error simulating message: {e}")
            return False
    
    def test_conversation_history(self, phone=TEST_PHONE):
        """Test conversation history retrieval"""
        try:
            response = self.session.get(f"{self.base_url}/admin/conversations/{phone}")
            
            if response.status_code == 200:
                data = response.json()
                print("Conversation history retrieved successfully")
                print(f"Total messages: {data.get('total', 0)}")
                
                # Show last messages
                messages = data.get('messages', [])
                if messages:
                    print("\nLast messages:")
                    for msg in messages[-3:]:
                        owner = msg.get('owner', 'unknown')
                        message = msg.get('message', '')[:50]
                        print(f"  {owner}: {message}...")
                
                return True
            else:
                print(f"Error retrieving history: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error in history test: {e}")
            return False
    
    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/admin/stats")
            
            if response.status_code == 200:
                stats = response.json()
                print("Statistics retrieved successfully:")
                print(f"  - Active conversations: {stats.get('total_active_conversations', 0)}")
                print(f"  - Total messages: {stats.get('total_messages', 0)}")
                print(f"  - Message types: {stats.get('message_types', {})}")
                return True
            else:
                print(f"Error in statistics: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error in stats test: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("STARTING WHATSAPP SERVER TESTS")
        print("=" * 50)
        
        tests = [
            ("Server Health", self.test_server_health),
            ("Webhook Verification", self.test_webhook_verification),
            ("Text Message", lambda: self.simulate_text_message(message="Test message")),
            ("Conversation History", self.test_conversation_history),
            ("Admin Statistics", self.test_admin_stats),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\nTesting {test_name}...")
            try:
                result = test_func()
                results[test_name] = result
            except Exception as e:
                print(f"Error in test '{test_name}': {e}")
                results[test_name] = False
            
            time.sleep(1)
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY:")
        
        passed = 0
        for test_name, result in results.items():
            status = "PASSED" if result else "FAILED"
            print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nResult: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("All tests passed! System working correctly.")
        else:
            print("Some tests failed. Check configuration.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "quick":
            tester = WhatsAppServerTester()
            print("Running quick test...")
            tester.test_server_health()
            tester.test_admin_stats()
            
        elif command == "message":
            tester = WhatsAppServerTester()
            message = sys.argv[2] if len(sys.argv) > 2 else "Test message"
            print(f"Sending test message: {message}")
            tester.simulate_text_message(message=message)
            
        else:
            print("Available commands:")
            print("  python mock_whatsapp_server_tester.py quick          # Quick test")
            print("  python mock_whatsapp_server_tester.py message 'text' # Send test message")
            print("  python mock_whatsapp_server_tester.py                # Run all tests")
    else:
        # Run all tests
        tester = WhatsAppServerTester()
        tester.run_all_tests()
