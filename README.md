[TOC]

# 接口文档（0.1）

## 项目简介

五音疗愈音乐生成器是一个基于 Django 和 MusicGen AI 模型的音乐生成平台。系统支持**中英文双语输入**，能够根据用户的文字描述自动生成独特的音乐作品。

### 核心特性

- 🎵 **AI 音乐生成**：基于 Facebook 的 MusicGen 模型，生成高质量音乐
- 🌏 **中文支持**：自动检测中文输入并翻译成英文，无需手动翻译
- ⚡ **实时处理**：流式响应，快速生成音乐文件
- 🎨 **可视化界面**：美观的音频可视化效果
- 📦 **多格式支持**：支持 WAV 和 MP3 格式输出

### 中文翻译功能

系统集成了自动翻译功能，当您使用中文描述音乐时：

1. **自动检测**：系统自动识别输入语言（中文、英文等）
2. **智能翻译**：中文描述自动转换为英文
3. **透明处理**：翻译过程对用户完全透明，无需额外操作
4. **英文直通**：如果输入已是英文，直接使用，不会重复翻译

**使用示例：**
- ✅ "浪漫的钢琴旋律，轻柔的弦乐背景" → 自动翻译并生成
- ✅ "欢快的电子舞曲，强烈的贝斯线" → 自动翻译并生成
- ✅ "Romantic piano melody" → 直接使用，无需翻译

### 技术栈

- **后端框架**：Django 5.2.2 + Django REST Framework
- **AI 模型**：AudioCraft MusicGen (Facebook)
- **翻译服务**：deep-translator + langdetect
- **音频处理**：PyTorch + TorchAudio

### 快速开始

#### 1. 环境准备

```bash
# 克隆项目
cd /home/ubuntu/health/music_h

# 激活虚拟环境
source ../env/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 启动服务

```bash
# 运行开发服务器
python manage.py runserver

# 访问音乐生成器
# 浏览器打开: http://localhost:8000/api/generate/
```

#### 3. 使用中文生成音乐

在音乐生成器页面输入中文描述即可，例如：
- "宁静的冥想音乐，舒缓放松"
- "热情的拉丁舞曲，充满活力"
- "悲伤的小提琴独奏，深情款款"

## 项目结构

```
├── manage.py
├── music_h
│   ├── __init__.py
│   ├── __pycache__
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── music_h_app
    ├── __init__.py
    ├── admin.py
    ├── api   (api的类视图)
    │   └── auth_view.py
    │   └── music_generator_view.py
    |   └── stu_view.py
    |   └── ...
    ├── utils.py   (封装好的组件)
    ├── apps.py
    ├── migrations
    ├── models.py   (实体类定义)
    ├── serializers.py   (序列化器)
    ├── tests.py
    └── views.py
```

todos：

- 用户信息尚且不清楚包含哪些内容
- 鉴权部分待完善（后续加入jwt？）
- 用户修改密码等部分需要添加


## 0. 音乐生成板块

### (1) 音乐生成页面

**访问音乐生成器界面**

- **URL:** `/api/generate/`
- **Method:** `GET`
- **权限：** 无

**功能说明：**
返回音乐生成器的 HTML 页面，用户可以通过界面输入描述生成音乐。

**支持中英文输入：**
- 中文描述会自动翻译成英文后生成音乐
- 英文描述直接使用，不进行翻译
- 翻译过程完全自动，用户无需关心

**页面特性：**
- 实时音频可视化效果
- 支持 5-120 秒时长设置
- WAV/MP3 格式选择
- 音频在线播放和下载

---

### (2) 音乐生成 API

**根据文本描述生成音乐**

- **URL:** `/api/generate/`
- **Method:** `POST`
- **权限：** 无
- **Content-Type:** `application/json`

**请求参数**

| 参数名     | 类型   | 必填 | 默认值 | 描述                           |
| ---------- | ------ | ---- | ------ | ------------------------------ |
| `prompt`   | string | 是   | -      | 音乐描述（支持中英文）         |
| `duration` | int    | 否   | 30     | 音乐时长（秒），最大 120 秒    |
| `format`   | string | 否   | mp3    | 音频格式：`wav` 或 `mp3`       |

**请求示例**

```json
{
    "prompt": "浪漫的钢琴旋律，轻柔的弦乐背景",
    "duration": 15,
    "format": "mp3"
}
```

或使用英文：

```json
{
    "prompt": "Romantic piano melody with soft string background",
    "duration": 15,
    "format": "mp3"
}
```

**响应说明**

成功时返回音频文件流（二进制数据）

**响应头**

| 响应头名称              | 描述                                |
| ----------------------- | ----------------------------------- |
| `Content-Type`          | `audio/mpeg` 或 `audio/wav`         |
| `Content-Disposition`   | `attachment; filename="音乐文件名"` |
| `X-Audio-Duration`      | 音频时长（秒）                      |
| `X-Original-Prompt`     | 原始输入描述                        |
| `X-Translated-Prompt`   | 翻译后的英文描述（如有翻译）        |
| `X-Was-Translated`      | 是否进行了翻译（true/false）        |

**成功响应 (200 OK)**

返回音频文件的二进制流，可直接下载或播放。

**错误响应**

- **400 Bad Request** - 参数验证失败
```json
{
    "prompt": ["此字段是必填项。"],
    "duration": ["请确保该值小于或等于 120。"]
}
```

- **500 Internal Server Error** - 生成失败
```json
{
    "error": "Music generation failed",
    "details": "错误详情"
}
```

**使用示例 (cURL)**

```bash
# 中文示例
curl -X POST http://localhost:8000/api/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "欢快的爵士乐，轻松愉快",
    "duration": 20,
    "format": "mp3"
  }' \
  --output music.mp3

