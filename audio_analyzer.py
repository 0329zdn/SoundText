import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional
import subprocess
import time

try:
    import faster_whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class AudioAnalyzer:
    def __init__(self):
        self._whisper_model = None
        self._whisper_model_size = "base"
        self._whisper_model_path = None
        self._whisper_model_device = None

    def extract_audio_from_video(
        self,
        video_path: str,
        audio_format: str = "wav",
        sample_rate: int = 16000
    ) -> str:
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 在当前目录创建临时文件夹
        current_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(current_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 创建唯一的音频文件名
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        audio_filename = f"audio_{unique_id}.{audio_format}"
        audio_path = os.path.join(temp_dir, audio_filename)
        
        # 确保路径是绝对路径
        audio_path = os.path.abspath(audio_path)

        print(f"从视频提取音频: {video_path}")
        print(f"输出音频路径: {audio_path}")
        start_time = time.time()

        if audio_format == "wav":
            acodec = "pcm_s16le"
        elif audio_format == "mp3":
            acodec = "libmp3lame"
        elif audio_format == "aac":
            acodec = "aac"
        else:
            acodec = "copy"

        # 获取本地 ffmpeg 路径
        ffmpeg_path = os.path.join(current_dir, "ffmpeg", "ffmpeg-master-latest-win64-gpl", "bin", "ffmpeg.exe")
        ffmpeg_path = os.path.abspath(ffmpeg_path)
        
        if not os.path.exists(ffmpeg_path):
            raise Exception(f"ffmpeg 未找到，请确保 ffmpeg 已正确解压到 {os.path.dirname(ffmpeg_path)}")

        cmd = [
            ffmpeg_path,
            "-i", str(video_path),
            "-vn",
            "-acodec", acodec,
            "-ar", str(sample_rate),
            "-ac", "1",
            "-y",
            audio_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            elapsed_time = time.time() - start_time
            print(f"音频提取成功: {audio_path}")
            print(f"音频提取耗时: {elapsed_time:.2f} 秒")
            return audio_path, temp_dir
        except subprocess.CalledProcessError as e:
            raise Exception(f"音频提取失败: {e.stderr}")
        except FileNotFoundError:
            raise Exception("ffmpeg 未安装，请安装 ffmpeg 后重试")

    def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model_size: str = "base",
        local_model_path: Optional[str] = None,
        device: str = "cpu"
    ) -> str:
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print(f"开始语音识别: {audio_path}")
        print(f"使用模型: {model_size}")
        if local_model_path:
            print(f"本地模型路径: {local_model_path}")

        if WHISPER_AVAILABLE:
            return self._transcribe_faster_whisper(audio_path, language, model_size, local_model_path, device)
        else:
            raise Exception(
                "未安装 faster-whisper 库。请运行以下命令安装:\n"
                "pip install faster-whisper\n"
            )

    def _transcribe_faster_whisper(
        self,
        audio_path: str,
        language: Optional[str],
        model_size: str,
        local_model_path: Optional[str],
        device: str = "cpu"
    ) -> str:
        print(f"[DEBUG] 开始处理音频文件: {audio_path}")
        start_time = time.time()
        model_key = local_model_path if local_model_path else model_size
        if self._whisper_model is None or model_size != self._whisper_model_size or local_model_path != self._whisper_model_path or device != self._whisper_model_device:
            if local_model_path:
                print(f"[DEBUG] 加载本地 faster-whisper 模型: {local_model_path} (设备: {device})")
                self._whisper_model = faster_whisper.WhisperModel(
                    local_model_path,
                    device=device
                )
            else:
                print(f"[DEBUG] 加载 faster-whisper 模型: {model_size} (设备: {device})")
                self._whisper_model = faster_whisper.WhisperModel(
                    model_size,
                    device=device
                )
            self._whisper_model_size = model_size
            self._whisper_model_path = local_model_path
            self._whisper_model_device = device

        print(f"[DEBUG] 开始转写...")
        segments, info = self._whisper_model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True
        )
        print(f"[DEBUG] 转写完成，开始遍历片段...")

        if language is None:
            print(f"检测到语言: {info.language} (概率: {info.language_probability:.2f})")

        full_text = []
        segment_count = 0

        for segment in segments:
            segment_count += 1
            text = segment.text.strip()
            if text:
                full_text.append(text)
                print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {text}")

        result = " ".join(full_text)
        print(f"[DEBUG] 拼接完成，结果长度: {len(result)} 字符")
        elapsed_time = time.time() - start_time
        print(f"[DEBUG] 语音识别完成，共 {segment_count} 个片段")
        print(f"[DEBUG] 语音识别耗时: {elapsed_time:.2f} 秒")
        print(f"[DEBUG] 准备返回结果...")

        if device == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    print(f"[DEBUG] GPU 内存已清理")
            except ImportError:
                pass

        return result



    def analyze_audio_from_video(
        self,
        video_path: str,
        language: Optional[str] = None,
        model_size: str = "base",
        local_model_path: Optional[str] = None,
        device: str = "cpu"
    ) -> dict:
        result = {
            "audio_path": None,
            "transcript": None,
            "temp_dir": None
        }

        audio_path, temp_dir = self.extract_audio_from_video(video_path)
        result["audio_path"] = audio_path
        result["temp_dir"] = temp_dir

        try:
            transcript = self.transcribe_audio(
                audio_path,
                language=language,
                model_size=model_size,
                local_model_path=local_model_path,
                device=device
            )
            result["transcript"] = transcript
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        return result

    def analyze_audio_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model_size: str = "base",
        local_model_path: Optional[str] = None,
        device: str = "cpu"
    ) -> dict:
        result = {
            "transcript": None
        }

        transcript = self.transcribe_audio(
            audio_path,
            language=language,
            model_size=model_size,
            local_model_path=local_model_path,
            device=device
        )
        result["transcript"] = transcript

        return result


def main(audio_path: str):
    import datetime
    
    analyzer = AudioAnalyzer()
    
    result_dir = Path("result")
    result_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(audio_path).stem
    output_prefix = result_dir / f"{base_name}_{timestamp}"

    print("=" * 80)
    print("音频分析测试")
    print("=" * 80)

    try:
        result = analyzer.analyze_audio_file(
            audio_path,
            language="zh",
            model_size="tiny",
            local_model_path="./base"
        )

        transcript_file = output_prefix / "transcript.txt"
        
        transcript_file.parent.mkdir(parents=True, exist_ok=True)
        
        if result["transcript"]:
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(result["transcript"])
            print(f"\n转写文本已保存到: {transcript_file}")
            print("\n" + "=" * 80)
            print("转写文本:")
            print("=" * 80)
            print(result["transcript"])

    except Exception as e:
        print(f"分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    dir_path = r"E:\video\杂\001-绪论_dec.mp4"
    main(dir_path)
