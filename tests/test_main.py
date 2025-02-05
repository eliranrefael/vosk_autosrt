import subprocess
import os
import glob
from pathlib import Path
import pytest
from gtts import gTTS

def get_media_file_name():
    return "media_mock_file"

def get_src_lang():
    return "en"

def get_des_lang():
    return "fr"

@pytest.fixture(autouse=True)
def subs_cleanup():
    yield
    for srt_file in glob.glob("*.srt"):
        os.remove(srt_file)

@pytest.fixture
def video_file_path():
    test_text="By default, pytest will only display the print output when a test fails, so if your tests pass, you won't see anything printed in the console. If you specifically want to see the output on successful tests, you can use the -s option mentioned earlier."

    #generate a mock video file to translate
    audio_mock_gen = gTTS(text=test_text, lang="en", slow=True)
    audio_mock_file_path = f"{get_media_file_name()}.mp3"
    video_mock_file_path = f"{get_media_file_name()}.mp4"
    audio_mock_gen.save(audio_mock_file_path)

    blank_video_file_path = "blank.mp4"
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=21",
        "-c:v", "libx264", blank_video_file_path
    ], check=True)

    subprocess.run([
        "ffmpeg", "-i", blank_video_file_path, "-i", audio_mock_file_path, "-c:v", "copy",
        "-c:a", "copy",  "-shortest", '-map', '0:v:0', '-map', '1:a:0', video_mock_file_path
    ], check=True)

    # Cleanup
    os.remove(audio_mock_file_path)
    os.remove(blank_video_file_path)
    return video_mock_file_path


def test_command_runs(video_file_path):
    """Test subs generation with no translation"""
    result = subprocess.run(["vosk_autosrt", "-S", f"{get_src_lang()}", f"{video_file_path}"], capture_output=True, text=True)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    print("run successfully with no translation")
    test_files_created()

    result = subprocess.run(["vosk_autosrt", "-S", f"{get_src_lang()}", "-D", f"{get_des_lang()}", f"{video_file_path}"], capture_output=True, text=True)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    print("run successfully with translation")
    test_files_created(translation=True)

    os.remove(video_file_path)


def test_files_created (translation = False, keep_src_output = True, subs_file_ext = "srt"):
    if keep_src_output:
        src_subs_file_path = f"{get_media_file_name()}.{get_src_lang()}.{subs_file_ext}"
        output_file = Path(src_subs_file_path)
        assert output_file.exists(), f"Missing file: {src_subs_file_path}"
    
    if translation:
        des_subs_file_path = f"{get_media_file_name()}.{get_des_lang()}.{subs_file_ext}"
        output_file = Path(des_subs_file_path)
        assert output_file.exists(), f"Missing file: {des_subs_file_path}"
