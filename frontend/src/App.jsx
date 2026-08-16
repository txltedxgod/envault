import { useState, useEffect } from 'react'

const api = async (url, opts = {}) => {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...opts
    })
    return res.json()
}

export default function App() {
    const [projects, setProjects] = useState([])
    const [activeProject, setActiveProject] = useState(null)
    const [variables, setVariables] = useState([])
    const [showModal, setShowModal] = useState(null) // 'project' | 'variable' | null
    const [visibleValues, setVisibleValues] = useState(new Set())

    useEffect(() => {
        loadProjects()
    }, [])

    useEffect(() => {
        if (activeProject) loadVariables(activeProject.id)
    }, [activeProject])

    async function loadProjects() {
        const data = await api('/api/projects')
        setProjects(data)
    }

    async function loadVariables(pid) {
        const data = await api(`/api/projects/${pid}/variables`)
        setVariables(data)
        setVisibleValues(new Set())
    }

    async function createProject(name, description) {
        await api('/api/projects', {
            method: 'POST',
            body: JSON.stringify({ name, description })
        })
        loadProjects()
    }

    async function deleteProject(pid) {
        if (!confirm('delete this project?')) return
        await api(`/api/projects/${pid}`, { method: 'DELETE' })
        setActiveProject(null)
        setVariables([])
        loadProjects()
    }

    async function addVariable(key, value) {
        await api(`/api/projects/${activeProject.id}/variables`, {
            method: 'POST',
            body: JSON.stringify({ key, value })
        })
        loadVariables(activeProject.id)
    }

    async function deleteVariable(vid) {
        await api(`/api/variables/${vid}`, { method: 'DELETE' })
        loadVariables(activeProject.id)
    }

    function toggleVisibility(vid) {
        const next = new Set(visibleValues)
        if (next.has(vid)) next.delete(vid)
        else next.add(vid)
        setVisibleValues(next)
    }

    async function exportEnv() {
        const res = await fetch(`/api/projects/${activeProject.id}/export`)
        const text = await res.text()
        const blob = new Blob([text], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${activeProject.name}.env`
        a.click()
    }

    return (
        <div className="app">
            <aside className="sidebar">
                <h1>envault</h1>
                <button className="btn btn-primary" style={{marginBottom: 12, width: '100%'}}
                    onClick={() => setShowModal('project')}>+ new project</button>
                <div className="project-list">
                    {projects.map(p => (
                        <div key={p.id}
                            className={`project-item ${activeProject?.id === p.id ? 'active' : ''}`}
                            onClick={() => setActiveProject(p)}>
                            {p.name}
                            <span className="count">{p.var_count}</span>
                        </div>
                    ))}
                </div>
            </aside>

            <div className="main-content">
                {activeProject ? (
                    <>
                        <div className="header-row">
                            <h2>{activeProject.name}</h2>
                            <div style={{display: 'flex', gap: 8}}>
                                <button className="btn btn-ghost" onClick={exportEnv}>export .env</button>
                                <button className="btn btn-primary" onClick={() => setShowModal('variable')}>+ add variable</button>
                                <button className="btn btn-danger" onClick={() => deleteProject(activeProject.id)}>delete</button>
                            </div>
                        </div>
                        {variables.length > 0 ? (
                            <table className="var-table">
                                <thead>
                                    <tr><th>Key</th><th>Value</th><th>Updated</th><th></th></tr>
                                </thead>
                                <tbody>
                                    {variables.map(v => (
                                        <tr key={v.id}>
                                            <td className="key">{v.key}</td>
                                            <td className={`value ${visibleValues.has(v.id) ? 'visible' : ''}`}>
                                                {visibleValues.has(v.id) ? v.value : '••••••••'}
                                            </td>
                                            <td style={{color: '#52525b', fontSize: 12}}>
                                                {new Date(v.updated_at).toLocaleDateString()}
                                            </td>
                                            <td className="actions">
                                                <button onClick={() => toggleVisibility(v.id)}>
                                                    {visibleValues.has(v.id) ? 'hide' : 'show'}
                                                </button>
                                                <button onClick={() => deleteVariable(v.id)}>delete</button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div className="empty-state">no variables yet. click "+ add variable" to start.</div>
                        )}
                    </>
                ) : (
                    <div className="empty-state">select a project from the sidebar</div>
                )}
            </div>

            {showModal === 'project' && (
                <ModalForm
                    title="New Project"
                    fields={[{name: 'name', placeholder: 'project name'}, {name: 'description', placeholder: 'description (optional)'}]}
                    onSubmit={(data) => { createProject(data.name, data.description); setShowModal(null) }}
                    onClose={() => setShowModal(null)}
                />
            )}
            {showModal === 'variable' && (
                <ModalForm
                    title="Add Variable"
                    fields={[{name: 'key', placeholder: 'KEY_NAME'}, {name: 'value', placeholder: 'value'}]}
                    onSubmit={(data) => { addVariable(data.key, data.value); setShowModal(null) }}
                    onClose={() => setShowModal(null)}
                />
            )}
        </div>
    )
}

function ModalForm({ title, fields, onSubmit, onClose }) {
    const [values, setValues] = useState({})

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!values[fields[0].name]) return
        onSubmit(values)
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <form className="modal" onClick={e => e.stopPropagation()} onSubmit={handleSubmit}>
                <h3>{title}</h3>
                {fields.map(f => (
                    <input key={f.name}
                        placeholder={f.placeholder}
                        value={values[f.name] || ''}
                        onChange={e => setValues({...values, [f.name]: e.target.value})}
                    />
                ))}
                <div className="modal-actions">
                    <button type="button" className="btn btn-ghost" onClick={onClose}>cancel</button>
                    <button type="submit" className="btn btn-primary">save</button>
                </div>
            </form>
        </div>
    )
}
