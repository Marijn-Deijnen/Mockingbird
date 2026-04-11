from voxcpm import VoxCPM
import soundfile as sf

# --- Configuration ---
VOICE  = "A young woman, gentle and sweet voice"
TEXT   = "Hello, this is a test."
OUTPUT = "output.wav"

# --- Generation ---
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)

prompt = f"({VOICE}){TEXT}"
wav = model.generate(text=prompt, cfg_value=2.0, inference_timesteps=10)

sf.write(OUTPUT, wav, model.tts_model.sample_rate)
print(f"Saved to {OUTPUT}")
