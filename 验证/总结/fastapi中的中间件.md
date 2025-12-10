# fastapi中的中间件
在 FastAPI 中，**中间件（Middleware）** 是一个在请求到达具体的路径操作（路由处理函数）**之前**以及响应返回给客户端**之后**执行的代码层。它允许你对 HTTP 请求和响应进行全局性的拦截、处理和修改。

---

### **主要作用**

1. **全局预处理请求**
    - 在请求被路由到具体的处理函数之前，中间件可以：
        - 验证身份认证（如检查 JWT Token）。
        - 记录请求日志（如 URL、方法、客户端 IP）。
        - 添加请求头或修改请求数据。
        - 限制访问频率（频率限制）。

2. **全局后处理响应**
    - 在响应返回给客户端之前，中间件可以：
        - 添加响应头（如 `X-Process-Time` 计算耗时）。
        - 修改响应内容（如统一封装响应格式）。
        - 记录响应日志。

3. **异常处理**
    - 捕获并处理请求过程中的异常，返回统一的错误格式。

4. **跨域资源共享（CORS）**
    - 通过内置的 `CORSMiddleware` 处理跨域请求。

---

### **工作原理**
```
客户端请求 → 中间件1 → 中间件2 → ... → 路径操作函数（路由） → 中间件2 → 中间件1 → 客户端响应
```
- 中间件按添加顺序执行（请求阶段正序，响应阶段逆序）。
- 每个中间件可以决定是否传递请求给下一个中间件或直接返回响应。

---

### **示例：添加请求处理时间的中间件**
```python
import time
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 请求前：记录开始时间
    start_time = time.time()
    
    # 将请求传递给下一个中间件或路由
    response = await call_next(request)
    
    # 响应前：计算耗时并添加响应头
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

---

### **常见内置中间件**
1. **`CORSMiddleware`**：处理跨域请求。
2. **`HTTPSRedirectMiddleware`**：强制 HTTPS 重定向。
3. **`TrustedHostMiddleware`**：验证请求的 Host 头。

---

### **注意事项**
- 中间件适用于**全局操作**，如果只需针对特定路由，建议使用**依赖注入（Dependencies）** 或**装饰器**。
- 避免在中间件中进行复杂业务逻辑，以免影响性能。
- 使用 `@app.middleware("http")` 注册自定义中间件。

---

### **与依赖注入的区别**
| 特性 | 中间件 | 依赖注入 |
|------|--------|----------|
| 作用范围 | 全局（所有请求） | 单个路由或路由组 |
| 执行时机 | 请求/响应的完整周期 | 路由处理函数执行前 |
| 典型用例 | 日志、CORS、限流 | 权限验证、数据库会话 |

---

如果需要进一步了解具体场景的实现方法（如认证、日志），我可以提供更详细的示例。