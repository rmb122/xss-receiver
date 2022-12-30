// Modify from https://github.com/egoist/vue-monaco

import assign from 'nano-assign'

export default {
    name: 'MonacoEditor',

    props: {
        value: {
            type: String,
            required: true
        },
        theme: {
            type: String,
            default: 'vs'
        },
        readonly: {
            type: Boolean,
            default: false,
        },
        language: String,
        filename: String,
        options: Object,
        amdRequire: {
            type: Function,
            required: true
        },
    },

    model: {
        event: 'change'
    },

    watch: {
        options: {
            deep: true,
            handler(options) {
                if (this.editor) {
                    const editor = this.getEditor()
                    editor.updateOptions(options)
                }
            }
        },

        value(newValue) {
            if (this.editor) {
                const editor = this.getEditor()
                if (newValue !== editor.getValue()) {
                    editor.setValue(newValue)
                }
            }
        },

        language(newVal) {
            if (this.editor) {
                const editor = this.getEditor()
                this.monaco.editor.setModelLanguage(editor.getModel(), newVal)
            }
        },

        filename(newVal) {
            if (this.editor) {
                this.setModelByFilename(newVal)
            }
        },

        theme(newVal) {
            if (this.editor) {
                this.monaco.editor.setTheme(newVal)
            }
        },

        readonly(newVal) {
            if (this.editor) {
                const editor = this.getEditor()
                editor.updateOptions({readOnly: newVal})
            }
        }
    },

    mounted() {
        this.amdRequire(['vs/editor/editor.main'], () => {
            this.monaco = window.monaco
            this.$nextTick(() => {
                this.initMonaco(window.monaco)
            })
        })
    },

    beforeDestroy() {
        this.editor && this.editor.dispose()
    },

    methods: {
        initMonaco(monaco) {
            this.$emit('editorWillMount', this.monaco)

            if (typeof this.filename === 'string' && this.filename.length > 0) {
                this.language = undefined;
            }

            const options = assign(
                {
                    value: this.value,
                    theme: this.theme,
                    language: this.language,
                    readOnly: this.readonly,
                },
                this.options
            )

            this.editor = monaco.editor.create(this.$el, options)
            if (typeof this.filename === 'string' && this.filename.length > 0) {
                this.setModelByFilename(this.filename)
            }

            this.editor.onDidChangeModelContent(event => {
                const value = this.editor.getValue()
                if (this.value !== value) {
                    this.$emit('change', value, event)
                }
            })

            this.$emit('editorDidMount', this.editor)
        },

        setModelByFilename(filename) {
            const uri = this.monaco.Uri.file(filename);
            let model = this.monaco.editor.getModel(uri);

            if (model == null) {
                model = this.monaco.editor.createModel(
                    this.value,
                    undefined,
                    uri,
                );
            }

            this.editor.setModel(model);
            this.editor.setValue(this.value);
        },

        getEditor() {
            return this.editor
        },

        focus() {
            this.editor.focus()
        }
    },

    render(h) {
        return h('div')
    }
}