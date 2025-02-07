import React from 'react';
import InstallForm from '../../components/forms/installform';

export default function Install() {
    return (
        <div class="container-inner">
            <div id="flashed-messages" class="small-center"></div>
            <div class="medium-center">
                <div class="panel mb64 pb0 m0 flex-grow flex flex-column">
                    <h2>Server Manager</h2>
                    <div class="panel-inset-lighter mb12">
                        <h3>Install</h3>
                        <InstallForm />
                    </div>
                </div>
            </div>
        </div>
    );
}
