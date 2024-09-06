import argparse
import random
import numpy as np
import pydub
import math
import PIL.Image as Image

from enum import Enum
from tqdm import tqdm

c_sample_rate = 44100
c_duration = 8
c_freq_min = 0
c_freq_max = 20000
c_output = "result.wav"
c_step_y = 1
c_offset = "45"

class OffsetMode(Enum):
	NONE = "none"
	ROT45 = "45"
	RANDOM = "random"

def array_to_i16(tone):
	return np.clip(tone * 32767, -32768, 32767).astype(np.int16)

def min_max_norm(value):
	min_val, max_val = value.min(), value.max()
	return (value - min_val) / (max_val - min_val)

def resize_interpolated(value, size):
	value_len = len(value)
	indices = np.linspace(0, value_len - 1, size)
	return np.interp(indices, np.arange(value_len), value)

def enum_to_string(enum_object):
	return f"[{', '.join([mode.value for mode in enum_object])}]"

def parse_arguments():
	parser = argparse.ArgumentParser(description="A CLI tool to transform images into waveforms")

	parser.add_argument(
		"--input", "-i",
		help="The image file to use",
		required=True, type=str
	)

	# Optional Arguments
	parser.add_argument(
		"--output", "-o",
		help="The output filename",
		type=str, default=c_output
	)

	parser.add_argument(
		"--freq-min",
		help=f"Sets the minimum frequency (defaults to {c_freq_min})",
		type=int, default=c_freq_min
	)

	parser.add_argument(
		"--freq-max",
		help=f"Sets the maximum frequency (defaults to {c_freq_max})",
		type=int, default=c_freq_max
	)

	parser.add_argument(
		"--duration", "-d",
		help=f"Sets the duration (defaults to {c_duration})",
		type=float, default=c_duration
	)

	parser.add_argument(
		"--sample-rate", "-r",
		help=f"Sets the sample rate (defaults to {c_sample_rate})",
		type=int, default=c_sample_rate
	)

	parser.add_argument(
		"--step-y",
		help=f"Sets the y step size (defaults to {c_step_y})",
		type=int, default=c_step_y
	)

	parser.add_argument(
		"--offsets",
		help=f"Offsets each tone by some amount with the objective to mitigate constructive interference. Available modes: {enum_to_string(OffsetMode)} (defaults to {c_offset})",
		type=str, default=c_offset
	)


	return parser.parse_args()

def main():
	arguments = parse_arguments()

	tone_offset = arguments.offsets.lower()
	sample_rate = arguments.sample_rate
	output_file = arguments.output
	input_file = arguments.input
	freq_min = arguments.freq_min
	freq_max = arguments.freq_max
	duration = arguments.duration
	step_y = arguments.step_y

	assert tone_offset in OffsetMode, f"Unknown offset mode {tone_offset}"
	assert step_y >= 1, "Expected step-y to be 1 or higher"
	
	sample_count = round(sample_rate * duration)
	freq_range = freq_max - freq_min
	waveform = np.zeros(sample_count, np.float64)

	image = Image.open(input_file).convert("RGB")
	image.load()
	_sx, sy = image.size
	
	# @todo make min-max normalization optional, and add more normalization methods
	values = np.rot90(min_max_norm(np.array(image).sum(axis=2) ** 2 / 765), -1)

	print(f"Normalized intensity range: {values.min():.2f}/{values.max():.2f}, shape: {values.shape}")
	print(f"Frequency(min: {freq_min}, max: {freq_max}, range: {freq_range})")
	print(f"Step Y: {step_y}, Offset method: {tone_offset}")

	time_values = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
	bar = tqdm(total=sy)

	for y in range(0, sy, step_y):
		percentage = (y + 1) / sy
		base_frequency = percentage * freq_range + freq_min
		
		match OffsetMode(tone_offset):
			case OffsetMode.NONE:
				offset = 0
			case OffsetMode.ROT45:
				offset = percentage * duration * base_frequency * np.pi
			case OffsetMode.RANDOM:
				offset = random.random() * np.pi * 2
		
		amplitudes = resize_interpolated(values[:, y], sample_count)
		frequency = time_values * base_frequency * np.pi * 2
		
		waveform += np.sin(frequency + offset) * amplitudes
	
		bar.n = y + 1
		bar.refresh()
	
	bar.n = sy
	bar.close()

	print(f"Normalizing by: {abs(waveform).max():.2f}")
	audio = pydub.AudioSegment(
		data=array_to_i16(waveform / abs(waveform).max()),
		sample_width=2,
		frame_rate=sample_rate,
		channels=1
	)
	file_format = output_file.split('.')[-1].lower()

	print(f"Saving to {output_file} with {file_format} format")
	audio.export(output_file, file_format)


if __name__ == "__main__":
	main()