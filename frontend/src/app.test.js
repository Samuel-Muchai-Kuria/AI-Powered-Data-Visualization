import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import App from './app';

jest.mock('axios');
const mockedAxios = axios;

test('renders app title', () => {
  render(<App />);
  const titleElement = screen.getByText(/AI-Powered Data Visualization PoC/i);
  expect(titleElement).toBeInTheDocument();
});

test('submits query and displays chart', async () => {
  const mockResponse = {
    data: {
      chart_type: 'bar',
      data: [{ region: 'North', total_sales: 1000 }],
      config: { x: 'region', y: 'total_sales', title: 'Sales by Region' }
    }
  };
  
  mockedAxios.post.mockResolvedValue(mockResponse);

  render(<App />);
  
  const input = screen.getByPlaceholderText(/Enter your query/i);
  const button = screen.getByText(/Generate Visualization/i);
  
  fireEvent.change(input, { target: { value: 'sales by region' } });
  fireEvent.click(button);
  
  await waitFor(() => {
    expect(screen.getByText(/Sales by Region/i)).toBeInTheDocument();
  });
});
