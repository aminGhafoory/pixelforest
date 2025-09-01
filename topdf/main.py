from PIL import Image, ImageDraw
import os

# ==== CONFIGURATION ====
input_folder = "images"       # folder with your 600x600 images
output_pdf = "print_sheets.pdf"
dpi = 300                     # print quality
img_size_cm = 5               # image size on paper (5 cm x 5 cm)
padding_cm = 0.0              # gap between images (0.2 cm = 2 mm)
margin_cm = 0.5               # margin around the whole page (1 cm)
line_color = 0                # black cut lines (0=black, 255=white)
line_width_px = 2             # thickness of the grid lines in pixels

# ==== CALCULATIONS ====
cm_to_inch = 1 / 2.54
img_size_px = int(img_size_cm * dpi * cm_to_inch)
padding_px = int(padding_cm * dpi * cm_to_inch)
margin_px = int(margin_cm * dpi * cm_to_inch)
cell_size_px = img_size_px + padding_px  # image + gap

# A4 size in pixels
a4_width_cm, a4_height_cm = 21.0, 29.7
a4_width_px = int(a4_width_cm * dpi * cm_to_inch)
a4_height_px = int(a4_height_cm * dpi * cm_to_inch)

# usable drawing area after margins
usable_width_px = a4_width_px - 2 * margin_px
usable_height_px = a4_height_px - 2 * margin_px

# grid layout
cols = usable_width_px // cell_size_px
rows = usable_height_px // cell_size_px
per_page = cols * rows
print(
    f"A4 with {margin_cm} cm margin can fit {cols} x {rows} = {per_page} images per sheet.")

# ==== LOAD IMAGES ====
files = [f for f in os.listdir(input_folder) if f.lower().endswith(
    (".png", ".jpg", ".jpeg", ".bmp", ".tif"))]
files.sort()

images = []
for file in files:
    img = Image.open(os.path.join(input_folder, file)
                     ).convert("L")  # grayscale
    img = img.resize((img_size_px, img_size_px), Image.LANCZOS)
    images.append(img)

# ==== MAKE PAGES ====
pages = []
for i in range(0, len(images), per_page):
    sheet = Image.new("L", (a4_width_px, a4_height_px),
                      255)  # white background
    draw = ImageDraw.Draw(sheet)
    batch = images[i:i + per_page]

    for idx, img in enumerate(batch):
        r = idx // cols
        c = idx % cols
        x = margin_px + c * cell_size_px
        y = margin_px + r * cell_size_px
        sheet.paste(img, (x, y))

        # Draw black rectangle around each image
        draw.rectangle(
            [x, y, x + img_size_px, y + img_size_px],
            outline=line_color,
            width=line_width_px
        )

    pages.append(sheet)

# ==== SAVE TO PDF ====
if pages:
    pages[0].save(output_pdf, save_all=True,
                  append_images=pages[1:], resolution=dpi)
    print(f"✅ Saved {len(pages)} page(s) to {output_pdf}")
else:
    print("⚠️ No images found in folder:", input_folder)
