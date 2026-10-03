import subprocess
import os
import sys

# Ensure output directories exist
os.makedirs("assets/video", exist_ok=True)

# 1. Create concat list for 5 chapters (each 60 seconds)
concat_file = "scratch/chapters_list.txt"
with open(concat_file, "w") as f:
    f.write("file '../assets/images/wildflower_meadow.jpg'\n")
    f.write("duration 60\n")
    f.write("file '../assets/images/nocturnal_bonfire.jpg'\n")
    f.write("duration 60\n")
    f.write("file '../assets/images/moonlit_skyline.jpg'\n")
    f.write("duration 60\n")
    f.write("file '../assets/images/pixel_flower.jpg'\n")
    f.write("duration 60\n")
    f.write("file '../assets/images/dawn_horizon.jpg'\n")
    f.write("duration 60\n")
    # Concat demuxer requires the last file repeated without duration to terminate correctly
    f.write("file '../assets/images/dawn_horizon.jpg'\n")

print("Created concat file.")

# Test building 1080p and 4K
# Let's do 1080p first as a fast responsive stream, then 4K UHD!
# 1080p command:
cmd_1080p = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", concat_file,
    "-i", "assets/audio/ambient_bonfire_5min.wav",
    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
    "-r", "24",
    "-t", "300",
    "-c:v", "h264_videotoolbox", "-b:v", "3500k",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    "assets/video/film_1080p_5min.mp4"
]

print("Rendering 1080p 5-minute video...")
res1 = subprocess.run(cmd_1080p, capture_output=True, text=True)
if res1.returncode != 0:
    print("1080p error:", res1.stderr)
    sys.exit(1)
print("1080p complete!")

# 4K command:
cmd_4k = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", concat_file,
    "-i", "assets/audio/ambient_bonfire_5min.wav",
    "-vf", "scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
    "-r", "24",
    "-t", "300",
    "-c:v", "h264_videotoolbox", "-b:v", "8000k",
    "-c:a", "aac", "-b:a", "256k",
    "-movflags", "+faststart",
    "assets/video/film_4k_5min.mp4"
]

print("Rendering 4K UHD 5-minute video...")
res2 = subprocess.run(cmd_4k, capture_output=True, text=True)
if res2.returncode != 0:
    print("4K error:", res2.stderr)
    sys.exit(1)
print("4K UHD complete!")
