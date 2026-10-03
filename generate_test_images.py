import os
from PIL import Image, ImageDraw, ImageFont

def create_sample_images():
    os.makedirs("sample_images", exist_ok=True)

    # 1. Beverage Can Image
    img1 = Image.new("RGB", (400, 600), color=(20, 20, 30))
    draw1 = ImageDraw.Draw(img1)
    # Draw bottle shape
    draw1.rectangle([120, 100, 280, 520], fill=(220, 50, 50), outline=(255, 255, 255), width=3)
    # Text on bottle
    draw1.text((140, 200), "ENERGY", fill=(255, 255, 255))
    draw1.text((140, 240), "DRINK", fill=(255, 255, 255))
    draw1.text((140, 280), "250 ML", fill=(255, 255, 255))
    draw1.text((140, 320), "CAFFEINE", fill=(255, 255, 255))
    img1.save("sample_images/beverage_can.jpg")

    # 2. Athletic Sneaker Image
    img2 = Image.new("RGB", (600, 400), color=(240, 240, 245))
    draw2 = ImageDraw.Draw(img2)
    # Draw shoe outline shape
    draw2.polygon([(100, 250), (200, 150), (450, 180), (520, 280), (100, 280)], fill=(40, 80, 200))
    draw2.rectangle([80, 280, 540, 320], fill=(250, 250, 250), outline=(0, 0, 0), width=2)
    # Label text
    draw2.text((220, 200), "NIKE AIR", fill=(255, 255, 255))
    draw2.text((220, 230), "RUNNING", fill=(255, 255, 255))
    img2.save("sample_images/sneakers.png")

    # 3. Skincare Cream Jar
    img3 = Image.new("RGB", (500, 500), color=(255, 250, 245))
    draw3 = ImageDraw.Draw(img3)
    # Draw Jar shape
    draw3.rectangle([150, 150, 350, 380], fill=(240, 240, 240), outline=(200, 160, 100), width=4)
    draw3.rectangle([130, 110, 370, 150], fill=(200, 160, 100))
    # Text on jar
    draw3.text((170, 200), "FACIAL CREAM", fill=(50, 50, 50))
    draw3.text((170, 240), "MOISTURIZER", fill=(50, 50, 50))
    draw3.text((170, 280), "50 ML SPF30", fill=(50, 50, 50))
    img3.save("sample_images/skincare_cream.png")

    # 4. Book Cover
    img4 = Image.new("RGB", (400, 600), color=(30, 70, 50))
    draw4 = ImageDraw.Draw(img4)
    draw4.rectangle([20, 20, 380, 580], outline=(210, 180, 90), width=4)
    draw4.text((60, 100), "PYTHON AI", fill=(255, 255, 255))
    draw4.text((60, 140), "HANDBOOK", fill=(255, 255, 255))
    draw4.text((60, 220), "JOHN DOE", fill=(210, 180, 90))
    draw4.text((60, 480), "EDITION 2026", fill=(200, 200, 200))
    img4.save("sample_images/book_cover.jpg")

    print("Created 4 diverse sample product images in sample_images/")

if __name__ == "__main__":
    create_sample_images()