# 英文示例
curl -X POST http://localhost:8000/api/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Upbeat jazz music, light and cheerful",
    "duration": 20,
    "format": "mp3"
  }' \
  --output music.mp3
```

**使用示例 (Python)**

```python
import requests

# 中文描述
response = requests.post(
    'http://localhost:8000/api/generate/',
    json={
        'prompt': '宁静的冥想音乐',
        'duration': 30,
        'format': 'mp3'
    }
)

# 保存音频文件
with open('meditation_music.mp3', 'wb') as f:
    f.write(response.content)

# 检查是否进行了翻译
was_translated = response.headers.get('X-Was-Translated')
if was_translated == 'true':
    original = response.headers.get('X-Original-Prompt')
    translated = response.headers.get('X-Translated-Prompt')
    print(f"原始描述: {original}")
    print(f"翻译结果: {translated}")
```

**中文音乐描述示例**

| 中文描述                          | 效果                 |
| --------------------------------- | -------------------- |
| 浪漫的钢琴旋律，轻柔的弦乐背景   | 抒情、温柔           |
| 欢快的电子舞曲，强烈的贝斯线     | 节奏感强、适合运动   |
| 宁静的冥想音乐，舒缓放松         | 适合冥想、睡眠       |
| 激昂的摇滚吉他独奏               | 有力、激情           |
| 80年代复古合成波，电子鼓         | 怀旧、电子           |
| 轻松的爵士钢琴三重奏             | 优雅、轻松           |
| 史诗电影配乐，宏大的管弦乐       | 震撼、史诗感         |
| 热带浩室音乐，海滩氛围           | 轻快、度假感         |

**技术实现细节**

1. **语言检测**：使用 `langdetect` 自动识别输入语言
2. **自动翻译**：通过 `deep-translator` 调用 Google Translate API
3. **模型调用**：使用翻译后的英文描述调用 MusicGen 模型
4. **容错机制**：翻译失败时使用原始输入，不影响生成流程

**注意事项**

- 首次加载模型需要较长时间（约 10-30 秒）
- 生成时间与音乐时长成正比，通常为音乐时长的 2-3 倍
- 中文翻译需要网络连接
- 建议使用专业音乐术语以获得更好的生成效果

---

## 1.大模型API调用板块

### 1.

## 2.鉴权版块

### (1) 用户注册

**用于用户注册**

- **url:** `/api/register/`
- **Method:**`POST`
- **权限：**无

**请求参数**

| 参数名      | 类型   | 必填 | 描述     |
| ----------- | ------ | ---- | -------- |
| `username`  | string | 是   | 用户名   |
| `password`  | string | 是   | 密码     |
| `password2` | string | 是   | 确认密码 |

**响应参数(后续无特殊说明，均采用状态码+响应信息方式)**

| 参数名    | 类型   | 描述     |
| --------- | ------ | -------- |
| `user_id` | string | 用户id   |
| `code`    | int    | 状态码   |
| `message` | string | 响应信息 |

**状态码说明**

- 200 OK 注册成功

- 400 Bad Request 参数缺失等

  ---

### （2） 用户登录

**用于用户登录**

- **URL**: `/api/login/`  
- **Method**: `POST`  
- **权限**: 无  

**请求参数**
| 参数名     | 类型   | 必填 | 描述   |
| ---------- | ------ | ---- | ------ |
| `username` | string | 是   | 用户名 |
| `password` | string | 是   | 密码   |

**响应参数**

| 参数名    | 类型   | 描述     |
| --------- | ------ | -------- |
| `user_id` | string | 用户id   |
| `code`    | int    | 状态码   |
| `message` | string | 响应信息 |

**状态码说明**

- 200 OK 登录成功

- 400 Bad Request 参数缺失或密码错误等

- 404 Not Found 用户不存在

  ---

  ### （3） 用户登录

  **用于用户登出**

  - **URL**: `/api/logout/`  
  - **Method**: `GET`  
  - **权限**: 无  

**无请求参数**

**状态码说明**

- 200 OK 登出成功

- 500 Internal Error 服务器内部错误

  ---

  ## 2.学生板块

  #### 1. 获取学生信息列表

  **获取全部学生信息**

  - **URL**: `/api/students/`  
  - **Method**: `GET`  
  - **权限**: 无  

  **请求参数**

  暂无

  **成功响应 (200 OK)**
```json
{
    "code": 200,
    "message": "学生列表获取成功！",
    "data": []
}
```
  ---

  #### 2. 创建学生信息

  **创建新的学生信息**

  - **URL**: `/api/students/`  
  - **Method**: `POST`  

  **请求参数**
  | 参数名    | 类型   | 必填 | 描述     |
  | --------- | ------ | ---- | -------- |
| `teacher`    | int | 是  | 老师账号的id     |
  | `name`    | string | 是   | 学生名称 |
  | `account` | string | 是   | 学生账号 |
  **请求示例**

  **成功响应 (201 Created)**
  ```json
  {
    "code": 201,
    "message": "学生创建成功！",
    "data": {
        "id": 5,
        "teacher": 1,
        "name": "小黑",
        "account": "ancdakd4"
    }
}
  ```

  **错误响应**
  - **400 Bad Request** (参数验证失败)

  

  ---

  #### 3. 获取学生信息详情

  **获取指定学生的详细信息**

  - **URL**: `/api/students/<int:pk>/`  
  - **Method**: `GET`  
  - **权限**: 无  

  **成功响应 (200 OK)**
  ```json
    {
        "code": 200,
        "message": "学生信息获取成功！",
        "data": {
            "id": 4,
            "teacher": 1,
            "name": "小黑",
            "account": "ancdakd4"
        }
    }
  ```

  **错误响应**
  - **404 Not Found** (学生信息不存在)

  ---

  #### 4. 更新学生信息

  **更新指定学生信息**

  - **URL**: `/api/students/<int:pk>/`  
  - **Method**: `PUT`  
  - **权限**: 暂无

  **请求参数**
  | 参数名    | 类型   | 必填 | 描述         |
  | --------- | ------ | ---- | ------------ |
   | `teacher`    | int | 否   | 老师账号的id     |
  | `name`    | string | 否   | 学生名称     |
  | `account` | string | 否   | 学生游戏账号 |

  **成功响应 (200 OK)**
  ```json
    {
        "code": 200,
        "message": "学生信息修改成功！",
        "data": {
            "id": 5,
            "teacher": 1,
            "name": "小黑",
            "account": "ancdakd4"
        }
    }
  ```

  **错误响应**
  - **404 Not Found** (学生信息不存在)
  ```json
    {
        "detail": "No Student matches the given query."
    }
  ```

  ---

  #### 5. 删除学生信息

  **删除指定学生信息**

  - **URL**: `/api/students/<int:pk>/`  
  - **Method**: `DELETE`  

  **成功响应 (204 No Content)**
  ```json
    {
    "code": 204,
    "message": "学生信息删除成功！"
    }
  ```

  **错误响应**
  - **404 Not Found** (学生信息不存在)
  ```json
    {
        "detail": "No Student matches the given query."
    }
  ```
