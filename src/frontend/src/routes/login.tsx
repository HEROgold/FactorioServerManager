import React, { useState } from 'react';
import { ENDPOINTS } from '../constants';
import { redirect } from 'react-router';

export default function Login() {
    const [email, setEmail] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [emailAuthCode, setEmailAuthCode] = useState<string>('');
    const [error, setError] = useState<string>('');

    const validateForm = () => {
        if (!email) {
            setError('Email is required');
            return false;
        }
        if (!password) {
            setError('Password is required');
            return false;
        }
        return true;
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        if (!validateForm()) {
            return;
        }

        const params = new URLSearchParams();
        params.append('email', email);
        params.append('password', password);
        params.append('emailAuthCode', emailAuthCode);

        try {
            const response = fetch(ENDPOINTS.Login, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: params,
            });
            response.then((res) => {
                if (res.ok) {
                    res.json().then((data) => {
                        localStorage.setItem('token', data.token);
                        redirect('/home');
                    });
                }
            });
        } catch (error) {
            setError(error.message);
        }
    };

    return (
        <div className="container-inner">
            <div className="panel small-center">
                <h2>Log in</h2>
                <p>Use your Factorio.com account</p>
                <form method="POST" action="/login" onSubmit={handleSubmit}>
                    <div className="panel-inset-lighter">
                        <dl>
                            <div>
                                <dt>Email</dt>
                                <dd style={{ width: '90%' }}>
                                    <input
                                        type="email"
                                        required
                                        placeholder="Email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </dd>
                            </div>
                            <div>
                                <dt>Password</dt>
                                <dd style={{ width: '90%' }}>
                                    <input
                                        type="password"
                                        required
                                        placeholder="Password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                    />
                                </dd>
                            </div>
                            <div>
                                <dt>Email Auth Code</dt>
                                <dd style={{ width: '200%' }}>
                                    <input
                                        type="text"
                                        placeholder="(Optional) Email code"
                                        value={emailAuthCode}
                                        onChange={(e) => setEmailAuthCode(e.target.value)}
                                    />
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div className="text-right">
                        <button type="submit" className="button-green-right">
                            Log in
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
