import json
import os
import sys

try:
    import cloudinary
    import cloudinary.uploader
except ImportError:
    print("Vui lòng cài: pip install cloudinary")
    sys.exit(1)

# ------------------- DATA PATH -------------------
TIMESTAMPS_FILE = "output_v2/timestamps.json"
LOCAL_AUDIO = "input/jlpt_n2.mp3"  

CLOUD_NAME = "dhhy6drmy" 
PUBLIC_ID = "JLPT_N2_Audio_T7_2025" 
FORMAT = "mp3" 

# Cấu hình credentials của bạn (Lập tức thay thế key)
cloudinary.config(
  cloud_name = CLOUD_NAME, 
  api_key = "",           # <--- THAY BẰNG API KEY CỦA BẠN
  api_secret = "",     # <--- THAY BẰNG API SECRET CỦA BẠN
  secure = True
)

def upload_to_cloudinary():
    """Hàm chạy lưu file audio gốc local lên Cloudinary"""
    if not os.path.exists(LOCAL_AUDIO):
        print(f"Lỗi: Không tìm thấy file gốc tại {LOCAL_AUDIO}")
        return False
        
    print(f"Bắt đầu upload từ {LOCAL_AUDIO}...\n(Vui lòng đợi mạng đẩy lên, có thể kéo dài nếu file nặng)")
    try:
        res = cloudinary.uploader.upload(
            LOCAL_AUDIO, 
            resource_type="video", # Cloudinary yêu cầu resource_type là video cho audio url manipulation!
            public_id=PUBLIC_ID
        )
        print(f"Upload thành công! URL gốc trên Server: {res.get('secure_url')}")
        return True
    except Exception as e:
        print(f"Upload thất bại (Vui lòng kiểm tra lại Api Key/Secret của Cloudinary trong code): {e}")
        return False

def generate_cloudinary_url(cloud_name, public_id, start_time, end_time, format="mp3"):
    return f"https://res.cloudinary.com/{cloud_name}/video/upload/so_{start_time}/eo_{end_time}/{public_id}.{format}"

def test_generate_urls():
    print(f"\n--- Generate Sub-URL từ {TIMESTAMPS_FILE} ---")
    if not os.path.exists(TIMESTAMPS_FILE):
        return
    try:
        with open(TIMESTAMPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for mondai in data.get("mondai", []):
            m_num = mondai.get("mondai_number")
            print(f"\n[ Mondai {m_num} ]")
            for q in mondai.get("questions", []):
                q_num = q.get("question_number")
                q_st = q.get("start_time")
                q_en = q.get("end_time")
                
                if q_st is not None and q_en is not None:
                    q_url = generate_cloudinary_url(CLOUD_NAME, PUBLIC_ID, q_st, q_en, FORMAT)
                    print(f"  - Câu {q_num} ({q_st}s -> {q_en}s):\n    {q_url}")
            break
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    # Bước 1: Gọi hàm Upload file input/jlpt_n2.mp3
    success = upload_to_cloudinary()
    
    # Bước 2: In URL test (mặc định luôn hiển thị để bạn test link sau khi nó upload thành công)
    if success:
        print("\n👇 ĐƯỜNG LINK CẮT SẴN (Nhấn vào test sau khi upload báo thành công) 👇")
    test_generate_urls()
