import wave
import struct
import math
import random
import os

sample_rate = 44100
duration_sec = 300  # Exactly 5 minutes (300 seconds)
num_samples = sample_rate * duration_sec

os.makedirs("assets/audio", exist_ok=True)
output_path = "assets/audio/ambient_bonfire_5min.wav"

print(f"Synthesizing 5-minute ambient bonfire soundtrack ({num_samples} samples)...")

# Chord progressions across the 5 minutes (each chapter shifts root slightly)
# Ch.1 (0-60s): Dm9 (D2, A2, F3, C4, E4)
# Ch.2 (60-120s): Bbmaj7 (Bb1, F2, D3, A3, C4)
# Ch.3 (120-180s): Fmaj9 (F1, C2, A2, E3, G3, C4)
# Ch.4 (180-240s): Gm9 (G1, D2, Bb2, F3, A3)
# Ch.5 (240-300s): Dsus2 / Dmaj (D2, A2, D3, F#3, A3, E4)

chords = [
    # (start_s, end_s, freqs)
    (0, 60, [73.42, 110.0, 174.61, 261.63, 329.63]),
    (60, 120, [58.27, 87.31, 146.83, 220.0, 261.63]),
    (120, 180, [43.65, 65.41, 110.0, 164.81, 196.0, 261.63]),
    (180, 240, [49.00, 73.42, 116.54, 174.61, 220.0]),
    (240, 300, [73.42, 110.0, 146.83, 185.00, 220.0, 329.63]),
]

# Pre-generate random crackle events (timestamp in seconds, amplitude, decay_tau)
crackles = []
for _ in range(1200): # ~4 crackles per second
    t_c = random.uniform(0, duration_sec)
    amp = random.uniform(0.04, 0.28)
    decay = random.uniform(0.005, 0.035)
    pan = random.uniform(0.2, 0.8) # stereo pan
    freq = random.uniform(1200, 3400) # crackle resonance
    crackles.append((t_c, amp, decay, pan, freq))

crackles.sort(key=lambda x: x[0])

# We can stream write in blocks of 44100 (1 second chunks) to keep memory tiny
crackle_idx = 0
active_crackles = []

with wave.open(output_path, 'w') as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(sample_rate)

    block_size = 44100
    total_blocks = duration_sec

    # Noise state for brown noise
    brown_left = 0.0
    brown_right = 0.0

    for block_num in range(total_blocks):
        block_frames = bytearray()
        block_start_s = block_num
        
        # Determine current chord and next chord for crossfade
        curr_chord_freqs = chords[0][2]
        next_chord_freqs = chords[0][2]
        fade_factor = 0.0

        for idx, (cs, ce, freqs) in enumerate(chords):
            if cs <= block_start_s < ce:
                curr_chord_freqs = freqs
                if ce - block_start_s < 10 and idx + 1 < len(chords):
                    fade_factor = (10 - (ce - block_start_s)) / 10.0
                    next_chord_freqs = chords[idx+1][2]
                else:
                    fade_factor = 0.0
                break

        # Process samples for this 1-second block
        for s_in_block in range(block_size):
            t = block_start_s + (s_in_block / sample_rate)

            # Master envelope: gentle 3s fade-in at 0, gentle 4s fade-out at end
            env = 1.0
            if t < 3.0:
                env = t / 3.0
            elif t > 296.0:
                env = max(0.0, (300.0 - t) / 4.0)

            # Slow meditative breathing LFO (cycle of ~12 seconds)
            lfo = 0.8 + 0.2 * math.sin(2 * math.pi * 0.083 * t)

            # Drone chord synthesis
            chord_sig1 = sum(math.sin(2 * math.pi * f * t) * (0.18 / (i + 1)**0.6) for i, f in enumerate(curr_chord_freqs))
            if fade_factor > 0:
                chord_sig2 = sum(math.sin(2 * math.pi * f * t) * (0.18 / (i + 1)**0.6) for i, f in enumerate(next_chord_freqs))
                synth = (chord_sig1 * (1.0 - fade_factor) + chord_sig2 * fade_factor)
            else:
                synth = chord_sig1

            # Soft tape/ember brownian noise
            white_l = random.uniform(-1.0, 1.0)
            white_r = random.uniform(-1.0, 1.0)
            brown_left = (brown_left + (0.02 * white_l)) / 1.02
            brown_right = (brown_right + (0.02 * white_r)) / 1.02
            noise_l = brown_left * 0.08
            noise_r = brown_right * 0.08

            # Campfire crackle handling
            while crackle_idx < len(crackles) and crackles[crackle_idx][0] <= t:
                active_crackles.append(crackles[crackle_idx])
                crackle_idx += 1

            crackle_l = 0.0
            crackle_r = 0.0
            # update active crackles
            still_active = []
            for c_t, c_amp, c_dec, c_pan, c_f in active_crackles:
                dt = t - c_t
                if dt < c_dec * 5:
                    c_val = c_amp * math.exp(-dt / c_dec) * math.sin(2 * math.pi * c_f * dt)
                    crackle_l += c_val * (1.0 - c_pan)
                    crackle_r += c_val * c_pan
                    still_active.append((c_t, c_amp, c_dec, c_pan, c_f))
            active_crackles = still_active

            # Chapter boundary bell chime at 0s, 60s, 120s, 180s, 240s
            chime = 0.0
            for mark in [0.5, 60.0, 120.0, 180.0, 240.0]:
                dt_chime = t - mark
                if 0 <= dt_chime < 6.0:
                    chime += 0.12 * math.exp(-dt_chime / 1.8) * (
                        math.sin(2 * math.pi * 523.25 * dt_chime) +
                        0.5 * math.sin(2 * math.pi * 1046.50 * dt_chime)
                    )

            # Combine and normalize
            out_l = env * (synth * lfo * 0.35 + noise_l + crackle_l + chime * 0.5)
            out_r = env * (synth * lfo * 0.35 + noise_r + crackle_r + chime * 0.5)

            samp_l = int(max(-32767, min(32767, out_l * 28000)))
            samp_r = int(max(-32767, min(32767, out_r * 28000)))

            block_frames.extend(struct.pack('<hh', samp_l, samp_r))

        wav.writeframes(block_frames)
        if (block_num + 1) % 60 == 0:
            print(f"Generated {(block_num + 1) // 60} / 5 minutes of soundtrack...")

print("5-minute audio track generated successfully at", output_path)
