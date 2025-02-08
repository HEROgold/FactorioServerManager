import React from 'react';

type StringFormatter = (...args: any) => string;

export class FormHandler {
    constructor(
        public method: string,
        public action: string | StringFormatter,
        private fields: FormField[] = [],
        public separator?: React.ReactNode
    ) {}

    addField(field: FormField) { this.fields.push(field); }
    removeField(field: FormField) { this.fields = this.fields.filter(f => f !== field); }
    linkAction(field: FormField) { field.changeHandler.add(() => {this.action = field.value}); }

    render() {
        if (this.action instanceof Function) {
            this.action = this.action();
        }
        return (
            <form method={this.method} action={this.action}>
                {this.fields.map((field, index) => (
                    <div key={index}>
                        {field.render()}
                        {index < this.fields.length - 1 && <>{this.separator}</>}
                    </div>
                ))}
            </form>
        );
    }
}

type FormElement = HTMLInputElement | HTMLSelectElement;

class changeHandler {
    private handlers: Function[];

    constructor() {
        this.handlers = new Array<Function>();
    }

    add(handler: Function) {
        this.handlers.push(handler);
    }

    run(event: React.ChangeEvent<FormElement>) {
        this.handlers.forEach(handler => handler(event));
    }
}

interface canBeString {
    toString(): string
}

export class FormField {
    name: string
    value: string
    type: string
    concat: string = "."
    changeHandler: changeHandler

    constructor(
        name: string,
        value: canBeString | String,
        type: string,
    ){
        this.name = name;
        this.value = value.toString();
        this.type = type;
        this.changeHandler = new changeHandler()
        this.changeHandler.add((event: React.ChangeEvent<FormElement>) => {
            if (typeof this.value === 'string') {
                this.value = event.target.value;
            }
        });
    }


    render() {
        return <>
            <label>{this.name}</label>
            <input 
                type={this.type}
                name={this.name}
                value={this.value}
                style={{ marginLeft: '5%', marginTop: '1%' }}
                onChange={this.changeHandler.run} 
            />
        </>
        ;
    }
}

export class FormSelector extends FormField {
    options: any[]

    constructor(
        name: string,
        options: any[],
        value: string,
    ) {
        super(name, value, 'select');
        this.options = options;
        this.changeHandler = new changeHandler();
        this.changeHandler.add((event: React.ChangeEvent<HTMLSelectElement>) => {
            this.value = event.target.value;
        });
    }


    render() {
        return <>
            <label>{this.name}</label>
            <select 
                name={this.name} 
                value={this.value} 
                onChange={this.changeHandler.run} 
                style={{ marginLeft: '5%', marginTop: '1%' }}
            >
                {this.options.map((option, index) => (
                    <option key={index} value={option}>{option}</option>
                ))}
            </select>
        </>
        ;
    }
}

export class FormSubmit extends FormField {
    constructor() {
        super('', '', 'submit');
    }

    render() {
        return <button type="submit">Submit</button>
    }
}