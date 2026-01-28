#!/usr/bin/env python3
"""
Combine images into a PDF with 16 images per A4 page (4x4 grid).
Images are separated by 5mm white spacing.
"""

import os
from fpdf import FPDF
from PIL import Image

# Configuration
PDF_NAME = "Album_16_per_page.pdf"
EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')

# Layout configuration
MARGIN = 5  # mm - margin on all sides
GAP = 5     # mm - gap between images
COLS = 4
ROWS = 4
IMAGES_PER_PAGE = COLS * ROWS

# A4 dimensions in mm
PAGE_WIDTH = 210
PAGE_HEIGHT = 297


def calculate_cell_dimensions():
    """Calculate the dimensions of each cell in the grid."""
    # Available space after margins
    available_width = PAGE_WIDTH - 2 * MARGIN
    available_height = PAGE_HEIGHT - 2 * MARGIN

    # Cell dimensions (accounting for gaps between cells)
    cell_width = (available_width - (COLS - 1) * GAP) / COLS
    cell_height = (available_height - (ROWS - 1) * GAP) / ROWS

    return cell_width, cell_height


def get_cell_position(index):
    """Get the top-left position of a cell given its index (0-15)."""
    cell_width, cell_height = calculate_cell_dimensions()

    col = index % COLS
    row = index // COLS

    x = MARGIN + col * (cell_width + GAP)
    y = MARGIN + row * (cell_height + GAP)

    return x, y, cell_width, cell_height


def fit_image_in_cell(img_width_px, img_height_px, cell_width, cell_height):
    """
    Calculate image dimensions to fit within cell while maintaining aspect ratio.
    Returns (display_width, display_height, x_offset, y_offset) for centering.
    """
    aspect_ratio = img_width_px / img_height_px
    cell_ratio = cell_width / cell_height

    if aspect_ratio > cell_ratio:
        # Image is wider than cell - fit by width
        disp_width = cell_width
        disp_height = cell_width / aspect_ratio
    else:
        # Image is taller than cell - fit by height
        disp_height = cell_height
        disp_width = cell_height * aspect_ratio

    # Calculate offsets to center the image in the cell
    x_offset = (cell_width - disp_width) / 2
    y_offset = (cell_height - disp_height) / 2

    return disp_width, disp_height, x_offset, y_offset


def make_pdf(input_dir='.', output_name=None):
    """Create PDF with 16 images per page from images in input_dir."""
    if output_name is None:
        output_name = PDF_NAME

    # Create A4 PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(False)

    # Get image files from directory
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(EXTENSIONS)]
    files.sort()  # Alphabetical order

    if not files:
        print("Aucune image trouvée dans ce dossier !")
        return None

    print(f"Traitement de {len(files)} images...")
    print(f"Configuration: {COLS}x{ROWS} = {IMAGES_PER_PAGE} images par page")

    cell_width, cell_height = calculate_cell_dimensions()
    print(f"Taille de chaque cellule: {cell_width:.1f}mm x {cell_height:.1f}mm")

    image_index = 0
    page_count = 0

    while image_index < len(files):
        # Add new page
        pdf.add_page()
        page_count += 1

        # White background (default)
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, 'F')

        # Place up to 16 images on this page
        for cell_index in range(IMAGES_PER_PAGE):
            if image_index >= len(files):
                break

            img_file = files[image_index]
            img_path = os.path.join(input_dir, img_file)

            try:
                # Open image to get dimensions
                with Image.open(img_path) as img:
                    img_width_px, img_height_px = img.size

                # Get cell position
                cell_x, cell_y, cell_w, cell_h = get_cell_position(cell_index)

                # Calculate image display size and centering
                disp_w, disp_h, x_off, y_off = fit_image_in_cell(
                    img_width_px, img_height_px, cell_w, cell_h
                )

                # Place image centered in cell
                pdf.image(img_path,
                         x=cell_x + x_off,
                         y=cell_y + y_off,
                         w=disp_w,
                         h=disp_h)

                print(f"  Page {page_count}, cellule {cell_index + 1}: {img_file}")

            except Exception as e:
                print(f"  Erreur sur {img_file}: {e}")

            image_index += 1

    # Save PDF
    try:
        output_path = os.path.join(input_dir, output_name)
        pdf.output(output_path)
        print(f"\nSUCCÈS ! Fichier créé : {output_path}")
        print(f"  - {len(files)} images sur {page_count} page(s)")
        return output_path
    except PermissionError:
        print(f"\nERREUR : Veuillez fermer le fichier {output_name} s'il est déjà ouvert.")
        return None


if __name__ == "__main__":
    import sys

    # Optional: pass directory as command line argument
    input_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    make_pdf(input_dir)
