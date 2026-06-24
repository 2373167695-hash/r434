/**
 * CloudBase 云函数 — AI 请求代理
 * 环境变量 MIMO_API_KEY 在云函数配置中设置
 * 
 * 前端调用：POST /proxyAI  { messages: [...] }
 * 返回：{ choices: [{ message: { content: "..." } }] }
 */
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

exports.main = async (event, context) => {
  const { messages } = event;

  if (!messages || !Array.isArray(messages)) {
    return { error: '缺少 messages 参数' };
  }

  const API_KEY = process.env.MIMO_API_KEY;
  if (!API_KEY) {
    return { error: '服务端未配置 API Key' };
  }

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
      temperature: 0.3,
      max_tokens: 4096
    })
  });

  const data = await resp.json();
  
  // Extract just the content for cleaner response
  const content = data.choices?.[0]?.message?.content || '';
  return { content, raw: data };
};
