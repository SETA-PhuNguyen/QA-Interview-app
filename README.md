# QA & SDET Interview Coach

Ứng dụng luyện phỏng vấn QA/SDET sử dụng Gemini để đặt câu hỏi và đánh giá câu trả lời.

## Yêu cầu

- Windows và Python 3.
- Gemini API key.

## Cài đặt lần đầu

Mở PowerShell và chạy:

```powershell
git clone <URL-repository>
cd qa-interview-app

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Tạo file `.env` ở thư mục gốc của dự án, rồi thêm API key:

```text
GEMINI_API_KEY=your_api_key_here
```

Không chia sẻ hoặc commit file `.env` lên Git.

## Chạy ứng dụng

Trong PowerShell, tại thư mục dự án:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ứng dụng sẽ mở trong trình duyệt. Để dừng ứng dụng, nhấn `Ctrl+C` trong PowerShell.

## Cập nhật sau khi pull code mới

Trong thư mục dự án, chạy:

```powershell
git pull
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Nếu `requirements.txt` không thay đổi, thường có thể bỏ qua bước cài thư viện và chạy thẳng ứng dụng.

## Dữ liệu cá nhân

Lịch sử câu hỏi và câu trả lời được lưu trong `assistant_history.json` trên máy của bạn. File này được bỏ qua khi push lên Git để tránh chia sẻ dữ liệu cá nhân.
