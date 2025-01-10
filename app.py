from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, session,make_response, flash
import sqlite3
from flask_cors import CORS
from auth import register_user, login_user
from database import init_db
from google.cloud import storage
from gradio_client import client
import tempfile
import replicate
import os
import time

import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app, resources={r"/*": {"origins": "*"}})
#client = Client("http://localhost:9872/")  # Gradio 的 API 地址


bucket_name = "store-ytes"
replicate.api_token = "r8_TnP2dK3lp3f5YVzJXutLajln4OV93le043KAy"
service_account_path = "./causal-destiny-425314-p0-66dbfdd6260e.json"
                       
# 預設的 LoRA 模型 ID
lora_model = "ostris/flux-dev-lora-trainer"  # LoRA 模型的 ID


# 初始化資料庫
init_db()


# 假设数据库连接是这样建立的
db = sqlite3.connect('audiobook.db')  # 使用您的数据库文件路径
cursor = db.cursor()

@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    return response
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # 获取用户输入并进行简单的校验
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return jsonify({"message": "用户名或密码不能为空"}), 400

        try:
            # 连接数据库
            conn = sqlite3.connect("audiobook.db")
            cursor = conn.cursor()

            # 检查用户是否已存在
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return jsonify({"message": "用户名已存在"}), 400

            # 插入新用户到数据库
            role = 'user'  # 明确赋值角色
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            conn.commit()  # 提交事务
            user_id = cursor.lastrowid  # 获取新用户的 ID
            session['user_id'] = user_id
            session['username'] = username

            # 注册成功后重定向到登录页面
            print(f"New user {username} registered successfully.")
            return redirect(url_for("login"))

        except Exception as e:
            return jsonify({"message": f"注册失败: {str(e)}"}), 500
        finally:
            conn.close()

    # 如果是 GET 请求，渲染注册页面
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if 'user_id' in session:
        print("User is already logged in. Redirecting to home...")
        return redirect(url_for('menu'))  # 如果已登入，重定向到 home 頁面
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = login_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[3]

            if user[3] == "admin":
                print(f"User logged in: {username}, Role: {user[3]}")
                print(url_for("admin_dashboard"))
                return redirect(url_for("admin_dashboard"))  # 管理員跳轉
            else:
                print(f"User logged in: {username}, Role: {user[3]}")
                return redirect(url_for("menu"))  # 普通用戶跳轉
            
        # 登入失败时传递错误信息
        return jsonify({"error": "用户名或密碼錯誤！"}), 400
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for("intro"))

