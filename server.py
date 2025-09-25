from socket import socket, AF_INET, SOCK_STREAM
import wave, time, pyaudio
from re import search
from subprocess import check_output

# Audio format (must match client)
SAMPLE_RATE = 48000
CHANNELS = 2
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes
CHUNK_SIZE = 4096  # Should match recv buffer size

# Server config
HOST = search(r'(?<!\d)((\d+\.){3}\d+)', check_output('ipconfig', shell=True).decode('utf-8')).group(1).strip() or '127.0.0.1'
PORT = 5001
OUTPUT_FILE = f"recording_{int(time.time())}.wav"

buffer = bytearray()

print(f"Listening on {HOST}:{PORT}...")

p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(SAMPLE_WIDTH),
				channels=CHANNELS,
				rate=SAMPLE_RATE,
				output=True,
				frames_per_buffer=CHUNK_SIZE)

with socket(AF_INET, SOCK_STREAM) as s:
	s.bind((HOST, PORT))
	s.listen(1)
	conn, addr = s.accept()
	print(f"Connected by {addr}")

	with conn:
		while True:
			data = conn.recv(CHUNK_SIZE)
			if not data:
				break
			buffer.extend(data)
			stream.write(data)  # Play chunk immediately

print(f"Connection closed. Saving to {OUTPUT_FILE}...")

stream.stop_stream()
stream.close()
p.terminate()

# Save all received data to WAV file
with wave.open(OUTPUT_FILE, 'wb') as wf:
	wf.setnchannels(CHANNELS)
	wf.setsampwidth(SAMPLE_WIDTH)
	wf.setframerate(SAMPLE_RATE)
	wf.writeframes(buffer)

print("Done.")
