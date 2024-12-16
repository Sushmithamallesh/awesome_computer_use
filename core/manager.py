import threading
import logging
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
import time
from contextlib import contextmanager
from queue import Queue
from dataclasses import dataclass

class BrowserManager:
    def __init__(self, headless: bool = False):
        self._id = id(self)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None  # Single page instance
        self._lock = threading.Lock()
        self.headless = headless
        self._initialized = False
        self._main_thread_id = threading.get_ident()  # Store main thread ID
        print(f"BrowserManager initialized with ID {self._id} in thread {self._main_thread_id}")
        
        # Initialize browser and page immediately in main thread
        self._initialize_browser()
    
    def _initialize_browser(self) -> None:
        """Initialize the browser if not already initialized."""
        if not self._initialized:
            try:
                print(f"Initializing browser in main thread {self._main_thread_id}...")
                self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(
                    headless=self.headless,
                    args=['--start-maximized']
                )
                self.context = self.browser.new_context(
                    viewport={"width": 1280, "height": 800}
                )
                self.page = self.context.new_page()
                self._initialized = True
                print("Browser and page successfully initialized")
            except Exception as e:
                print(f"Failed to initialize browser: {e}")
                self.cleanup()
                raise

    @contextmanager
    def get_page(self) -> Page:
        """Get the singleton page instance."""
        if not self._initialized or not self.page:
            raise RuntimeError("Browser not properly initialized")
        
        current_thread = threading.get_ident()
        print(f"Accessing page from thread {current_thread}")
        
        with self._lock:
            try:
                # Verify page is still valid
                # This will raise if the page is no longer usable
                self.page.evaluate("1")  
                yield self.page
            except Exception as e:
                print(f"Error accessing page: {e}")
                # If page is invalid, try to recreate it
                try:
                    print("Attempting to recreate page...")
                    self.page = self.context.new_page()
                    yield self.page
                except Exception as recreate_error:
                    print(f"Failed to recreate page: {recreate_error}")
                    raise

    def cleanup(self) -> None:
        """Clean up browser resources."""
        with self._lock:
            if not self._initialized:
                return
                
            print(f"Starting browser cleanup in thread {threading.get_ident()}...")
            
            try:
                if self.page:
                    self.page.close()
                if self.context:
                    self.context.close()
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
                print("Browser cleanup completed successfully")
            except Exception as e:
                print(f"Error during cleanup: {e}")
            finally:
                self.page = None
                self.context = None
                self.browser = None
                self.playwright = None
                self._initialized = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()