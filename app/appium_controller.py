import subprocess
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
from PIL import Image

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

class AppiumController:
    """
    Simplified Vision-Based Mobile Automation Controller
    Contains only core Appium interaction methods for coordinate-based automation
    """
    
    def __init__(self, appium_server_url: str = "http://127.0.0.1:4723", platform: str = "android"):
        self.appium_server_url = appium_server_url
        self.platform = platform.lower()
        self.driver: Optional[webdriver.Remote] = None
        self.device_name: Optional[str] = self._get_connected_device()
        
        # Screenshot setup
        self.screenshot_dir = "screenshots"
        self.screenshot_counter = 0
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Screen dimensions
        self.screen_width = 0
        self.screen_height = 0
        
        if not self.device_name:
            raise ConnectionError("No connected Android/iOS devices found.")
        print(f"Controller initialized for {self.platform} device: {self.device_name}")

    def __getattr__(self, name: str):
        """Magic method to proxy attribute access to the underlying driver."""
        if self.driver and hasattr(self.driver, name):
            return getattr(self.driver, name)
        
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'. "
            "Is an app session active?"
        )


    # DEVICE DETECTION & SESSION MANAGEMENT

    def _get_connected_device(self) -> Optional[str]:
        """Get the first connected device."""
        try:
            if self.platform == "android":
                result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
                devices = [line.split('\t')[0] for line in result.stdout.strip().splitlines()[1:] 
                          if line.endswith('\tdevice')]
                return devices[0] if devices else None
            else:  # iOS
                return "iOS Device"
        except Exception:
            return None

    def setup_driver(self):
        """Setup Appium driver for general mobile automation"""
        try:
            if self.platform == "android":
                options = UiAutomator2Options()
                options.platform_name = 'Android'
                options.device_name = self.device_name
                options.automation_name = 'UiAutomator2'
                options.no_reset = True
                options.auto_grant_permissions = True
                options.disable_window_animation = True
                options.auto_launch = False  
                
            else:  # iOS
                options = XCUITestOptions()
                options.platform_name = 'iOS'
                options.device_name = 'iPhone 13'  
                options.automation_name = 'XCUITest'
                options.no_reset = True
                options.bundle_id = 'com.apple.springboard' 
            
            self.driver = webdriver.Remote(self.appium_server_url, options=options)
            self._update_screen_dimensions()
            
            print(f"{self.platform.upper()} driver ready")
            return self.driver
            
        except Exception as e:
            print(f"Failed to setup driver: {e}")
            self.driver = None
            raise

    def _update_screen_dimensions(self):
        """Update screen dimensions from device."""
        if self.driver:
            try:
                window_size = self.driver.get_window_size()
                self.screen_width = window_size['width']
                self.screen_height = window_size['height']
                print(f"Screen dimensions: {self.screen_width}x{self.screen_height}")
            except Exception as e:
                print(f"Could not get screen dimensions: {e}")
                if self.platform == "android":
                    self.screen_width, self.screen_height = 1080, 1920
                else:
                    self.screen_width, self.screen_height = 375, 812


    # SCREENSHOT METHODS  

    def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot for vision analysis."""
        if not self.driver:
            return {"success": False, "error": "No active session"}
        
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.screenshot_counter += 1
                filename = f"screenshot_{timestamp}_{self.screenshot_counter:03d}.png"
            
            screenshot_path = os.path.join(self.screenshot_dir, filename)
            screenshot = self.driver.get_screenshot_as_png()
            
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot)
            
            with Image.open(screenshot_path) as img:
                img_width, img_height = img.size
            
            result = {
                "success": True,
                "screenshot_path": screenshot_path,
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "image_dimensions": {"width": img_width, "height": img_height}
            }
            
            print(f"Screenshot saved: {filename}")
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # COORDINATE-BASED INTERACTION METHODS

    def click_coordinates(self, x: int, y: int) -> Dict[str, Any]:
        """Click at specific coordinates using W3C Actions."""
        if not self.driver:
            return {"success": False, "error": "No active session"}
        
        try:
            if not self._validate_coordinates(x, y):
                return {"success": False, "error": f"Invalid coordinates ({x}, {y})"}
            
            actions = ActionChains(self.driver)
            actions.w3c_actions = ActionBuilder(
                self.driver,
                mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
            )
            
            actions.w3c_actions.pointer_action.move_to_location(x, y)
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.pointer_up()
            actions.perform()

            print(f"Clicked at ({x}, {y})")
            return {
                "success": True,
                "action": "click",
                "coordinates": (x, y),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def double_click_coordinates(self, x: int, y: int) -> Dict[str, Any]:
        """Double click at specific coordinates."""
        if not self.driver:
            return {"success": False, "error": "No active session"}
        
        try:
            if not self._validate_coordinates(x, y):
                return {"success": False, "error": f"Invalid coordinates ({x}, {y})"}
            

            result1 = self.click_coordinates(x, y)
            time.sleep(0.1)  
            result2 = self.click_coordinates(x, y)

            print(f"Double clicked at ({x}, {y})")
            return {
                "success": result1["success"] and result2["success"],
                "action": "double_click",
                "coordinates": (x, y),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def long_press_coordinates(self, x: int, y: int, duration_ms: int = 2000) -> Dict[str, Any]:
        """Long press at coordinates for specified duration."""
        if not self.driver:
            return {"success": False, "error": "No active session"}
        
        try:
            if not self._validate_coordinates(x, y):
                return {"success": False, "error": f"Invalid coordinates ({x}, {y})"}
            
            actions = ActionChains(self.driver)
            actions.w3c_actions = ActionBuilder(
                self.driver,
                mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
            )
            
            actions.w3c_actions.pointer_action.move_to_location(x, y)
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.pause(duration_ms / 1000)
            actions.w3c_actions.pointer_action.pointer_up()
            actions.perform()
            
            print(f"Long pressed at ({x}, {y}) for {duration_ms}ms")
            return {
                "success": True,
                "action": "long_press",
                "coordinates": (x, y),
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def swipe_coordinates(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Swipe from start coordinates to end coordinates."""
        if not self.driver:
            return {"success": False, "error": "No active session"}
        
        try:
            if not (self._validate_coordinates(start_x, start_y) and 
                   self._validate_coordinates(end_x, end_y)):
                return {"success": False, "error": "Invalid coordinates"}
            
            actions = ActionChains(self.driver)
            actions.w3c_actions = ActionBuilder(
                self.driver,
                mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
            )
            
            actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)
            actions.w3c_actions.pointer_action.pointer_up()
            actions.perform()
            
            print(f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            return {
                "success": True,
                "action": "swipe",
                "start_coordinates": (start_x, start_y),
                "end_coordinates": (end_x, end_y),
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def scroll_down(self, distance: int = 400) -> Dict[str, Any]:
        """Scroll down from screen center."""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        start_x, start_y = center_x, center_y
        end_x, end_y = center_x, center_y - distance
        return self.swipe_coordinates(start_x, start_y, end_x, end_y)

    def scroll_up(self, distance: int = 400) -> Dict[str, Any]:
        """Scroll up from screen center."""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        start_x, start_y = center_x, center_y
        end_x, end_y = center_x, center_y + distance
        return self.swipe_coordinates(start_x, start_y, end_x, end_y)

    def scroll_left(self, distance: int = 400) -> Dict[str, Any]:
        """Scroll left from screen center."""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        start_x, start_y = center_x, center_y
        end_x, end_y = center_x + distance, center_y
        return self.swipe_coordinates(start_x, start_y, end_x, end_y)

    def scroll_right(self, distance: int = 400) -> Dict[str, Any]:
        """Scroll right from screen center."""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        start_x, start_y = center_x, center_y
        end_x, end_y = center_x - distance, center_y
        return self.swipe_coordinates(start_x, start_y, end_x, end_y)

    # TEXT INPUT METHODS
 
    def type_text_at_coordinates(self, x: int, y: int, text: str) -> Dict[str, Any]:
        """Click at coordinates and type text."""
        if not self.driver:
            return {"success": False, "error": "No active session"}
        
        try:
            # First click to focus
            click_result = self.click_coordinates(x, y)
            if not click_result["success"]:
                return click_result
            
            time.sleep(0.5) 
            
            if self.platform == "android":
                self.driver.execute_script('mobile: type', {'text': text})
            else:  # iOS
                self.driver.execute_script('mobile: type', {'text': text})
            
            print(f"Typed '{text}' at ({x}, {y})")
            return {
                "success": True,
                "action": "type_text",
                "coordinates": (x, y),
                "text": text
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def clear_text_field(self, x: int, y: int) -> Dict[str, Any]:
        """Click at coordinates and clear text field."""
        if not self.driver:
            return {"success": False, "error": "No active session"}
        
        try:
            click_result = self.click_coordinates(x, y)
            if not click_result["success"]:
                return click_result
            
            time.sleep(0.5)
            
            if self.platform == "android":
                self.driver.execute_script('mobile: key', {'key': 'ctrl+a'})
                time.sleep(0.2)
                self.driver.execute_script('mobile: key', {'key': 'del'})
            else:  # iOS
                self.driver.execute_script('mobile: clearText')
            
            print(f"🗑️ Cleared text field at ({x}, {y})")
            return {"success": True, "action": "clear_text", "coordinates": (x, y)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_enter_key(self) -> Dict[str, Any]:
        """Send Enter/Return key."""
        try:
            if self.platform == "android":
                self.driver.press_keycode(66)  # KEYCODE_ENTER
            else:  # iOS
                self.driver.execute_script('mobile: key', {'key': 'return'})

            print("Pressed Enter key")
            return {"success": True, "action": "enter_key"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


    # SYSTEM NAVIGATION METHODS

    def press_back_button(self) -> Dict[str, Any]:
        """Press the system back button."""
        try:
            if self.platform == "android":
                self.driver.press_keycode(4)  # KEYCODE_BACK
            else:  # iOS - swipe from left edge
                self.swipe_coordinates(10, self.screen_height // 2, 
                                     self.screen_width // 2, self.screen_height // 2, 300)
            
            time.sleep(1)
            print("Pressed back button")
            return {"success": True, "action": "back_button"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def press_home_button(self) -> Dict[str, Any]:
        """Press the system home button."""
        try:
            if self.platform == "android":
                self.driver.press_keycode(3)  # KEYCODE_HOME
            else:  # iOS
                self.driver.execute_script('mobile: pressButton', {'name': 'home'})
            
            time.sleep(1)
            print("Pressed home button")
            return {"success": True, "action": "home_button"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_app_switcher(self) -> Dict[str, Any]:
        """Open the app switcher/recent apps."""
        try:
            if self.platform == "android":
                self.driver.press_keycode(187)  # KEYCODE_APP_SWITCH
            else:  # iOS - double tap home
                self.driver.execute_script('mobile: pressButton', {'name': 'home'})
                time.sleep(0.1)
                self.driver.execute_script('mobile: pressButton', {'name': 'home'})
            
            time.sleep(1)
            print("Opened app switcher")
            return {"success": True, "action": "app_switcher"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        

    def open_app(self, app_package: str) -> Dict[str, Any]:
        """
        Open/launch a specific app by package name (simplified version)
        """
        if not self.driver:
            return {"success": False, "error": "No active session"}
        
        try:
            if self.platform == "android":
                try:
                    self.driver.activate_app(app_package)
                    print(f"Activated existing app: {app_package}")
                    method_used = "activate"
                except:
                    self.driver.execute_script('mobile: startActivity', {
                        'component': app_package
                    })
                    print(f"🚀 Launched new app: {app_package}")
                    method_used = "launch"
            else:  # iOS
                try:
                    self.driver.activate_app(app_package)
                    print(f"Activated iOS app: {app_package}")
                    method_used = "activate"
                except Exception as e:
                    print(f"Could not activate iOS app {app_package}: {e}")
                    return {"success": False, "error": f"Failed to open iOS app: {str(e)}"}
            
            time.sleep(2) 
            self._update_screen_dimensions()  
            
            return {
                "success": True,
                "action": "open_app",
                "app_package": app_package,
                "method": method_used,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Failed to open app {app_package}: {e}")
            return {"success": False, "error": str(e), "app_package": app_package}


    def pull_down_notifications(self) -> Dict[str, Any]:
        """Pull down the notification panel."""
        try:
            start_x = self.screen_width // 2
            start_y = 50
            end_x = start_x
            end_y = self.screen_height // 2
            
            result = self.swipe_coordinates(start_x, start_y, end_x, end_y)
            if result["success"]:
                print("Pulled down notifications")
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rotate_screen_to_landscape(self) -> Dict[str, Any]:
        """Rotate screen to landscape orientation."""
        try:
            self.driver.orientation = "LANDSCAPE"
            time.sleep(2)
            self._update_screen_dimensions()
            
            print("Rotated to landscape")
            return {"success": True, "action": "rotate_landscape"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rotate_screen_to_portrait(self) -> Dict[str, Any]:
        """Rotate screen to portrait orientation."""
        try:
            self.driver.orientation = "PORTRAIT"
            time.sleep(2)
            self._update_screen_dimensions()
            
            print("Rotated to portrait")
            return {"success": True, "action": "rotate_portrait"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


    # UTILITY METHODS

    def wait_seconds(self, seconds: float) -> Dict[str, Any]:
        """Wait for specified number of seconds."""
        try:
            time.sleep(seconds)
            print(f"Waited {seconds} seconds")
            return {"success": True, "action": "wait", "duration": seconds}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate_coordinates(self, x: int, y: int) -> bool:
        """Validate coordinates are within screen bounds."""
        return (0 <= x <= self.screen_width and 0 <= y <= self.screen_height)

    def get_screen_info(self) -> Dict[str, Any]:
        """Get current screen information."""
        if not self.driver:
            return {"active_session": False}
        
        try:
            return {
                "active_session": True,
                "platform": self.platform,
                "device_name": self.device_name,
                "screen_dimensions": {
                    "width": self.screen_width,
                    "height": self.screen_height
                },
                "orientation": getattr(self.driver, 'orientation', 'PORTRAIT'),
                "screenshot_count": self.screenshot_counter
            }
        except Exception as e:
            return {"active_session": True, "error": str(e)}

    # SESSION MANAGEMENT

    def quit_session(self):
        """Quit the current session."""
        if self.driver:
            print(f"Closing {self.platform} session")
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error during cleanup: {e}")
            finally:
                self.driver = None

    def restart_session(self) -> bool:
        """Restart the session."""
        self.quit_session()
        try:
            self.setup_driver()
            return True
        except:
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit_session()
