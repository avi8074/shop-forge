import torch
import torchvision.models as models
from PIL import Image, ImageDraw

def test_visual_model():
    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights).eval()
    preprocess = weights.transforms()

    # Create a plain shoe image (NO text on it)
    img_shoe = Image.new("RGB", (500, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img_shoe)
    # Draw shoe shape
    draw.polygon([(80, 260), (180, 140), (420, 170), (460, 270), (80, 270)], fill=(220, 40, 40))
    draw.rectangle([60, 270, 480, 310], fill=(30, 30, 30))
    img_shoe.save("sample_images/plain_shoe_no_text.png")

    # Create a plain mug image (NO text on it)
    img_mug = Image.new("RGB", (400, 400), color=(255, 255, 255))
    draw_mug = ImageDraw.Draw(img_mug)
    # Draw cup body
    draw_mug.rectangle([120, 120, 280, 320], fill=(40, 120, 220))
    draw_mug.arc([250, 160, 330, 280], start=270, end=90, fill=(40, 120, 220), width=15)
    img_mug.save("sample_images/plain_mug_no_text.png")

    for img_path in ["sample_images/plain_shoe_no_text.png", "sample_images/plain_mug_no_text.png"]:
        pil_img = Image.open(img_path).convert("RGB")
        batch = preprocess(pil_img).unsqueeze(0)
        with torch.no_grad():
            prediction = model(batch).squeeze(0).softmax(0)
        
        top5_prob, top5_catid = torch.topk(prediction, 5)
        print(f"\n--- Visual Predictions for {img_path} (NO TEXT ON IMAGE) ---")
        for i in range(5):
            cat_name = weights.meta['categories'][top5_catid[i]]
            prob = top5_prob[i].item()
            print(f"{i+1}. {cat_name} ({prob:.2%})")

if __name__ == "__main__":
    test_visual_model()
