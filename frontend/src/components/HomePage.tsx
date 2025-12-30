/**
 * Home page component for database upload or playground access.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadDatabase } from '../lib/api';
import type { UploadResponse } from '../lib/api';

export function HomePage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);

    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setProgress(0);

    try {
      const response: UploadResponse = await uploadDatabase(file, (p) => setProgress(p));
      // Redirect to the dashboard for this session
      navigate(response.redirect_url);
    } catch (err: any) {
      // Extract error message from axios error response
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Upload failed. Please try again.');
      }
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handlePlayground = () => {
    const tables = 'categories,customers,order_items,orders,products';
    const filters = encodeURIComponent(
      JSON.stringify([
        {
          table: 'products',
          column: 'price',
          operator: 'gt',
          value: '60',
        },
      ])
    );
    navigate(`/playground?tables=${tables}&filters=${filters}`);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f3f4f6', padding: '40px 20px' }}>
      <div style={{ maxWidth: '1400px', width: '100%' }}>
        {/* Hero Section */}
        <div style={{ textAlign: 'center', marginBottom: '50px' }}>
          <h1 style={{ fontSize: '42px', fontWeight: 'bold', marginBottom: '15px', color: '#1f2937' }}>
            SQL Dashboard
          </h1>
          <p style={{ fontSize: '18px', color: '#6b7280', maxWidth: '900px', margin: '0 auto' }}>
            A lightweight, intuitive dashboard for exploring SQLite databases with dynamic filtering and instant sharing capabilities!
          </p>
        </div>

        {/* Two Column Layout */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '40px', alignItems: 'start' }}>

          {/* Left Column - Features */}
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '25px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <div style={{ fontSize: '28px', marginBottom: '10px' }}>⚡</div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                  Dynamic Data Exploration
                </h3>
                <p style={{ fontSize: '13px', color: '#6b7280', lineHeight: '1.5' }}>
                  View multiple tables with real-time filtering
                </p>
              </div>

              <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '25px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <div style={{ fontSize: '28px', marginBottom: '10px' }}>🔗</div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                  URL State Management
                </h3>
                <p style={{ fontSize: '13px', color: '#6b7280', lineHeight: '1.5' }}>
                  Share results instantly by copying the URL
                </p>
              </div>

              <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '25px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <div style={{ fontSize: '28px', marginBottom: '10px' }}>🎨</div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                  Intuitive Interface
                </h3>
                <p style={{ fontSize: '13px', color: '#6b7280', lineHeight: '1.5' }}>
                  Zero learning curve, start exploring immediately
                </p>
              </div>

              <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '25px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <div style={{ fontSize: '28px', marginBottom: '10px' }}>🔄</div>
                <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                  Cross-Table Filtering
                </h3>
                <p style={{ fontSize: '13px', color: '#6b7280', lineHeight: '1.5' }}>
                  Filters work across table relationships
                </p>
              </div>
            </div>
          </div>

          {/* Right Column - Upload Section */}
          <div>
            <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '35px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
              <h2 style={{ fontSize: '24px', fontWeight: 'bold', textAlign: 'center', marginBottom: '10px', color: '#1f2937' }}>
                Get Started
              </h2>
              <p style={{ textAlign: 'center', color: '#6b7280', marginBottom: '25px', fontSize: '14px' }}>
                Upload your SQLite database or try our playground
              </p>

          {/* Upload section */}
          <div style={{ marginBottom: '30px' }}>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              style={{
                border: `2px dashed ${isDragging ? '#000000' : '#d1d5db'}`,
                borderRadius: '8px',
                padding: '40px 20px',
                textAlign: 'center',
                backgroundColor: isDragging ? '#f3f4f6' : '#f9fafb',
                cursor: 'pointer',
                transition: 'all 0.2s',
                marginBottom: '20px',
              }}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".db,.sqlite,.sqlite3"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <div style={{ fontSize: '48px', marginBottom: '10px' }}>📁</div>
              {file ? (
                <p style={{ color: '#374151', fontWeight: '500' }}>{file.name}</p>
              ) : (
                <>
                  <p style={{ color: '#374151', marginBottom: '5px' }}>
                    <strong>Click to select</strong> or drag and drop
                  </p>
                  <p style={{ color: '#9ca3af', fontSize: '14px' }}>
                    SQLite files only (.db, .sqlite, .sqlite3)
                  </p>
                </>
              )}
            </div>

            {file && !uploading && (
              <button
                onClick={handleUpload}
                style={{
                  width: '100%',
                  backgroundColor: '#000000',
                  color: 'white',
                  padding: '12px',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#333333')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#000000')}
              >
                Upload Database
              </button>
            )}

            {uploading && (
              <div>
                <div style={{ width: '100%', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden', marginBottom: '10px' }}>
                  <div
                    style={{
                      width: `${progress}%`,
                      backgroundColor: '#000000',
                      height: '8px',
                      transition: 'width 0.3s',
                    }}
                  />
                </div>
                <p style={{ textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                  Uploading... {Math.round(progress)}%
                </p>
              </div>
            )}

            {error && (
              <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '12px', marginTop: '15px' }}>
                <p style={{ color: '#dc2626', fontSize: '14px', margin: 0 }}>{error}</p>
              </div>
            )}
          </div>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', margin: '30px 0' }}>
            <div style={{ flex: 1, height: '1px', backgroundColor: '#e5e7eb' }} />
            <span style={{ padding: '0 15px', color: '#9ca3af', fontSize: '14px' }}>or</span>
            <div style={{ flex: 1, height: '1px', backgroundColor: '#e5e7eb' }} />
          </div>

          {/* Playground button */}
          <button
            onClick={handlePlayground}
            style={{
              width: '100%',
              backgroundColor: 'white',
              color: '#374151',
              padding: '12px',
              borderRadius: '6px',
              border: '2px solid #d1d5db',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f9fafb';
              e.currentTarget.style.borderColor = '#9ca3af';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'white';
              e.currentTarget.style.borderColor = '#d1d5db';
            }}
          >
            Try Playground Database
          </button>

          <p style={{ textAlign: 'center', color: '#9ca3af', fontSize: '12px', marginTop: '20px' }}>
            Max file size: 50MB • Sessions expire after 7 days
          </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
