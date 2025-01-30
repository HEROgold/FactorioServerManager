import React, { useState } from 'react';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [emailAuthCode, setEmailAuthCode] = useState('');

    const handleSubmit = (event) => {
        event.preventDefault();
        // Handle form submission logic here
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
