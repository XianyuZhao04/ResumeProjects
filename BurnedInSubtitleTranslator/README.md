# Full-screen Chinese-To-English Subtitle Translator

A Python application that reads burned-in Chinese subtitles from YouTube videos using screen capture and OCR, then translates them to English in real-time.

## Features

- **Accurate Chinese OCR** - Uses EasyOCR for Chinese text recognition
- **Real-time Translation** - Asynchronous translation keeps the overlay responsive
- **Screen Capture** - Captures subtitles directly from your screen
- **Translation Cache** - Reused translations appear instantly
- **Clean Overlay** - Transparent, draggable window that doesn't obstruct your video
- **GPU Acceleration** - Optional GPU support for 3-5x faster OCR (NVIDIA GPUs)
- **Automatic Detection** - Continuously monitors for new subtitles

## How It Works

1. **Screen Capture** - Captures a specified region of your screen where subtitles appear
2. **OCR Processing** - Uses EasyOCR to extract Chinese text from the captured region
3. **Translation** - Sends Chinese text to Google Translate API for English translation
4. **Display** - Shows translated text in a transparent overlay window

## Prerequisites

- **Python 3.8+** installed
- **pip** package manager
- **NVIDIA GPU with CUDA** (optional, for GPU acceleration)

## 🔧 Installation

### Step 1: Install Python

Verify installation is 3.8 or higher

### Step 2: Download/Clone Repository

### Step 3: Install Dependencies

Open terminal in the `YouTubeSubtitleTranslator` folder and run:

```bash
pip install -r requirements.txt
```

**Note:** First run will download EasyOCR models (~100MB) - this is one-time only!

### Step 4: Configure Capture Region

Edit `subtitle_translator.py` and adjust these values (around line 48-52):

```python
self.capture_x = 460      # Left edge - adjust based on your screen
self.capture_y = 850      # Top edge - adjust based on your screen  
self.capture_width = 1000  # Width of subtitle area
self.capture_height = 200  # Height of subtitle area
```

**How to find the right coordinates:**
1. Open video with subtitles
2. Use Windows Snipping Tool or any screenshot tool
3. Note the X,Y position and size of the subtitle area
4. Update the values in the script

## ⚡ Performance Optimizations

### Asynchronous Translation
- Translation runs in background thread pool
- Can capture next frame while translating current one
- No blocking of the capture loop

### Faster Loop Speed
- Checks every 150ms for maximum responsiveness (line 320)

### Smart Translation Cancellation
- Cancels old translations when new subtitle appears
- Only keeps the latest translation request

### Better Cache Management
- Cache size of 200 entries
- Automatic cleanup when full
- Instant translation for cached entries

## 🎮 GPU Acceleration (Optional)

If you have an NVIDIA GPU with CUDA support, you can enable GPU acceleration for faster OCR:

1. **Install CUDA Toolkit**
   - Download from [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
   - Follow installation instructions

2. **Install PyTorch with CUDA support**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Enable GPU in code** (already enabled by default)
   - GPU is enabled by default in `subtitle_translator.py` (line 27)
   - If GPU is not available, it will automatically fall back to CPU

## 🐛 Other Notes:

### EasyOCR Models Downloading Slowly
- First run downloads ~100MB of models
- This is normal and only happens once
- Future runs will be instant

### Not Detecting Subtitles
- Check that capture region coordinates match where subtitles appear
- Make sure subtitles are visible and clear
- Increase `capture_width` and `capture_height` if subtitles are larger
- Verify subtitle area is not obscured by other windows

### Translation is Slow
- Normal first translation may take 1-2 seconds
- Subsequent translations use cache (instant)
- Network latency affects translation speed

### GPU Not Working
- Verify CUDA is installed
- Check PyTorch CUDA support
- Script will automatically fall back to CPU if GPU unavailable

### Overlay Window Not Appearing
- Check that no other window is covering it
- Try dragging the overlay if it's off-screen
- Restart the application

## 🔍 Dependencies

- **easyocr** - Text OCR engine
- **opencv-python** - Image processing
- **pyautogui** - Screen capture
- **Pillow** - Image handling
- **requests** - HTTP requests for translation API
- **numpy** - Numerical operations

## 💡 Tips

- **Position the overlay**: The overlay window is draggable - position it where subtitles appear
- **Adjust capture region**: Fine-tune the capture coordinates for your screen setup
- **GPU acceleration**: Enable GPU if available for much faster OCR
- **Network connection**: Stable internet required for translation API

**Made with AI and ❤️ for watching Chinese content on YouTube lol**
