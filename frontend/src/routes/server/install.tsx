import React from 'react';
import InstallForm from '../../components/forms/installform.tsx';

export default function ServerInstall() {
    return (
        <div className="container-inner">
            <div id="flashed-messages" className="small-center"></div>
            <div className="medium-center">
                <div className="panel mb64 pb0 m0 flex-grow flex flex-column">
                    <h2>Server Manager</h2>
                    <div className="panel-inset-lighter mb12">
                        <h3>Install</h3>
                        <InstallForm />
                    </div>
                </div>
            </div>
        </div>
    );
}
