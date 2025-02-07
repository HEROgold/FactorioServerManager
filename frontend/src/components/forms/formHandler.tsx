import React from 'react';
import { StringTransformer } from '../../types';

export class FormHandler {
    constructor(
        public method: string,
        public action: string | StringTransformer,
        private fields: FormField<any>[] = [],
        public separator?: HTMLElement
    ) {}

    addField(field: FormField<any>) { this.fields.push(field); }
    removeField(field: FormField<any>) { this.fields = this.fields.filter(f => f !== field); }
    linkAction(field: FormField<string>) {
        field.changeHandler = (event: React.ChangeEvent<HTMLInputElement>) => {
            field.changeHandler(event);
            if (typeof this.action === 'function')
                this.action = this.action(field.value);
            else
                this.action = field.value;
        };
    }

    render() {
        return (
            <form method={this.method} action={this.action}>
                {this.fields.map((field, index) => (
                    <div key={index}>
                        {field.render()}
                        {index < this.fields.length - 1 && this.separator}
                    </div>
                ))}
            </form>
        );
    }
}

export class FormField<T> {
    constructor(
        public name: string,
        public value: T,
        public type: string,
        public concat: string = "."
    ) {}

    changeHandler(event: React.ChangeEvent<HTMLInputElement>) {
        this.value = event.target.value;
    }

    render() {
        <>
            <label>{this.name}</label>
            <input 
                type={this.type}
                name={this.name}
                value={Array.isArray(this.value) ? this.value.join(this.concat) : this.value}
                onChange={this.changeHandler} 
            />
        </>
        ;
    }
}

export class FormSubmit extends FormField<string> {
    constructor() {
        super('', '', 'submit');
    }

    render() {
        <button type="submit">Submit</button>
    }
}