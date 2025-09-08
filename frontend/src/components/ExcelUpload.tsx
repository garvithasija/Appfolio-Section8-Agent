import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import config from '../config';
import './ExcelUpload.css';

interface ExcelUploadProps {
  onJobCreated: (jobId: string, data: any) => void;
  currentJobId: string | null;
}

interface JobStatus {
  job_id: string;
  status: string;
  progress: string;
  total_rows: number;
  completed_rows: number;
  errors: number;
}

const ExcelUpload: React.FC<ExcelUploadProps> = ({ onJobCreated, currentJobId }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<any[]>([]);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string>('');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    console.log('Files dropped:', acceptedFiles);
    const file = acceptedFiles[0];
    if (!file) {
      console.log('No file selected');
      return;
    }

    console.log('Starting upload for file:', file.name);
    setIsUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${config.apiUrl}/jobs`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { job_id, preview: previewData } = response.data;
      setPreview(previewData);
      onJobCreated(job_id, response.data);

      // Fetch initial job status
      const statusResponse = await axios.get(`${config.apiUrl}/jobs/${job_id}/status`);
      setJobStatus(statusResponse.data);

    } catch (err: any) {
      console.error('Upload error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Upload failed';
      setError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, [onJobCreated]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
    },
    multiple: false,
  });

  const refreshStatus = async () => {
    if (!currentJobId) return;

    try {
      const response = await axios.get(`${config.apiUrl}/jobs/${currentJobId}/status`);
      setJobStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  return (
    <div className="excel-upload">
      <h2>Upload Excel or CSV File</h2>
      
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${isUploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <p>Uploading...</p>
        ) : isDragActive ? (
          <p>Drop the Excel/CSV file here...</p>
        ) : (
          <p>Drag & drop an Excel (.xlsx) or CSV file here, or click to select</p>
        )}
      </div>

      {error && (
        <div className="error">
          <p>{error}</p>
        </div>
      )}

      {preview.length > 0 && (
        <div className="preview">
          <h3>File Preview (First 5 rows)</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  {Object.keys(preview[0]).map((key) => (
                    <th key={key}>{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value: any, i) => (
                      <td key={i}>{String(value)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {jobStatus && (
        <div className="job-status">
          <h3>Job Status</h3>
          <div className="status-info">
            <p><strong>Job ID:</strong> {jobStatus.job_id}</p>
            <p><strong>Status:</strong> {jobStatus.status}</p>
            <p><strong>Progress:</strong> {jobStatus.progress}</p>
            <p><strong>Total Rows:</strong> {jobStatus.total_rows}</p>
            <p><strong>Completed:</strong> {jobStatus.completed_rows}</p>
            <p><strong>Errors:</strong> {jobStatus.errors}</p>
          </div>
          <button onClick={refreshStatus} className="refresh-btn">
            Refresh Status
          </button>
        </div>
      )}
    </div>
  );
};

export default ExcelUpload;