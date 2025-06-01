import os
import csv
import datetime
import base64
import uuid
from flask_cors import CORS
from flask import Flask, request, jsonify, send_from_directory
import requests

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = 'uploads'
IMAGE_DIR = os.path.join(UPLOAD_DIR, 'images')
HISTORY_CSV = os.path.join(UPLOAD_DIR, 'history.csv')

# 確保目錄存在
os.makedirs(IMAGE_DIR, exist_ok=True)

# 確保 CSV 檔案存在
if not os.path.exists(HISTORY_CSV):
    with open(HISTORY_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "filename", "label", "status", "uploaded_at", "reviewed_at", "reason"])

# 讀取 CSV 內容
def read_csv():
    with open(HISTORY_CSV, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

# 寫入 CSV 內容
def write_csv(rows):
    with open(HISTORY_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "filename", "label", "status", "uploaded_at", "reviewed_at", "reason"])
        writer.writerows(rows)

# 讀取圖片並轉為 Base64
def get_base64_image(filename):
    filepath = os.path.join(IMAGE_DIR, filename)
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

TARGET_URL = "https://www.kutech.tw:4443/api/MED_page/get_med_cloud"
"https://pharma-cetrlm.tph.mohw.gov.tw/"
@app.route('/upload', methods=['GET'])
def fetch_and_filter_data():
    """
        {
            "name_list": ["med_01", "med_02", "med_03]
        }
    """
    try:
        # 發送 POST 請求
        response = requests.post(TARGET_URL, json={})
        response.raise_for_status()  # 確保請求成功

        # 取得回應內容並確保是字典格式
        data = response.json()
        if not isinstance(data, dict):
            return jsonify({"error": "Response is not a dictionary", "details": data}), 500

        # **確保回應格式正確**
        if "Data" not in data:
            return jsonify({"error": "Missing 'Data' key in response", "details": data}), 500

        # 取得 "Data" 陣列
        data_list = data["Data"]
        # 確保 "Data" 是列表
        if not isinstance(data_list, list):
            return jsonify({"error": "Unexpected response format in 'Data'", "details": data_list}), 500

        # 篩選 "TORW" 為 "中藥" 的 "NAME" 欄位
        names = [f"{item['NAME']}({item['SKDIACODE']})" for item in data_list
                 if isinstance(item, dict)
                 and item.get("TORW") == "中藥"
                 and "飲片" in item.get("NAME", "")
                 and "SKDIACODE" in item]

        set_names = list(set(names))

        print(set(set_names))

        return jsonify({"name_list": names})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

