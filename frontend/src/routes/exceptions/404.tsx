import React from 'react';

export default function NotFound(error: Error) {
    return (
        <div className="container-inner">
            <div className="panel">
                <h1>404</h1>
                <p>Page not found.</p>
                <div className="panel-inset-lighter">
                    <p>{error.message}</p>
                </div>
            </div>
        </div>
    );
}
