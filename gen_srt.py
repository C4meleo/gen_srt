import os
import subprocess
import datetime
import argparse
import shutil

def isolate_audio(input_video, output_audio):
    command = f"ffmpeg -i {input_video} -vn -acodec pcm_s16le -ar 44100 -ac 2 {output_audio}"
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def download_and_extract_model(model_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    model_zip = os.path.join(output_dir, "model.zip")
    subprocess.run(["curl", "-L", model_url, "-o", model_zip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["unzip", model_zip, "-d", output_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(model_zip)

def clear_previous_model(model_dir):
    shutil.rmtree(model_dir, ignore_errors=True)

def install_dependencies():
    subprocess.run(["pip3", "install", "vosk"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transcribe_audio(audio_file, model_path, output_text):
    command = f"vosk-transcriber -i {audio_file} -m {model_path} > {output_text}"
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def convert_to_srt(input_file, output_file, video_duration):
    with open(input_file, 'r', encoding='utf-8') as infile:
        lines = infile.read().splitlines()

    output_lines = []
    counter = 1
    time_increment = video_duration / len(lines)

    for line in lines:
        line = line.strip()
        if line:
            output_lines.append(str(counter))
            start_time = datetime.timedelta(seconds=(counter - 1) * time_increment)
            start_datetime = datetime.datetime(1900, 1, 1) + start_time
            end_time = datetime.timedelta(seconds=counter * time_increment)
            end_datetime = datetime.datetime(1900, 1, 1) + end_time
            output_lines.append(f"{start_datetime:%H:%M:%S},{start_datetime.microsecond // 1000:03d} --> {end_datetime:%H:%M:%S},{end_datetime.microsecond // 1000:03d}")
            output_lines.append(line)
            output_lines.append('')
            counter += 1

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write('\n'.join(output_lines))

def add_subtitles(input_video, input_srt, output_video):
    command = f"ffmpeg -i {input_video} -i {input_srt} -c copy -c:s mov_text {output_video}"
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def parse_args():
    parser = argparse.ArgumentParser(description="Automatically generate subtitles for videos using Vosk.")
    parser.add_argument("video_input", help="Input video file.")
    parser.add_argument("--dl-vosk-model", action="store_true", help="Download and extract the Vosk model.")
    parser.add_argument("--dl-vosk-model-clear", action="store_true", help="Download, extract, and clear the previous Vosk model.")
    parser.add_argument("--first-use", action="store_true", help="Install dependencies (Vosk and ffmpeg) for the first use.")
    return parser.parse_args()

def main():
    args = parse_args()

    if args.first_use:
        install_dependencies()

    if args.dl_vosk_model_clear or args.dl_vosk_model:
        print("Downloading and extracting Vosk model...")
        download_and_extract_model("https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip", "vosk_model")
        print("Model downloaded and extracted.")

    video_duration_command = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {args.video_input}"
    video_duration = float(subprocess.check_output(video_duration_command, shell=True, text=True).strip())

    audio_output = "output_audio.wav"
    model_output = "vosk_model/vosk-model-fr-0.22"
    transcribed_text_output = "transcribed_text.txt"
    subtitles_output = "subtitles.srt"
    video_output = "video_with_subtitles.mp4"

    print("Isolating audio...")
    isolate_audio(args.video_input, audio_output)
    print("Audio isolated.")

    print("Transcribing audio...")
    transcribe_audio(audio_output, model_output, transcribed_text_output)
    print("Audio transcribed.")

    print("Converting to SRT...")
    convert_to_srt(transcribed_text_output, subtitles_output, video_duration)
    print("Conversion to SRT complete.")

    print("Adding subtitles to the video...")
    add_subtitles(args.video_input, subtitles_output, video_output)
    print("Subtitles added to the video.")

    print("Clear temp files...")
    if args.dl_vosk_model_clear:
        clear_previous_model("vosk_model")
    # Nettoyer les fichiers temporaires (à ajuster selon vos besoins)
    os.remove(audio_output)
    os.remove(transcribed_text_output)
    os.remove(subtitles_output)
    print("Temp files clear.")

if __name__ == "__main__":
    main()
