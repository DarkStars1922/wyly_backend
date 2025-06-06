// 获取CSRF令牌
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 登录表单处理
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const csrftoken = getCookie('csrftoken');
        
        try {
            const response = await fetch('/api/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ 
                    username: username, 
                    password: password 
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showSuccess(data.message || '登录成功！');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            } else {
                showError('loginPassword', data.error || '登录失败');
            }
        } catch (error) {
            showError('loginPassword', '网络错误，请稍后重试');
        }
    });
}

// 注册表单处理
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('regUsername').value;
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;
        const csrftoken = getCookie('csrftoken');
        
        try {
            const response = await fetch('/api/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ 
                    username: username, 
                    password: password,
                    password2: confirmPassword
                })
            });
            
            const data = await response.json();
            
            if (response.status === 201) {
                showSuccess(data.message || '注册成功！');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            } else {
                showError('regPassword', data.error || '注册失败');
            }
        } catch (error) {
            showError('regPassword', '网络错误，请稍后重试');
        }
    });
}

// 登出功能
if (document.getElementById('logout-link')) {
    document.getElementById('logout-link').addEventListener('click', async function(e) {
        e.preventDefault();
        
        try {
            const response = await fetch('/api/logout/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                window.location.href = '/';
            }
        } catch (error) {
            console.error('登出失败:', error);
        }
    });
}

// 显示错误信息
function showError(inputId, message) {
    const input = document.getElementById(inputId);
    if (input) {
        input.style.borderColor = '#f87171';
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.style.color = '#f87171';
        errorElement.style.marginTop = '5px';
        errorElement.textContent = message;
        
        // 移除旧的错误信息
        const oldError = input.parentNode.querySelector('.error-message');
        if (oldError) oldError.remove();
        
        input.parentNode.appendChild(errorElement);
    }
}

// 清除错误信息
function clearError(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.style.borderColor = '';
        const errorElement = input.parentNode.querySelector('.error-message');
        if (errorElement) errorElement.remove();
    }
}

// 在输入时清除错误
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', function() {
        clearError(this.id);
    });
});