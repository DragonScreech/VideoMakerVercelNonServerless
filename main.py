from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, TextClip, VideoFileClip, ColorClip, ImageSequenceClip
import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile
from dotenv import load_dotenv
import time
from werkzeug.utils import secure_filename
load_dotenv()

app = Flask(__name__)
CORS(app)

def create_video_with_audio(audio_path, num_images, uid, output_path="final_video.mov"):
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration  # Get audio duration in seconds

    # Calculate display duration for each image
    image_display_duration = audio_duration / num_images

    # Generate list of image paths
    image_paths = [f'image_{index}_{uid}.png' for index in range(num_images)]

    # Create ImageSequenceClip
    video_clip = ImageSequenceClip(image_paths, durations=[image_display_duration] * num_images)
    video_clip = video_clip.set_audio(audio_clip)

    # Write the final video to file
    video_clip.write_videofile(output_path, fps=24, codec='libx264', preset='ultrafast')

def delete_file_with_retry(file_path, max_attempts=3, sleep_interval=1):
    for attempt in range(max_attempts):
        try:
            os.remove(file_path)
            print(f"Successfully deleted {file_path}")
            break
        except PermissionError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(sleep_interval)
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

@app.route('/generate-video', methods=['POST'])
def genVideo():
    uid = request.form['uid']
    pdfVideo = request.form.get('pdf')
    strNumImages = request.form['imageCount']
    numImages = int(strNumImages)
    
    # Save audio file
    audio_file = request.files['audio']
    audio_file_path = secure_filename(f'speech_{uid}.mp3')
    audio_file.save(audio_file_path)

    # Save image files
    image_paths = []
    for i in range(numImages):
        image_file = request.files[f'image_{i}']
        image_file_path = secure_filename(f'image_{i}_{uid}.png')
        image_file.save(image_file_path)
        image_paths.append(image_file_path)

    temp_video_path = tempfile.mktemp(suffix=".mov")
    create_video_with_audio(audio_file_path, numImages, uid, temp_video_path)

    # Load the generated video (without overlaying captions)
    video_clip = VideoFileClip(temp_video_path)

    # Save the final video without captions
    final_output_path = tempfile.mktemp(suffix=".mov")
    video_clip.write_videofile(final_output_path,
                               fps=24,
                               codec='libx264',
                               preset='ultrafast')

    time.sleep(1)

    delete_file_with_retry(audio_file_path)

    if pdfVideo == 'true':
        delete_file_with_retry(f'user_pdf_{uid}.pdf')

    for image_path in image_paths:
        delete_file_with_retry(image_path)
    
    return send_file(final_output_path, as_attachment=True, download_name='final_video.mov')

if __name__ == '__main__':
  app.run(debug=True, port=5000)


