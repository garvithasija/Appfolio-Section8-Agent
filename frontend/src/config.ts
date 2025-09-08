// API Configuration
const config = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  wsUrl: process.env.REACT_APP_WS_URL || (
    process.env.REACT_APP_API_URL?.replace(/^https?/, 'wss') || 'ws://localhost:8000'
  )
};

export default config;