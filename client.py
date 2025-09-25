import pyaudio, threading, queue, requests

# Configuration
global chunk
global sample_format
global channelcount
global fs
global seconds
global device_id
global server_url
chunk = 1024
sample_format = pyaudio.paInt16
channelcount = 2
fs = 48000
seconds = 20
device_id = 4 #? find the one you want with ./get_device_id.py
server_url = "http://127.0.0.1:5001"

# Thread-safe queue for audio chunks
audio_queue = queue.Queue()

# Recording thread
def record_audio():
	p = pyaudio.PyAudio()
	device_info = p.get_device_info_by_index(device_id)
	
	try:
		channelcount = int(device_info["maxInputChannels"]) if int(device_info["maxInputChannels"]) > 0 else int(channelcount)
	except UnboundLocalError|Exception: channelcount = int(2)
	rate = int(device_info["defaultSampleRate"])
	stream = p.open(format=sample_format,
					channels=channelcount,
					rate=rate,
					input=True,
					frames_per_buffer=chunk,
					input_device_index=device_info["index"],
					# as_loopback=True
					)

	print("Recording started...")

	for _ in range(int(fs / chunk * seconds)):
		data = stream.read(chunk, exception_on_overflow=False)
		copied_chunk = data[:]
		audio_queue.put(copied_chunk)

	stream.stop_stream()
	stream.close()
	p.terminate()

	audio_queue.put(None)  # Sentinel to stop the sending thread
	print("Recording stopped.")

# Synchronous sending thread
def send_chunks():
	count = 0
	while True:
		chunk_data = audio_queue.get()
		if chunk_data is None:
			break  # End of stream

		try:
			resp = requests.post(
				server_url,
				headers={"Content-Type": "application/octet-stream"},
				data=chunk_data
			)
			count += 1
			print(f"Sent chunk {count}: {resp.status_code}")
		except Exception as e:
			print(f"Failed to send chunk {count}: {e}")

# Start both threads
rec_thread = threading.Thread(target=record_audio)
send_thread = threading.Thread(target=send_chunks)

rec_thread.start()
send_thread.start()

rec_thread.join()
send_thread.join()

print("All chunks sent.")
