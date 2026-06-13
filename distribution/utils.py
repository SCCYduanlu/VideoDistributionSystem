import os
import subprocess
import json
import threading
import time
import numpy as np
import soundfile as sf
from scipy.fftpack import dct, idct
from django.conf import settings
from cryptography.fernet import Fernet
from django.core.files.storage import default_storage

def get_fernet():
    return Fernet(settings.WATERMARK_SECRET_KEY)

def generate_token(extraction_code_id, video_id):
    f = get_fernet()
    data = f"{extraction_code_id}:{video_id}".encode()
    return f.encrypt(data).decode()

def decrypt_token(token):
    f = get_fernet()
    try:
        data = f.decrypt(token.encode()).decode()
        extraction_code_id, video_id = data.split(':')
        return int(extraction_code_id), int(video_id)
    except Exception:
        return None, None

def get_video_duration(file_path):
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def embed_audio_watermark(audio_path, token):
    # A simplified spread-spectrum or high-frequency modulation approach for audio watermarking
    
    # 优化：对于低内存服务器 (如 2GB)，一次性读取整个音频到 numpy 数组会直接 OOM 被系统 kill 掉。
    # 改为使用 soundfile 的块读取 (block processing) 机制
    out_path = audio_path.replace('.wav', '_watermarked.wav')
    
    # Convert token to binary string
    binary_token = ''.join(format(ord(c), '08b') for c in token)
    segment_size = 256
    
    info = sf.info(audio_path)
    sr = info.samplerate
    
    # 使用块处理，每次处理 1MB 的采样帧 (约几秒钟的音频)
    block_size = 1024 * 1024 
    
    with sf.SoundFile(audio_path, 'r') as f_in, sf.SoundFile(out_path, 'w', samplerate=sr, channels=info.channels, subtype=info.subtype) as f_out:
        
        bits_embedded = 0
        total_bits = len(binary_token)
        
        for block in f_in.blocks(blocksize=block_size):
            # Process first channel for simplicity
            if len(block.shape) > 1:
                channel_data = block[:, 0]
            else:
                channel_data = block
                
            num_segments = len(channel_data) // segment_size
            
            for i in range(num_segments):
                if bits_embedded >= total_bits:
                    break # 所有水印位已注入完毕，后续音频块不再处理 DCT，直接原样写出以节省 CPU
                    
                segment = channel_data[i*segment_size : (i+1)*segment_size]
                segment_dct = dct(segment, norm='ortho')
                
                # Modify high frequency components
                freq_idx = int(segment_size * 0.8) # Very high frequency
                
                bit = int(binary_token[bits_embedded])
                magnitude = 0.5 
                if bit == 1:
                    segment_dct[freq_idx:freq_idx+2] = magnitude
                else:
                    segment_dct[freq_idx:freq_idx+2] = -magnitude
                    
                segment_idct = idct(segment_dct, norm='ortho')
                
                # Replace the segment
                if len(block.shape) > 1:
                    block[i*segment_size : (i+1)*segment_size, 0] = segment_idct
                else:
                    block[i*segment_size : (i+1)*segment_size] = segment_idct
                    
                bits_embedded += 1
                
            f_out.write(block)

    return out_path

def extract_audio_watermark(audio_path, token_length=120): 
    # Extract the token embedded by the function above
    try:
        data, sr = sf.read(audio_path)
        if len(data.shape) > 1:
            channel_data = data[:, 0]
        else:
            channel_data = data
            
        binary_token = ""
        segment_size = 256
        
        # Determine token length dynamically or use a max buffer
        # Let's try to extract up to token_length
        num_bits = token_length * 8
        
        if len(channel_data) < num_bits * segment_size:
            num_bits = len(channel_data) // segment_size
            
        for i in range(num_bits):
            segment = channel_data[i*segment_size : (i+1)*segment_size]
            segment_dct = dct(segment, norm='ortho')
            freq_idx = int(segment_size * 0.8)
            
            # Check the average of the forced coefficients
            avg_val = np.mean(segment_dct[freq_idx:freq_idx+2])
            if avg_val > 0:
                binary_token += '1'
            else:
                binary_token += '0'
                
        # Convert binary to string
        chars = [chr(int(binary_token[i:i+8], 2)) for i in range(0, len(binary_token), 8) if len(binary_token[i:i+8]) == 8]
        token = ''.join(chars)
        
        # Find the fernet token
        start_idx = token.find('gAAAAAB')
        if start_idx != -1:
            # Fernet tokens are usually ~100 chars
            extracted = token[start_idx:start_idx+100]
            # Clean up trailing garbage if any
            clean_token = ''.join(c for c in extracted if c.isprintable())
            return clean_token
            
        return None
    except Exception as e:
        print(f"Extraction error: {e}")
        return None
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def process_watermark(watermarked_video_id):
    import django
    django.setup()
    from .models import WatermarkedVideo
    
    wv = WatermarkedVideo.objects.get(id=watermarked_video_id)
    wv.status = 'processing'
    wv.save()
    
    try:
        video_obj = wv.video
        input_path = video_obj.video_file.path
        
        output_dir = os.path.join(settings.MEDIA_ROOT, 'watermarked', str(wv.extraction_code.project.id))
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = f"{wv.extraction_code.code}_{video_obj.id}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        token = generate_token(wv.extraction_code.id, video_obj.id)
        
        # 1. Extract audio from video
        wv.status = 'extracting'
        wv.save(update_fields=['status'])
        temp_audio_path = os.path.join(output_dir, f"temp_{wv.id}.wav")
        extract_cmd = ['ffmpeg', '-y', '-i', input_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', temp_audio_path]
        subprocess.run(extract_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 2. Embed watermark into audio
        wv.status = 'embedding'
        wv.save(update_fields=['status'])
        watermarked_audio_path = embed_audio_watermark(temp_audio_path, token)
        
        # 3. Mux video (stream copy) with watermarked audio
        wv.status = 'muxing'
        wv.save(update_fields=['status'])
        mux_cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-i', watermarked_audio_path,
            '-c:v', 'copy',
            '-c:a', 'alac', # 使用无损且编码极快的 Apple Lossless Audio Codec
            '-map', '0:v:0',
            '-map', '1:a:0',
            output_path
        ]
        
        subprocess.run(mux_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Cleanup temp files
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if os.path.exists(watermarked_audio_path):
            os.remove(watermarked_audio_path)
        
        wv.file_path = f"watermarked/{wv.extraction_code.project.id}/{output_filename}"
        wv.status = 'done'
        wv.save()
        
    except Exception as e:
        print(f"Audio Watermark Error: {e}")
        wv.status = 'failed'
        wv.save()

def start_watermark_task(watermarked_video_id):
    t = threading.Thread(target=process_watermark, args=(watermarked_video_id,))
    t.daemon = True
    t.start()