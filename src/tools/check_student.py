import requests
from bs4 import BeautifulSoup

def check_bupt_student(username, password):
    # 北邮统一身份认证登录地址
    login_url = "https://auth.bupt.edu.cn/authserver/login"
    
    # 使用 Session 保持 Cookie 状态
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    try:
        # 1. 访问登录页，获取必要的隐藏参数 execution
        response = session.get(login_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取登录表单中的 execution 值（CAS 协议要求）
        execution_element = soup.find('input', {'name': 'execution'})
        if not execution_element:
            return False, "无法连接到认证服务器或页面解析失败"
        
        execution = execution_element.get('value')

        # 2. 构造登录数据
        payload = {
            'username': username,
            'password': password,
            'submit': '登录',
            'type': 'username_password',
            'execution': execution,
            '_eventId': 'submit'
        }

        # 3. 提交登录请求
        # allow_redirects=False 是为了捕捉登录成功后的跳转行为
        res = session.post(login_url, data=payload, allow_redirects=False, timeout=10)

        # 4. 判断逻辑：
        # CAS 成功后通常会返回 302 重定向到 service 地址
        # 如果还在原页面（返回 200）或包含错误提示，则登录失败
        if res.status_code == 302:
            return True, "验证成功：是北京邮电大学学生"
        else:
            # 也可以进一步解析 res.text 查找“账号或密码错误”等字样
            return False, "验证失败：学号或密码错误，或非该校学生"

    except Exception as e:
        return False, f"网络错误: {str(e)}"

# --- 终端交互部分 ---
if __name__ == "__main__":
    print("=== 北邮学生身份验证系统 ===")
    student_id = input("请输入学号: ")
    password = input("请输入密码: ")

    print("\n正在向 BUPT 认证服务器验证...")
    is_student, message = check_bupt_student(student_id, password)
    
    print("-" * 30)
    print(message)
    print("-" * 30)