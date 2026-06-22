# 人大434备考系统 - GitHub Pages + Cloudflare Worker 部署指南

## 架构

```
用户浏览器
    ↓
GitHub Pages (静态文件: HTML + data/*.json)
    ↓ AI请求
Cloudflare Worker (代理 DeepSeek API)
```

## 第一步：部署 Cloudflare Worker

```bash
cd deploy/

# 1. 安装 wrangler (如果未安装)
npm install -g wrangler

# 2. 登录 Cloudflare
wrangler login

# 3. 设置 DeepSeek API Key
wrangler secret put DEEPSEEK_KEY
# 输入你的 key (格式: sk-xxxxx)

# 4. 部署
wrangler deploy
```

部署成功后会显示 Worker URL，例如：
```
https://r434-ai-proxy.你的用户名.workers.dev
```
**记下这个 URL。**

## 第二步：更新前端配置

编辑 `deploy/index.html`，找到：
```javascript
var AI_URL = "https://YOUR_WORKER.workers.dev";
```
替换为你的 Worker URL。

## 第三步：部署到 GitHub Pages

1. 在 GitHub 创建仓库 `r434-prep`
2. 将 `deploy/` 目录下的内容推送到仓库：
```bash
cd deploy/
git init
git add .
git commit -m "R434备考系统 v1.0"
git remote add origin https://github.com/你的用户名/r434-prep.git
git push -u origin main
```
3. 在仓库 Settings → Pages 中，选择 `main` 分支部署
4. 等待几分钟，访问 `https://你的用户名.github.io/r434-prep/`

## 注意事项

- Cloudflare Worker 免费额度：10万次/天，足够个人使用
- GitHub Pages 免费，无限流量
- API Key 存储在 Worker 的环境变量中，前端代码不会暴露
- 不要将 .env 文件上传到 GitHub
