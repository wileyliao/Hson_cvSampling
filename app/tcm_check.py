from flask import Flask, jsonify
import requests
import json  # 用於解析 JSON 字串

app = Flask(__name__)

# 目標 API


TARGET_URL = "https://www.kutech.tw:4443/api/MED_page/get_med_cloud"
@app.route('/', methods=['GET'])
def fetch_and_filter_data():
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
        print(data)

        # 確保 "Data" 是列表
        if not isinstance(data_list, list):
            return jsonify({"error": "Unexpected response format in 'Data'", "details": data_list}), 500

        # 篩選 "TORW" 為 "中藥" 的 "NAME" 欄位
        names = [item["NAME"] for item in data_list if isinstance(item, dict) and item.get("TORW") == "中藥"]

        return jsonify({"name_list": names})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
