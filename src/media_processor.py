import io
import os
import asyncio
import subprocess
import tempfile
import librosa
import soundfile as sf
# Импорт speech_recognition лучше вынести на уровень модуля, если он не будет опциональным
import speech_recognition as sr 

r_recognizer = sr.Recognizer() # Инициализируем один раз

def recognize_speech_from_object(audio_file_like_object):
    with sr.AudioFile(audio_file_like_object) as source:
        audio = r_recognizer.record(source)
    try:
        text = r_recognizer.recognize_google(audio, language='ru-RU')
        return text
    except sr.UnknownValueError:
        return "Не удалось распознать речь"
    except sr.RequestError as e:
        print(f"Speech recognition API error: {e}")
        return f"Ошибка сервиса распознавания: {e}" # Не показываем детали ошибки пользователю

async def extract_audio_from_video_note(video_note_file: io.BytesIO) -> io.BytesIO | None:
    input_video_path, output_audio_path = None, None # Для блока finally
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video_file:
            tmp_video_file.write(video_note_file.getvalue())
            input_video_path = tmp_video_file.name

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio_file:
            output_audio_path = tmp_audio_file.name
        
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", # Меньше вывода от ffmpeg
            "-i", input_video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            "-y", output_audio_path
        ]
        process = await asyncio.create_subprocess_exec(
            *command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"FFmpeg error processing video note (code {process.returncode}): {stderr.decode(errors='ignore')}")
            return None

        audio_bytes_io = io.BytesIO()
        with open(output_audio_path, "rb") as f_audio:
            audio_bytes_io.write(f_audio.read())
        audio_bytes_io.seek(0)
        return audio_bytes_io
    except Exception as e:
        print(f"Error in extract_audio_from_video_note: {e}")
        return None
    finally:
        if input_video_path and os.path.exists(input_video_path):
            os.remove(input_video_path)
        if output_audio_path and os.path.exists(output_audio_path):
            os.remove(output_audio_path)

def process_audio_data(audio_file_io: io.BytesIO) -> io.BytesIO:
    """Приводит аудио к WAV 16kHz mono для speech_recognition"""
    y, sr_orig = librosa.load(audio_file_io, sr=None) # Загружаем с оригинальной sr
    # Ресемплируем до 16kHz, если нужно
    if sr_orig != 16000:
        y = librosa.resample(y, orig_sr=sr_orig, target_sr=16000)
    
    # Конвертируем в моно, если нужно (берем первый канал)
    if y.ndim > 1:
        y = y[0]

    converted_audio_io = io.BytesIO()
    # Убедимся, что данные в нужном формате для sf.write
    # librosa.load возвращает float, sf.write с PCM_16 ожидает int16 или float в диапазоне [-1, 1]
    # Если y не в [-1,1], его нужно нормализовать или конвертировать в int16
    # sf.write сам нормализует float для PCM, если он в [-1,1]
    sf.write(converted_audio_io, y, 16000, format='WAV', subtype='PCM_16')
    converted_audio_io.seek(0)
    return converted_audio_io