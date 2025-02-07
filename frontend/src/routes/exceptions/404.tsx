import React from 'react';

export default function NotFound(error: Error) {
    return (
        <div class="container-inner">
            <div class="panel">
                <h1>404</h1>
                <p>Page not found.</p>
                <div class="panel-inset-lighter">
                    <p>{error.message}</p>
                </div>
            </div>
        </div>
    );
}
