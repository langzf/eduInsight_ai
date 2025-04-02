/**
 * API测试脚本
 * 用于测试API连接和验证配置是否正确
 */

const axios = require('axios');

// API配置参数
const BASE_URL = 'http://localhost:6060';
const API_VERSION = 'v1';
const API_URL = `${BASE_URL}/api/${API_VERSION}`;

// 测试API接口
async function testAPI() {
  console.log('===== API测试开始 =====');
  console.log(`基础URL: ${BASE_URL}`);
  console.log(`API版本: ${API_VERSION}`);
  console.log(`完整API地址: ${API_URL}`);
  console.log('---------------------');

  try {
    // 测试服务状态接口
    console.log('1. 测试服务状态接口...');
    const statusResponse = await axios.get(`${API_URL}/auth/status`);
    console.log('   状态: 成功');
    console.log(`   响应: ${JSON.stringify(statusResponse.data)}`);
  } catch (error) {
    console.log('   状态: 失败');
    if (error.response) {
      console.log(`   错误: ${error.response.status} - ${JSON.stringify(error.response.data)}`);
    } else if (error.request) {
      console.log('   错误: 无法连接到服务器');
    } else {
      console.log(`   错误: ${error.message}`);
    }
  }
  
  console.log('---------------------');
  
  try {
    // 测试登录接口
    console.log('2. 测试登录接口...');
    const loginUrl = `${API_URL}/auth/login`;
    console.log(`   登录URL: ${loginUrl}`);
    
    const loginData = {
      phone: '13800000000',
      password: 'admin123'
    };
    
    const loginResponse = await axios.post(loginUrl, loginData);
    console.log('   状态: 成功');
    console.log('   响应: 登录成功，获取到令牌');
    if (loginResponse.data.access_token) {
      console.log(`   令牌: ${loginResponse.data.access_token.substring(0, 20)}...`);
    }
  } catch (error) {
    console.log('   状态: 失败');
    if (error.response) {
      console.log(`   错误: ${error.response.status} - ${JSON.stringify(error.response.data)}`);
    } else if (error.request) {
      console.log('   错误: 无法连接到服务器');
    } else {
      console.log(`   错误: ${error.message}`);
    }
  }
  
  console.log('===== API测试结束 =====');
}

// 执行测试
testAPI(); 