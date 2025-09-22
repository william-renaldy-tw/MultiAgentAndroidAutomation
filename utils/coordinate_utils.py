
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


def create_grid_overlay(screenshot_path: str, grid_size: int = 75) -> Dict[str, Any]:
    """Create screenshot with numbered grid overlay"""
    try:
        
        with Image.open(screenshot_path) as img:
            img_width, img_height = img.size
            

            overlay = img.copy()
            draw = ImageDraw.Draw(overlay)
            
            try:
                font = ImageFont.truetype("arial.ttf", 32)
            except:
                font = ImageFont.load_default(size=32)

            cols = img_width // grid_size
            rows = img_height // grid_size
            
            grid_map = {}
            cell_number = 1
            
            for i in range(cols + 1):
                x = i * grid_size
                draw.line([(x, 0), (x, img_height)], fill="red", width=2)
            
            for i in range(rows + 1):
                y = i * grid_size
                draw.line([(0, y), (img_width, y)], fill="red", width=2)
            
            for row in range(rows):
                for col in range(cols):
                    x = col * grid_size
                    y = row * grid_size
                    
                    center_x = x + grid_size // 2
                    center_y = y + grid_size // 2
                    
                    draw.text((x + 5, y + 5), str(cell_number), fill="blue", font=font)
                    
                    grid_map[cell_number] = {
                        "cell": cell_number,
                        "bounds": {
                            "x": x,
                            "y": y, 
                            "width": grid_size,
                            "height": grid_size
                        },
                        "center": [center_x, center_y]
                    }
                    
                    cell_number += 1
            
            grid_path = screenshot_path.replace(".png", "_grid.png")

            output_dir = "screenshot_grids"
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.basename(grid_path)
            output_path = os.path.join(output_dir, filename)
            overlay.save(output_path)
            
            return {
                "success": True,
                "grid_image_path": output_path,
                "original_image_path": screenshot_path,
                "grid_size": grid_size,
                "dimensions": {
                    "width": img_width,
                    "height": img_height,
                    "cols": cols,
                    "rows": rows,
                    "total_cells": len(grid_map)
                },
                "grid_map": grid_map
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def sanitize_grid_coordinates(text: str) -> Optional[List[int]]:
    """
    Extracts the list of cell_numbers from a ```json block``` in the text.
    Returns a list of integers, or None if not found.
    """
    pattern = r'```json\s*(\{[^`]*\})\s*```'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        json_text = match.group(1)
        json_text = re.sub(r'(\w+)\s*:', r'"\1":', json_text)

        try:
            data = json.loads(json_text)
            values = data.get("cell_numbers")
            if isinstance(values, list) and all(isinstance(v, int) for v in values):
                return values
        except json.JSONDecodeError:
            return None
    return None


def grid_to_coordinates(grid_data: Dict, cell_numbers: List[int]) -> Tuple[int, int]:
    """
    Convert a list of grid cell numbers to the average center coordinates.
    Returns a tuple (avg_x, avg_y).
    """
    centers = []
    grid_map = grid_data["grid_map"]
    
    for cell_num in cell_numbers:
        if cell_num in grid_map:
            centers.append(grid_map[cell_num]["center"])
        else:
            print(f"Invalid cell number: {cell_num}")
    
    if not centers:
        return (0, 0)
    
    avg_x = sum(c[0] for c in centers) // len(centers)
    avg_y = sum(c[1] for c in centers) // len(centers)
    
    return (avg_x, avg_y)


def replace_json_with_coordinates(llm_output: str, coordinates: Tuple[int, int], cell_numbers: List[int]) -> str:
    """
    Replaces the ```json {cell_numbers: ...}``` block in llm_output
    with the provided coordinates tuple and the original list of cell_numbers.
    """
    pattern = r'```json\s*\{[^`]*\}\s*```'
    replacement = f"```json\n{{\"cell_numbers\": {cell_numbers}, \"coordinates\": {coordinates}}}\n```"
    replaced_text = re.sub(pattern, replacement, llm_output, count=1, flags=re.DOTALL)
    return replaced_text


def annotate_coordinates_from_llm(llm_output: str, screen_image: str) -> Optional[dict]:
    """
    Extracts coordinates from the LLM output JSON block, draws a rectangle and circle
    on the image at that location, and saves the annotated screenshot.
    
    Returns a dictionary with:
        - bbox: bounding box dict
        - center: (x, y) tuple
    Returns None if coordinates not found.
    """
    pattern = r'```json\s*(\{[^`]*\})\s*```'
    match = re.search(pattern, llm_output, re.DOTALL)
    if not match:
        return None
    
    json_text = match.group(1)
    json_text = re.sub(r'(\w+)\s*:', r'"\1":', json_text)
    json_text = json_text.replace("(", "[").replace(")", "]")

    try:
        data = json.loads(json_text)
        coords = data.get("coordinates")
        if not (isinstance(coords, list) and len(coords) == 2):
            return None
        center_x, center_y = int(coords[0]), int(coords[1])
    except json.JSONDecodeError:
        return None

    try:
        with Image.open(screen_image) as pil_img:
            draw = ImageDraw.Draw(pil_img)
            box_size = 20
            x1 = center_x - box_size // 2
            y1 = center_y - box_size // 2
            x2 = center_x + box_size // 2
            y2 = center_y + box_size // 2
            bbox = {"x": x1, "y": y1, "width": box_size, "height": box_size}
            
            draw.rectangle([x1, y1, x2, y2], outline="cyan", width=3)
            r = 5
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill="blue")
            
            output_dir = "screenshot_coordinates"
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.basename(screen_image)
            output_path = os.path.join(output_dir, filename)
            pil_img.save(output_path)
            
    except Exception as e:
        print(f"Error annotating image: {e}")
        return None

    return {
        "bbox": bbox,
        "center": (center_x, center_y)
    }


if __name__ == "__main__":
    x = """
    The user's task is to take a photo. Based on the provided screenshot of a camera application, the most relevant element is the large, white, circular \"Shutter button\" located at the bottom center of the screen. This button is used to capture a photo.\n\nI have identified the grid cells that contain this shutter button. The button occupies a significant area and spans multiple cells. To ensure a successful click, I will include all the cells that cover the button's tappable area.\n\nThe shutter button covers the following grid cells:\n- Top part: 787, 788, 789\n- Middle parts: 808, 809, 810, 811, 829, 830, 831, 832\n- Bottom part: 850, 851, 852\n\nTherefore, I will output the list of all these cell numbers.\n\n```json\n{\"cell_numbers\": [787, 788, 789, 808, 809, 810, 811, 829, 830, 831, 832, 850, 851, 852], \"coordinates\": (539, 1950)}\n```

"""
    print(annotate_coordinates_from_llm(x,"screenshots/screenshot_20250921_210014_002.png"))