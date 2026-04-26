import os
import sys
import urllib.request
from pathlib import Path

def download_models():
    print("🚀 Đang khởi tạo quá trình tải model cho Style-Bert-VITS2...")
    
    try:
        from tqdm import tqdm
    except ImportError:
        print("❌ Lỗi: Chưa cài đặt 'tqdm'. Hãy chạy: pip install tqdm")
        sys.exit(1)

    # Thư mục models cục bộ nằm cùng cấp với file script này (để Docker map vào /app/models)
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Danh sách các model giọng tiếng Nhật chuyên dụng cho JLPT
    model_configs = {
        # --- NHÓM GIỌNG NỮ (FEMALE) ---
        "jvnv-F1-jp": { # Nữ chuẩn (Giáo viên / Nhân viên văn phòng)
            "repo": "litagin/style_bert_vits2_jvnv",
            "files": ["jvnv-F1-jp/jvnv-F1-jp_e160_s14000.safetensors", "jvnv-F1-jp/config.json", "jvnv-F1-jp/style_vectors.npy"]
        },
        "jvnv-F2-jp": { # Nữ trầm (Giọng phụ nữ lớn tuổi, bình tĩnh)
            "repo": "litagin/style_bert_vits2_jvnv",
            "files": ["jvnv-F2-jp/jvnv-F2_e166_s20000.safetensors", "jvnv-F2-jp/config.json", "jvnv-F2-jp/style_vectors.npy"]
        },
        "hamidashi-asu": { # Nữ anime học sinh (Năng động JLPT N4)
            "repo": "him1920212/style-bert-vits2-hamidashi",
            "files": ["asu/asu_e100_s28700.safetensors", "asu/config.json", "asu/style_vectors.npy"]
        },
        "jp-extra-amazing": { # Nữ trẻ xinh (Giọng dễ thương JLPT N3)
            "repo": "Mofa-Xingche/girl-style-bert-vits2-JPExtra-models",
            "files": ["NotAnimeJPManySpeaker_e120_s22200.safetensors", "config.json", "style_vectors.npy"]
        },

        # --- NHÓM GIỌNG NAM (MALE) ---
        "jvnv-M1-jp": { # Nam chuẩn (Thanh niên / Nhân viên nam)
            "repo": "litagin/style_bert_vits2_jvnv",
            "files": ["jvnv-M1-jp/jvnv-M1-jp_e158_s14000.safetensors", "jvnv-M1-jp/config.json", "jvnv-M1-jp/style_vectors.npy"]
        },
        "jvnv-M2-jp": { # Nam trầm (Sếp nam / Người già)
            "repo": "litagin/style_bert_vits2_jvnv",
            "files": ["jvnv-M2-jp/jvnv-M2-jp_e159_s17000.safetensors", "jvnv-M2-jp/config.json", "jvnv-M2-jp/style_vectors.npy"]
        },
        "jp-extra-cool-young": { # Bé trai trẻ (Giọng cool trẻ con JLPT N5)
            "repo": "RikkaBotan/style_bert_vits2_jp_extra_cool_original",
            "files": ["rikka_botan_cool.safetensors", "config.json", "style_vectors.npy"]
        },
        "myvoiceclone-male": { # Nam trung niên (Giọng Clone Jun)
            "repo": "ThePioneer/MyVoiceClone-Style-Bert-VITS2",
            "files": ["jun_e200_s10600.safetensors", "config.json", "style_vectors.npy"]
        }
    }

    # Hàm tải file có thanh tiến trình
    def download_file(url, dest_path):
        class DownloadProgressBar(tqdm):
            def update_to(self, b=1, bsize=1, tsize=None):
                if tsize is not None:
                    self.total = tsize
                self.update(b * bsize - self.n)

        with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=os.path.basename(dest_path)) as t:
            urllib.request.urlretrieve(url, filename=dest_path, reporthook=t.update_to)

    for folder, info in model_configs.items():
        print(f"\n📂 Đang kiểm tra model: {folder}")
        target_subfolder = models_dir / folder
        target_subfolder.mkdir(parents=True, exist_ok=True)

        for file_path in info["files"]:
            filename_only = os.path.basename(file_path)
            local_file = target_subfolder / filename_only

            if local_file.exists():
                print(f"  ✅ Đã có: {filename_only}")
                continue

            print(f"  ⬇️ Đang tải: {filename_only}...")
            url = f"https://huggingface.co/{info['repo']}/resolve/main/{file_path}"
            
            try:
                # Đặt header user-agent để tránh bị chặn
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    # Kiểm tra xem file có thực sự tồn tại (đôi khi hf trả về 404 HTML)
                    if response.status != 200:
                        raise Exception(f"HTTP Error {response.status}")
                        
                download_file(url, local_file)
            except Exception as e:
                print(f"  ❌ Lỗi khi tải {filename_only} (Từ URL: {url}): {e}")

    print("\n" + "="*50)
    print("✅ HOÀN TẤT CẬP NHẬT MODEL!")
    print(f"📍 Vị trí: {models_dir.absolute()}")
    print("🎭 Các giọng đã sẵn sàng cho hệ thống JLPT của bạn.")
    print("="*50)

if __name__ == "__main__":
    download_models()
