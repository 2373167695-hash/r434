/**
 * CloudBase 云函数 — AI 请求代理（HTTP 触发器）
 * 
 * 部署步骤：
 * 1. 在 CloudBase 控制台 → 云函数 → 新建云函数，命名为 proxyAI
 * 2. 上传 index.js 和 package.json
 * 3. 在函数配置 → 环境变量 中设置 MIMO_API_KEY
 * 4. 开启 HTTP 访问（点击"HTTP 访问"标签 → 创建路由）
 * 5. 复制生成的 HTTP 触发地址
 * 
 * 前端调用：POST {云函数HTTP地址}
 * 请求体：{ messages: [...], temperature: 0.3, max_tokens: 4096 }
 * 返回：{ content: "...", usage: { prompt_tokens, completion_tokens } }
 */

exports.main = async (event, context) => {
  const { httpMethod, body } = event;
  
  // CORS preflight
  if (httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
      }
    };
  }

  if (httpMethod !== 'POST') {
    return { 
      statusCode: 405, 
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: '只支持 POST 请求' }) 
    };
  }

  let params;
  try {
    params = typeof body === 'string' ? JSON.parse(body) : body;
  } catch (e) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: '请求体 JSON 解析失败' })
    };
  }

  const { messages, temperature = 0.3, max_tokens = 4096 } = params;
  
  if (!messages || !Array.isArray(messages)) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: '缺少 messages 参数' })
    };
  }

  const API_KEY = process.env.MIMO_API_KEY;
  if (!API_KEY) {
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: '服务器 API Key 未配置' })
    };
  }

  try {
    const resp = await fetch('https://api.xiaomimimo.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'mimo-v2.5',
        messages: messages,
        stream: false,
        temperature: temperature,
        max_tokens: max_tokens
      })
    });

    if (!resp.ok) {
      const errText = await resp.text();
      return {
        statusCode: resp.status,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ error: `AI API 错误 (${resp.status}): ${errText.substring(0, 200)}` })
      };
    }

    const data = await resp.json();
    
    // 提取 content（过滤 reasoning_content）
    let content = '';
    if (data.choices && data.choices[0] && data.choices[0].message) {
      content = data.choices[0].message.content || '';
    }
    
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ content: content, usage: data.usage || {} })
    };
  } catch (err) {
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: '请求 AI API 失败: ' + err.message })
    };
  }
};
