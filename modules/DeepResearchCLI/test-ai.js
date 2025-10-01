const axios = require('axios');

async function testAI() {
  try {
    console.log('Testing AI connection...');

    const response = await axios.post('https://grid.ai.juspay.net/chat/completions', {
      model: 'qwen3-coder-480b',
      messages: [
        { role: 'user', content: 'Reply with exactly "TEST_OK"' }
      ],
      temperature: 0,
      max_tokens: 10,
      stream: false
    }, {
      headers: {
        'Authorization': 'Bearer sk-RkZpXuxw4iQeR2Ct9VsImA',
        'Content-Type': 'application/json'
      },
      timeout: 60000
    });

    console.log('✅ AI Response:', response.data);
    console.log('✅ Content:', response.data.choices[0].message.content);
    console.log('✅ Tokens used:', response.data.usage?.total_tokens || 0);

  } catch (error) {
    console.log('❌ AI Error:', error.response?.data || error.message);
    if (error.response) {
      console.log('❌ Status:', error.response.status);
      console.log('❌ Headers:', error.response.headers);
    }
  }
}

testAI();