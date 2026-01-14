#!/usr/bin/env python3
"""
Script Generator - Tạo script tiếng Nhật cho các file audio đã tách

Chức năng:
- Quét tất cả file MP3 đã tách (mondai và questions)
- Sử dụng Whisper để transcribe từng file
- Tạo script tiếng Nhật (text) cho mỗi file
- Export ra file .txt và .json có cấu trúc

Author: PBL5 Team
Version: 1.0
"""

import whisper
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('generate_scripts.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScriptGenerator:
    """
    Class tạo script tiếng Nhật cho các file audio đã tách
    """
    
    def __init__(
        self,
        audio_dir: str = "output/mondai",
        output_dir: str = "output/scripts",
        whisper_model: str = "base"
    ):
        """
        Khởi tạo Script Generator
        
        Args:
            audio_dir: Thư mục chứa các file audio đã tách
            output_dir: Thư mục output cho scripts
            whisper_model: Model Whisper (tiny/base/small/medium/large)
        """
        logger.info("🚀 Khởi tạo Script Generator")
        
        self.audio_dir = Path(audio_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        if not self.audio_dir.exists():
            raise FileNotFoundError(f"❌ Thư mục audio không tồn tại: {audio_dir}")
        
        # Load Whisper model
        logger.info(f"🔄 Đang load Whisper model ({whisper_model})...")
        self.model = whisper.load_model(whisper_model)
        logger.info("✅ Whisper model loaded")
        
        self.stats = {
            "start_time": datetime.now(),
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0
        }
    
    def find_audio_files(self) -> List[Path]:
        """
        Tìm tất cả file MP3 trong thư mục audio
        
        Returns:
            List các path đến file MP3
        """
        logger.info(f"🔍 Đang quét file audio trong: {self.audio_dir}")
        
        audio_files = []
        
        # Tìm file mondai chính
        mondai_files = sorted(self.audio_dir.glob("mondai_*.mp3"))
        audio_files.extend(mondai_files)
        
        # Tìm file questions trong các thư mục con
        for questions_dir in sorted(self.audio_dir.glob("mondai_*_questions")):
            question_files = sorted(questions_dir.glob("question_*.mp3"))
            audio_files.extend(question_files)
        
        logger.info(f"✅ Tìm thấy {len(audio_files)} file audio")
        self.stats["total_files"] = len(audio_files)
        
        return audio_files
    
    def transcribe_file(self, audio_path: Path) -> Dict:
        """
        Transcribe một file audio thành text tiếng Nhật
        
        Args:
            audio_path: Path đến file audio
            
        Returns:
            Dict chứa transcript và metadata
        """
        logger.info(f"📝 Transcribing: {audio_path.name}")
        
        try:
            result = self.model.transcribe(
                str(audio_path),
                language="ja",  # Japanese
                task="transcribe",
                verbose=False,
                word_timestamps=True  # Timestamps chi tiết
            )
            
            # Extract thông tin quan trọng
            transcript_data = {
                "file_name": audio_path.name,
                "file_path": str(audio_path.relative_to(self.audio_dir)),
                "text": result["text"].strip(),
                "segments": [
                    {
                        "id": seg["id"],
                        "start": round(seg["start"], 2),
                        "end": round(seg["end"], 2),
                        "text": seg["text"].strip()
                    }
                    for seg in result["segments"]
                ],
                "duration": round(result["segments"][-1]["end"], 2) if result["segments"] else 0,
                "num_segments": len(result["segments"]),
                "language": result.get("language", "ja")
            }
            
            logger.info(f"  ✅ Duration: {transcript_data['duration']}s, Segments: {transcript_data['num_segments']}")
            
            return transcript_data
            
        except Exception as e:
            logger.error(f"  ❌ Lỗi transcribe {audio_path.name}: {e}")
            raise
    
    def save_transcript(self, transcript: Dict, audio_path: Path) -> None:
        """
        Lưu transcript ra file .txt và .json
        
        Args:
            transcript: Transcript data
            audio_path: Path gốc của file audio
        """
        # Tạo cấu trúc thư mục tương ứng
        relative_path = audio_path.relative_to(self.audio_dir)
        
        if relative_path.parent.name == ".":
            # File mondai chính
            output_subdir = self.output_dir
        else:
            # File question trong thư mục con
            output_subdir = self.output_dir / relative_path.parent
        
        output_subdir.mkdir(exist_ok=True, parents=True)
        
        # Tên file output (bỏ .mp3)
        base_name = audio_path.stem
        
        # Lưu file .txt (chỉ text)
        txt_path = output_subdir / f"{base_name}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript["text"])
        
        # Lưu file .json (full data với timestamps)
        json_path = output_subdir / f"{base_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        
        logger.info(f"  💾 Saved: {txt_path.relative_to(self.output_dir)}")
    
    def generate_all_scripts(self) -> Dict:
        """
        Generate scripts cho tất cả file audio
        
        Returns:
            Statistics dict
        """
        logger.info("\n" + "="*70)
        logger.info("🎬 BẮT ĐẦU TẠO SCRIPTS")
        logger.info("="*70)
        
        # Tìm tất cả file audio
        audio_files = self.find_audio_files()
        
        if not audio_files:
            logger.warning("⚠️  Không tìm thấy file audio nào!")
            return self.stats
        
        # Tạo summary file
        all_transcripts = []
        
        # Process từng file
        for i, audio_path in enumerate(audio_files, 1):
            logger.info(f"\n[{i}/{len(audio_files)}] Processing: {audio_path.relative_to(self.audio_dir)}")
            
            try:
                # Transcribe
                transcript = self.transcribe_file(audio_path)
                
                # Save
                self.save_transcript(transcript, audio_path)
                
                # Add to summary
                all_transcripts.append(transcript)
                
                self.stats["processed_files"] += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to process {audio_path.name}: {e}")
                self.stats["failed_files"] += 1
                continue
        
        # Save summary file
        self._save_summary(all_transcripts)
        
        # Print statistics
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        logger.info("\n" + "="*70)
        logger.info("✨ HOÀN THÀNH!")
        logger.info("="*70)
        logger.info(f"⏱️  Tổng thời gian: {elapsed:.1f}s")
        logger.info(f"📊 Kết quả:")
        logger.info(f"   - Tổng files: {self.stats['total_files']}")
        logger.info(f"   - Thành công: {self.stats['processed_files']}")
        logger.info(f"   - Thất bại: {self.stats['failed_files']}")
        logger.info(f"📁 Output: {self.output_dir.absolute()}")
        logger.info("="*70)
        
        return self.stats
    
    def _save_summary(self, transcripts: List[Dict]) -> None:
        """
        Lưu file summary tổng hợp
        
        Args:
            transcripts: List tất cả transcripts
        """
        summary_path = self.output_dir / "all_transcripts.json"
        
        summary_data = {
            "generated_at": datetime.now().isoformat(),
            "total_files": len(transcripts),
            "whisper_model": self.model.model_name if hasattr(self.model, 'model_name') else "base",
            "transcripts": transcripts
        }
        
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📄 Summary saved: {summary_path}")
        
        # Tạo file README.txt hướng dẫn
        readme_path = self.output_dir / "README.txt"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("🎬 JLPT Audio Scripts\n")
            f.write("="*50 + "\n\n")
            f.write("Cấu trúc thư mục:\n")
            f.write("  - mondai_X.txt/json: Script cho mondai X\n")
            f.write("  - mondai_X_questions/: Scripts cho các câu hỏi trong mondai X\n")
            f.write("    - question_Y.txt: Script text thuần\n")
            f.write("    - question_Y.json: Script với timestamps chi tiết\n\n")
            f.write(f"Tổng số files: {len(transcripts)}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def main():
    """
    Entry point - CLI interface
    """
    parser = argparse.ArgumentParser(
        description="Tạo script tiếng Nhật cho các file audio JLPT đã tách"
    )
    parser.add_argument(
        "--audio-dir",
        default="output/mondai",
        help="Thư mục chứa file audio đã tách (default: output/mondai)"
    )
    parser.add_argument(
        "--output-dir",
        default="output/scripts",
        help="Thư mục output cho scripts (default: output/scripts)"
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )
    
    args = parser.parse_args()
    
    try:
        # Khởi tạo và chạy
        generator = ScriptGenerator(
            audio_dir=args.audio_dir,
            output_dir=args.output_dir,
            whisper_model=args.model
        )
        
        stats = generator.generate_all_scripts()
        
        # Success
        return 0 if stats["failed_files"] == 0 else 1
        
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Lỗi không xác định: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
