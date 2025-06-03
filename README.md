[TOC]

# 接口文档（0.1）

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

## 1.鉴权版块

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
