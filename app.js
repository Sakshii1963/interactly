import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [dbType, setDbType] = useState('elasticsearch');

  const handleFileUpload = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('db_type', dbType);
    try {
      const response = await axios.post('http://localhost:5000/upload', formData);
      alert(response.data.message);
    } catch (error) {
      alert('Error uploading file');
    }
  };

  const handleMatch = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:5000/match', { job_description: jobDescription, db_type: dbType });
      setCandidates(response.data);
    } catch (error) {
      alert('Error matching candidates');
    }
  };

  return (
    <div>
      <h1>Candidate Matcher</h1>
      <form onSubmit={handleFileUpload}>
        <input type="file" onChange={(e) => setFile(e.target.files[0])} accept=".xlsx" required />
        <select value={dbType} onChange={(e) => setDbType(e.target.value)}>
          <option value="elasticsearch">Elasticsearch</option>
          <option value="mongodb">MongoDB</option>
          <option value="postgresql">PostgreSQL</option>
        </select>
        <button type="submit">Upload Excel File</button>
      </form>
      <form onSubmit={handleMatch}>
        <textarea 
          value={jobDescription} 
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Enter job description"
          required
        />
        <button type="submit">Match Candidates</button>
      </form>
      <div>
        {candidates.map((candidate, index) => (
          <div key={index}>
            <h3>{candidate.name}</h3>
            <p>Skills: {candidate.skills}</p>
            <p>Experience: {candidate.experience}</p>
            <p>Generated Response: {candidate.generated_response}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;