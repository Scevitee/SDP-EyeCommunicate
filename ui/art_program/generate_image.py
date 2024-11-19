import sys
from auto1111sdk import StableDiffusionXLPipeline
import torch
from PIL import Image

def generate_image(input_path, output_path, prompt):
    # Empty CUDA cache before running
    torch.cuda.empty_cache()

    # Load the input image
    input_image = Image.open(input_path)

    # Initialize the model pipeline
    pipe = StableDiffusionXLPipeline("models/sdxl2.safetensors", " --lowvram --opt-split-attention")
    pipe.set_vae("models/sdxl.vae.safetensors")

    # Generate image
    output = pipe.generate_img2img(init_image=input_image, prompt=prompt, height=400, width=400, steps=15)
    output[0].save(output_path)

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    prompt = sys.argv[3]
    generate_image(input_path, output_path, prompt)