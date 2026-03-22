#!/usr/bin/env python3
"""
mTLS Remote Testing Script
Tests mTLS authentication with different certificates against a remote server
"""

import requests
import json
import sys
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from urllib.parse import urljoin

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


@dataclass
class TestResult:
    """Test result data"""
    name: str
    passed: bool
    expected_status: int
    actual_status: int
    message: str
    response_data: Optional[Dict] = None


class MTLSRemoteTester:
    """Test mTLS authentication against remote server"""
    
    def __init__(self, base_url: str, certs_dir: str = "./certs"):
        """
        Initialize tester
        
        Args:
            base_url: Base URL of the server (e.g., https://example.com)
            certs_dir: Directory containing certificates
        """
        self.base_url = base_url.rstrip('/')
        self.certs_dir = certs_dir
        self.results: List[TestResult] = []
        
        # Certificate configurations
        self.certificates = {
            'admin': {
                'cert': os.path.join(certs_dir, 'client-admin.pem'),
                'description': 'Admin (full access)',
                'expected_scopes': ['scim.read', 'scim.write', 'supportingdata.read']
            },
            'readonly': {
                'cert': os.path.join(certs_dir, 'client-readonly.pem'),
                'description': 'Read-only',
                'expected_scopes': ['scim.read', 'supportingdata.read']
            },
            'scim': {
                'cert': os.path.join(certs_dir, 'client-scim.pem'),
                'description': 'SCIM-only',
                'expected_scopes': ['scim.read', 'scim.write']
            }
        }
    
    def verify_certificates(self) -> bool:
        """Verify all certificates exist"""
        print(f"\n{BLUE}Verifying certificates...{RESET}")
        all_exist = True
        
        for name, config in self.certificates.items():
            cert_path = config['cert']
            if os.path.exists(cert_path):
                print(f"  ✓ {name}: {cert_path}")
            else:
                print(f"  ✗ {name}: {cert_path} NOT FOUND")
                all_exist = False
        
        return all_exist
    
    def make_request(self, method: str, endpoint: str, cert_path: Optional[str] = None,
                    data: Optional[Dict] = None, expected_status: int = 200) -> Tuple[int, Optional[Dict]]:
        """
        Make HTTP request with optional client certificate
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /scim/v2/Users)
            cert_path: Path to client certificate (optional)
            data: Request body data (optional)
            expected_status: Expected HTTP status code
            
        Returns:
            Tuple of (status_code, response_data)
        """
        url = urljoin(self.base_url, endpoint)
        headers = {'Content-Type': 'application/json'} if data else {}
        
        try:
            kwargs = {
                'headers': headers,
                'verify': False,  # Skip server cert verification for testing
                'timeout': 10
            }
            
            if cert_path:
                kwargs['cert'] = cert_path
            
            if data:
                kwargs['json'] = data
            
            response = requests.request(method, url, **kwargs)
            
            try:
                response_data = response.json()
            except:
                response_data = {'text': response.text}
            
            return response.status_code, response_data
            
        except requests.exceptions.SSLError as e:
            return 0, {'error': f'SSL Error: {str(e)}'}
        except requests.exceptions.ConnectionError as e:
            return 0, {'error': f'Connection Error: {str(e)}'}
        except Exception as e:
            return 0, {'error': f'Error: {str(e)}'}
    
    def test_no_certificate(self):
        """Test access without certificate (should fail if mTLS required)"""
        print(f"\n{BLUE}Test 1: Access without certificate{RESET}")
        
        status, data = self.make_request('GET', '/scim/v2/ServiceProviderConfig')
        
        # Could be 401 (auth required) or 200 (optional cert mode)
        if status in [200, 401]:
            result = TestResult(
                name="No Certificate",
                passed=True,
                expected_status=status,
                actual_status=status,
                message=f"Server responded as expected (status {status})",
                response_data=data
            )
            print(f"  {GREEN}✓ PASS{RESET}: {result.message}")
        else:
            result = TestResult(
                name="No Certificate",
                passed=False,
                expected_status=200,
                actual_status=status,
                message=f"Unexpected status: {status}",
                response_data=data
            )
            print(f"  {RED}✗ FAIL{RESET}: {result.message}")
        
        self.results.append(result)
    
    def test_admin_read_users(self):
        """Test admin certificate reading users"""
        print(f"\n{BLUE}Test 2: Admin certificate - Read users{RESET}")
        
        cert_path = self.certificates['admin']['cert']
        status, data = self.make_request('GET', '/scim/v2/Users?count=2', cert_path)
        
        passed = status == 200 and data is not None and 'Resources' in data
        result = TestResult(
            name="Admin - Read Users",
            passed=passed,
            expected_status=200,
            actual_status=status,
            message="Successfully read users" if passed else f"Failed: {data.get('detail', 'Unknown error') if data else 'No response'}",
            response_data=data
        )
        
        if passed and data:
            print(f"  {GREEN}✓ PASS{RESET}: Retrieved {len(data.get('Resources', []))} users")
        else:
            print(f"  {RED}✗ FAIL{RESET}: {result.message}")
        
        self.results.append(result)
    
    def test_admin_create_user(self):
        """Test admin certificate creating a user"""
        print(f"\n{BLUE}Test 3: Admin certificate - Create user{RESET}")
        
        cert_path = self.certificates['admin']['cert']
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": f"test.mtls.{os.getpid()}@example.com",
            "name": {
                "givenName": "Test",
                "familyName": "MTLS"
            },
            "emails": [{
                "value": f"test.mtls.{os.getpid()}@example.com",
                "primary": True
            }]
        }
        
        status, data = self.make_request('POST', '/scim/v2/Users', cert_path, user_data)
        
        passed = status == 201
        result = TestResult(
            name="Admin - Create User",
            passed=passed,
            expected_status=201,
            actual_status=status,
            message="Successfully created user" if passed else f"Failed: {data.get('detail', 'Unknown error') if data else 'No response'}",
            response_data=data
        )
        
        if passed and data:
            print(f"  {GREEN}✓ PASS{RESET}: Created user {data.get('userName')}")
        else:
            print(f"  {RED}✗ FAIL{RESET}: {result.message}")
        
        self.results.append(result)
    
    def test_readonly_read_users(self):
        """Test readonly certificate reading users"""
        print(f"\n{BLUE}Test 4: Readonly certificate - Read users{RESET}")
        
        cert_path = self.certificates['readonly']['cert']
        status, data = self.make_request('GET', '/scim/v2/Users?count=2', cert_path)
        
        passed = status == 200 and data is not None and 'Resources' in data
        result = TestResult(
            name="Readonly - Read Users",
            passed=passed,
            expected_status=200,
            actual_status=status,
            message="Successfully read users" if passed else f"Failed: {data.get('detail', 'Unknown error') if data else 'No response'}",
            response_data=data
        )
        
        if passed and data:
            print(f"  {GREEN}✓ PASS{RESET}: Retrieved {len(data.get('Resources', []))} users")
        else:
            print(f"  {RED}✗ FAIL{RESET}: {result.message}")
        
        self.results.append(result)
    
    def test_readonly_create_user(self):
        """Test readonly certificate creating a user (should fail)"""
        print(f"\n{BLUE}Test 5: Readonly certificate - Create user (should fail){RESET}")
        
        cert_path = self.certificates['readonly']['cert']
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "should.fail@example.com",
            "name": {"givenName": "Should", "familyName": "Fail"}
        }
        
        status, data = self.make_request('POST', '/scim/v2/Users', cert_path, user_data)
        
        passed = status == 403  # Should be forbidden
        result = TestResult(
            name="Readonly - Create User (should fail)",
            passed=passed,
            expected_status=403,
            actual_status=status,
            message="Correctly blocked write operation" if passed else f"Unexpected: {status}",
            response_data=data
        )
        
        if passed:
            print(f"  {GREEN}✓ PASS{RESET}: Write operation correctly blocked (403)")
        else:
            print(f"  {RED}✗ FAIL{RESET}: Expected 403, got {status}")
        
        self.results.append(result)
    
    def test_scim_read_users(self):
        """Test SCIM-only certificate reading users"""
        print(f"\n{BLUE}Test 6: SCIM-only certificate - Read users{RESET}")
        
        cert_path = self.certificates['scim']['cert']
        status, data = self.make_request('GET', '/scim/v2/Users?count=2', cert_path)
        
        passed = status == 200 and data is not None and 'Resources' in data
        result = TestResult(
            name="SCIM - Read Users",
            passed=passed,
            expected_status=200,
            actual_status=status,
            message="Successfully read users" if passed else f"Failed: {data.get('detail', 'Unknown error') if data else 'No response'}",
            response_data=data
        )
        
        if passed and data:
            print(f"  {GREEN}✓ PASS{RESET}: Retrieved {len(data.get('Resources', []))} users")
        else:
            print(f"  {RED}✗ FAIL{RESET}: {result.message}")
        
        self.results.append(result)
    
    def test_scim_create_user(self):
        """Test SCIM-only certificate creating a user"""
        print(f"\n{BLUE}Test 7: SCIM-only certificate - Create user{RESET}")
        
        cert_path = self.certificates['scim']['cert']
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": f"scim.test.{os.getpid()}@example.com",
            "name": {"givenName": "SCIM", "familyName": "Test"}
        }
        
        status, data = self.make_request('POST', '/scim/v2/Users', cert_path, user_data)
        
        passed = status == 201
        result = TestResult(
            name="SCIM - Create User",
            passed=passed,
            expected_status=201,
            actual_status=status,
            message="Successfully created user" if passed else f"Failed: {data.get('detail', 'Unknown error') if data else 'No response'}",
            response_data=data
        )
        
        if passed and data:
            print(f"  {GREEN}✓ PASS{RESET}: Created user {data.get('userName')}")
        else:
            print(f"  {RED}✗ FAIL{RESET}: {result.message}")
        
        self.results.append(result)
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{'='*70}")
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        print(f"\nTotal Tests: {len(self.results)}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        
        if failed > 0:
            print(f"\n{RED}Failed Tests:{RESET}")
            for result in self.results:
                if not result.passed:
                    print(f"  ✗ {result.name}: {result.message}")
        
        print(f"\n{'='*70}\n")
        
        return failed == 0
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{'='*70}")
        print(f"{BLUE}mTLS REMOTE TESTING{RESET}")
        print(f"{'='*70}")
        print(f"Base URL: {self.base_url}")
        print(f"Certificates: {self.certs_dir}")
        
        if not self.verify_certificates():
            print(f"\n{RED}ERROR: Some certificates are missing!{RESET}")
            print(f"Run: ./tools/generate_mtls_certs.sh")
            return False
        
        # Run tests
        self.test_no_certificate()
        self.test_admin_read_users()
        self.test_admin_create_user()
        self.test_readonly_read_users()
        self.test_readonly_create_user()
        self.test_scim_read_users()
        self.test_scim_create_user()
        
        # Print summary
        return self.print_summary()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test mTLS authentication against remote server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test local Docker container
  python test_mtls_remote.py https://localhost:8443
  
  # Test remote server
  python test_mtls_remote.py https://your-server.com
  
  # Custom certificates directory
  python test_mtls_remote.py https://localhost:8443 --certs ./my-certs
        """
    )
    
    parser.add_argument(
        'base_url',
        help='Base URL of the server (e.g., https://localhost:8443)'
    )
    parser.add_argument(
        '--certs',
        default='./certs',
        help='Directory containing certificates (default: ./certs)'
    )
    
    args = parser.parse_args()
    
    # Disable SSL warnings for testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Run tests
    tester = MTLSRemoteTester(args.base_url, args.certs)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

# Made with Bob
