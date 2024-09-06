import matplotlib.colors as colors
import matplotlib.pyplot as plt
import matplotlib as mpl
import argparse
import pydub
import numpy as np

from matplotlib.colors import LinearSegmentedColormap, to_rgba_array

c_window_size = 2048
c_freq_min = 0
c_freq_max = 20000
c_channel = 0
c_factor = 16

def audio_to_array(audio):
	sample_rate = audio.frame_rate
	channels = audio.channels
	divisor = 2 ** (audio.sample_width * 8) / 2
	samples = np.array(audio.get_array_of_samples()).reshape((channels, -1))
	waveform = samples / divisor
	duration = samples.size / sample_rate / channels

	return waveform, duration, sample_rate

def parse_ratio(ratio):
	return np.array(list(map(float, ratio.split(':'))))

def normalize_ratio(ratio, factor):
	return ratio / ratio.max() * factor

def increase_saturation(cmap, factor=2.0):
	quantization = cmap.N
	color_list = cmap(np.arange(quantization))

	hsv_colors = colors.rgb_to_hsv(color_list[:, :3])
	hsv_colors[:, 1] *= factor
	hsv_colors[:, 1] = np.clip(hsv_colors[:, 1], 0, 1)
	
	return LinearSegmentedColormap.from_list(
		"saturated",
		colors.hsv_to_rgb(hsv_colors),
		quantization
	)

def parse_arguments():
	parser = argparse.ArgumentParser(description="A CLI tool to transform audio into spectrograms")

	parser.add_argument(
		"--input", "-i",
		help="The audio file to use",
		required=True, type=str
	)

	parser.add_argument(
		"--output", "-o",
		help="The output filename",
		required=True, type=str
	)

	parser.add_argument(
		"--ratio", "-r",
		help="The image ratio, format should be X:Y",
		required=True, type=str
	)

	# Optional Arguments
	parser.add_argument(
		"--view", "-v",
		help="Open a window with the result",
		action="store_true"
	)

	parser.add_argument(
		"--factor", "-f",
		help=f"Scaling factor to use (defaults to {c_factor})",
		type=float, default=c_factor
	)

	parser.add_argument(
		"--channel", "-c",
		help=f"Which channel to use (defaults to {c_channel})",
		type=int, default=c_channel
	)

	parser.add_argument(
		"--size", "-s",
		help=f"Sets the window size (defaults to {c_window_size})",
		type=int, default=c_window_size
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

	return parser.parse_args()

def main():
	arguments = parse_arguments()

	window_size = arguments.size
	output_file = arguments.output
	input_file = arguments.input
	freq_min = arguments.freq_min
	freq_max = arguments.freq_max
	channel = arguments.channel
	factor = arguments.factor
	ratio = arguments.ratio
	view = arguments.view

	audio = pydub.AudioSegment.from_file(input_file)
	waveform, _duration, sample_rate = audio_to_array(audio)

	scaling = normalize_ratio(parse_ratio(ratio), factor)

	overlap = window_size // 2
	window = np.hanning(window_size)
	
	fig, ax = plt.subplots(figsize=tuple(reversed(scaling)))
	fig.subplots_adjust(0, 0, 1, 1)
	ax.specgram(
		waveform[channel] * 20,
		window_size,
		sample_rate, 0,
		window=window,
		noverlap=overlap,
		cmap=increase_saturation(mpl.colormaps["gray"], 2),
		vmin=-100, vmax=0
	)
	ax.set_ylim(freq_min, freq_max)
	ax.axis("off")
	
	if view:
		plt.show()
	
	fig.savefig(output_file, pad_inches=0)
	plt.close(fig)


if __name__ == "__main__":
	main()