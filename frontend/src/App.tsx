import React, { useState } from 'react';
import './App.css';
import ExcelUpload from './components/ExcelUpload';
import ChatInterface from './components/ChatInterface';

function App() {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobData, setJobData] = useState<any>(null);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Section 8 Form Filling Agent</h1>
      </header>
      <div className="main-container">
        <div className="upload-section">
          <ExcelUpload 
            onJobCreated={(jobId, data) => {
              setCurrentJobId(jobId);
              setJobData(data);
            }}
            currentJobId={currentJobId}
          />
        </div>
        <div className="chat-section">
          <ChatInterface 
            jobId={currentJobId}
            jobData={jobData}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
