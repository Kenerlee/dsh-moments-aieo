#!/usr/bin/env python3
"""
Favicon Generator Script
Generate favicon.ico from logo or brand colors.
"""

from PIL import Image, ImageDraw, ImageFont
import sys
import os

def create_favicon_from_logo(logo_path: str, output_path: str = 'favicon.ico'):
    """
    Create favicon from an existing logo image.
    
    Args:
        logo_path: Path to logo image (PNG, JPG, SVG)
        output_path: Output path for favicon.ico
    """
    try:
        img = Image.open(logo_path)
        
        # Convert to RGBA if necessary
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create multiple sizes for ICO
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        images = []
        
        for size in sizes:
            resized = img.copy()
            resized.thumbnail(size, Image.LANCZOS)
            
            # Create square canvas with transparent background
            square = Image.new('RGBA', size, (0, 0, 0, 0))
            
            # Center the resized image
            offset = ((size[0] - resized.width) // 2, 
                      (size[1] - resized.height) // 2)
            square.paste(resized, offset, resized if resized.mode == 'RGBA' else None)
            images.append(square)
        
        # Save as ICO with multiple sizes
        images[0].save(output_path, format='ICO', sizes=[(s, s) for s in [16, 32, 48, 64]])
        print(f"✅ Favicon created: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating favicon from logo: {e}")
        return False


def create_letter_favicon(
    letter: str,
    bg_color: str = '#3B82F6',
    text_color: str = '#FFFFFF',
    output_path: str = 'favicon.ico',
    font_path: str = None,
    shape: str = 'rounded'
):
    """
    Create a simple letter-based favicon.
    
    Args:
        letter: Single letter or short text
        bg_color: Background color (hex)
        text_color: Text color (hex)
        output_path: Output path for favicon.ico
        font_path: Optional custom font path
        shape: 'rounded', 'circle', or 'square'
    """
    
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    bg_rgb = hex_to_rgb(bg_color)
    text_rgb = hex_to_rgb(text_color)
    
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    images = []
    
    for size in sizes:
        # Create image with transparent background
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw background shape
        if shape == 'circle':
            draw.ellipse([0, 0, size[0]-1, size[1]-1], fill=bg_rgb)
        elif shape == 'rounded':
            radius = size[0] // 4
            draw.rounded_rectangle([0, 0, size[0]-1, size[1]-1], 
                                   radius=radius, fill=bg_rgb)
        else:  # square
            draw.rectangle([0, 0, size[0]-1, size[1]-1], fill=bg_rgb)
        
        # Draw letter
        font_size = int(size[0] * 0.6)
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                # Try system fonts
                for font_name in ['Arial Bold', 'Helvetica Bold', 'DejaVuSans-Bold']:
                    try:
                        font = ImageFont.truetype(font_name, font_size)
                        break
                    except:
                        continue
                else:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), letter.upper(), font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2 - bbox[1]
        
        draw.text((x, y), letter.upper(), fill=text_rgb, font=font)
        images.append(img)
    
    # Save as ICO
    images[0].save(output_path, format='ICO', sizes=[(s, s) for s in [16, 32, 48, 64]])
    print(f"✅ Letter favicon created: {output_path}")
    return True


def create_gradient_favicon(
    letter: str,
    color1: str = '#6366F1',
    color2: str = '#8B5CF6',
    text_color: str = '#FFFFFF',
    output_path: str = 'favicon.ico'
):
    """
    Create a favicon with gradient background.
    
    Args:
        letter: Single letter
        color1: Start color (hex)
        color2: End color (hex)
        text_color: Text color (hex)
        output_path: Output path for favicon.ico
    """
    
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)
    text_rgb = hex_to_rgb(text_color)
    
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Create diagonal gradient
        for y in range(size[1]):
            for x in range(size[0]):
                # Calculate gradient position (diagonal)
                t = (x + y) / (size[0] + size[1] - 2)
                r = int(c1[0] + (c2[0] - c1[0]) * t)
                g = int(c1[1] + (c2[1] - c1[1]) * t)
                b = int(c1[2] + (c2[2] - c1[2]) * t)
                img.putpixel((x, y), (r, g, b, 255))
        
        # Apply rounded mask
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        radius = size[0] // 4
        mask_draw.rounded_rectangle([0, 0, size[0]-1, size[1]-1], 
                                    radius=radius, fill=255)
        img.putalpha(mask)
        
        # Draw letter
        font_size = int(size[0] * 0.6)
        try:
            font = ImageFont.truetype('Arial Bold', font_size)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), letter.upper(), font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2 - bbox[1]
        
        draw.text((x, y), letter.upper(), fill=text_rgb, font=font)
        images.append(img)
    
    images[0].save(output_path, format='ICO', sizes=[(s, s) for s in [16, 32, 48, 64]])
    print(f"✅ Gradient favicon created: {output_path}")
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate favicon.ico')
    parser.add_argument('--logo', help='Path to logo image')
    parser.add_argument('--letter', help='Letter for text-based favicon')
    parser.add_argument('--bg-color', default='#3B82F6', help='Background color (hex)')
    parser.add_argument('--text-color', default='#FFFFFF', help='Text color (hex)')
    parser.add_argument('--shape', default='rounded', choices=['rounded', 'circle', 'square'])
    parser.add_argument('--gradient', action='store_true', help='Use gradient background')
    parser.add_argument('--color2', default='#8B5CF6', help='Second gradient color')
    parser.add_argument('--output', default='favicon.ico', help='Output path')
    
    args = parser.parse_args()
    
    if args.logo:
        create_favicon_from_logo(args.logo, args.output)
    elif args.letter:
        if args.gradient:
            create_gradient_favicon(args.letter, args.bg_color, args.color2, 
                                   args.text_color, args.output)
        else:
            create_letter_favicon(args.letter, args.bg_color, args.text_color,
                                 args.output, shape=args.shape)
    else:
        print("Please provide --logo or --letter argument")
        sys.exit(1)
