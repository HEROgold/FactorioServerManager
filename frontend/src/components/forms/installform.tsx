import React, {useState} from 'react';
import { ENDPOINTS } from '../../constants';
import { FormField, FormHandler, FormSubmit } from './formHandler';
import { FactorioVersion } from "../../types";


export type InstallFormProps = {
    name: string;
    version: [number, number, number];
    port: number;
};

export default function InstallForm() {
    const serverName = "FactorioServer";
    const nameField = new FormField<string>('name', serverName, 'text');
    const formHandler = new FormHandler('post', ENDPOINTS.InstallServer, [
        nameField,
        new FormField<FactorioVersion>('version', [1, 0, 0], 'text'),
        new FormField<number>('port', 34197, 'number'),
        new FormSubmit(),
    ]);
    formHandler.linkAction(nameField);
    
    return formHandler.render()

    // Original code:
    // const changeHandler = (e: React.ChangeEvent<HTMLInputElement>) => setProps({...props, [e.target.name]: e.target.value});
    // return (
    //     <form method="post" action={ENDPOINTS.InstallServer(props.name)}>
    //         <label>{props.name}</label>
    //         <input type="text" name="name" value={props.name} onChange={changeHandler} />
    //         <br />
    //         <label>{props.version.join('.')}</label>
    //         <input type="number" name="version" value={props.version.join('.')} onChange={changeHandler} />
    //         <br />
    //         <label>{props.port}</label>
    //         <input type="number" name="port" value={props.port} onChange={changeHandler} />
    //         <button type="submit">Submit</button>
    //     </form>
    // );
}