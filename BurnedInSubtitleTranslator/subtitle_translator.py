"""
Subtitle Translator with EasyOCR
Reads burned-in Chinese subtitles from YouTube videos using screen capture + OCR
"""

import easyocr
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
import pyautogui
import requests
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

class SubtitleTranslator:
    def __init__(self):
        print("🔧 Initializing EasyOCR (first run downloads models - one time only)...")
        # Initialize EasyOCR with Chinese and English support
        # First run will download models (~100MB)
        # Optimized settings for speed
        self.reader = easyocr.Reader(
            ['ch_sim', 'en'], 
            gpu=True,  # GPU enabled! (3-5x faster OCR)
            verbose=False,  # Less output = faster
            quantize=True  # Faster inference
        )
        print("✅ EasyOCR initialized!")
        
        # Translation cache
        self.translation_cache = {}
        self.last_subtitle_text = ""
        self.last_displayed_text = ""  # Keep track of what we're showing
        self.pending_translations = {}  # Track in-progress translations
        
        # Keep subtitle visible timing
        self.last_subtitle_time = 0  # When we last detected a subtitle
        self.subtitle_timeout = 2.5  # Keep subtitle visible for 2.5 seconds after it disappears
        self.initial_state = True  # Track if we've shown any subtitle yet
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.translation_queue = Queue()
        
        # Screen capture settings - ADJUST THESE FOR YOUR SCREEN
        self.capture_x = 460      # Left edge of subtitle area
        self.capture_y = 850      # Top edge of subtitle area
        self.capture_width = 1000  # Width of subtitle area
        self.capture_height = 200  # Height of subtitle area
        
        # Create overlay window (very small, less intrusive)
        self.root = tk.Tk()
        self.root.title("Subtitle Translator")
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.8)  # More transparent
        self.root.configure(bg='black')
        self.root.geometry('700x50+610+895')  # Much smaller window, positioned below video
        
        # Make window draggable
        self.root.overrideredirect(True)
        
        # Create frame for label and close button
        frame = tk.Frame(self.root, bg='black')
        frame.pack(fill='both', expand=True, padx=6, pady=3)
        
        self.label = tk.Label(
            frame,
            text="Waiting for subtitles...",
            font=('Arial', 11, 'bold'),  # Much smaller font
            fg='white',
            bg='black',
            wraplength=650,  # Adjusted for smaller window
            justify='center'
        )
        self.label.pack(side='left', fill='both', expand=True)
        
        # Add close button (X)
        close_btn = tk.Button(
            frame,
            text='×',
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#333333',
            activebackground='#ff4444',
            activeforeground='white',
            borderwidth=0,
            width=3,
            height=1,
            command=self.stop
        )
        close_btn.pack(side='right', padx=(5, 0))
        
        # Store reference to label for direct updates
        self.current_display_text = "Waiting for subtitles..."
        
        # Make window draggable (but not when clicking close button)
        self.frame = frame
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.on_drag)
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self.is_running = False
        self.translation_thread = None
        
    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        self.root.geometry(f'+{x}+{y}')
        
    def capture_screen(self):
        """Capture the subtitle region from screen"""
        try:
            screenshot = pyautogui.screenshot(region=(
                self.capture_x,
                self.capture_y,
                self.capture_width,
                self.capture_height
            ))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Capture error: {e}")
            return None
    
    def extract_chinese_text(self, image):
        """Extract Chinese text using EasyOCR (optimized for speed)"""
        if image is None:
            return ""
        
        try:
            # Optimize image for faster OCR - aggressive optimization
            # Resize if too large (smaller = faster OCR)
            h, w = image.shape[:2]
            # More aggressive resizing for speed - max width 1000px
            if w > 1000:
                scale = 1000 / w
                new_w = int(w * scale)
                new_h = int(h * scale)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            # Also downscale if height is too large
            elif h > 150:
                scale = 150 / h
                new_w = int(w * scale)
                new_h = int(h * scale)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # EasyOCR with optimized parameters for MAXIMUM speed
            results = self.reader.readtext(
                image,
                paragraph=False,  # Faster processing
                detail=1,  # We need confidence scores
                width_ths=0.7,  # Faster text detection
                height_ths=0.7,  # Faster text detection
                batch_size=1  # Process immediately
            )
            
            # Filter for Chinese text and combine
            chinese_lines = []
            for (bbox, text, confidence) in results:
                # Check if text contains Chinese characters
                if any('\u4e00' <= char <= '\u9fff' for char in text):
                    if confidence > 0.35:  # Lower threshold for speed (was 0.4)
                        chinese_lines.append(text)
            
            return " ".join(chinese_lines).strip()
            
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    def translate_text_sync(self, chinese_text):
        """Translate Chinese text to English (synchronous)"""
        if not chinese_text:
            return ""
        
        # Check cache first
        if chinese_text in self.translation_cache:
            return self.translation_cache[chinese_text]
        
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'zh-CN',
                'tl': 'en',
                'dt': 't',
                'q': chinese_text
            }
            
            response = requests.get(url, params=params, timeout=1.5)  # Faster timeout
            if response.ok:
                data = response.json()
                if data and data[0]:
                    translated = "".join([item[0] for item in data[0] if item[0]])
                    self.translation_cache[chinese_text] = translated
                    # Limit cache size
                    if len(self.translation_cache) > 200:
                        # Remove oldest entry
                        first_key = next(iter(self.translation_cache))
                        del self.translation_cache[first_key]
                    return translated
        except Exception as e:
            print(f"Translation error: {e}")
        
        return ""
    
    def translate_text_async(self, chinese_text, callback):
        """Translate Chinese text asynchronously"""
        if not chinese_text:
            callback("")
            return
        
        # Check cache first (instant)
        if chinese_text in self.translation_cache:
            callback(self.translation_cache[chinese_text])
            return
        
        # Cancel previous translation for this text if still pending
        if chinese_text in self.pending_translations:
            future = self.pending_translations[chinese_text]
            if not future.done():
                future.cancel()
        
        # Start new translation in thread pool
        future = self.executor.submit(self.translate_text_sync, chinese_text)
        self.pending_translations[chinese_text] = future
        
        # Call callback when done
        def on_complete(f):
            try:
                result = f.result()
                if result:
                    callback(result)
            except Exception as e:
                print(f"Async translation error: {e}")
            finally:
                # Clean up
                if chinese_text in self.pending_translations:
                    del self.pending_translations[chinese_text]
        
        future.add_done_callback(on_complete)
    
    def update_overlay(self, text, is_clearing=False):
        """Update the overlay window with translated text"""
        def update_gui():
            if text:
                # New translation - show it immediately
                self.current_display_text = text
                self.last_displayed_text = text
                self.last_subtitle_time = time.time()
                self.initial_state = False
                self.label.config(text=text)
            elif is_clearing:
                # Clearing - only show "Waiting..." if initial state
                if self.initial_state:
                    self.current_display_text = "Waiting for subtitles..."
                    self.label.config(text="Waiting for subtitles...")
                else:
                    # Don't clear - keep last translation visible
                    # (This shouldn't be called often due to timeout check)
                    pass
            # If text is empty and not clearing, do nothing (keep current display)
        
        self.root.after(0, update_gui)
    
    def translation_loop(self):
        """Main translation loop running in separate thread (optimized for speed)"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # Capture screen (fast)
                screenshot = self.capture_screen()
                
                if screenshot is not None:
                    # Extract Chinese text (this is the slow part, but necessary)
                    chinese_text = self.extract_chinese_text(screenshot)
                    
                    if chinese_text and chinese_text != self.last_subtitle_text:
                        print(f"📝 Detected: {chinese_text}")
                        
                        # Translate ASYNCHRONOUSLY (don't block the loop!)
                        # This allows us to capture the next frame while translating
                        def on_translation_complete(english_text):
                            if english_text:
                                print(f"🌐 Translated: {english_text}")
                                self.update_overlay(english_text)
                                self.last_subtitle_time = time.time()  # Update timestamp
                            else:
                                # Don't clear on translation failure - keep last one
                                pass
                        
                        # Update last text immediately to prevent duplicates
                        self.last_subtitle_text = chinese_text
                        
                        # Start async translation (non-blocking!)
                        self.translate_text_async(chinese_text, on_translation_complete)
                        
                    elif not chinese_text:
                        # No subtitle detected - check if we should clear
                        if self.last_subtitle_text:
                            # Check if enough time has passed since last subtitle
                            time_since_last = current_time - self.last_subtitle_time
                            
                            if time_since_last >= self.subtitle_timeout:
                                # Only clear after timeout
                                self.update_overlay("", is_clearing=True)
                                self.last_subtitle_text = ""
                                self.last_displayed_text = ""
                            # Otherwise, keep showing last translation
                
                # Much faster loop - check every 150ms for maximum responsiveness
                time.sleep(0.15)
                
            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(0.3)
    
    def start(self):
        """Start the translation service"""
        print("\n🚀 Starting subtitle translator...")
        print(f"📍 Capture region: ({self.capture_x}, {self.capture_y}) {self.capture_width}x{self.capture_height}")
        print("💡 Drag the overlay window to position it where you want")
        print("⚠️  Make sure your video is playing with Chinese subtitles visible\n")
        
        self.is_running = True
        self.translation_thread = threading.Thread(target=self.translation_loop, daemon=True)
        self.translation_thread.start()
        
        # Run GUI
        self.root.mainloop()
    
    def stop(self):
        """Stop the translation service"""
        self.is_running = False
        self.executor.shutdown(wait=False)  # Don't wait - just stop
        self.root.quit()

if __name__ == "__main__":
    translator = SubtitleTranslator()
    
    try:
        translator.start()
    except KeyboardInterrupt:
        print("\n👋 Stopping translator...")
        translator.stop()

