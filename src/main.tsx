import { Amplify } from 'aws-amplify';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { amplifyConfig } from './amplify-config';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';

if (amplifyConfig.Auth?.Cognito?.userPoolId && amplifyConfig.Auth?.Cognito?.userPoolClientId) {
  Amplify.configure(amplifyConfig);
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);
