<template>
  <div class="login-page">
    <div class="login-bg-pattern"></div>
    <div class="login-wrapper">
      <div class="login-brand">
        <div class="brand-mark">
          <svg viewBox="0 0 80 80" class="brand-svg">
            <rect x="15" y="20" width="50" height="45" rx="8" fill="none" stroke="#fff" stroke-width="2.5"/>
            <line x1="25" y1="32" x2="55" y2="32" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
            <line x1="25" y1="40" x2="50" y2="40" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".7"/>
            <line x1="25" y1="48" x2="45" y2="48" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".4"/>
            <circle cx="58" cy="58" r="12" fill="#f59e0b" opacity=".9"/>
            <text x="58" y="62" text-anchor="middle" fill="#fff" font-size="14" font-weight="700">AI</text>
          </svg>
        </div>
        <h1 class="brand-name">青藜伴读</h1>
        <p class="brand-desc">AI 驱动的个性化学习平台</p>
        <div class="brand-features">
          <span>📖 智能推荐</span>
          <span>🎯 精准练习</span>
          <span>💬 苏格拉底式辅导</span>
          <span>📊 学情分析</span>
        </div>
      </div>

      <div class="login-card">
        <h2>欢迎回来</h2>
        <p class="card-sub">登录你的学习账号，继续进步</p>

        <el-tabs v-model="activeTab" class="ai-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="ai-form">
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="用户名"
                  size="large"
                />
              </el-form-item>
              <el-form-item prop="password" class="pw-row">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="密码"
                  size="large"
                  show-password
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              <el-form-item>
                <button class="login-btn" :disabled="loading" @click="handleLogin">
                  <span v-if="!loading">进入青藜伴读</span>
                  <span v-else>登录中…</span>
                </button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" class="ai-form">
              <el-form-item prop="username">
                <el-input v-model="registerForm.username" placeholder="用户名" size="large" />
              </el-form-item>
              <el-form-item prop="email">
                <el-input v-model="registerForm.email" placeholder="邮箱" size="large" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="registerForm.password" type="password" placeholder="密码（至少 6 位）" size="large" show-password />
              </el-form-item>
              <el-form-item>
                <button class="login-btn" :disabled="registerLoading" @click="handleRegister">创建账号</button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <p class="demo-hint">
          <el-divider>演示账号</el-divider>
          <span>用户名：demo &nbsp;|&nbsp; 密码：demo123</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { aiApi } from '@/api/ai'

const router = useRouter()

const activeTab = ref('login')
const loading = ref(false)
const registerLoading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}
const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ]
}

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await aiApi.login(loginForm.username, loginForm.password)
    if (res && res.status === 'success' && res.token) {
      localStorage.setItem('token', res.token)
      localStorage.setItem('student_id', res.student_id || '1')
      localStorage.setItem('username', loginForm.username)
      if (!localStorage.getItem('education_level')) {
        localStorage.setItem('education_level', 'high_school')
      }
      router.push('/')
    } else {
      ElMessage.error(res?.detail || '用户名或密码错误')
    }
  } catch {
    if (loginForm.username === 'demo' && loginForm.password === 'demo123') {
      localStorage.setItem('token', 'demo-token-' + Date.now())
      localStorage.setItem('student_id', '1')
      localStorage.setItem('username', 'demo')
      if (!localStorage.getItem('education_level')) {
        localStorage.setItem('education_level', 'high_school')
      }
      router.push('/')
    } else {
      ElMessage.error('用户名或密码错误（demo / demo123）')
    }
  }
  loading.value = false
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.email || !registerForm.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  registerLoading.value = true
  try {
    const res = await aiApi.register(registerForm.username, registerForm.email, registerForm.password)
    if (res?.status === 'success') {
      ElMessage.success('注册成功，请登录')
      activeTab.value = 'login'
    } else {
      ElMessage.error(res?.detail || '注册失败')
    }
  } catch {
    ElMessage.success('注册已提交，请登录')
    activeTab.value = 'login'
  }
  registerLoading.value = false
}

onMounted(() => {
  const hasToken = !!localStorage.getItem('token')
  if (hasToken) router.push('/')
})
</script>

<style scoped>
.login-page {
  width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(160deg, #0f766e 0%, #0d9488 30%, #115e59 70%, #0f172a 100%);
  position: relative; overflow: hidden;
}
.login-bg-pattern {
  position: absolute; inset: 0; opacity: .04;
  background-image: radial-gradient(circle, #fff 1px, transparent 1px);
  background-size: 32px 32px;
}
.login-wrapper { position: relative; z-index: 1; display: flex; gap: 64px; align-items: center; padding: 40px; }
.login-brand { text-align: center; }
.brand-mark { margin-bottom: 20px; }
.brand-svg { width: 90px; height: 90px; }
.brand-name { font-size: 44px; font-weight: 800; letter-spacing: 8px; color: #fff; margin-bottom: 8px; }
.brand-desc { font-size: 16px; color: rgba(255,255,255,.7); letter-spacing: 3px; margin-bottom: 28px; }
.brand-features { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.brand-features span { padding: 8px 18px; background: rgba(255,255,255,.1); border-radius: 20px; color: rgba(255,255,255,.85); font-size: 14px; backdrop-filter: blur(4px); }

.login-card {
  width: 420px; padding: 42px 38px; background: #fff; border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0,0,0,.2);
}
.login-card h2 { font-size: 26px; font-weight: 700; color: #0f172a; }
.card-sub { font-size: 14px; color: #64748b; margin: 6px 0 20px; }

.ai-tabs :deep(.el-tabs__nav-wrap::after) { background-color: #e7e5e2; }
.ai-tabs :deep(.el-tabs__item) { font-size: 14px; font-weight: 500; }
.ai-tabs :deep(.el-tabs__item.is-active) { color: #0d9488 !important; font-weight: 600; }
.ai-tabs :deep(.el-tabs__active-bar) { background-color: #0d9488 !important; }
.ai-tabs :deep(.el-input__wrapper) { background: #fff !important; border-radius: 12px; }

.ai-form { display: flex; flex-direction: column; gap: 2px; margin-top: 6px; }

.login-btn {
  width: 100%; padding: 14px; border: none; border-radius: 12px;
  font-family: inherit; font-size: 15px; font-weight: 600; letter-spacing: 4px;
  background: #0d9488; color: #fff;
  transition: all .2s ease; cursor: pointer;
  margin-top: 6px;
}
.login-btn:hover:not(:disabled) { background: #0f766e; transform: translateY(-1px); box-shadow: 0 6px 20px rgba(13, 148, 136, .35); }
.login-btn:disabled { opacity: .65; }

.demo-hint { margin-top: 18px; text-align: center; }
.demo-hint :deep(.el-divider) { --el-divider-text-color: #94a3b8; --el-divider-border-color: #e7e5e2; font-size: 11px; letter-spacing: 2px; }
.demo-hint span { font-size: 12px; color: #64748b; }

@media (max-width: 820px) {
  .login-wrapper { flex-direction: column; gap: 24px; padding: 20px; }
  .login-card { width: 100%; max-width: 420px; padding: 28px 24px; }
  .brand-name { font-size: 32px; }
}
</style>
