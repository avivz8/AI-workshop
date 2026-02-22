import React, { useState, useEffect } from 'react';
import './App.css';

interface Todo {
  id: number;
  title: string;
  completed: boolean;
}

function App() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('https://jsonplaceholder.typicode.com/todos?_limit=10')
      .then((res) => res.json())
      .then((data) => {
        setTodos(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleToggle = (id: number) => {
    setTodos((prev) =>
      prev.map((todo) =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    );
  };

  if (loading) {
    return (
      <div className="App" data-testid="app-loading">
        Loading...
      </div>
    );
  }

  return (
    <div className="App" data-testid="app">
      <h1 data-testid="app-title">AI Workshop</h1>
      <ul data-testid="todo-list">
        {todos.map((todo) => (
          <li key={todo.id} data-testid={`todo-item-${todo.id}`}>
            <label>
              <input
                type="checkbox"
                checked={todo.completed}
                onChange={() => handleToggle(todo.id)}
                data-testid={`todo-checkbox-${todo.id}`}
              />
              <span data-testid={`todo-title-${todo.id}`}>{todo.title}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
