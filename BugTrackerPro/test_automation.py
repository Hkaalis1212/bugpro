import asyncio
from playwright.async_api import async_playwright
import json
import sys
import os
from datetime import datetime

async def run_replay(actions, base_url="http://localhost:5000"):
    """
    Run automated test replay using Playwright
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for headless
        context = await browser.new_context(
            record_video_dir="test_videos/",
            record_video_size={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        # Create test results directory
        os.makedirs("test_results", exist_ok=True)
        os.makedirs("test_videos", exist_ok=True)
        
        test_results = {
            "start_time": datetime.now().isoformat(),
            "actions_executed": [],
            "errors": [],
            "success": False
        }
        
        try:
            print(f"Navigating to {base_url}")
            await page.goto(base_url)
            await page.wait_for_load_state('networkidle')
            
            for i, step in enumerate(actions):
                action = step.get("action")
                selector = step.get("selector")
                value = step.get("value", "")
                
                print(f"Step {i+1}: {action} on {selector}")
                
                if action == "click":
                    # Wait for element to be visible and clickable
                    await page.wait_for_selector(selector, state="visible", timeout=10000)
                    await page.click(selector)
                    test_results["actions_executed"].append(f"Clicked {selector}")
                    
                elif action == "type":
                    # Wait for input field to be available
                    await page.wait_for_selector(selector, state="visible", timeout=10000)
                    await page.fill(selector, value)
                    test_results["actions_executed"].append(f"Typed '{value}' in {selector}")
                    
                elif action == "wait":
                    wait_time = step.get("duration", 1000)
                    await page.wait_for_timeout(wait_time)
                    test_results["actions_executed"].append(f"Waited {wait_time}ms")
                
                # Small delay between actions
                await page.wait_for_timeout(500)
            
            # Take final screenshot
            screenshot_path = f"test_results/final_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            
            # Wait to show final state
            await page.wait_for_timeout(2000)
            
            test_results["success"] = True
            test_results["screenshot"] = screenshot_path
            print("Test completed successfully!")
            
        except Exception as e:
            error_msg = f"Error during replay at step {len(test_results['actions_executed'])}: {str(e)}"
            test_results["errors"].append(error_msg)
            print(error_msg)
            
            # Take error screenshot
            try:
                error_screenshot = f"test_results/error_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=error_screenshot)
                test_results["error_screenshot"] = error_screenshot
            except:
                pass
                
        finally:
            test_results["end_time"] = datetime.now().isoformat()
            
            # Save test results
            results_file = f"test_results/test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(test_results, f, indent=2)
            
            print(f"Test results saved to {results_file}")
            await context.close()
            await browser.close()
        
        return test_results

async def test_login_flow():
    """Test the login flow specifically"""
    login_actions = [
        {"action": "click", "selector": "a[href='/login']"},
        {"action": "wait", "duration": 1000},
        {"action": "type", "selector": "#email", "value": "admin@example.com"},
        {"action": "type", "selector": "#password", "value": "admin123"},
        {"action": "click", "selector": "#submit"},
        {"action": "wait", "duration": 2000}
    ]
    
    return await run_replay(login_actions)

async def test_onboarding_tutorial():
    """Test the onboarding tutorial functionality"""
    onboarding_actions = [
        {"action": "wait", "duration": 2000},
        {"action": "click", "selector": "button[onclick='startOnboarding()']"},
        {"action": "wait", "duration": 2000},
        {"action": "click", "selector": ".btn-next"},
        {"action": "wait", "duration": 1000},
        {"action": "click", "selector": ".btn-next"},
        {"action": "wait", "duration": 1000},
        {"action": "click", "selector": ".btn-next"},
        {"action": "wait", "duration": 1000},
        {"action": "click", "selector": ".btn-next"},
        {"action": "wait", "duration": 1000},
        {"action": "click", "selector": ".btn-next"},
        {"action": "wait", "duration": 2000}
    ]
    
    return await run_replay(onboarding_actions)

async def test_bug_submission_flow():
    """Test the complete bug submission flow"""
    bug_submission_actions = [
        {"action": "type", "selector": "#title", "value": "Test Bug Report from Automation"},
        {"action": "type", "selector": "#description", "value": "This is an automated test bug report. The application should handle this correctly and generate AI-parsed reproduction steps."},
        {"action": "click", "selector": "button[type='submit']"},
        {"action": "wait", "duration": 5000}
    ]
    
    return await run_replay(bug_submission_actions)

async def test_admin_dashboard_flow():
    """Test accessing the admin dashboard"""
    admin_actions = [
        {"action": "click", "selector": "a[href='/login']"},
        {"action": "wait", "duration": 1000},
        {"action": "type", "selector": "#email", "value": "admin@example.com"},
        {"action": "type", "selector": "#password", "value": "admin123"},
        {"action": "click", "selector": "#submit"},
        {"action": "wait", "duration": 2000},
        {"action": "click", "selector": "a[href='/admin']"},
        {"action": "wait", "duration": 3000}
    ]
    
    return await run_replay(admin_actions)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run custom actions from command line
        actions = json.loads(sys.argv[1])
        base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5000"
        asyncio.run(run_replay(actions, base_url))
    else:
        # Run predefined test suites
        print("Running automated test suites...")
        
        print("\n1. Testing login flow...")
        login_result = asyncio.run(test_login_flow())
        
        print("\n2. Testing bug submission flow...")
        bug_result = asyncio.run(test_bug_submission_flow())
        
        print("\n3. Testing admin dashboard flow...")
        admin_result = asyncio.run(test_admin_dashboard_flow())
        
        print("\n=== Test Summary ===")
        print(f"Login test: {'PASSED' if login_result['success'] else 'FAILED'}")
        print(f"Bug submission test: {'PASSED' if bug_result['success'] else 'FAILED'}")
        print(f"Admin dashboard test: {'PASSED' if admin_result['success'] else 'FAILED'}")