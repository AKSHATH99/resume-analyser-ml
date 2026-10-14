import { useRef, useState } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [text, setText] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  const handleFile = (f) => {
    setError('')
    if (!f) return
    if (f.type !== 'application/pdf') {
      setError('Please select a PDF file.')
      setFile(null)
      return
    }
    setFile(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    handleFile(e.dataTransfer.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please choose a PDF first.')
      return
    }
    const formData = new FormData()
    formData.append('file', file)
    setLoading(true)
    setError('')
    setText('')
    setCategory('')
    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail || 'Extraction failed.')
      } else {
        setText(data.text)
        setCategory(data.category)
      }
    } catch {
      setError('Upload failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container">
      <h1>Resume Analyser</h1>
      <p>Upload your resume as a PDF to get started.</p>
      <form onSubmit={handleSubmit}>
        <div
          className="dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
        >
          {file ? (
            <span>{file.name}</span>
          ) : (
            <span>Drag &amp; drop a PDF here, or click to browse</span>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            hidden
            onChange={(e) => handleFile(e.target.files[0])}
          />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Processing…' : 'Upload'}
        </button>
        {loading && <p>Extracting text, please wait…</p>}
        {category && (
          <p className="category">
            Predicted category: <strong>{category}</strong>
          </p>
        )}
        {text && (
          <pre className="extracted">{text}</pre>
        )}
      </form>
    </main>
  )
}

export default App
