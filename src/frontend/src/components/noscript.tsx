import React from 'react';

export default function NoScript() {
    return (
        <>
            <noscript>
                <div class="medium-center">
                    <div class="panel alert alert-warning">
                        <button class="close-button" aria-label="Close alert" ><i class="fa-solid fa-xmark"></i></button>
                        <h2>Warning</h2>
                        <div class="panel-inset mb0">
                            JavaScript is required for logging in and making changes to your servers.
                        </div>
                    </div>
                </div>
            </noscript>
        </>
    )
}
