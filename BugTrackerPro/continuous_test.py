#!/usr/bin/env python3
"""
Continuous Testing Script
Monitors the application and runs tests when changes are detected
"""

import time
import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path

class ContinuousTestRunner:
    def __init__(self):
        self.last_test_time = 0
        self.test_interval = 30  # Run tests every 30 seconds
        self.watched_files = [
            'app.py',
            'models.py',
            'templates/',
            'static/'
        ]
        
    def get_file_modification_time(self, filepath):
        """Get the last modification time of a file or directory"""
        try:
            if os.path.isdir(filepath):
                # For directories, get the most recent modification time
                mod_times = []
                for root, dirs, files in os.walk(filepath):
                    for file in files:
                        full_path = os.path.join(root, file)
                        mod_times.append(os.path.getmtime(full_path))
                return max(mod_times) if mod_times else 0
            else:
                return os.path.getmtime(filepath)
        except (OSError, ValueError):
            return 0
    
    def files_changed(self):
        """Check if any watched files have changed"""
        for filepath in self.watched_files:
            if os.path.exists(filepath):
                mod_time = self.get_file_modification_time(filepath)
                if mod_time > self.last_test_time:
                    return True
        return False
    
    def run_tests(self):
        """Run the quick test suite"""
        print(f"\n{'='*50}")
        print(f"Running tests at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}")
        
        try:
            # Run quick tests
            result = subprocess.run(['python', 'quick_tests.py'], 
                                  capture_output=True, text=True, timeout=60)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            success = result.returncode == 0
            
            if success:
                print("✅ All tests passed!")
            else:
                print("❌ Some tests failed!")
                
            return success
            
        except subprocess.TimeoutExpired:
            print("⏰ Tests timed out")
            return False
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    def monitor(self):
        """Start continuous monitoring"""
        print("🔍 Starting continuous test monitoring...")
        print(f"Watching files: {', '.join(self.watched_files)}")
        print(f"Test interval: {self.test_interval} seconds")
        print("Press Ctrl+C to stop")
        
        # Run initial test
        self.run_tests()
        self.last_test_time = time.time()
        
        try:
            while True:
                time.sleep(5)  # Check every 5 seconds
                
                current_time = time.time()
                
                # Run tests if files changed or interval passed
                if (self.files_changed() or 
                    current_time - self.last_test_time > self.test_interval):
                    
                    self.run_tests()
                    self.last_test_time = current_time
                    
        except KeyboardInterrupt:
            print("\n🛑 Continuous testing stopped")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        runner = ContinuousTestRunner()
        runner.monitor()
    else:
        print("Continuous Test Runner")
        print("Usage:")
        print("  python continuous_test.py --continuous")
        print("  This will monitor files and run tests automatically")

if __name__ == '__main__':
    main()