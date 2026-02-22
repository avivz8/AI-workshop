import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

const mockTodos = [
  { id: 1, title: 'Todo 1', completed: false },
  { id: 2, title: 'Todo 2', completed: true },
];

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      json: () => Promise.resolve(mockTodos),
    })
  ) as jest.Mock;
});

test('renders heading', async () => {
  render(<App />);
  await waitFor(() => {
    expect(screen.getByTestId('app-title')).toBeInTheDocument();
  });
  expect(screen.getByText(/AI Workshop/i)).toBeInTheDocument();
});

test('renders checkboxes with data-testid after loading', async () => {
  render(<App />);

  await waitFor(() => {
    expect(screen.getByTestId('todo-checkbox-1')).toBeInTheDocument();
    expect(screen.getByTestId('todo-checkbox-2')).toBeInTheDocument();
  });

  const checkboxes = screen.getAllByTestId(/^todo-checkbox-/);
  expect(checkboxes).toHaveLength(2);
});
