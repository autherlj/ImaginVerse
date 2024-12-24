import os
import requests
from flask import Blueprint, request, jsonify, render_template, Response
from werkzeug.utils import secure_filename

# 创建蓝图
app = Blueprint('app', __name__, template_folder='../templates')

# 配置上传文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/workflows/run', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return render_template('index.html', error="请选择要上传的文件")
    
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error="请选择要上传的文件")

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            # 确保上传目录存在
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(filepath)
            
            # 准备文件信息
            file_info = {
                'path': filepath,
                'name': filename,
                'type': file.content_type
            }
            
            # 上传文件
            file_id = upload_file(file_info, request.form.get('user', 'default_user'))
            if not file_id:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return render_template('index.html', error="文件上传失败")

            # 获取表单数据
            platform = request.form.get('platform', '')
            style = request.form.get('style', '')
            description = request.form.get('description', '')
            user = request.form.get('user', 'default_user')

            print(f"Starting workflow with parameters:")
            print(f"Platform: {platform}")
            print(f"Style: {style}")
            print(f"Description: {description}")
            print(f"User: {user}")
            print(f"File ID: {file_id}")

            # 运行工作流
            def generate():
                workflow_url = "http://1.14.95.70/v1/workflows/run"
                headers = {
                    "Authorization": "Bearer app-gGcvdsKxglvBwWBowPDvlQAg",
                    "Content-Type": "application/json"
                }

                inputs = {
                    "images": {
                        "transfer_method": "local_file",
                        "upload_file_id": file_id,
                        "type": "image"
                    },
                    "platform": platform,
                    "style": style,
                    "description": description
                }

                data = {
                    "inputs": inputs,
                    "response_mode": "streaming",
                    "user": user
                }

                print(f"Sending request to workflow API...")
                print(f"Request data: {data}")

                try:
                    with requests.post(workflow_url, headers=headers, json=data, stream=True) as response:
                        print(f"Workflow API response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            print("Starting to stream response...")
                            for line in response.iter_lines():
                                if line:
                                    line = line.decode('utf-8')
                                    print(f"Received line: {line}")
                                    if line.startswith('data: '):
                                        data = line[6:]
                                        yield f"data: {data}\n\n"
                        else:
                            print(f"Error response from workflow API: {response.text}")
                            error_message = response.json().get('message', '未知错误')
                            yield f"data: {{'error': '{error_message}'}}\n\n"
                except Exception as e:
                    print(f"Exception in generate: {str(e)}")
                    yield f"data: {{'error': '{str(e)}'}}\n\n"

                print("Finished streaming response")

            # 删除临时文件
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Warning: Failed to remove temporary file: {e}")

            print("Starting SSE response")
            return Response(generate(), mimetype='text/event-stream')
            
        except Exception as e:
            print(f"Exception in main handler: {str(e)}")
            # 确保在发生错误时也能清理临时文件
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            return render_template('index.html', error=f"处理请求时发生错误: {str(e)}")

def upload_file(file, user):
    upload_url = "http://1.14.95.70/v1/files/upload"
    headers = {
        "Authorization": "Bearer app-gGcvdsKxglvBwWBowPDvlQAg",
    }

    try:
        print("Uploading file...")
        with open(file['path'], 'rb') as f:
            files = {
                'file': (file['name'], f, file['type'])
            }
            data = {
                "user": user,
                "type": "image"  # 修改为 image 类型
            }

            response = requests.post(upload_url, headers=headers, files=files, data=data)
            print(f"Upload response status: {response.status_code}")
            print(f"Upload response content: {response.text}")
            
            if response.status_code == 201:
                print("File uploaded successfully")
                return response.json().get("id")
            else:
                print(f"File upload failed, status code: {response.status_code}")
                print(f"Response content: {response.text}")
                return None

    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return None

def run_workflow(file_id, user, response_mode="streaming"):
    workflow_url = "http://1.14.95.70/v1/workflows/run"
    headers = {
        "Authorization": "Bearer app-gGcvdsKxglvBwWBowPDvlQAg",
        "Content-Type": "application/json"
    }

    # 从表单中获取平台、风格和描述信息
    platform = request.form.get('platform', '')
    style = request.form.get('style', '')
    description = request.form.get('description', '')

    print(f"Received form data - platform: {platform}, style: {style}, description: {description}")

    # 构建输入参数
    inputs = {
        "images": {  # 使用复数形式 "images"
            "transfer_method": "local_file",
            "upload_file_id": file_id,
            "type": "image"
        },
        "platform": platform,
        "style": style,
        "description": description
    }

    data = {
        "inputs": inputs,
        "response_mode": response_mode,
        "user": user
    }

    try:
        print("Running workflow...")
        print(f"Request data: {data}")
        response = requests.post(workflow_url, headers=headers, json=data)
        print(f"Workflow response status: {response.status_code}")
        print(f"Workflow response content: {response.text}")
        
        if response.status_code == 200:
            print("Workflow executed successfully")
            return response.json()
        else:
            error_message = response.json().get('message', '未知错误')
            print(f"Workflow execution failed: {error_message}")
            return {"status": "error", "message": error_message}
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {"status": "error", "message": str(e)}