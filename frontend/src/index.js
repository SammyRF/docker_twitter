import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import Register from './containers/Register';
import Login from './containers/Login';
import Header from './components/Header';
import { GlobalContextProvider } from './utils/context';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <GlobalContextProvider>
      <Header />
      <Login />
      <Register />
    </GlobalContextProvider>
  </React.StrictMode>,
);
