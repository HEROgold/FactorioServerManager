import React from 'react';
import LoginForm from '../components/forms/loginform.tsx';

export default function Login() {
  return (
    <div className="container-inner">
      <div className="panel small-center">
        <h2>Log in</h2>
        <p>Use your Factorio.com account</p>
        <LoginForm />
      </div>
    </div>
  );
};
