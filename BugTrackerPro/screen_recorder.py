"""
Screen recording functionality using Playwright for bug reproduction
"""

import asyncio
import os
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime
import base64

class ScreenRecorder:
    def __init__(self):
        self.recording_dir = Path("recordings")
        self.recording_dir.mkdir(exist_ok=True)
    
    async def start_recording_session(self, actions_description="Manual bug reproduction"):
        """Start a recording session with browser automation"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                record_video_dir=str(self.recording_dir),
                record_video_size={"width": 1280, "height": 720}
            )
            
            page = await context.new_page()
            
            # Record the session
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = self.recording_dir / f"bug_reproduction_{timestamp}.webm"
            
            return {
                'browser': browser,
                'context': context,
                'page': page,
                'video_path': video_path,
                'timestamp': timestamp
            }
    
    async def record_bug_reproduction(self, url, steps, duration=60):
        """Record a bug reproduction session"""
        session = await self.start_recording_session()
        
        try:
            page = session['page']
            
            # Navigate to the bug location
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            
            # Take initial screenshot
            screenshot_data = await page.screenshot()
            
            # Auto-scroll and interact based on steps
            if "form" in steps.lower():
                await self._interact_with_forms(page)
            if "click" in steps.lower():
                await self._simulate_clicks(page)
            if "upload" in steps.lower():
                await self._simulate_file_upload(page)
            
            # Wait for specified duration
            await asyncio.sleep(duration)
            
            # Close and get video
            await session['context'].close()
            await session['browser'].close()
            
            return {
                'video_path': session['video_path'],
                'screenshot': base64.b64encode(screenshot_data).decode('utf-8'),
                'timestamp': session['timestamp']
            }
            
        except Exception as e:
            await session['browser'].close()
            raise e
    
    async def _interact_with_forms(self, page):
        """Simulate form interactions"""
        # Fill common form fields
        await page.fill('#title', 'Test Bug Title')
        await page.fill('#description', 'This is a test bug description with sufficient length for testing.')
        await asyncio.sleep(2)
    
    async def _simulate_clicks(self, page):
        """Simulate clicking on common elements"""
        buttons = await page.query_selector_all('button, .btn')
        if buttons:
            await buttons[0].click()
            await asyncio.sleep(1)
    
    async def _simulate_file_upload(self, page):
        """Simulate file upload"""
        file_input = await page.query_selector('input[type="file"]')
        if file_input:
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write('Test file content for bug reproduction')
                test_file = f.name
            
            await file_input.set_input_files(test_file)
            os.unlink(test_file)
            await asyncio.sleep(2)
    
    def get_recording_url(self, video_path):
        """Generate URL for accessing recorded video"""
        return f"/recordings/{Path(video_path).name}"
    
    def cleanup_old_recordings(self, days=7):
        """Clean up recordings older than specified days"""
        import time
        cutoff = time.time() - (days * 24 * 60 * 60)
        
        for video_file in self.recording_dir.glob("*.webm"):
            if video_file.stat().st_mtime < cutoff:
                video_file.unlink()