@app.route("/admin_dashboard")
def admin_dashboard():
    if 'user_id' in session:
        username = session['username']

        # 连接数据库并获取训练记录
        conn = sqlite3.connect('audiobook.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trainings")  # 查询所有训练记录
        trainings = cursor.fetchall()  # 获取所有记录
        conn.close()

        # 渲染 admin_dashboard.html，并传递训练记录和用户名
        return render_template('admin_dashboard.html', username=username, trainings=trainings)
    else:
        # 如果用户未登录，重定向到登录页面
        return redirect(url_for('login'))



@app.route('/')
def intro():
    # 渲染故事線引導頁面
    return render_template('intro.html')

@app.route('/menu')
def menu():
    if 'user_id' in session:
        username = session['username']
        user_role = session.get('role')  # 取得用戶的角色

        # 如果是 admin，重定向到 admin_dashboard
        if user_role == 'admin':
            return redirect(url_for('admin_dashboard'))
        
        # 如果是普通用戶，渲染 menu 頁面
        return render_template('menu.html', username=username)
    
    # 如果用户未登录，直接重定向到登录页面
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' in session:
        username = session['username']
        # 渲染 train.html 并将 username 传递给模板
        return render_template('home.html', username=username)
    else:
        # 如果用户未登录，可以重定向到登录页面
        return redirect(url_for('login'))

@app.route('/train')
def train():
    if 'user_id' in session:
        username = session['username']
        # 渲染 train.html 并将 username 传递给模板
        return render_template('train.html', username=username)
    else:
        # 如果用户未登录，可以重定向到登录页面
        return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'user_id' in session:
        username = session['username']
        # 渲染 train.html 并将 username 传递给模板
        return render_template('index.html', username=username)
    else:
        # 如果用户未登录，可以重定向到登录页面
        return redirect(url_for('login'))

@app.route('/voice')
def voice():
    if 'user_id' in session:
        username = session['username']
        # 渲染 train.html 并将 username 传递给模板
        return render_template('voice.html', username=username)
    else:
        # 如果用户未登录，可以重定向到登录页面
        return redirect(url_for('login'))

def upload_to_gcs(file):
    client = storage.Client.from_service_account_json(service_account_path)
    bucket = client.bucket(bucket_name)
    
    original_file_name = file.filename  # 這會獲取上傳文件的檔名

    # 如果需要，您可以添加一些檢查來確保檔名的唯一性
    # 例如：在檔名中添加時間戳或其他識別符
    file_name = original_file_name  # 使用原始檔名
    blob = bucket.blob(file_name)
    blob.upload_from_file(file)
    
    return f"https://storage.googleapis.com/{bucket_name}/{file_name}"

trainings = {}

@app.route('/upload', methods=['POST'])
def upload_file():

    if 'user_id' not in session:
        return jsonify({"message": "請先登入"}), 401  # 用戶未登入返回錯誤
    
    user_id = session.get('user_id', None)
    file = request.files['file']
    target = request.form.get('id')
    trigger_word = request.form.get("triggerWord")
    autocaption_prefix = request.form.get("autocaptionPrefix")

    version = "待更改"  # 固定的版本號，或者根據需求動態設置

    if file:
        file_url = upload_to_gcs(file)
        
        try:
            training = replicate.trainings.create(
                model="ostris/flux-dev-lora-trainer",
                version="e440909d3512c31646ee2e0c7d6f6f4923224863a6a10c494606e79fb5844497",
                destination="ytes10419/lewis",
                input={
                    "steps": 1000,
                    "lora_rank": 16,
                    "optimizer": "adamw8bit",
                    "batch_size": 1,
                    "resolution": "512,768,1024",
                    "autocaption": True,
                    "input_images": file_url,
                    "trigger_word": trigger_word,
                    "learning_rate": 0.0004,
                    "wandb_project": "flux_train_replicate",
                    "autocaption_prefix": autocaption_prefix,
                    "wandb_save_interval": 100,
                    "caption_dropout_rate": 0.05,
                    "cache_latents_to_disk": False,
                    "wandb_sample_interval": 100,
                }
            )
             # 抓取训练 ID
            training_id = training.id

            if user_id:
                save_training_data(target, training_id, version, user_id)


            return jsonify({"message": "訓練啟動成功", "training_id": training_id ,"target": target}), 200
        
        except Exception as e:
            return jsonify({"message": f"訓練啟動失敗: {str(e)}"}), 500
    else:
        return jsonify({"message": "請提供 ZIP 檔案"}), 400


@app.route("/update_training", methods=["POST"])
def update_training():
    if 'user_id' in session:
        # 获取表单数据
         # 获取提交的表单数据
        ids = request.form.getlist('id[]')
        training_ids = request.form.getlist('training_id[]')
        targets = request.form.getlist('target[]')
        versions = request.form.getlist('version[]')
        user_ids = request.form.getlist('user_id[]')

        # 连接到数据库
        conn = sqlite3.connect('audiobook.db')
        cursor = conn.cursor()

        # 更新每一条记录
        for i in range(len(ids)):
            cursor.execute('''
            UPDATE trainings 
            SET training_id = ?, target = ?, version = ?, user_id = ? 
            WHERE id = ?
        ''', (training_ids[i], targets[i], versions[i], user_ids[i], ids[i]))

        # 提交更改并关闭连接
        conn.commit()
        conn.close()

        return redirect(url_for('admin_dashboard'))  # 更新后返回到首页
    else:
        # 如果用户未登录，重定向到登录页面
        return redirect(url_for('login'))




def save_training_data(target, training_id, version, user_id):
    try:
        # 連接到 SQLite 資料庫
        conn = sqlite3.connect('audiobook.db')
        cursor = conn.cursor()

        # 插入訓練數據到 'trainings' 表
        cursor.execute('''
            INSERT INTO trainings (target, training_id, version, user_id)
            VALUES (?, ?, ?, ?)
        ''', (target, training_id, version, user_id))

        # 提交更改並關閉連接
        conn.commit()
        print("訓練數據儲存成功")
    except Exception as e:
        print(f"儲存訓練數據時出錯: {str(e)}")
    finally:
        conn.close()

# 設定上傳目錄
UPLOAD_FOLDER = 'static/uploaded_wav/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 確保目錄存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# 設定上傳目錄
UPLOAD_FOLDER = 'static/uploaded_wav/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 確保目錄存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)




@app.route('/generate', methods=['POST'])
def generate():
    # 从 session 中获取用户名
    username = session.get('username')

    # 检查用户名是否存在
    if not username:
        return jsonify({"message": "使用者未登入"}), 401
    
    user_id = session['user_id']
    target = request.form['target']  # 从表单获取 target 名称

    # 从数据库查询对应的模型版本
    try:
        conn = sqlite3.connect('audiobook.db')
        cursor = conn.cursor()

        # 查询模型信息
        cursor.execute('''
            SELECT version FROM trainings
            WHERE target = ? AND user_id = ?
        ''', (target, user_id))
        result = cursor.fetchone()

        if not result:
            return jsonify({"message": "找不到與該 target 對應的模型"}), 404
        
        model = result[0]  # 获取模型版本
    except Exception as e:
        return jsonify({"message": f"讀取模型資料失敗: {str(e)}"}), 500
    finally:
        conn.close()


    prompt = request.form['prompt']
    story = request.form['story']

    # 獲取其他參數（省略默認值代碼，與原來一致）
    lora_scale = float(request.form.get('lora_scale', 0.5))
    guidance_scale = float(request.form.get('guidance_scale', 7.5))
    num_inference_steps = int(request.form.get('num_inference_steps', 50))
    num_outputs = int(request.form.get('num_outputs', 1))
    aspect_ratio = request.form.get('aspect_ratio', '1:1')

    # 上傳音檔
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        # 呼叫 Replicate API 生成圖像
        output = replicate.run(
            model,
            input={
                "prompt": prompt,
                "lora_scale": lora_scale,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps,
                "num_outputs": num_outputs,
                "aspect_ratio": aspect_ratio
            }
        )
        if output and isinstance(output, list):
            image_url = output[0]

            # 檢查 image 資料夾是否存在，若不存在則創建
            image_folder = "static/image"
            if not os.path.exists(image_folder):
                os.makedirs(image_folder)

            # 下載圖片
            response = requests.get(image_url)
            if response.status_code == 200:
                # 將下載的圖片讀取為二進制流
                image = Image.open(BytesIO(response.content))

                timestamp = int(time.time())
                image_name = os.path.join(image_folder, f"output_image_{timestamp}.jpg")
                image = image.convert("RGB")  # 確保圖片格式為 RGB
                image.save(image_name, "JPEG")
                image_url = f"/static/image/output_image_{timestamp}.jpg"

                print(f"圖片已成功儲存為 {image_name}")
            else:
                print(f"無法下載圖片，HTTP 狀態碼: {response.status_code}")

            try:
                conn = sqlite3.connect("audiobook.db")
                cursor = conn.cursor()

                # 获取当前用户的最大 page_number
                cursor.execute('''
                SELECT MAX(page_number) FROM pages WHERE user_id = ?
                ''', (user_id,))
                max_page_number = cursor.fetchone()[0]
    
                # 如果没有记录，设置 page_number 为 1
                page_number = (max_page_number or 0) + 1

                cursor.execute('''
                    INSERT INTO pages (title, content, audio_file,image_url ,page_number, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (prompt, story, file.filename, image_url, page_number,user_id))
            
                conn.commit()

            except Exception as db_error:
                return jsonify({"message": f"資料庫儲存失敗: {str(db_error)}"}), 500
            finally:
                conn.close()

            # 跳轉到新生成的頁面（使用 page_id 作為參數）
            return redirect(url_for('story', username=username, page_number=page_number))
        else:
            return jsonify({"message": "圖像生成失敗，請重試"}), 500

    except Exception as e:
        print(f"Image generation failed: {str(e)}")
        return jsonify({"message": f"Image generation failed: {str(e)}"}), 500

    

@app.route('/story/<username>/<int:page_number>')
def story(username, page_number):
    try:
    # 確認使用者存在
        conn = sqlite3.connect("audiobook.db")
        cursor = conn.cursor()
         # 確認使用者是否存在
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_result = cursor.fetchone()
        if not user_result:
            return jsonify({"message": "找不到該使用者"}), 404
        user_id = user_result[0]

        cursor.execute('''
            SELECT title, content, audio_file, image_url, page_number,user_id FROM pages
            WHERE user_id= ? AND page_number = ?
        ''', (user_id, page_number))
        page = cursor.fetchone()
    
        if not page:
            # 使用 JavaScript 实现 alert 和跳转
            response = make_response("""
            <script>
                alert("快去生成屬於你的有聲書吧!!!");
                window.location.href = "{}";
            </script>
            """.format(url_for('menu')))
            return response
        
        column_names = [column[0] for column in cursor.description]
        page_data = dict(zip(column_names, page))

        cursor.execute('''
            SELECT page_number FROM pages WHERE user_id = ? AND page_number < ? ORDER BY page_number DESC LIMIT 1
        ''', (user_id, page_number))
        prev_page = cursor.fetchone()

        cursor.execute('''
            SELECT page_number FROM pages WHERE user_id = ? AND page_number > ? ORDER BY page_number ASC LIMIT 1
        ''', (user_id, page_number))
        next_page = cursor.fetchone()

        prev_page_number = prev_page[0] if prev_page else None
        next_page_number = next_page[0] if next_page else None

            # 返回頁面數據（可以是渲染模板或 JSON）
        return render_template(
                    'story.html',
                    page_data=page_data,
                    page_number=page_number,
                    prev_page_number=prev_page_number,
                    next_page_number=next_page_number,
                    username=username
                    )

    except Exception as e:
        
        return jsonify({"message": f"讀取頁面失敗: {str(e)}"}), 500
    finally:
        conn.close()

# 刪除指定頁面的路由
@app.route('/delete_page/<int:page_number>', methods=['POST'])
def delete_page(page_number):
    print(f"收到的頁面編號: {page_number}")
    username = session.get('username')  # 假设用户名存储在会话中
    try:
        # 连接数据库
        conn = sqlite3.connect("audiobook.db")
        cursor = conn.cursor()


        # 查询用户 ID
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_result = cursor.fetchone()
        if not user_result:
            return jsonify({"message": "找不到該使用者"}), 404
        user_id = user_result[0]

        # 查询该页面是否存在
        cursor.execute("SELECT * FROM pages WHERE user_id = ? AND page_number = ?", (user_id, page_number))
        page = cursor.fetchone()

        if not page:
            return jsonify({"message": "找不到該頁面"}), 404

        # 如果该页面存在，删除页面记录
        cursor.execute("DELETE FROM pages WHERE user_id = ? AND page_number = ?", (user_id, page_number))


        # 重新分配页面 ID
        cursor.execute("""
            UPDATE pages
            SET page_number = page_number - 1
            WHERE user_id = ? AND page_number > ?
        """, (user_id, page_number))
        conn.commit()

        # 如果有音频文件，删除服务器上的文件
        audio_file = page[3]  # 假设音频文件路径在第4列
        audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file)
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

         # 查询剩余页面数量
        cursor.execute("SELECT page_number FROM pages  WHERE user_id = ? ORDER BY page_number", (user_id,))
        remaining_pages = cursor.fetchall()


        # 计算重定向 URL
        if not remaining_pages:
            redirect_url = url_for('menu')  # 如果没有剩余页面，返回首页
        else:
            # 找到前一页或下一页的 ID
            if page_number > remaining_pages[-1][0]:
                new_page_number = remaining_pages[-1][0]  # 最后一页
            else:
                new_page_number = page_number  # 下一页
            redirect_url = url_for('story', page_number=new_page_number, username=username)

        # 返回成功消息
        return jsonify({"message": "頁面刪除成功","redirect_url": redirect_url}), 200

    except Exception as e:
        # 捕获错误并返回
        return jsonify({"message": f"刪除頁面時發生錯誤: {str(e)}"}), 500

    finally:
        conn.close()
    

@app.route('/api/generate', methods=['POST'])
def generate_voice():
    try:
        text = request.form['text']
        language = request.form['language']
        ref_audio = request.files['ref_audio']

        audio_data = ref_audio.read()
        result = client.predict(
            text, audio_data, language, api_name="/generate"
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(result)
            audio_path = temp_audio.name

        response = make_response(jsonify({"audio_url": audio_path}))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    finally:
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.remove(audio_path)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    init_db()  # 確保資料庫和表格已經創建
    app.run(debug=True)
