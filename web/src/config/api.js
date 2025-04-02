/**
 * API配置文件
 * 集中管理所有API相关的配置
 */

const config = {
    // 基本URL，优先使用环境变量中的值，如果不存在则使用固定值
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:6060',
    
    // API版本
    version: 'v1',
    
    // 获取完整的API基础URL
    get apiBaseURL() {
        // 检查环境变量是否已经包含了 /api/v1 路径
        if (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.includes('/api/v1')) {
            return process.env.REACT_APP_API_URL;
        }
        // 否则，添加 /api/v1 路径
        return `${this.baseURL}/api/${this.version}`;
    },
    
    // 请求超时时间（毫秒）
    timeout: 10000,
    
    // 请求头
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
};

export default config; 