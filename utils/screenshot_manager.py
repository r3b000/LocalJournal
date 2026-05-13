"""
Screenshot Manager - FIXED VERSION
Handles multiple screenshot uploads without session state conflicts
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import streamlit as st
from PIL import Image
import logging
import io

logger = logging.getLogger(__name__)

# Screenshot categories
SCREENSHOT_CATEGORIES = [
    "Chart",
    "P&L",
    "Indicators",
    "Entry Setup",
    "Exit Reason",
    "Other"
]


class ScreenshotUploader:
    """
    Manages multiple screenshot uploads with preview
    FIXED: No more stuck uploads!
    """
    
    def __init__(
        self,
        key_prefix: str,
        trade_type: str = "ENTRY",
        max_screenshots: int = 10,
        show_preview: bool = True
    ):
        """
        Initialize screenshot uploader
        
        Args:
            key_prefix: Unique prefix for widget keys (e.g., "entry_open", "exit_close")
            trade_type: "ENTRY" or "EXIT"
            max_screenshots: Maximum number of screenshots allowed
            show_preview: Whether to show image previews
        """
        self.key_prefix = key_prefix
        self.trade_type = trade_type
        self.max_screenshots = max_screenshots
        self.show_preview = show_preview
        
        # Session state key for storing uploads
        self.session_key = f"screenshots_{key_prefix}"
        
        # Initialize session state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = []
    
    def render(self) -> List[Dict]:
        """
        Render the screenshot uploader UI
        
        Returns:
            List of screenshot dictionaries with 'file' and 'category' keys
        """
        st.markdown(f"### {self.trade_type.title()} Screenshots (Optional)")
        st.caption(f"Upload up to {self.max_screenshots} screenshots")
        
        # Get current screenshots
        current_screenshots = st.session_state[self.session_key]
        
        # Show current count
        if len(current_screenshots) > 0:
            st.info(f"𝄜 **{len(current_screenshots)} screenshot(s) ready to upload**")
        
        # File uploader
        if len(current_screenshots) < self.max_screenshots:
            
            # Use a unique key that includes current count to force refresh
            uploader_key = f"{self.key_prefix}_uploader_{len(current_screenshots)}"
            
            uploaded_file = st.file_uploader(
                "Choose screenshot",
                type=['png', 'jpg', 'jpeg'],
                accept_multiple_files=False,  # ONE AT A TIME TO AVOID CONFLICTS
                key=uploader_key,
                help="Upload one screenshot at a time"
            )
            
            if uploaded_file is not None:
                # Check if not already added (by name)
                if not any(ss['file_name'] == uploaded_file.name for ss in current_screenshots):
                    
                    # Read file data immediately
                    file_bytes = uploaded_file.read()
                    
                    # Add to list with file bytes (not file object)
                    current_screenshots.append({
                        'file_name': uploaded_file.name,
                        'file_bytes': file_bytes,
                        'file_type': uploaded_file.type,
                        'category': 'Chart'  # Default category
                    })
                    
                    st.session_state[self.session_key] = current_screenshots
                    
                    logger.info(f"Screenshot added: {uploaded_file.name}")
                    
                    # Force rerun to clear uploader
                    st.rerun()
        else:
            st.warning(f"⚠ Maximum {self.max_screenshots} screenshots reached")
        
        # Display current screenshots
        if len(current_screenshots) > 0:
            st.markdown("---")
            st.markdown("#### 📋 Uploaded Screenshots")
            
            for idx, screenshot in enumerate(current_screenshots):
                self._render_screenshot_item(idx, screenshot)
            
            st.markdown("---")
        
        return current_screenshots
    
    def _render_screenshot_item(self, idx: int, screenshot: Dict):
        """Render a single screenshot item with preview and controls"""
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        
        with col1:
            # Show filename
            st.markdown(f"**{idx + 1}. {screenshot['file_name']}**")
            
            # Show preview if enabled
            if self.show_preview:
                try:
                    # Load image from bytes
                    img = Image.open(io.BytesIO(screenshot['file_bytes']))
                    
                    # Show thumbnail
                    st.image(img, width=150)
                except Exception as e:
                    st.warning(f"⚠ Preview unavailable")
        
        with col2:
            # Category selector
            category = st.selectbox(
                "Category",
                options=SCREENSHOT_CATEGORIES,
                index=SCREENSHOT_CATEGORIES.index(screenshot.get('category', 'Chart')),
                key=f"{self.key_prefix}_cat_{idx}"
            )
            
            # Update category in session state
            current_screenshots = st.session_state[self.session_key]
            current_screenshots[idx]['category'] = category
            st.session_state[self.session_key] = current_screenshots
        
        with col3:
            # File size
            try:
                size_kb = len(screenshot['file_bytes']) / 1024
                st.caption(f"**Size:**\n{size_kb:.1f} KB")
            except:
                st.caption("Size: N/A")
        
        with col4:
            # Delete button
            if st.button("🗑️", key=f"{self.key_prefix}_del_{idx}", help="Remove screenshot"):
                current_screenshots = st.session_state[self.session_key]
                current_screenshots.pop(idx)
                st.session_state[self.session_key] = current_screenshots
                logger.info(f"Screenshot deleted: {screenshot['file_name']}")
                st.rerun()
    
    def clear(self):
        """Clear all screenshots"""
        st.session_state[self.session_key] = []
        logger.info(f"All screenshots cleared for {self.key_prefix}")
    
    def get_screenshots(self) -> List[Dict]:
        """Get current screenshots"""
        return st.session_state.get(self.session_key, [])


def save_screenshots(
    trade_id: int,
    screenshots: List[Dict],
    trade_type: str,
    screenshot_dir: Path,
    db_add_function
) -> Tuple[int, int]:
    """
    Save multiple screenshots to disk and database
    
    Args:
        trade_id: Trade ID
        screenshots: List of screenshot dicts with 'file_name', 'file_bytes', 'category'
        trade_type: 'ENTRY' or 'EXIT'
        screenshot_dir: Directory to save screenshots
        db_add_function: Function to add screenshot to database
        
    Returns:
        Tuple of (successful_uploads, failed_uploads)
    """
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    successful = 0
    failed = 0
    
    for idx, screenshot in enumerate(screenshots):
        try:
            file_name = screenshot['file_name']
            file_bytes = screenshot['file_bytes']
            category = screenshot.get('category', 'Other')
            
            # Generate filename with category
            file_extension = Path(file_name).suffix
            clean_category = category.lower().replace(' ', '_')
            filename = f"{trade_type.lower()}_{idx + 1}_{clean_category}{file_extension}"
            
            file_path = screenshot_dir / filename
            
            # Save image from bytes
            img = Image.open(io.BytesIO(file_bytes))
            img.save(file_path)
            
            # Add to database
            db_add_function(
                trade_id=trade_id,
                screenshot_type=trade_type,
                file_path=str(file_path),
                category=category
            )
            
            successful += 1
            
            logger.info(f"Screenshot saved: {filename} (Category: {category})")
            
        except Exception as e:
            logger.error(f"Failed to save screenshot {idx + 1}: {e}")
            failed += 1
    
    return successful, failed


def display_screenshot_gallery(screenshots: List[Dict], columns: int = 3):
    """
    Display screenshots in a gallery view
    
    Args:
        screenshots: List of screenshot dicts with 'file_path', 'screenshot_category', 'screenshot_type'
        columns: Number of columns in gallery
    """
    if not screenshots:
        st.info("📷 No screenshots available")
        return
    
    st.markdown("### 📸 Screenshot Gallery")
    
    # Group by type
    entry_screenshots = [ss for ss in screenshots if ss.get('screenshot_type') == 'ENTRY']
    exit_screenshots = [ss for ss in screenshots if ss.get('screenshot_type') == 'EXIT']
    
    if entry_screenshots:
        st.markdown("#### 📥 Entry Screenshots")
        _render_gallery_grid(entry_screenshots, columns)
    
    if exit_screenshots:
        st.markdown("#### 📤 Exit Screenshots")
        _render_gallery_grid(exit_screenshots, columns)


def _render_gallery_grid(screenshots: List[Dict], columns: int):
    """Render screenshots in a grid"""
    for i in range(0, len(screenshots), columns):
        cols = st.columns(columns)
        
        for j, col in enumerate(cols):
            if i + j < len(screenshots):
                screenshot = screenshots[i + j]
                
                with col:
                    try:
                        # Load and display image
                        img_path = Path(screenshot['file_path'])
                        
                        if img_path.exists():
                            img = Image.open(img_path)
                            st.image(img, use_column_width=True)
                            
                            # Show category
                            category = screenshot.get('screenshot_category', 'N/A')
                            st.caption(f"**{category}**")
                        else:
                            st.warning("⚠ Image not found")
                    
                    except Exception as e:
                        st.error(f"❌ Error loading image: {e}")
