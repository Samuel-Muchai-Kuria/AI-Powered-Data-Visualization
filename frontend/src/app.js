import React, { useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line } from 'recharts';
import './app.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/query/text-to-viz`, {
        query: query
      });
      setChartData(response.data);
    } catch (err) {
      setError('Failed to generate visualization: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderChart = () => {
    if (!chartData) return null;

    const { chart_type, data, config } = chartData;

    switch (chart_type) {
      case 'bar':
        return (
          <BarChart width={600} height={300} data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={config.x} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={config.y} fill="#8884d8" />
          </BarChart>
        );
      case 'line':
        return (
          <LineChart width={600} height={300} data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={config.x} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={config.y} stroke="#8884d8" />
          </LineChart>
        );
      case 'table':
        return (
          <table className="data-table">
            <thead>
              <tr>
                {Object.keys(data[0] || {}).map(key => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr key={index}>
                  {Object.values(row).map((value, idx) => (
                    <td key={idx}>{value}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        );
      default:
        return <p>Unsupported chart type: {chart_type}</p>;
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI-Powered Data Visualization PoC</h1>
        
        <form onSubmit={handleSubmit} className="query-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query (e.g., 'show me sales by region')"
            className="query-input"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Generating...' : 'Generate Visualization'}
          </button>
        </form>

        {error && <div className="error-message">{error}</div>}

        <div className="chart-container">
          {chartData && (
            <div>
              <h2>{chartData.config.title}</h2>
              {renderChart()}
            </div>
          )}
        </div>

        <div className="sample-queries">
          <h3>Try these sample queries:</h3>
          <ul>
            <li>show me sales by region</li>
            <li>sales over time</li>
            <li>display all sales data</li>
          </ul>
        </div>
      </header>
    </div>
  );
}

export default App;