# 1️⃣ 上傳圖片 API
@app.route('/upload', methods=['POST'])
def upload_file():
    """
    {
        "images": [
            {
                "filename": "image file name",
                "label": "cat",
                "file": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
            },
            {
                "filename": "image file name"
                "label": "dog",
                "file": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
            }
        ]
    }
    """
    try:
        data = request.json
        images = data.get("images", [])

        uploaded_files = []
        for img in images:
            file_name = img["filename"]
            label = img["label"]
            file_data = img["file"]

            # 生成唯一檔名
            unique_id = str(uuid.uuid4())[:4]  # 取前 8 碼
            filename = f"{file_name}_{unique_id}.jpg"
            save_path = os.path.join(IMAGE_DIR, filename)

            # 解碼 base64 並儲存圖片
            try:
                image_data = base64.b64decode(file_data)
                with open(save_path, "wb") as f:
                    f.write(image_data)
            except Exception as e:
                return jsonify({"error": f"Invalid base64 data: {str(e)}"}), 400

            uploaded_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 讀取現有 CSV，找出最大 ID
            records = read_csv()
            new_id = str(max([int(r["id"]) for r in records] + [0]) + 1)

            # 新增圖片記錄
            with open(HISTORY_CSV, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([new_id, filename, label, "pending", uploaded_at, "", ""])

            uploaded_files.append({
                "Name": filename,
                "status": "pending",
                "label": label
            })

        return jsonify({"uploaded": uploaded_files}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2️⃣-2 批量審核 API
@app.route('/review', methods=['POST'])
def review_images():
    """
        {
            "reviews": [
                {
                    "filename": "cat_12345678.jpg",
                    "status": "pass"
                },
                {
                    "filename": "bird_11223344.jpg",
                    "status": "fail",
                    "failureReason": "Blurry image"
                }
            ]
        }
    """
    try:
        data = request.json
        reviews = data.get("reviews", [])

        updated_rows = []
        reviewed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_count = 0

        records = read_csv()
        for record in records:
            for review in reviews:
                if record["filename"] == review["filename"] and record["status"] == "pending":
                    record["status"] = review["status"]
                    record["reviewed_at"] = reviewed_at
                    record["reason"] = review.get("customReason", review.get("failureReason", ""))
                    updated_count += 1
            updated_rows.append(list(record.values()))
        write_csv(updated_rows)

        return jsonify({"updated": updated_count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# 2️⃣ 取得待審核圖片 API
@app.route('/review', methods=['GET'])
def get_pending_images():
    """
        {
            "images": [
                {
                    "filename": "cat_12345678.jpg",
                    "label": "cat",
                    "imageData": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
                },
                {
                    "filename": "bird_11223344.jpg",
                    "label": "bird",
                    "imageData": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
                }
            ]
        }
    """
    records = read_csv()
    pending_images = []

    for r in records:
        if r["status"] == "pending":
            image_data = get_base64_image(r["filename"])
            if image_data is None:
                continue  # 若讀取失敗則跳過該圖片

            pending_images.append({
                "filename": r["filename"],
                "label": r["label"],
                "imageData": image_data
            })

    return jsonify({"images": pending_images}), 200

# 3️⃣ 取得歷史紀錄 API
@app.route('/history', methods=['GET'])
def get_history():
    """
    {
        "history": [
            {
                "filename": "bird_11223344.jpg",
                "date": "2025-03-18 12:45:00",
                "status": "pending",
                "label": "bird",
                "imageData": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
            },
            {
                "filename": "fish_99999999.jpg",
                "date": "2025-03-19 09:20:00",
                "status": "fail",
                "label": "fish",
                "imageData": "/9j/4AAQSkZJRgABAQAAAQABAAD...",
                "reason": "Blurry image"
            },
            {
                "filename": "tree_66666666.jpg",
                "date": "2025-03-19 08:30:00",
                "status": "pass",
                "label": "tree",
                "imageData": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
            }
        ]
    }
    """
    start_date = request.args.get("startDate", "")
    end_date = request.args.get("endDate", "")
    status_filter = request.args.get("status", "all")

    records = read_csv()
    history = []

    for r in records:
        if status_filter != "all" and r["status"] != status_filter:
            continue
        if start_date and r["uploaded_at"] < start_date:
            continue
        if end_date and r["uploaded_at"] > end_date:
            continue

        image_data = get_base64_image(r["filename"])
        if image_data is None:
            continue  # 若讀取失敗則跳過該圖片

        entry = {
            "filename": r["filename"],
            "date": r["uploaded_at"],
            "status": r["status"],
            "label": r["label"],
            "imageData": image_data
        }

        # 若圖片被標記為 "fail"，則加入失敗原因
        if r["status"] == "fail":
            entry["reason"] = r["reason"]

        history.append(entry)

    return jsonify({"history": history}), 200


@app.route('/ai_respond', methods=['POST'])
def ai_classifier():
    """
    POST:
        {
            "filename": "image file name"
            "bs64": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
        }

    Return:
        {
            "result": "bird"
        }
    """

@app.route('/ai_respond', methods=['GET'])
def ai_classifier():
    """
        {
            "list": ["med_01", "med_02", "med_03]
        }
    """


@app.route('/ai_respond_judge', methods=['POST'])
def ai_classifier():
    """
    POST:
        {
            "judgment": "True/False",
            "label": "bird" # False only
        }
    """

if __name__ == '__main__':
    app.run(debug=True)